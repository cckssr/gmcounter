"""File dialog utilities for UI layer.

This module provides UI-specific file dialog functionality, separated from
the core business logic in SaveService.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import QWidget, QFileDialog

from ...core.utils import (
    sanitize_subterm_for_folder,
    create_dropbox_foldername,
)
from ...core.services import SaveService
from ...infrastructure.logging import Debug
from . import dialogs as MessageHelper


class FileDialogManager:
    """Manager for file dialogs (UI layer only).

    This class handles ONLY the UI interaction (file picker dialogs).
    All business logic and actual saving is delegated to SaveService (core layer).
    """

    def __init__(self, save_service: SaveService):
        """Initialize the file dialog manager.

        Args:
            save_service: The SaveService instance to use for actual file operations.
        """
        self.save_service = save_service

    def manual_save_measurement(
        self,
        parent: QWidget,
        rad_sample: str,
        group_letter: str,
        data: list[list[str]],
        start: datetime,
        end: datetime,
        subterm: str = "",
        extra_metadata: dict | None = None,
    ) -> Optional[Path]:
        """Open a save dialog and store the measurement.

        This method only handles the UI interaction (file picker).
        The actual saving is done by SaveService.

        Args:
            parent: Parent widget for the dialog.
            rad_sample: Radioactive sample identifier.
            group_letter: Group letter.
            data: Measurement data to save.
            start: Start time of the measurement.
            end: End time of the measurement.
            subterm: Subgroup term for folder naming.
            extra_metadata: Additional metadata to include.

        Returns:
            Path to the saved file, or None if cancelled.
        """
        if not data:
            MessageHelper.show_warning(
                parent,
                "Keine Messdaten zum Speichern vorhanden.",
                "Warnung",
            )
            return None

        if not rad_sample or not group_letter:
            MessageHelper.show_warning(
                parent,
                "Bitte wählen Sie eine radioaktive Probe und eine Gruppenzuordnung aus.",
                "Warnung",
            )
            return None

        # Create suggested folder path in dropbox style
        sanitized_subterm = ""
        if subterm:
            sanitized_subterm = sanitize_subterm_for_folder(subterm, max_length=20)

        folder_name = create_dropbox_foldername(
            group_letter, self.save_service.tk_designation, sanitized_subterm
        )

        suggested_folder = self.save_service.base_dir / folder_name
        suggested_folder.mkdir(parents=True, exist_ok=True)

        # Open file dialog (UI interaction)
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

        # Delegate actual saving to SaveService (core layer)
        try:
            metadata = self.save_service.create_metadata(
                start,
                end,
                group_letter,
                rad_sample,
                subterm,
                extra=extra_metadata,
            )
            saved_path = self.save_service.save_measurement(file_path, data, metadata)
            Debug.info(f"Measurement saved via file dialog: {saved_path}")
            return saved_path
        except Exception as e:
            Debug.error(f"Failed to save measurement via file dialog: {e}")
            MessageHelper.show_error(
                parent,
                f"Fehler beim Speichern: {str(e)}",
                "Fehler",
            )
            return None
