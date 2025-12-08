"""
DEPRECATED: This module is being phased out.

Please use the new modular structure:
- SaveManager → gmcounter.core.services.SaveService
- MessageHelper → gmcounter.ui.common.dialogs functions
- Statusbar → gmcounter.ui.common.statusbar.StatusBarManager
- Utility functions → gmcounter.core.utils

This file now re-exports from the new locations for backwards compatibility.
"""

# Import actual classes from old helper_classes for full compatibility
from .helper_classes import SaveManager, Statusbar, AlertWindow, Helper

# Re-export new functions
from .ui.common.dialogs import (
    show_info,
    show_warning,
    show_error,
    ask_question,
    ask_save_file,
)
from .core.utils import (
    sanitize_subterm_for_folder,
    create_dropbox_foldername,
    create_group_name,
)
from .infrastructure.config import import_config

# For backwards compatibility
from PySide6.QtWidgets import QWidget
from .infrastructure.logging import Debug


class MessageHelper:
    """
    DEPRECATED: Use gmcounter.ui.common.dialogs functions instead.

    Kept for backwards compatibility.
    """

    @staticmethod
    def info(parent: QWidget, message: str, title: str = "Information") -> None:
        show_info(parent, message, title)

    @staticmethod
    def warning(parent: QWidget, message: str, title: str = "Warning") -> None:
        show_warning(parent, message, title)

    @staticmethod
    def error(parent: QWidget, message: str, title: str = "Error") -> None:
        show_error(parent, message, title)

    @staticmethod
    def question(
        parent: QWidget,
        message: str,
        title: str = "Question",
    ) -> bool:
        return ask_question(parent, message, title)


__all__ = [
    "SaveManager",
    "Statusbar",
    "MessageHelper",
    "AlertWindow",
    "Helper",
    "import_config",
    "sanitize_subterm_for_folder",
    "create_dropbox_foldername",
    "create_group_name",
]
