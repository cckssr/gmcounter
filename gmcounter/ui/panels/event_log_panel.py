"""Timestamped scrollback of the status messages."""

from __future__ import annotations

from datetime import datetime
from html import escape

from PySide6.QtWidgets import QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.pyqt.ui_event_log_panel import Ui_EventLogPanel
from gmcounter.ui.i18n import apply_strings

_COLORS = {
    "green": "#22aa44",
    "blue": "#2266cc",
    "orange": "#cc7700",
    "red": "#cc2222",
    "yellow": "#aaaa00",
    "gray": "#888888",
}


class EventLogPanel(QWidget):
    """Read-only log; the document keeps at most 500 lines (set in the form)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_EventLogPanel()
        self.ui.setupUi(self)
        self.ui.buttonClear.clicked.connect(self.clear_log)

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings."""
        apply_strings(self, config.section("ui").get("event_log_panel", {}))

    def append(self, text: str, color: str = "") -> None:
        """Add ``[HH:MM:SS] text``; known colour names tint the line, others use the palette."""
        line = escape(f"[{datetime.now():%H:%M:%S}] {text}")
        hex_color = _COLORS.get(color.lower())
        if hex_color:
            line = f'<span style="color:{hex_color}">{line}</span>'
        self.ui.editLog.appendHtml(line)

    def clear_log(self) -> None:
        self.ui.editLog.clear()
