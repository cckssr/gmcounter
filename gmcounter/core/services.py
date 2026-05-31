# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import MeasurementSession, MeasurementPoint, DeviceSettings
from .utils import (
    create_dropbox_foldername,
    sanitize_subterm_for_folder,
    create_group_name,
)

_log = logging.getLogger(__name__)


class MeasurementService:
    """Lifecycle management for a single MeasurementSession."""

    def __init__(self) -> None:
        self.current_session: Optional[MeasurementSession] = None
        self._unsaved = False

    def start_session(
        self,
        radioactive_sample: str = "",
        subterm: str = "",
        group: str = "",
    ) -> MeasurementSession:
        self.current_session = MeasurementSession(
            points=[],
            start_time=datetime.now(),
            radioactive_sample=radioactive_sample,
            subterm=subterm,
            group=group,
        )
        self._unsaved = False
        _log.info("New measurement session started")
        return self.current_session

    def stop_session(self) -> Optional[MeasurementSession]:
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self._unsaved = True
            _log.info(
                "Measurement session stopped with %d points",
                self.current_session.count,
            )
        return self.current_session

    def add_point(self, index: int, value: float, timestamp: str) -> None:
        if not self.current_session:
            _log.warning("No active session — creating one")
            self.start_session()
        point = MeasurementPoint(index=index, value=value, timestamp=timestamp)
        self.current_session.points.append(point)  # type: ignore[union-attr]
        self._unsaved = True

    def clear_session(self) -> None:
        self.current_session = None
        self._unsaved = False
        _log.info("Measurement session cleared")

    def has_unsaved_data(self) -> bool:
        return self._unsaved and self.current_session is not None

    def mark_saved(self) -> None:
        self._unsaved = False

    def get_data_as_list(self) -> list[list[str]]:
        if not self.current_session:
            return []
        data = [["Index", "Value (µs)", "Timestamp"]]
        for p in self.current_session.points:
            data.append([str(p.index), str(p.value), p.timestamp])
        return data


