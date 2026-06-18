# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
#
# TabExport (§7): experiment tabs declare what to save; the generic
# infrastructure.save_service does the byte-level I/O.
"""Tab export schema and path composition (§7).

Experiment tabs produce a :class:`TabExport`; the infrastructure layer
handles all I/O.  Nothing in this module touches the filesystem.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import MeasurementSession
from .utils import (
    create_dropbox_foldername,
    create_group_name,
    sanitize_subterm_for_folder,
)

_log = logging.getLogger(__name__)


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


def build_gm_tab_export(
    session: MeasurementSession,
    *,
    tk_designation: str = "TK00",
    extra_metadata: Optional[dict] = None,
) -> TabExport:
    """Build a TabExport from a completed GMTiming MeasurementSession.

    This is pure composition — no I/O.
    """
    columns = ["Index", "Value (µs)", "Time"]
    rows = [[str(p.index), str(p.value), p.timestamp] for p in session.points]

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
    if extra_metadata:
        metadata.update(extra_metadata)

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
