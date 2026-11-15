# Layer: infrastructure — generic TabExport byte-level writer.
# No per-experiment code lives here; experiments speak TabExport.

import csv
import hashlib
import json
import logging
from pathlib import Path

from ..core.export import TabExport, compose_save_path

_log = logging.getLogger(__name__)


def write_export(export: TabExport, csv_path: Path) -> Path:
    """Write *export* to *csv_path* + adjacent *_MD.json* sidecar.

    Low-level helper — does no path composition. Callers that need
    auto-generated paths should use SaveService.save() instead.
    """
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(export.columns)
        writer.writerows(export.rows)

    metadata = dict(export.metadata)
    metadata["file"] = {
        "name": csv_path.name,
        "rows": len(export.rows),
        "columns": list(export.columns),
        "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    _write_metadata(metadata_path(csv_path), metadata)

    _log.info("Saved export to %s", csv_path)
    return csv_path


def session_folder_path(csv_path: Path) -> Path:
    """Path for *csv_path* inside a new folder named after the file.

    A measurement series (distance or voltage sweep, interval run) writes a summary and one
    file per point; they belong together in ``<chosen dir>/<chosen stem>/``. A folder that
    already holds files is never reused (``<stem>_2``, ``<stem>_3``, ...), so an earlier
    series is not mixed with or overwritten by a new one. Nothing is created here.
    """
    csv_path = Path(csv_path)
    folder = csv_path.parent / csv_path.stem
    counter = 2
    while folder.exists() and any(folder.iterdir()):
        folder = csv_path.parent / f"{csv_path.stem}_{counter}"
        counter += 1
    return folder / csv_path.name


def metadata_path(csv_path: Path) -> Path:
    """Path of the ``_MD.json`` sidecar that belongs to *csv_path*."""
    csv_path = Path(csv_path)
    return csv_path.parent / (csv_path.stem + "_MD.json")


def update_metadata(csv_path: Path, fields: dict) -> None:
    """Add or replace top-level *fields* in the sidecar of an already written CSV."""
    path = metadata_path(csv_path)
    with open(path, encoding="utf-8") as fh:
        metadata = json.load(fh)
    metadata.update(fields)
    _write_metadata(path, metadata)


def _write_metadata(path: Path, metadata: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False)


class SaveService:
    """Write a TabExport to CSV + sidecar _MD.json.

    Wraps core.export.compose_save_path with actual filesystem I/O.
    Every experiment that implements PlotTabBase.export() -> TabExport
    gets the same atomic write, sidecar metadata, and directory creation.
    """

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self._index = 0
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            _log.error("Failed to create base dir %s: %s", self.base_dir, exc)

    def save(
        self,
        export: TabExport,
        suffix: str = "",
    ) -> Path:
        """Write *export* to an auto-composed path and return it."""
        self._index += 1
        csv_path = compose_save_path(
            export, self.base_dir, index=self._index, suffix=suffix
        )
        try:
            write_export(export, csv_path)
        except Exception as exc:
            _log.error("Failed to save export: %s", exc)
        return csv_path
