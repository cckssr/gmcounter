# Layer: ui/widgets — EventLogPanel dock widget (§9).
# A dockable timestamped scrollback of every status_message line.

from datetime import datetime

from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QWidget,
)

_COLOR_MAP = {
    "green": "#22aa44",
    "blue": "#2266cc",
    "orange": "#cc7700",
    "red": "#cc2222",
    "yellow": "#aaaa00",
    "gray": "#888888",
    "white": "#cccccc",
}
_MAX_ENTRIES = 500


class EventLogPanel(QDockWidget):
    """Dockable log of status messages fed from AppController.status_message."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__("Ereignisprotokoll", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._list = QListWidget()
        self._list.setWordWrap(True)
        self.setWidget(self._list)

    def append(self, text: str, color: str = "") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{ts}] {text}")
        hex_color = _COLOR_MAP.get(color.lower(), _COLOR_MAP.get("white", "#cccccc"))
        item.setForeground(Qt.GlobalColor.white)
        item.setData(Qt.ItemDataRole.ForegroundRole, None)
        item.setToolTip(text)
        self._list.insertItem(0, item)

        # Keep list bounded
        while self._list.count() > _MAX_ENTRIES:
            self._list.takeItem(self._list.count() - 1)

    def clear_log(self) -> None:
        self._list.clear()
