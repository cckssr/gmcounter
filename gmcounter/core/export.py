# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
#
# TabExport (§7): experiment tabs declare what to save; the generic
# infrastructure.save_service does the byte-level I/O.

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import MeasurementSession
from .utils import (
    calculate_statistics,
    create_dropbox_foldername,
    create_group_name,
    sanitize_subterm_for_folder,
)

_log = logging.getLogger(__name__)

# One raw-data format for every measurement file (single run, sweep point, interval).
# "Duration (s)" is the device time the whole file covers; it repeats in every row so a
# file stays self-describing when it is read without its sidecar.
RAW_COLUMNS: tuple[str, ...] = ("Index", "Value (µs)", "Time", "Duration (s)")

# Version of the metadata sidecar layout (_MD.json); bump when keys change meaning.
METADATA_SCHEMA_VERSION = 2


@dataclass
class TabExport:
    """Everything an experiment tab needs to export one measurement.

    Infrastructure's save_service consumes this and handles file I/O.
    """

    filename_hint: str  # e.g. "gm_timing"
    columns: list[str]  # CSV header row
    rows: list[list[str]]  # already-stringified data rows
    metadata: dict  # Dublin-Core-style sidecar dict
    filename_tokens: list[str] = field(default_factory=list)


def format_duration(duration_s: float) -> str:
    """Duration as written into the CSV: seconds with millisecond resolution."""
    return f"{duration_s:.3f}"


def raw_rows(points, duration_s: float) -> list[list[str]]:
    """Stringify ``(index, value_us, timestamp)`` triples in the shared raw-data format.

    *duration_s* is the device time covered by the whole file.
    """
    duration = format_duration(duration_s)
    return [
        [str(index), str(value), str(stamp), duration] for index, value, stamp in points
    ]


def merge_missing(target: dict, extra: dict) -> dict:
    """Add the keys of *extra* that *target* does not have yet; return *target*.

    Per-measurement values (set when a point was taken) win over session-wide ones.
    """
    for key, value in extra.items():
        target.setdefault(key, value)
    return target


def apply_sample_metadata(metadata: dict, sample: dict) -> dict:
    """Write the detector and sample distance of the sample panel into *metadata*.

    Existing values are replaced, and a value the panel leaves empty (no detector, distance 0)
    is removed, so the sidecar always shows what was entered. Returns *metadata*.
    """
    distance = float(sample.get("distance_cm", 0.0))
    settings = metadata.get("settings")
    if not isinstance(settings, dict):
        settings = metadata["settings"] = {}

    detector = sample.get("detector")
    if detector:
        metadata["detector_code"] = detector
    else:
        metadata.pop("detector_code", None)

    if distance > 0.0:
        settings["sample_distance_cm"] = distance
        metadata["sample_distance_cm"] = distance
    else:
        settings.pop("sample_distance_cm", None)
        metadata.pop("sample_distance_cm", None)
    return metadata


def build_run_info(
    *,
    experiment: str,
    sample: dict,
    device_settings: dict,
    voltage_readback_v: float,
    target_duration_s: int,
    device_info: dict,
    port: str = "",
    baudrate: int = 0,
    gui_version: str = "",
) -> dict:
    """Snapshot of everything that defines one measurement run, taken when it starts.

    *sample* is the sample panel metadata, *device_settings* the device panel settings.
    Pure composition: the keys land unchanged in the ``_MD.json`` sidecar.
    """
    settings: dict = {
        "gm_voltage_set_v": int(device_settings.get("voltage", 0)),
        "gm_voltage_readback_v": float(voltage_readback_v),
        "target_duration_s": int(target_duration_s),  # 0 = until stopped
        "count_mode": "repeat" if device_settings.get("repeat") else "single",
        "query_mode": "auto" if device_settings.get("auto_query") else "manual",
    }
    device: dict = {}
    for source, target in (
        ("version", "firmware_version"),
        ("openbis", "openbis_code"),
        ("copyright", "copyright"),
    ):
        value = device_info.get(source, "")
        if value and value != "unknown":
            device[target] = value
    if port and port != "None":
        device["port"] = port
    if baudrate:
        device["baudrate"] = int(baudrate)

    info: dict = {
        "schema_version": METADATA_SCHEMA_VERSION,
        "experiment": experiment,
        "gui_version": gui_version,
        "settings": settings,
        "device": device,
    }
    apply_sample_metadata(info, sample)
    # Legacy flat keys, kept so existing readers of the sidecar keep working.
    if device.get("openbis_code"):
        info["counter_openbis_code"] = device["openbis_code"]
    if device.get("firmware_version"):
        info["counter_firmware_version"] = device["firmware_version"]
    return info


