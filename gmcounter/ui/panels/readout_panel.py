"""Live counts, rate and the high-speed indicator."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.pyqt.ui_readout_panel import Ui_ReadoutPanel
from gmcounter.ui.i18n import apply_strings


class ReadoutPanel(QGroupBox):
    """Display only: setters update the LCDs and the high-speed LED."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_ReadoutPanel()
        self.ui.setupUi(self)
        self._text_on = ""
        self._text_off = ""

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings and the high-speed texts."""
        strings = config.section("ui").get("readout_panel", {})
        apply_strings(self, strings)
        self._text_on = strings.get("text_high_speed_on", "")
        self._text_off = strings.get("text_high_speed_off", "")
        self.set_high_speed(self.ui.ledHighSpeed.state == "busy")

    def set_count(self, count: int) -> None:
        self.ui.lcdCount.display(count)

    def set_rate(self, hz: float) -> None:
        self.ui.lcdRate.display(hz)

    def set_last_count(self, count: int) -> None:
        self.ui.lcdLastCount.display(count)

    def set_high_speed(self, active: bool) -> None:
        """Switch the high-speed LED and its text."""
        self.ui.ledHighSpeed.set_state("busy" if active else "off")
        self.ui.valueHighSpeed.setText(self._text_on if active else self._text_off)
