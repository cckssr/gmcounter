"""Connection status and read-back of the device settings."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.pyqt.ui_device_status_panel import Ui_DeviceStatusPanel
from gmcounter.ui.i18n import apply_strings

# Colour names used by the controller -> StatusLed state.
_LED_STATES = {
    "green": "ok",
    "blue": "busy",
    "yellow": "busy",
    "orange": "busy",
    "red": "error",
    "ok": "ok",
    "busy": "busy",
    "error": "error",
}


class DeviceStatusPanel(QGroupBox):
    """Display only: the owner pushes status, device state and device info into it."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_DeviceStatusPanel()
        self.ui.setupUi(self)
        self._label_map: dict[str, str] = {}

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings and the repeat / query mode labels."""
        apply_strings(self, config.section("ui").get("device_status_panel", {}))
        self._label_map = dict(config.section("gm_counter").get("label_map", {}))

    def set_status(self, text: str, colour_name: str) -> None:
        """Show ``text`` next to the LED; unknown colour names turn the LED off."""
        self.ui.ledStatus.set_state(_LED_STATES.get(colour_name.lower(), "off"))
        self.ui.valueStatus.setText(text)

    def set_device_state(self, data: dict) -> None:
        """Update the read-back from a ``device_state_updated`` dict.

        A corrupted or incomplete read (``error`` set) is ignored so the displays are never
        overwritten with zeros.
        """
        if data.get("error"):
            return
        self.ui.lcdVoltage.display(data.get("voltage", 0))
        self.ui.lcdDuration.display(data.get("counting_time", 0))
        repeat = "repeat_on" if data.get("repeat", False) else "repeat_off"
        self.ui.valueMode.setText(self._label_map.get(repeat, repeat))
        if "auto_query" in data:
            auto = "auto_on" if data["auto_query"] else "auto_off"
            self.ui.valueQueryMode.setText(self._label_map.get(auto, auto))

    def set_device_info(self, info: dict) -> None:
        """Show firmware version and OpenBIS code."""
        self.ui.valueFirmware.setText(info.get("version", ""))
        self.ui.valueOpenbis.setText(info.get("openbis", ""))
