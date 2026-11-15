"""Common UI dialog helpers - reusable across the application."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QWidget,
    QMessageBox,
    QFileDialog,
)

from .messages import message


def show_info(parent: QWidget, text: str, title: Optional[str] = None) -> None:
    """Display an information message dialog.

    Args:
        parent: Parent widget for the dialog
        text: Message to display
        title: Dialog title (default: the matching ``title_*`` message)
    """
    QMessageBox.information(
        parent, title or message("title_info"), text, QMessageBox.StandardButton.Ok
    )


def show_warning(parent: QWidget, text: str, title: Optional[str] = None) -> None:
    """Display a warning message dialog.

    Args:
        parent: Parent widget for the dialog
        text: Message to display
        title: Dialog title (default: the matching ``title_*`` message)
    """
    QMessageBox.warning(
        parent, title or message("title_warning"), text, QMessageBox.StandardButton.Ok
    )


def show_error(parent: QWidget, text: str, title: Optional[str] = None) -> None:
    """Display an error message dialog.

    Args:
        parent: Parent widget for the dialog
        text: Message to display
        title: Dialog title (default: the matching ``title_*`` message)
    """
    QMessageBox.critical(
        parent, title or message("title_error"), text, QMessageBox.StandardButton.Ok
    )


def ask_question(
    parent: QWidget,
    text: str,
    title: Optional[str] = None,
) -> bool:
    """Ask a yes/no question.

    Args:
        parent: Parent widget for the dialog
        text: Question to ask
        title: Dialog title (default: the matching ``title_*`` message)

    Returns:
        True if user clicked Yes, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        title or message("title_question"),
        text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def ask_save_file(
    parent: QWidget,
    title: Optional[str] = None,
    default_dir: Optional[Path] = None,
    default_name: str = "",
    file_filter: Optional[str] = None,
) -> Optional[Path]:
    """Open a save file dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title (default: the matching ``title_*`` message)
        default_dir: Default directory to open
        default_name: Default file name
        file_filter: File type filter

    Returns:
        Path to selected file or None if cancelled
    """
    if default_dir is None:
        default_dir = Path.home() / "Documents"

    start_path = str(default_dir / default_name) if default_name else str(default_dir)

    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        title or message("title_save_file"),
        start_path,
        file_filter or message("filter_csv"),
    )

    if file_path:
        return Path(file_path)
    return None


def ask_open_file(
    parent: QWidget,
    title: Optional[str] = None,
    default_dir: Optional[Path] = None,
    file_filter: Optional[str] = None,
) -> Optional[Path]:
    """Open a file selection dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title (default: the matching ``title_*`` message)
        default_dir: Default directory to open
        file_filter: File type filter

    Returns:
        Path to selected file or None if cancelled
    """
    if default_dir is None:
        default_dir = Path.home() / "Documents"

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title or message("title_open_file"),
        str(default_dir),
        file_filter or message("filter_csv"),
    )

    if file_path:
        return Path(file_path)
    return None


def confirm_close(parent: QWidget, event) -> None:
    """Handle close event with confirmation dialog.

    Args:
        parent: Parent widget
        event: Close event to accept or ignore
    """
    reply = QMessageBox.question(
        parent,
        message("title_quit"),
        message("confirm_quit"),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )

    if reply == QMessageBox.StandardButton.Yes:
        event.accept()
    else:
        event.ignore()
