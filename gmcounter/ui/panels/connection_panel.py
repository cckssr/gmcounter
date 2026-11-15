"""Serial connection: port and baud rate selection, connect / disconnect, link status."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.infrastructure.serial_ports import SerialPortInfo
from gmcounter.pyqt.ui_connection_panel import Ui_ConnectionPanel
from gmcounter.ui.i18n import apply_strings

# Panel state -> (LED state, button shows "disconnect", selection editable, button enabled)
_STATES = {
    "disconnected": ("off", False, True, True),
    "failed": ("error", False, True, True),
    "lost": ("error", False, True, True),
    "connecting": ("busy", False, False, False),
    "connected": ("ok", True, False, True),
    "reconnecting": ("busy", True, False, True),
}


class ConnectionPanel(QGroupBox):
    """Port selection and the connect button; the connection controller drives it."""

    connect_requested = Signal(str, int)  # port, baud rate
    disconnect_requested = Signal()
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_ConnectionPanel()
        self.ui.setupUi(self)
        self._strings: dict = {}
        self._state = "disconnected"
        self._locked = False
        self._fixed_baud = False
        self.ui.buttonConnect.clicked.connect(self._on_button)
        self.ui.buttonRefreshPorts.clicked.connect(self.refresh_requested)
        self.ui.comboPort.currentIndexChanged.connect(self._show_description)

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings and the offered baud rates."""
        self._strings = config.section("ui").get("connection_panel", {})
        apply_strings(self, self._strings)
        gm = config.section("gm_counter")
        rates = [int(rate) for rate in gm.get("baud_rates", [])] or [1_000_000]
        default = int(gm.get("default_baud", rates[-1]))
        if default not in rates:
            rates.append(default)
        combo = self.ui.comboBaud
        combo.clear()
        for rate in rates:
            combo.addItem(str(rate), rate)
        combo.setCurrentIndex(rates.index(default))
        self.set_state("disconnected", self._text("text_disconnected"))

    def _text(self, key: str) -> str:
        return str(self._strings.get(key, key))

    # ---- setters ---------------------------------------------------------------------------
    def set_ports(self, ports: Sequence[SerialPortInfo], current: int = 0) -> None:
        """Offer ``ports`` and select the one at ``current`` (-1: none)."""
        combo = self.ui.comboPort
        combo.blockSignals(True)
        combo.clear()
        for port in ports:
            combo.addItem(port.device, port.description)
            combo.setItemData(
                combo.count() - 1, port.description, Qt.ItemDataRole.ToolTipRole
            )
        combo.setCurrentIndex(current if 0 <= current < len(ports) else -1)
        combo.blockSignals(False)
        self._show_description()
        self._update_enabled()

    def select_port(self, device: str) -> None:
        """Select ``device`` if it is offered."""
        index = self.ui.comboPort.findText(device)
        if index >= 0:
            self.ui.comboPort.setCurrentIndex(index)

    def set_baud(self, baudrate: int) -> None:
        """Select ``baudrate`` if it is offered."""
        index = self.ui.comboBaud.findData(int(baudrate))
        if index >= 0:
            self.ui.comboBaud.setCurrentIndex(index)

    def set_baud_fixed(self, fixed: bool) -> None:
        """A simulated device ignores the baud rate: the selector is disabled."""
        self._fixed_baud = fixed
        self._update_enabled()

    def set_state(self, state: str, text: str) -> None:
        """Show the link ``state`` (keys of ``_STATES``) with ``text`` next to the LED."""
        if state not in _STATES:
            raise ValueError(f"unknown connection state {state!r}")
        self._state = state
        led, connected, _editable, _enabled = _STATES[state]
        self.ui.ledStatus.set_state(led)
        self.ui.valueStatus.setText(text)
        self.ui.buttonConnect.setText(
            self._text("text_disconnect" if connected else "text_connect")
        )
        self._update_enabled()

    def set_locked(self, locked: bool) -> None:
        """While a measurement runs the connection cannot be changed."""
        self._locked = locked
        self._update_enabled()

    # ---- getters ---------------------------------------------------------------------------
    @property
    def state(self) -> str:
        return self._state

    def current_port(self) -> str:
        return self.ui.comboPort.currentText()

    def current_baud(self) -> int:
        data = self.ui.comboBaud.currentData()
        return int(data) if data is not None else 0

    # ---- internals -------------------------------------------------------------------------
    def _on_button(self) -> None:
        if _STATES[self._state][1]:
            self.disconnect_requested.emit()
        elif self.current_port():
            self.connect_requested.emit(self.current_port(), self.current_baud())

    def _show_description(self, _index: int = -1) -> None:
        data = self.ui.comboPort.currentData()
        self.ui.valueDescription.setText(str(data) if data else "")

    def _update_enabled(self) -> None:
        _led, connected, editable, enabled = _STATES[self._state]
        editable = editable and not self._locked
        ui = self.ui
        ui.comboPort.setEnabled(editable)
        ui.buttonRefreshPorts.setEnabled(editable)
        ui.comboBaud.setEnabled(editable and not self._fixed_baud)
        has_port = ui.comboPort.count() > 0 and bool(self.current_port())
        ui.buttonConnect.setEnabled(
            enabled and not self._locked and (connected or has_port)
        )
