"""Status bar management utilities."""

import re
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QStatusBar,
    QLabel,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module

from ...infrastructure.logging import Debug


class StatusBarManager:
    """
    Manager for status bar messages and styles.

    Attributes:
        statusbar (QStatusBar): The status bar widget.
        old_state (list): The previous state of the status bar.
    """

    def __init__(self, statusbar: QStatusBar) -> None:
        """Initialize the status bar manager.

        Args:
            statusbar: QStatusBar widget to manage
        """
        self.statusbar = statusbar
        self.old_state: list[str] = []
        self._save_state()

    def show_message(
        self, message: str, backcolor: str = "", duration: int = 0
    ) -> None:
        """Display a temporary message on the status bar.

        Args:
            message: Message to display
            backcolor: Background color (CSS format)
            duration: Duration in milliseconds (0 = permanent until next message)
        """
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)

        if duration != 0:
            self.statusbar.showMessage(message, duration)
            Debug.info(f"Statusbar message: {message} with duration: {duration}")
            # reset to old state after duration
            QTimer.singleShot(
                duration, lambda: self.statusbar.setStyleSheet(self.old_state[1])
            )
            QTimer.singleShot(
                duration, lambda: self.statusbar.showMessage(self.old_state[0])
            )
        else:
            self.statusbar.showMessage(message)
            Debug.info(f"Permanent Statusbar message: {message}")

    def add_permanent_widget(
        self, message: str, index: int = 0, backcolor: str = ""
    ) -> None:
        """Add a permanent message widget to the status bar.

        Args:
            message: Message to display
            index: Position index for the widget
            backcolor: Background color (CSS format)
        """
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)
        label = QLabel()
        label.setText(message)
        self.statusbar.insertPermanentWidget(index, label)
        Debug.info(f"Permanent Statusbar message: {message} at index: {index}")

    def _update_statusbar_style(self, backcolor: str) -> str:
        """Update the style of the status bar.

        Args:
            backcolor: Background color to apply

        Returns:
            New style string
        """
        self._save_state()

        if backcolor:
            if "background-color:" in self.old_state[1]:
                # if old style had backcolor, replace it with the new one
                new_style = self.old_state[1].replace(
                    re.search(r"background-color:\s*[^;]+;", self.old_state[1]).group(
                        0
                    ),
                    f"background-color: {backcolor};",
                )
                Debug.info(
                    f"Statusbar background color updated: {self.old_state[1]} -> {new_style}"
                )
            else:
                # otherwise append the new backcolor
                new_style = self.old_state[1] + f"background-color: {backcolor};"
                Debug.info(f"Statusbar background color set: {new_style}")
        else:
            new_style = self.old_state[1]
            Debug.info("No background color change")
        return new_style

    def _save_state(self):
        """Save the current state of the status bar."""
        self.old_state = [self.statusbar.currentMessage(), self.statusbar.styleSheet()]


# Backwards compatibility alias
Statusbar = StatusBarManager
