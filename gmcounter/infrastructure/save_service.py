# Layer: infrastructure — generic TabExport byte-level writer.
# No per-experiment code lives here; experiments speak TabExport.
"""Generic TabExport filesystem writer.

:func:`write_export` is the low-level function that writes one CSV and its
``_MD.json`` sidecar to a caller-supplied path.  :class:`SaveService` wraps
it with auto-index path composition for the common "save to base directory"
workflow.
"""

import csv
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

    meta_path = csv_path.parent / (csv_path.stem + "_MD.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(export.metadata, fh, indent=2)

    _log.info("Saved export to %s", csv_path)
    return csv_path


class SaveService:
    """Write a TabExport to CSV + sidecar _MD.json.

    Wraps core.export.compose_save_path with actual filesystem I/O.
    Every experiment that implements PlotTabBase.export() -> TabExport
    gets the same atomic write, sidecar metadata, and directory creation.
    """

    def __init__(self, base_dir: Path | str) -> None:
        """Create the service and ensure *base_dir* exists.

        Args:
            base_dir: Root directory for all exports managed by this service.
        """
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