class SaveService:
    """Write measurement data to CSV + _MD.json sidecar on disk.

    No Qt imports — byte-level I/O only.
    """

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        tk_designation: str = "TKXX",
    ) -> None:
        if base_dir is None:
            base_dir = Path.home() / "Documents" / "GMCounter"
        if isinstance(base_dir, str):
            base_dir = Path.home() / "Documents" / base_dir

        self.base_dir = Path(base_dir)
        self.tk_designation = tk_designation
        self.index = 0
        self._backup_counter = 0
        self._unsaved = False

        _log.info("SaveService base dir: %s", self.base_dir)
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            _log.error("Failed to create base dir %s: %s", self.base_dir, exc)

    # ------------------------------------------------------------------
    # Unsaved-state tracking

    def has_unsaved(self) -> bool:
        return self._unsaved

    def mark_saved(self) -> None:
        self._unsaved = False

    def mark_unsaved(self) -> None:
        self._unsaved = True

    # ------------------------------------------------------------------
    # Filename / path composition

    def generate_filename(
        self,
        rad_sample: str,
        group_letter: str,
        subterm: str = "",
        suffix: str = "",
        extension: str = ".csv",
    ) -> str:
        """Compose a Dropbox-compatible relative path for saving."""
        if not rad_sample:
            _log.error("Radioactive sample name cannot be empty")
            return ""
        if not group_letter:
            _log.error("Group letter cannot be empty")
            return ""

        timestamp = datetime.now().strftime("%Y_%m_%d")
        if suffix and not suffix.startswith("-"):
            suffix = "-" + suffix
        self.index += 1

        sanitized = (
            sanitize_subterm_for_folder(subterm, max_length=20) if subterm else ""
        )
        folder = create_dropbox_foldername(
            group_letter, self.tk_designation, sanitized or None
        )
        filename = f"{timestamp}-{self.index:02d}-{rad_sample}{suffix}{extension}"
        return f"{folder}/{filename}"

    # ------------------------------------------------------------------
    # Metadata builder

    def create_metadata(
        self,
        start: datetime,
        end: datetime,
        group: str,
        sample: str,
        subterm: str = "",
        extra: Optional[dict] = None,
    ) -> dict:
        """Build a Dublin-Core-style metadata dict."""
        group_name = (
            group if group and len(str(group)) > 1 else create_group_name(group)
        )
        meta = {
            "dc:date": start.strftime("%Y-%m-%d"),
            "dc:creator": group_name,
            "dc:title": sample,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "radioactive_sample": sample,
            "subgroup": subterm or "",
        }
        if extra:
            meta.update(extra)
        return meta

    # ------------------------------------------------------------------
    # Writers

    def save_measurement(
        self,
        file_name: str,
        data: list[list[str]],
        metadata: dict,
    ) -> Path:
        """Write CSV rows + sidecar _MD.json. Returns the CSV path."""
        csv_path = Path(file_name)
        if not csv_path.is_absolute():
            csv_path = self.base_dir / csv_path

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(data)
            meta_path = csv_path.parent / (csv_path.stem + "_MD.json")
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(metadata, fh, indent=2)
            _log.info("Saved measurement to %s", csv_path)
        except Exception as exc:
            _log.error("Failed to save measurement: %s", exc)
        return csv_path

    def auto_save(
        self,
        rad_sample: str,
        group_letter: str,
        data: list[list[str]],
        start: datetime,
        end: datetime,
        subterm: str = "",
        suffix: str = "",
    ) -> Optional[Path]:
        if not data:
            _log.error("No data provided for auto save")
            return None
        file_name = self.generate_filename(rad_sample, group_letter, subterm, suffix)
        meta = self.create_metadata(start, end, group_letter, rad_sample, subterm)
        return self.save_measurement(file_name, data, meta)

    def auto_backup(
        self,
        data: list[list[str]],
        start: datetime,
        rad_sample: str = "unknown",
        group_letter: str = "unknown",
        subterm: str = "",
        extra_metadata: Optional[dict] = None,
    ) -> Optional[Path]:
        """Incremental backup — call every 30 s during measurement."""
        if not data or len(data) <= 1:
            return None

        try:
            backup_dir = self.base_dir / ".backup"
            backup_dir.mkdir(parents=True, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._backup_counter += 1
            bk_path = backup_dir / f"backup_{ts}_{self._backup_counter:03d}.csv"

            meta = self.create_metadata(
                start,
                datetime.now(),
                group_letter,
                rad_sample,
                subterm,
                extra=extra_metadata,
            )
            with open(bk_path, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(data)
            meta_path = bk_path.parent / (bk_path.stem + "_MD.json")
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(meta, fh, indent=2)

            _log.debug("Auto-backup: %s (%d points)", bk_path, len(data) - 1)
            self.cleanup_old_backups(backup_dir)
            return bk_path

        except Exception as exc:
            _log.error("Failed to create auto-backup: %s", exc)
            return None

    def cleanup_old_backups(self, backup_dir: Path, max_age_hours: int = 24) -> None:
        """Remove backup files older than max_age_hours."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        try:
            for f in backup_dir.glob("backup_*.csv"):
                if f.stat().st_mtime < cutoff.timestamp():
                    f.unlink(missing_ok=True)
                    (f.parent / (f.stem + "_MD.json")).unlink(missing_ok=True)
                    _log.debug("Deleted old backup: %s", f)
        except Exception as exc:
            _log.info("Error cleaning up old backups: %s", exc)


class MeasurementStateService:
    """Track whether a measurement is currently active.

    Pure domain state — no I/O, no hardware references.
    """

    def __init__(self) -> None:
        self._measurement_active = False

    @property
    def measurement_active(self) -> bool:
        return self._measurement_active

    def start_measurement(self) -> None:
        self._measurement_active = True
        _log.debug("MeasurementStateService: started")

    def stop_measurement(self) -> None:
        self._measurement_active = False
        _log.debug("MeasurementStateService: stopped")

    def reset(self) -> None:
        self._measurement_active = False
        _log.debug("MeasurementStateService: reset")


class DeviceControlService:
    """Apply DeviceSettings to a connected device.

    Takes a device reference at construction time; callers supply the
    infrastructure GMCounter (duck-typed via the command set).
    """

    def __init__(self, device) -> None:
        self.device = device

    def apply_settings(self, settings: DeviceSettings) -> bool:
        import time as _time

        try:
            _log.debug(
                "Applying settings: repeat=%s counting_time=%d voltage=%d",
                settings.repeat,
                settings.counting_time,
                settings.voltage,
            )
            self.device.set_repeat(settings.repeat)
            self.device.set_stream(4 if settings.auto_query else 1)
            self.device.set_counting_time(settings.counting_time)
            self.device.set_voltage(settings.voltage)
            _time.sleep(0.2)
            return True
        except Exception as exc:
            _log.error("Error applying settings: %s", exc)
            return False