def build_gm_tab_export(
    session: MeasurementSession,
    *,
    tk_designation: str = "TK00",
    extra_metadata: Optional[dict] = None,
) -> TabExport:
    """Build a TabExport from a completed GMTiming MeasurementSession.

    This is pure composition — no I/O.
    """
    start = session.start_time or datetime.now()
    end = session.end_time or datetime.now()

    group_name = (
        session.group
        if session.group and len(str(session.group)) > 1
        else create_group_name(session.group)
    )

    metadata: dict = {
        "dc:date": start.strftime("%Y-%m-%d"),
        "dc:creator": group_name,
        "dc:title": session.radioactive_sample,
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "radioactive_sample": session.radioactive_sample,
        "subgroup": session.subterm or "",
    }
    values = [p.value for p in session.points]
    stats = calculate_statistics(values)
    duration_s = session.duration_seconds
    # The first event after INIT only sets the time reference and has no row of its own
    # (firmware: gmProcessAcquisition), so n rows mean n + 1 events. The live display and
    # the sweep summaries count the same way.
    events = session.count + 1 if session.count else 0
    metadata.update(
        {
            "schema_version": METADATA_SCHEMA_VERSION,
            "duration_s": round(duration_s, 3),
            "total_count": events,
            "rate_hz": round(events / duration_s, 3) if duration_s > 0 else 0.0,
            "statistics_us": {
                "min": stats["min"],
                "max": stats["max"],
                "mean": stats["mean"],
                "stdev": stats["std"],
            },
            "columns": list(RAW_COLUMNS),
        }
    )
    if extra_metadata:
        metadata.update(extra_metadata)
    # The device time is what the run was cut by; it is the duration the rate refers to.
    device_time_s = (metadata.get("timing") or {}).get("device_time_s")
    if device_time_s:
        metadata["duration_s"] = round(device_time_s, 3)
        metadata["rate_hz"] = round(events / device_time_s, 3)

    columns = list(RAW_COLUMNS)
    rows = raw_rows(
        ((p.index, p.value, p.timestamp) for p in session.points),
        metadata["duration_s"],
    )

    sanitized = sanitize_subterm_for_folder(session.subterm) if session.subterm else ""
    folder_token = create_dropbox_foldername(
        session.group, tk_designation, sanitized or None
    )

    return TabExport(
        filename_hint="gm_timing",
        columns=columns,
        rows=rows,
        metadata=metadata,
        filename_tokens=[folder_token] if folder_token else [],
    )


def compose_save_path(
    export: TabExport,
    base_dir: Path,
    *,
    index: int = 1,
    suffix: str = "",
) -> Path:
    """Compose the full save path for a TabExport without touching the filesystem.

    Returns an absolute path; the caller (save_service) creates directories and
    writes the bytes.
    """
    timestamp = datetime.now().strftime("%Y_%m_%d")
    if suffix and not suffix.startswith("-"):
        suffix = "-" + suffix

    stem = f"{timestamp}-{index:02d}-{export.filename_hint}{suffix}"

    if export.filename_tokens:
        folder = Path(*export.filename_tokens)
        return base_dir / folder / f"{stem}.csv"

    return base_dir / f"{stem}.csv"
