"""Common UI dialog helpers - reusable across the application."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QWidget,
    QMessageBox,
    QFileDialog,
)


def show_info(parent: QWidget, message: str, title: str = "Information") -> None:
    """Display an information message dialog.

    Args:
        parent: Parent widget for the dialog
        message: Message to display
        title: Dialog title
    """
    QMessageBox.information(parent, title, message, QMessageBox.StandardButton.Ok)


def show_warning(parent: QWidget, message: str, title: str = "Warning") -> None:
    """Display a warning message dialog.

    Args:
        parent: Parent widget for the dialog
        message: Message to display
        title: Dialog title
    """
    QMessageBox.warning(parent, title, message, QMessageBox.StandardButton.Ok)


def show_error(parent: QWidget, message: str, title: str = "Error") -> None:
    """Display an error message dialog.

    Args:
        parent: Parent widget for the dialog
        message: Message to display
        title: Dialog title
    """
    QMessageBox.critical(parent, title, message, QMessageBox.StandardButton.Ok)


def ask_question(
    parent: QWidget,
    message: str,
    title: str = "Question",
) -> bool:
    """Ask a yes/no question.

    Args:
        parent: Parent widget for the dialog
        message: Question to ask
        title: Dialog title

    Returns:
        True if user clicked Yes, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def ask_save_file(
    parent: QWidget,
    title: str = "Save File",
    default_dir: Optional[Path] = None,
    default_name: str = "",
    file_filter: str = "CSV Files (*.csv);;All Files (*.*)",
) -> Optional[Path]:
    """Open a save file dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
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
        title,
        start_path,
        file_filter,
    )

    if file_path:
        return Path(file_path)
    return None


def ask_open_file(
    parent: QWidget,
    title: str = "Open File",
    default_dir: Optional[Path] = None,
    file_filter: str = "CSV Files (*.csv);;All Files (*.*)",
) -> Optional[Path]:
    """Open a file selection dialog.

    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        default_dir: Default directory to open
        file_filter: File type filter

    Returns:
        Path to selected file or None if cancelled
    """
    if default_dir is None:
        default_dir = Path.home() / "Documents"

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        str(default_dir),
        file_filter,
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
        "Beenden",
        "Wollen Sie sicher das Programm schließen?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )

    if reply == QMessageBox.StandardButton.Yes:
        event.accept()
    else:
        event.ignore()
