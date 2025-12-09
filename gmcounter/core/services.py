"""Business logic services - NO Qt dependencies allowed."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from .models import MeasurementSession, MeasurementPoint, DeviceSettings
from .utils import (
    create_dropbox_foldername,
    sanitize_subterm_for_folder,
    create_group_name,
)
from ..infrastructure.logging import Debug


class MeasurementService:
    """Service for managing measurement sessions."""

    def __init__(self):
        self.current_session: Optional[MeasurementSession] = None
        self._unsaved = False

    def start_session(
        self, radioactive_sample: str = "", subterm: str = "", group: str = ""
    ) -> MeasurementSession:
        """Start a new measurement session."""
        self.current_session = MeasurementSession(
            points=[],
            start_time=datetime.now(),
            radioactive_sample=radioactive_sample,
            subterm=subterm,
            group=group,
        )
        self._unsaved = False
        Debug.info("New measurement session started")
        return self.current_session

    def stop_session(self) -> Optional[MeasurementSession]:
        """Stop the current measurement session."""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self._unsaved = True
            Debug.info(
                f"Measurement session stopped with {self.current_session.count} points"
            )
        return self.current_session

    def add_point(self, index: int, value: float, timestamp: str):
        """Add a measurement point to the current session."""
        if not self.current_session:
            Debug.warning("No active session - creating one")
            self.start_session()

        point = MeasurementPoint(index=index, value=value, timestamp=timestamp)
        self.current_session.points.append(point)
        self._unsaved = True

    def clear_session(self):
        """Clear the current session."""
        self.current_session = None
        self._unsaved = False
        Debug.info("Measurement session cleared")

    def has_unsaved_data(self) -> bool:
        """Check if there is unsaved data."""
        return self._unsaved and self.current_session is not None

    def mark_saved(self):
        """Mark current data as saved."""
        self._unsaved = False

    def get_data_as_list(self) -> List[List[str]]:
        """Export current session data as list of rows for CSV."""
        if not self.current_session:
            return []

        data = [["Index", "Value (µs)", "Timestamp"]]
        for point in self.current_session.points:
            data.append([str(point.index), str(point.value), point.timestamp])
        return data


class SaveService:
    """Service for saving measurement data - NO Qt dependencies."""

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        tk_designation: str = "TKXX",
    ):
        if base_dir is None:
            base_dir = Path.home() / "Documents" / "GMCounter"
        if isinstance(base_dir, str):
            base_dir = Path.home() / "Documents" / base_dir

        self.base_dir = Path(base_dir)
        self.tk_designation = tk_designation
        self.index = 0
        self._backup_counter = 0  # Counter for backup file numbering
        self._unsaved = False  # Track unsaved data state

        Debug.info(f"Using base directory for saving: {self.base_dir}")
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            Debug.error(f"Failed to create base directory {self.base_dir}: {exc}")

    def has_unsaved(self) -> bool:
        """Check if there is unsaved data.

        Returns:
            bool: True if there is unsaved data, False otherwise.
        """
        return self._unsaved

    def mark_saved(self):
        """Mark current data as saved."""
        self._unsaved = False

    def mark_unsaved(self):
        """Mark current data as unsaved."""
        self._unsaved = True

    def generate_filename(
        self,
        rad_sample: str,
        group_letter: str,
        subterm: str = "",
        suffix: str = "",
        extension: str = ".csv",
    ) -> str:
        """Generate a standard file name with Dropbox-compatible folder path.

        The folder follows the Dropbox naming convention:
        <Day><Group><TK>-<Subterm> (e.g., "MoATK08-Mueller")

        Args:
            rad_sample: Sample identifier to include in the file name.
            group_letter: Group letter to include in the file name.
            subterm: Subgroup term to include in folder name.
            suffix: Optional suffix (``-run1`` etc.).
            extension: File extension including leading dot.

        Returns:
            Generated file name with folder path.
        """
        if not rad_sample:
            Debug.error("Radioactive sample name cannot be empty.")
            return ""
        if not group_letter:
            Debug.error("Group letter cannot be empty.")
            return ""

        timestamp = datetime.now().strftime("%Y_%m_%d")
        if suffix and not suffix.startswith("-"):
            suffix = "-" + suffix
        self.index += 1

        # Create Dropbox-compatible folder name
        sanitized_subterm = ""
        if subterm:
            sanitized_subterm = sanitize_subterm_for_folder(subterm, max_length=20)
        folder_name = create_dropbox_foldername(
            group_letter, self.tk_designation, sanitized_subterm
        )

        filename = f"{timestamp}-{self.index:02d}-{rad_sample}{suffix}{extension}"
        return f"{folder_name}/{filename}"

    def create_metadata(
        self,
        start: datetime,
        end: datetime,
        group: str,
        sample: str,
        subterm: str = "",
        extra: dict | None = None,
    ) -> dict:
        """Create metadata dictionary following basic Dublin Core fields."""
        group_name = (
            group if group and len(str(group)) > 1 else create_group_name(group)
        )
        metadata = {
            "dc:date": start.strftime("%Y-%m-%d"),
            "dc:creator": group_name,
            "dc:title": sample,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "radioactive_sample": sample,
            "subgroup": subterm if subterm else "",
        }
        if extra:
            metadata.update(extra)
        return metadata

    def save_measurement(
        self, file_name: str, data: List[List[str]], metadata: dict
    ) -> Path:
        """Save CSV data and accompanying metadata.

        file_name may be an absolute path or a simple file name. Relative
        names are stored below base_dir. If file_name contains a subfolder,
        it will be created automatically.
        """
        csv_path = Path(file_name)
        if not csv_path.is_absolute():
            csv_path = self.base_dir / csv_path

        # Create parent directory if it doesn't exist
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csv_f:
                writer = csv.writer(csv_f)
                writer.writerows(data)
            # Metadata als JSON speichern
            metadata_path = csv_path.parent / (csv_path.stem + "_MD.json")
            with open(metadata_path, "w", encoding="utf-8") as js_f:
                json.dump(metadata, js_f, indent=2)
            Debug.info(f"Saved measurement to {csv_path}")
        except Exception as exc:
            Debug.error(f"Failed to save measurement: {exc}", exc_info=exc)
        return csv_path

    def auto_save(
        self,
        rad_sample: str,
        group_letter: str,
        data: List[List[str]],
        start: datetime,
        end: datetime,
        subterm: str = "",
        suffix: str = "",
    ) -> Optional[Path]:
        """Automatically save data using a generated file name."""
        if not data:
            Debug.error("No data provided for auto save")
            return None

        file_name = self.generate_filename(rad_sample, group_letter, subterm, suffix)
        meta = self.create_metadata(start, end, group_letter, rad_sample, subterm)
        return self.save_measurement(file_name, data, meta)

    def auto_backup(
        self,
        data: List[List[str]],
        start: datetime,
        rad_sample: str = "unknown",
        group_letter: str = "unknown",
        subterm: str = "",
        extra_metadata: dict | None = None,
    ) -> Optional[Path]:
        """Automatically backup measurement data to temporary file.

        This method is designed to be called periodically during a measurement
        to create incremental backups that can be recovered in case of crashes.

        Args:
            data: Measurement data to backup (list of rows including header)
            start: Measurement start time
            rad_sample: Radioactive sample identifier (default: "unknown")
            group_letter: Group letter (default: "unknown")
            subterm: Subgroup term
            extra_metadata: Additional metadata to include (e.g., device info, GUI version)

        Returns:
            Path to backup file or None if backup failed
        """
        if not data or len(data) <= 1:  # Only header present
            return None

        try:
            # Create backup directory
            backup_dir = self.base_dir / ".backup"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create unique backup filename with timestamp and counter
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._backup_counter += 1
            backup_filename = f"backup_{timestamp}_{self._backup_counter:03d}.csv"
            backup_path = backup_dir / backup_filename

            # Create metadata
            metadata = self.create_metadata(
                start,
                datetime.now(),  # Current time as end
                group_letter,
                rad_sample,
                subterm,
                extra=extra_metadata,
            )

            # Save CSV
            with open(backup_path, "w", newline="", encoding="utf-8") as csv_f:
                writer = csv.writer(csv_f)
                writer.writerows(data)

            # Save metadata
            metadata_path = backup_path.parent / (backup_path.stem + "_MD.json")
            with open(metadata_path, "w", encoding="utf-8") as js_f:
                json.dump(metadata, js_f, indent=2)

            Debug.debug(
                f"Auto-backup created: {backup_path} ({len(data)-1} data points)"
            )

            # Cleanup old backups
            self.cleanup_old_backups(backup_dir)

            return backup_path

        except Exception as exc:
            Debug.error(f"Failed to create auto-backup: {exc}", exc_info=exc)
            return None

    def cleanup_old_backups(self, backup_dir: Path, max_age_hours: int = 24):
        """Remove backup files older than specified age.

        Args:
            backup_dir: Directory containing backup files
            max_age_hours: Maximum age of backups in hours (default: 24)
        """
        try:
            from datetime import timedelta

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            for file in backup_dir.glob("backup_*.csv"):
                if file.stat().st_mtime < cutoff_time.timestamp():
                    file.unlink()
                    # Delete associated metadata
                    metadata_file = file.parent / (file.stem + "_MD.json")
                    if metadata_file.exists():
                        metadata_file.unlink()
                    Debug.debug(f"Deleted old backup: {file}")
        except Exception as exc:
            Debug.info(f"Error cleaning up old backups: {exc}")


class DeviceControlService:
    """Service for controlling GM Counter device - NO Qt dependencies."""

    def __init__(self, device_manager):
        """Initialize with device manager reference.

        Args:
            device_manager: The device manager (from infrastructure layer)
        """
        self.device_manager = device_manager
        self.gm_counter = device_manager.device if device_manager else None
        self.measurement_active = False

    def apply_settings(self, settings: DeviceSettings) -> bool:
        """Apply settings to the GM counter.

        Args:
            settings: DeviceSettings instance

        Returns:
            True if successful, False otherwise
        """
        import time

        try:
            Debug.debug(
                f"Applying settings: repeat={settings.repeat}, "
                f"auto_query={settings.auto_query}, "
                f"counting_time={settings.counting_time}, "
                f"voltage={settings.voltage}"
            )

            # Apply to GM counter
            self.gm_counter.set_repeat(settings.repeat)
            self.gm_counter.set_stream(4 if settings.auto_query else 1)
            self.gm_counter.set_counting_time(settings.counting_time)
            self.gm_counter.set_voltage(settings.voltage)

            time.sleep(0.2)  # Wait for settings to apply

            Debug.debug("Settings applied successfully.")
            return True

        except Exception as e:
            Debug.error(f"Error applying settings: {e}", exc_info=e)
            return False

    def get_current_settings(self) -> Optional[dict]:
        """Retrieve current settings from the GM counter.

        Returns:
            Dictionary with current settings or None on error
        """
        try:
            data = self.gm_counter.get_data()
            if not data:
                Debug.error("No data received from GM counter.")
                return None

            # Check if measurement is active (started from hardware)
            if not self.measurement_active and data.get("progress", 0) > 0:
                self.measurement_active = True
                Debug.info("Measurement started.")
            return data

        except Exception as e:
            Debug.error(f"Error retrieving settings: {e}", exc_info=e)
            return None

    def reset_settings(self) -> bool:
        """Reset the GM counter settings to default values."""
        import time

        try:
            # Reset to default values
            self.gm_counter.set_repeat(False)
            self.gm_counter.set_stream(0)  # No streaming
            self.gm_counter.set_counting_time(0)  # Unlimited
            self.gm_counter.set_voltage(500)  # Default voltage

            time.sleep(0.2)  # Wait for reset to apply

            Debug.debug("Settings reset successfully.")
            return True

        except Exception as e:
            Debug.error(f"Error resetting settings: {e}", exc_info=e)
            return False


class MeasurementStateService:
    """Service for managing measurement state - domain logic only.

    This service encapsulates the domain state of whether a measurement
    is active, separate from the hardware/infrastructure layer.
    """

    def __init__(self):
        """Initialize the measurement state service."""
        self._measurement_active = False

    @property
    def measurement_active(self) -> bool:
        """Check if measurement is currently active."""
        return self._measurement_active

    def start_measurement(self) -> None:
        """Mark measurement as started."""
        self._measurement_active = True
        Debug.debug("MeasurementStateService: measurement started")

    def stop_measurement(self) -> None:
        """Mark measurement as stopped."""
        self._measurement_active = False
        Debug.debug("MeasurementStateService: measurement stopped")

    def reset(self) -> None:
        """Reset measurement state."""
        self._measurement_active = False
        Debug.debug("MeasurementStateService: state reset")
