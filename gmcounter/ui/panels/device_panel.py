"""Device settings: count mode, query mode, count duration and GM voltage."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.pyqt.ui_device_panel import Ui_DevicePanel
from gmcounter.ui.i18n import apply_strings
from gmcounter.ui.panels import fill_combo

_WARNING_STYLE = "QSpinBox { background-color: orange; color: black; }"
_DEFAULT_DURATIONS_S = (0, 1, 10, 60, 100, 300)
_DEFAULT_VOLTAGE_WARNING_V = 650


class DevicePanel(QGroupBox):
    """Settings that are sent to the device when the apply button is pressed."""

    apply_requested = Signal()
    voltage_warning = Signal(int)  # voltage above the warning threshold

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_DevicePanel()
        self.ui.setupUi(self)
        self._duration_presets_s: tuple[int, ...] = _DEFAULT_DURATIONS_S
        self._warning_threshold_v = _DEFAULT_VOLTAGE_WARNING_V
        self._locked = False
        self._connected = True
        self.ui.buttonApply.clicked.connect(self.apply_requested)
        self.ui.dialVoltage.valueChanged.connect(self.ui.spinVoltage.setValue)
        self.ui.spinVoltage.valueChanged.connect(self._on_voltage_changed)

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings, duration presets and voltage defaults."""
        strings = config.section("ui").get("device_panel", {})
        apply_strings(self, strings)
        fill_combo(
            self.ui.comboDuration,
            strings.get("combo_duration_items", []),
            keep_empty=False,
        )
        presets = strings.get("combo_duration_seconds")
        if presets:
            self._duration_presets_s = tuple(int(value) for value in presets)
        gm = config.section("gm_counter")
        self._warning_threshold_v = int(
            gm.get("voltage_warning_threshold", _DEFAULT_VOLTAGE_WARNING_V)
        )
        if "default_voltage" in gm:
            self.set_voltage(int(gm["default_voltage"]))

    def settings(self) -> dict:
        """Device settings as entered: ``voltage`` (V), ``repeat`` and ``auto_query`` flags."""
        return {
            "voltage": int(self.ui.spinVoltage.value()),
            "repeat": self.ui.radioModeRepeat.isChecked(),
            "auto_query": self.ui.radioQueryAuto.isChecked(),
        }

    def duration_s(self) -> int:
        """Count duration in seconds; 0 means unlimited (also for invalid input).

        A preset item maps through ``combo_duration_seconds``; a custom value typed into the
        editable combo box is parsed as a number and rounded.
        """
        combo = self.ui.comboDuration
        index = combo.currentIndex()
        if 0 <= index < len(self._duration_presets_s):
            return self._duration_presets_s[index]
        try:
            return max(0, int(round(float(combo.currentText().replace(",", ".")))))
        except ValueError:
            return 0

    def set_voltage(self, volts: int) -> None:
        """Show ``volts`` in the spin box and the dial."""
        self.ui.spinVoltage.setValue(int(volts))

    def set_connected(self, connected: bool) -> None:
        """Settings can be entered at any time, but only applied to a connected device."""
        self._connected = connected
        self.ui.buttonApply.setEnabled(connected and not self._locked)

    def set_locked(self, locked: bool) -> None:
        """Disable (``True``) or re-enable every control while a measurement runs."""
        self._locked = locked
        self.ui.buttonApply.setEnabled(self._connected and not locked)
        for widget in (
            self.ui.spinVoltage,
            self.ui.dialVoltage,
            self.ui.comboDuration,
            self.ui.radioModeSingle,
            self.ui.radioModeRepeat,
            self.ui.radioQueryManual,
            self.ui.radioQueryAuto,
        ):
            widget.setEnabled(not locked)

    def _on_voltage_changed(self, volts: int) -> None:
        self.ui.dialVoltage.setValue(volts)
        if volts > self._warning_threshold_v:
            self.ui.spinVoltage.setStyleSheet(_WARNING_STYLE)
            self.voltage_warning.emit(volts)
        else:
            self.ui.spinVoltage.setStyleSheet("")
