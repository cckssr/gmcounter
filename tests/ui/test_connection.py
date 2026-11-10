"""Connecting in the main window: the connection panel, its controller and ``--simulate``."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Signal

from gmcounter.infrastructure.config import load_config
from gmcounter.infrastructure.device_manager import DeviceManager
from gmcounter.infrastructure.serial_ports import SerialPortInfo
from gmcounter.infrastructure.simulation import simulation_available
from gmcounter.ui.controllers.connection_controller import ConnectionController
from gmcounter.ui.panels.connection_panel import ConnectionPanel
from gmcounter.ui.windows.main_window import MainWindow

from .conftest import IdleDevice

PORTS = [
    SerialPortInfo("/dev/cu.usbmodem1101", "Arduino UNO"),
    SerialPortInfo("/dev/cu.usbmodem2201", "Other board"),
]

needs_pty = pytest.mark.skipif(
    not simulation_available(), reason="the simulated counter needs mocks and a pty"
)


# ---- panel ---------------------------------------------------------------------------------
@pytest.fixture
def panel(qtbot, config):
    panel = ConnectionPanel()
    qtbot.addWidget(panel)
    panel.apply_config(config)
    return panel


def test_the_baud_combo_offers_the_configured_rates_with_the_default_selected(
    panel, config
):
    rates = config.get("gm_counter.baud_rates")
    combo = panel.ui.comboBaud
    assert [int(combo.itemText(i)) for i in range(combo.count())] == rates
    assert panel.current_baud() == config.get("gm_counter.default_baud")


def test_the_panel_starts_disconnected_and_offers_connect_only_with_a_port(
    panel, config
):
    assert panel.state == "disconnected"
    assert panel.ui.ledStatus.state == "off"
    assert panel.ui.valueStatus.text() == config.text(
        "connection_panel.text_disconnected"
    )
    assert not panel.ui.buttonConnect.isEnabled()  # no port yet
    panel.set_ports(PORTS, 1)
    assert panel.current_port() == "/dev/cu.usbmodem2201"
    assert panel.ui.valueDescription.text() == "Other board"
    assert panel.ui.buttonConnect.isEnabled()


def test_the_button_requests_connect_and_then_disconnect(qtbot, panel, config):
    panel.set_ports(PORTS, 0)
    panel.set_baud(115200)
    with qtbot.waitSignal(panel.connect_requested) as blocker:
        panel.ui.buttonConnect.click()
    assert blocker.args == ["/dev/cu.usbmodem1101", 115200]

    panel.set_state("connected", "ok")
    assert panel.ui.buttonConnect.text() == config.text(
        "connection_panel.text_disconnect"
    )
    assert not panel.ui.comboPort.isEnabled() and not panel.ui.comboBaud.isEnabled()
    with qtbot.waitSignal(panel.disconnect_requested):
        panel.ui.buttonConnect.click()


def test_while_connecting_or_measuring_nothing_can_be_changed(panel):
    panel.set_ports(PORTS, 0)
    panel.set_state("connecting", "...")
    assert panel.ui.ledStatus.state == "busy"
    assert not panel.ui.buttonConnect.isEnabled() and not panel.ui.comboPort.isEnabled()
    panel.set_state("connected", "ok")
    panel.set_locked(True)
    assert not panel.ui.buttonConnect.isEnabled()
    panel.set_locked(False)
    assert panel.ui.buttonConnect.isEnabled()


# ---- controller ----------------------------------------------------------------------------
class FakeCtrl(QObject):
    """The part of the AppController the connection controller uses."""

    connect_finished = Signal(bool)
    connection_changed = Signal(bool)
    reconnecting = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.device_manager = DeviceManager()
        self.is_connected = False
        self.is_connecting = False
        self.is_reconnecting = False
        self.calls: list = []

    def connect_device(self, port: str, baud: int) -> bool:
        self.calls.append(("connect", port, baud))
        return True

    def disconnect_device(self) -> None:
        self.calls.append(("disconnect",))
        self.connection_changed.emit(False)


@pytest.fixture
def harness(qtbot, config, layout_settings):
    ctrl = FakeCtrl()
    connection = ConnectionController(
        config, ctrl, list_ports=lambda: list(PORTS), settings=layout_settings
    )
    states: list[tuple[str, str]] = []
    notes: list[str] = []
    connection.state_changed.connect(lambda state, text: states.append((state, text)))
    connection.notify.connect(lambda text, _colour: notes.append(text))
    return ctrl, connection, states, notes


def test_a_connect_goes_through_connecting_to_connected(harness, config):
    ctrl, connection, states, _notes = harness
    assert connection.connect_port("/dev/cu.usbmodem1101", 1_000_000)
    assert ctrl.calls == [("connect", "/dev/cu.usbmodem1101", 1_000_000)]
    assert states[-1] == (
        "connecting",
        config.text("connection_panel.text_connecting", port="/dev/cu.usbmodem1101"),
    )
    ctrl.connect_finished.emit(True)
    ctrl.connection_changed.emit(True)
    assert states[-1][0] == "connected"


def test_a_failed_connect_is_shown_and_reported(harness, config):
    ctrl, connection, states, notes = harness
    connection.connect_port("/dev/cu.usbmodem1101", 9600)
    ctrl.connect_finished.emit(False)
    assert states[-1][0] == "failed"
    assert notes == [config.message("connect_failed", port="/dev/cu.usbmodem1101")]


def test_a_dropped_link_shows_reconnecting_and_after_the_last_attempt_lost(harness):
    ctrl, connection, states, _notes = harness
    seen: list[bool] = []
    connection.connected_changed.connect(seen.append)
    ctrl.reconnecting.emit()
    assert states[-1][0] == "reconnecting" and seen == [False]
    ctrl.connection_changed.emit(False)
    assert states[-1][0] == "lost"


def test_a_user_disconnect_shows_disconnected_not_lost(harness, config):
    ctrl, connection, states, notes = harness
    connection.disconnect_port()
    assert ctrl.calls == [("disconnect",)]
    assert [state for state, _text in states] == ["disconnected"]
    assert notes == [config.message("disconnected")]


def test_the_last_successful_port_is_remembered_and_preselected(
    harness, config, layout_settings
):
    ctrl, connection, _states, _notes = harness
    connection.connect_port("/dev/cu.usbmodem2201", 115200)
    ctrl.connect_finished.emit(True)
    assert connection.last_used() == ("/dev/cu.usbmodem2201", 115200)

    fresh = ConnectionController(
        config, FakeCtrl(), list_ports=lambda: list(PORTS), settings=layout_settings
    )
    published: list = []
    fresh.ports_changed.connect(lambda ports, index: published.append(index))
    fresh.refresh_ports()
    assert published == [1]


def test_a_failed_port_is_not_remembered(harness):
    ctrl, connection, _states, _notes = harness
    connection.connect_port("/dev/cu.usbmodem2201", 115200)
    ctrl.connect_finished.emit(False)
    assert connection.last_used() == (None, None)


def test_the_simulation_offers_only_its_port(config):
    connection = ConnectionController(
        config,
        FakeCtrl(),
        list_ports=lambda: list(PORTS),
        simulation_port="/dev/ttys042",
    )
    assert [p.device for p in connection.ports()] == ["/dev/ttys042"]
    assert connection.simulated


# ---- window --------------------------------------------------------------------------------
@pytest.fixture
def offline(qtbot, config):
    """A window that starts without a connection (as after a normal program start)."""
    win = MainWindow(config, DeviceManager(), persist=False)
    win.connection._list_ports = lambda: list(PORTS)  # no real serial scan
    win.connection.refresh_ports()
    qtbot.addWidget(win)
    win.show()
    yield win
    win.close()


def test_the_window_opens_without_a_connection_dialog_and_waits_for_a_connect(
    offline, config
):
    panel = offline.ui.connectionPanel
    assert panel.isVisibleTo(offline) and panel.state == "disconnected"
    assert panel.current_port() == "/dev/cu.usbmodem1101"  # hint "UNO" of config.json
    assert not offline.ui.measurementPanel.ui.buttonStart.isEnabled()
    assert not offline.ui.devicePanel.ui.buttonApply.isEnabled()
    assert offline.ui.statusBar.currentMessage() == config.message("please_connect")


def _fake_connect(manager: DeviceManager, ok: bool):
    def connect_device(port: str, baudrate: int, device_class=None) -> bool:
        if ok:
            manager.device = IdleDevice()  # type: ignore[assignment]
            manager.connected = True
            manager.port, manager.baudrate = port, baudrate
        return ok

    return connect_device


def test_connecting_in_the_panel_enables_the_measurement(qtbot, offline, monkeypatch):
    manager = offline.device_manager
    monkeypatch.setattr(manager, "connect_device", _fake_connect(manager, True))
    panel = offline.ui.connectionPanel
    with qtbot.waitSignal(offline.ctrl.connection_changed, timeout=5000):
        panel.ui.buttonConnect.click()
    assert panel.state == "connected" and panel.ui.ledStatus.state == "ok"
    assert offline.ui.measurementPanel.ui.buttonStart.isEnabled()
    assert offline.ui.devicePanel.ui.buttonApply.isEnabled()

    panel.ui.buttonConnect.click()  # now "Trennen"
    assert panel.state == "disconnected" and not manager.connected
    assert not offline.ui.measurementPanel.ui.buttonStart.isEnabled()


def test_a_failed_connect_keeps_the_measurement_disabled(qtbot, offline, monkeypatch):
    manager = offline.device_manager
    monkeypatch.setattr(manager, "connect_device", _fake_connect(manager, False))
    panel = offline.ui.connectionPanel
    with qtbot.waitSignal(offline.ctrl.connect_finished, timeout=5000):
        panel.ui.buttonConnect.click()
    assert panel.state == "failed" and panel.ui.ledStatus.state == "error"
    assert panel.ui.buttonConnect.isEnabled()  # try again or pick another port
    assert not offline.ui.measurementPanel.ui.buttonStart.isEnabled()


def test_a_window_on_a_connected_device_shows_the_connection(window):
    panel = window.ui.connectionPanel
    assert panel.state == "connected" and panel.current_port() == "test"
    assert window.ui.measurementPanel.ui.buttonStart.isEnabled()


def test_the_student_profile_hides_the_baud_rate(qtbot):
    win = MainWindow(load_config(profile="student"), DeviceManager(), persist=False)
    qtbot.addWidget(win)
    assert not win.ui.connectionPanel.ui.comboBaud.isVisibleTo(win)
    assert win.ui.connectionPanel.ui.comboPort.isVisibleTo(win)


def test_the_cli_offers_simulate():
    from gmcounter.main import parse_args

    assert not parse_args([]).simulate
    if simulation_available():
        assert parse_args(["--simulate"]).simulate


# ---- --simulate against the PTY mock ------------------------------------------------------
@needs_pty
@pytest.mark.integration
def test_the_simulated_window_connects_and_measures(
    qtbot, config, monkeypatch, tmp_path
):
    from gmcounter.infrastructure.session_journal import SessionJournal
    from gmcounter.ui.controllers import app_controller

    monkeypatch.setattr(
        app_controller, "SessionJournal", lambda: SessionJournal(session_dir=tmp_path)
    )
    win = MainWindow(config, simulate=True, persist=False)
    qtbot.addWidget(win)
    win.show()
    panel = win.ui.connectionPanel
    assert win.simulation is not None and panel.current_port() == win.simulation.port
    assert not panel.ui.comboBaud.isEnabled()
    assert win.windowTitle().endswith("Simulation")

    with qtbot.waitSignal(win.ctrl.connection_changed, timeout=15_000) as blocker:
        panel.ui.buttonConnect.click()
    assert blocker.args == [True] and panel.state == "connected"

    win.ui.devicePanel.ui.comboDuration.setCurrentIndex(1)  # 1 s of device time
    with qtbot.waitSignal(win.ctrl.measurement_started, timeout=5000):
        win.ui.measurementPanel.ui.buttonStart.click()
    with qtbot.waitSignal(win.ctrl.measurement_stopped, timeout=40_000):
        pass
    assert len(win.tabs["gm_timing"].export().rows) > 0
    win.context.save_service.mark_saved()
    simulation = win.simulation
    win.close()
    assert not simulation.running  # the window started it, so it stops it


@needs_pty
def test_the_launcher_keeps_one_simulation_across_a_profile_switch(qtbot):
    from gmcounter.ui.launcher import Launcher

    launcher = Launcher(persist=False, simulate=True)
    try:
        first = launcher.start()
        port = launcher.simulation.port
        assert first.ui.connectionPanel.current_port() == port
        second = launcher.switch_to("student")
        assert second is not first and second.simulation is launcher.simulation
        assert second.ui.connectionPanel.current_port() == port
    finally:
        if launcher.window is not None:
            launcher.window.close_for_switch()
        simulation = launcher.simulation
        launcher.shutdown()
    assert not simulation.running
