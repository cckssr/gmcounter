"""Connection to the GM counter from the main window: ports, connect / disconnect, link state.

The window used to ask for the port in a dialog before it opened; now the connection panel in
the control dock does that, and this controller drives it. It never touches widgets: it emits
``ports_changed`` and ``state_changed`` for the panel and delegates the device work to the
``AppController`` (background connect, acquisition, automatic reconnect).
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QSettings, Signal, Slot

from ...infrastructure.config import AppConfig
from ...infrastructure.serial_ports import (
    SerialPortInfo,
    list_serial_ports,
    preferred_port,
    with_port,
)

SETTING_PORT = "connection/port"
SETTING_BAUD = "connection/baud"


class ConnectionController(QObject):
    """State machine of the serial link as the connection panel shows it.

    ``simulation_port`` replaces the serial scan by the port of the simulated counter
    (``--simulate``). ``settings`` (a ``QSettings`` factory, ``None`` in tests) remembers the
    last successfully used port and baud rate.
    """

    ports_changed = Signal(
        object, int
    )  # list[SerialPortInfo], index to select (-1: none)
    state_changed = Signal(str, str)  # panel state, text
    connected_changed = Signal(bool)
    notify = Signal(str, str)  # status-bar / event-log text, colour

    def __init__(
        self,
        config: AppConfig,
        ctrl,
        *,
        list_ports: Callable[[], list[SerialPortInfo]] = list_serial_ports,
        simulation_port: str | None = None,
        settings: Callable[[], QSettings] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._ctrl = ctrl
        self._list_ports = list_ports
        self._simulation_port = simulation_port
        self._settings = settings
        self._port = ""
        self._baud = 0
        self._disconnecting = False

        ctrl.connect_finished.connect(self._on_connect_finished)
        ctrl.connection_changed.connect(self._on_connection_changed)
        ctrl.reconnecting.connect(self._on_reconnecting)

    # ---- helpers ---------------------------------------------------------------------------
    def _t(self, key: str, **fmt: object) -> str:
        return self._config.text(f"connection_panel.{key}", **fmt)

    def _state(self, state: str, key: str) -> None:
        self.state_changed.emit(state, self._t(key, port=self._port))

    @property
    def simulated(self) -> bool:
        return self._simulation_port is not None

    @property
    def is_connected(self) -> bool:
        return bool(self._ctrl.is_connected)

    def last_used(self) -> tuple[str | None, int | None]:
        """Port and baud rate of the last successful connect (from the user settings)."""
        if self._settings is None or self.simulated:
            return None, None
        settings = self._settings()
        port = settings.value(SETTING_PORT)
        baud = settings.value(SETTING_BAUD)
        try:
            baud_value = int(baud) if baud is not None else None
        except (TypeError, ValueError):
            baud_value = None
        return (str(port) if port else None), baud_value

    def _remember(self) -> None:
        if self._settings is None or self.simulated or not self._port:
            return
        settings = self._settings()
        settings.setValue(SETTING_PORT, self._port)
        settings.setValue(SETTING_BAUD, self._baud)

    # ---- ports -----------------------------------------------------------------------------
    def ports(self) -> list[SerialPortInfo]:
        """The ports to offer: the simulated one, or the serial ports of the system."""
        if self._simulation_port is not None:
            return [
                SerialPortInfo(
                    self._simulation_port, self._t("text_simulation_description")
                )
            ]
        return self._list_ports()

    @Slot()
    def refresh_ports(self) -> None:
        """Rescan and publish the ports; the connected or last used port is preselected."""
        ports = self.ports()
        manager = self._ctrl.device_manager
        current = None
        if manager.connected and manager.port and manager.port != "None":
            ports = with_port(ports, manager.port)
            current = manager.port
        last_port, _baud = self.last_used()
        index = preferred_port(
            ports,
            last_port=current or self._port or last_port,
            hint=str(self._config.get("gm_counter.default_arduino", "") or ""),
        )
        self.ports_changed.emit(ports, index)

    def publish_state(self) -> None:
        """Publish the ports and the current link state (a window may start connected)."""
        self.refresh_ports()
        manager = self._ctrl.device_manager
        if self.is_connected:
            self._port = manager.port
            self._baud = manager.baudrate
            self._state("connected", "text_connected")
        else:
            self._state("disconnected", "text_disconnected")
        self.connected_changed.emit(self.is_connected)

    # ---- connect / disconnect ----------------------------------------------------------------
    @Slot(str, int)
    def connect_port(self, port: str, baudrate: int) -> bool:
        """Start connecting to ``port``; the result arrives as a state change."""
        if not port or self._ctrl.is_connecting:
            return False
        self._port = port
        self._baud = int(baudrate)
        self._state("connecting", "text_connecting")
        return bool(self._ctrl.connect_device(port, self._baud))

    @Slot()
    def disconnect_port(self) -> None:
        """User-initiated disconnect (also cancels a running automatic reconnect)."""
        self._disconnecting = True
        try:
            self._ctrl.disconnect_device()
        finally:
            self._disconnecting = False
        self._state("disconnected", "text_disconnected")
        self.notify.emit(self._config.message("disconnected"), "")

    # ---- AppController signals -------------------------------------------------------------
    @Slot(bool)
    def _on_connect_finished(self, ok: bool) -> None:
        if ok:
            self._remember()
            return  # connection_changed(True) follows and shows the connected state
        self._state("failed", "text_failed")
        self.notify.emit(self._config.message("connect_failed", port=self._port), "red")

    @Slot(bool)
    def _on_connection_changed(self, up: bool) -> None:
        if up:
            self._state("connected", "text_connected")
        elif not self._disconnecting:
            # down without a user disconnect: all automatic reconnect attempts failed
            self._state("lost", "text_lost")
        self.connected_changed.emit(up)

    @Slot()
    def _on_reconnecting(self) -> None:
        self._state("reconnecting", "text_reconnecting")
        self.connected_changed.emit(False)
