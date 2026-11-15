"""Status bar management utilities."""

import re
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QStatusBar,
    QLabel,
)
from PySide6.QtCore import QTimer  # pylint: disable=no-name-in-module
from PySide6.QtGui import QColor  # pylint: disable=no-name-in-module
from shiboken6 import isValid

from ...infrastructure.logging import Debug


_BACKGROUND_RE = re.compile(r"background-color:\s*[^;]+;")
_TEXT_COLOR_RE = re.compile(r"(?<![-\w])color:\s*[^;]+;")
_DARK_TEXT_FROM_LUMA = 150  # brighter backgrounds (orange, yellow) get dark text


def text_color_for(backcolor: str) -> str:
    """Readable text colour for *backcolor*: black on bright, white on dark backgrounds.

    Returns ``""`` for a colour Qt cannot parse, so the default text colour stays.
    """
    colour = QColor(backcolor)
    if not colour.isValid():
        return ""
    luma = (299 * colour.red() + 587 * colour.green() + 114 * colour.blue()) / 1000
    return "black" if luma >= _DARK_TEXT_FROM_LUMA else "white"


class StatusBarManager:
    """Manager for status bar messages and styles.

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
        self.old_state: list[str] = []  # [currentMessage, styleSheet]
        self._save_state()

    def show_message(
        self, message: str, backcolor: str = "", duration: int = 0
    ) -> None:
        """Display a (temporary) message on the status bar.

        Args:
            message: Message to display
            backcolor: Background color (CSS format)
            duration: Duration in milliseconds (0 = permanent until next message)
        """
        new_style = self._update_statusbar_style(backcolor)
        self.statusbar.setStyleSheet(new_style)

        if duration != 0:
            self.statusbar.showMessage(message, duration)
            Debug.debug(f"Statusbar message: {message} with duration: {duration}")
            # reset to old state after duration
            QTimer.singleShot(duration, self._restore_state)
        else:
            self.statusbar.showMessage(message)
            Debug.debug(f"Permanent Statusbar message: {message}")

    def _restore_state(self) -> None:
        """Back to the saved message and style (no-op if the window is already gone)."""
        if not isValid(self.statusbar):
            return
        self.statusbar.setStyleSheet(self.old_state[1])
        self.statusbar.showMessage(self.old_state[0])

    def add_permanent_widget(
        self, message: str, index: int = 0, backcolor: str = ""
    ) -> None:
        """Add a permanent message widget to the status bar.

        This message or widget will remain in the status bar until removed.

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
        Debug.debug(f"Permanent Statusbar message: {message} at index: {index}")

    def _update_statusbar_style(self, backcolor: str) -> str:
        """Update the style of the status bar.

        Args:
            backcolor: Background color to apply

        Returns:
            str: New style sheet for the status bar as string
        """
        self._save_state()
        if not backcolor:
            Debug.info("No background color change")
            return self.old_state[1]

        # Replace an earlier background and text colour, then set the pair that fits.
        base = _TEXT_COLOR_RE.sub("", _BACKGROUND_RE.sub("", self.old_state[1]))
        new_style = base + f"background-color: {backcolor};"
        text_color = text_color_for(backcolor)
        if text_color:
            new_style += f"color: {text_color};"
        Debug.debug(f"Statusbar style: {self.old_state[1]!r} -> {new_style!r}")
        return new_style

    def _save_state(self):
        """Save the current state of the status bar."""
        self.old_state = [self.statusbar.currentMessage(), self.statusbar.styleSheet()]


# Backwards compatibility alias
Statusbar = StatusBarManager
