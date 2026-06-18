"""File dialog utilities for UI layer."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QWidget, QFileDialog

from ...core.services import SaveState
from ...core.export import TabExport
from ...infrastructure.save_service import write_export
from ...infrastructure.logging import Debug
from . import dialogs as MessageHelper


class FileDialogManager:
    """Handles save-file dialogs (UI layer only).

    State (base_dir, unsaved flag) is held in SaveState.
    Actual I/O is delegated to write_export.
    """

    def __init__(self, save_state: SaveState) -> None:
        self.save_state = save_state

    def manual_save_export(
        self,
        parent: QWidget,
        export: TabExport,
        rad_sample: str,
        group_letter: str,
        subterm: str = "",
    ) -> Optional[Path]:
        """Open a save dialog and write a TabExport to CSV + sidecar.

        Returns the saved path, or None if the user cancelled.
        """
        if not export or not export.rows:
            MessageHelper.show_warning(
                parent, "Keine Messdaten zum Speichern.", "Warnung"
            )
            return None
        if not rad_sample or not group_letter:
            MessageHelper.show_warning(
                parent,
                "Bitte Probe und Gruppe auswählen.",
                "Warnung",
            )
            return None

        if export.filename_tokens:
            suggested_folder = self.save_state.base_dir / Path(*export.filename_tokens)
        else:
            suggested_folder = self.save_state.base_dir
        suggested_folder.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Messung speichern",
            str(suggested_folder),
            "CSV-Dateien (*.csv);;Alle Dateien (*)",
            "CSV-Dateien (*.csv)",
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        try:
            csv_path = write_export(export, Path(file_path))
            Debug.info(f"Export saved via file dialog: {csv_path}")
            return csv_path
        except Exception as exc:
            Debug.error(f"Failed to save export: {exc}")
            MessageHelper.show_error(parent, f"Fehler beim Speichern: {exc}", "Fehler")
            return None
