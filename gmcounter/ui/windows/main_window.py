# Layer: ui/windows — thin MainWindow.
# main_window.ui + panels + tabs from the TabRegistry; controllers hold the logic.

from __future__ import annotations

import logging
import tempfile

from PySide6.QtCore import QEvent, QSettings, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QWidget

from gmcounter.pyqt.ui_main_window import Ui_MainWindow

from ...core.services import SaveService
from ...infrastructure.config import AppConfig
from ...infrastructure.device_manager import DeviceManager
from ...infrastructure.modules.registry import ModuleRegistry
from ...infrastructure.simulation import SimulatedCounter
from .. import tabs as _tabs  # noqa: F401  (registers the experiment tabs)
from ..common.file_dialogs import FileDialogManager
from ..common.prompt import MessageBoxPrompt
from ..common.statusbar import StatusBarManager
from ..context import AppContext
from ..controllers.app_controller import AppController
from ..controllers.connection_controller import ConnectionController
from ..controllers.session_controller import SessionController
from ..i18n import apply_strings
from ..profile import apply_profile, next_profile
from ..tabs.base import PlotTabBase
from ..tabs.registry import TabRegistry
from ..widgets.vscroll import lock_vertical_scroll

_log = logging.getLogger(__name__)

WINDOW_MODES = ("maximized", "fullscreen", "normal")
SETTINGS_ORGANISATION = "gmcounter"
SETTINGS_APPLICATION = "gmcounter"
DEFAULT_PROFILE = "expert"
TAB_COLORS = {"info": "green", "warning": "orange", "error": "red"}
VOLTAGE_WARNING_MS = 3000
CONNECTED_MESSAGE_MS = 3000
AUTO_SAVE_MESSAGE_MS = 1000


def layout_settings() -> QSettings:
    """The user settings that hold the window layout."""
    return QSettings(SETTINGS_ORGANISATION, SETTINGS_APPLICATION)


class MainWindow(QMainWindow):
    """Main application window — chrome only.

    Logic lives in AppController (timers, acquisition, reconnect), ConnectionController
    (port selection, connect / disconnect in the connection panel), SessionController
    (Start / Stop / Save / Reset of the selected tab) and the experiment tabs.

    ``device_manager`` may already be connected (profile switch); without one the window
    creates its own. ``simulate=True`` starts a simulated counter on a pseudo-terminal (or
    uses ``simulation``, which the caller owns) and offers only its port.
    ``persist=False`` keeps window layout, save folder and last port out of the user's
    files (tests).
    """

    _device_info_received = Signal(dict)
    profile_switch_requested = Signal(str)  # id of the profile to switch to

    def __init__(
        self,
        config: AppConfig,
        device_manager: DeviceManager | None = None,
        parent: QWidget | None = None,
        persist: bool = True,
        *,
        simulate: bool = False,
        simulation: SimulatedCounter | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        if device_manager is None:
            device_manager = DeviceManager()
        self.device_manager = device_manager
        self._owns_simulation = simulate and simulation is None
        if self._owns_simulation:
            simulation = SimulatedCounter()
            simulation.start()
        self.simulation = simulation
        self._persist = persist
        self._was_maximized = False
        self._keep_device = False  # set while closing for a profile switch
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_strings(self, config.section("ui").get("main_window", {}))
        for panel in self._panels():
            panel.apply_config(config)

        self._status_bar = StatusBarManager(self.ui.statusBar)
        base_dir = (
            config.get("save.base_folder", "GMCounter")
            if persist
            else tempfile.mkdtemp(prefix="gmcounter-test-")
        )
        save_service = SaveService(
            base_dir=base_dir,
            tk_designation=config.get("save.tk_designation", "TK47"),
        )
        self.ctrl = AppController(
            device_manager, status_bar=self._status_bar, parent=self
        )
        self.ctrl.event_log = self.ui.eventLogPanel
        self.connection = ConnectionController(
            config,
            self.ctrl,
            simulation_port=simulation.port if simulation is not None else None,
            settings=(lambda: layout_settings()) if persist else None,
            parent=self,
        )
        self.context = AppContext(
            config=config,
            device_manager=device_manager,
            ctrl=self.ctrl,
            save_service=save_service,
            file_dialogs=FileDialogManager(save_service),
            voltage_readback=self.ui.deviceStatusPanel.voltage,
            device_settings=self.ui.devicePanel.settings,
            sample_metadata=self.ui.samplePanel.metadata,
        )
        self.tabs: dict[str, PlotTabBase] = {}
        self._build_tabs()
        # before the docks measure their minimum width: hidden controls take no room
        self.missing_profile_names = apply_profile(self)
        self.session = self._build_session(save_service)
        self._connect_panels()
        self._connect_ctrl()
        self._setup_docks()
        self._setup_profile_switch()
        self._setup_full_screen()

        device_manager.on_device_info = self._device_info_received.emit
        self._device_info_received.connect(self._on_device_info)
        if device_manager.device and device_manager.connected:
            device_manager._fetch_device_info()  # pylint: disable=protected-access

        self.session.initial_state()
        self._setup_connection()
        if persist:
            self._restore_layout()

    # ==================== Construction ====================

    def _panels(self) -> list:
        ui = self.ui
        return [
            ui.connectionPanel,
            ui.devicePanel,
            ui.samplePanel,
            ui.measurementPanel,
            ui.readoutPanel,
            ui.deviceStatusPanel,
            ui.eventLogPanel,
        ]

    def _build_tabs(self) -> None:
        """Create the registered tabs in order; the timing tab fills ``context.timing``."""
        hidden = set(self.config.hidden_tabs())
        for tab_class in TabRegistry.available(ModuleRegistry.all()):
            if tab_class.tab_id in hidden and not tab_class.provides_timing:
                continue
            tab = tab_class(self.context)  # added to tabWidget below (or kept hidden)
            tab.build()
            if tab.provides_timing:
                self.context.timing = tab
                self.ctrl.set_active_tab(tab)
                tab.status_message.connect(self._on_tab_status)
                tab.high_speed_changed.connect(self.ui.readoutPanel.set_high_speed)
                tab.readout_changed.connect(self._on_readout)
            self.tabs[tab.tab_id] = tab
            if tab_class.tab_id not in hidden:
                self.ui.tabWidget.addTab(tab, tab.title)
            else:
                tab.setParent(self)
                tab.hide()

    def _build_session(self, save_service: SaveService) -> SessionController:
        ui = self.ui
        session = SessionController(
            self.config,
            self.ctrl,
            self.context.timing,
            save_service,
            self.context.file_dialogs,
            MessageBoxPrompt(self),
            current_tab=lambda: ui.tabWidget.currentWidget(),
            duration_s=ui.devicePanel.duration_s,
            sample_metadata=ui.samplePanel.metadata,
            apply_settings=self._apply_settings,
            dialog_parent=self,
            parent=self,
        )
        # Connected after the timing tab became the active tab: it sees a stop first.
        self.ctrl.measurement_started.connect(session.on_measurement_started)
        self.ctrl.measurement_stopped.connect(session.on_measurement_stopped)
        self.ctrl.reconnect_succeeded.connect(session.on_reconnect_succeeded)
        self.ctrl.connection_lost.connect(session.on_connection_lost)
        session.buttons_changed.connect(ui.measurementPanel.set_state)
        session.status_changed.connect(ui.deviceStatusPanel.set_status)
        session.settings_locked.connect(ui.devicePanel.set_locked)
        session.settings_locked.connect(ui.connectionPanel.set_locked)
        session.tabs_locked.connect(self._lock_tabs)
        session.progress_cleared.connect(ui.measurementPanel.clear_progress)
        session.message.connect(
            lambda text, ms: self._status_bar.show_message(text, duration=ms)
        )
        return session

    def _connect_panels(self) -> None:
        ui = self.ui
        panel = ui.measurementPanel
        panel.start_requested.connect(self.session.start)
        panel.stop_requested.connect(self.session.stop)
        panel.save_requested.connect(self.session.save)
        panel.reset_requested.connect(self.session.reset)
        ui.devicePanel.apply_requested.connect(self._apply_settings)
        ui.devicePanel.voltage_warning.connect(self._on_voltage_warning)
        ui.samplePanel.auto_save_toggled.connect(self._on_auto_save_toggled)
        ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(ui.tabWidget.currentIndex())

    def _connect_ctrl(self) -> None:
        ctrl, ui = self.ctrl, self.ui
        ctrl.device_state_updated.connect(self._on_device_state)
        ctrl.progress_updated.connect(ui.measurementPanel.set_progress)

    def _setup_connection(self) -> None:
        """Wire the connection panel and publish the initial link state."""
        panel, connection = self.ui.connectionPanel, self.connection
        panel.connect_requested.connect(connection.connect_port)
        panel.disconnect_requested.connect(connection.disconnect_port)
        panel.refresh_requested.connect(connection.refresh_ports)
        connection.ports_changed.connect(panel.set_ports)
        connection.state_changed.connect(panel.set_state)
        connection.connected_changed.connect(self._on_connected_changed)
        connection.notify.connect(self.notify)
        panel.set_baud_fixed(connection.simulated)
        _port, baud = connection.last_used()
        if self.device_manager.connected:
            baud = self.device_manager.baudrate
        if baud:
            panel.set_baud(baud)
        if self.simulation is not None:
            self.setWindowTitle(
                self.config.text(
                    "main_window.text_title_simulation", title=self.windowTitle()
                )
            )
        connection.publish_state()
        if self.simulation is not None:
            self.notify(self.config.message("simulation_active"), "orange")
        elif not self.device_manager.connected:
            self._status_bar.show_message(self.config.message("please_connect"))

    # ==================== Slots ====================

    def _on_connected_changed(self, connected: bool) -> None:
        self.session.set_connected(connected)
        self.ui.devicePanel.set_connected(connected)
        if connected:
            self._status_bar.show_message(
                self.config.message("connected").format(self.device_manager.port),
                duration=CONNECTED_MESSAGE_MS,
            )
        elif not self.ctrl.is_reconnecting:
            self._on_device_info({})

    def current_tab(self) -> PlotTabBase | None:
        tab = self.ui.tabWidget.currentWidget()
        return tab if isinstance(tab, PlotTabBase) else None

    def _on_tab_changed(self, _index: int) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        self.ui.samplePanel.set_distance_visible(not tab.hides_global_distance)
        self.session.on_tab_changed(tab)

    def _lock_tabs(self, active: PlotTabBase | None) -> None:
        """While a session runs only its tab stays usable."""
        tabs = self.ui.tabWidget
        for index in range(tabs.count()):
            tabs.setTabEnabled(index, active is None or tabs.widget(index) is active)

    def _apply_settings(self) -> None:
        settings = self.ui.devicePanel.settings()
        # Always infinite counting time: the host controls the duration via delta accumulation.
        self.ctrl.apply_settings(
            voltage=settings["voltage"],
            counting_time=0,
            repeat=settings["repeat"],
            auto_query=settings["auto_query"],
        )

    def _on_tab_status(self, level: str, text: str) -> None:
        color = TAB_COLORS.get(level, "white")
        self._status_bar.show_message(text, backcolor=color)
        self.ui.eventLogPanel.append(text, color)

    def _on_readout(self, count: int, rate: float) -> None:
        self.ui.readoutPanel.set_count(count)
        self.ui.readoutPanel.set_rate(rate)

    def _on_device_state(self, data: dict) -> None:
        # A corrupted read must never overwrite the displays with zeros.
        if data.get("error"):
            return
        self.ui.deviceStatusPanel.set_device_state(data)
        self.ui.readoutPanel.set_count(data.get("count", 0))
        self.ui.readoutPanel.set_last_count(data.get("last_count", 0))

    def _on_device_info(self, info: dict) -> None:
        self.ui.deviceStatusPanel.set_device_info(info)
        self.session.set_device_info(info)

    def _on_voltage_warning(self, volts: int) -> None:
        self._status_bar.show_message(
            self.config.message("voltage_warning").format(volts),
            duration=VOLTAGE_WARNING_MS,
        )

    def _on_auto_save_toggled(self, checked: bool) -> None:
        key = "auto_save_enabled" if checked else "auto_save_disabled"
        self._status_bar.show_message(
            self.config.message(key), duration=AUTO_SAVE_MESSAGE_MS
        )

    # ==================== Docks, layout persistence, full screen ====================

    def _setup_docks(self) -> None:
        """Side docks never scroll horizontally; each has a toggle action wired both ways."""
        ui = self.ui
        for dock, scroll, action in (
            (ui.dockControls, ui.scrollControls, ui.actionToggleControls),
            (ui.dockLive, ui.scrollLive, ui.actionToggleLive),
            (ui.dockLog, None, ui.actionToggleLog),
        ):
            if scroll is not None:
                dock.setMinimumWidth(lock_vertical_scroll(scroll) + 2)
            action.setChecked(not dock.isHidden())
            action.toggled.connect(dock.setVisible)
            dock.visibilityChanged.connect(action.setChecked)

    def _setup_profile_switch(self) -> None:
        """The toolbar action names the profile it leads to; it is off without a second one."""
        action = self.ui.actionSwitchProfile
        names = self.config.profile_names
        target = next_profile(self.config.profile, names)
        available = target != self.config.profile
        action.setVisible(available)
        action.setEnabled(available)
        if available:
            target_name = self.config.get(f"profiles.{target}.name", target)
            action.setText(
                self.config.text("main_window.text_switch_profile", profile=target_name)
            )
            action.triggered.connect(
                lambda _checked=False: self.profile_switch_requested.emit(target)
            )

    def switch_blocker(self) -> str | None:
        """Why the profile cannot be switched right now (config message), else ``None``."""
        if self.session.is_busy():
            return self.config.message("profile_switch_busy")
        if self.session.has_unsaved():
            return self.config.message("profile_switch_unsaved")
        return None

    def notify(self, text: str, color: str = "") -> None:
        """Show ``text`` in the status bar and the event log."""
        self._status_bar.show_message(text, backcolor=color)
        self.ui.eventLogPanel.append(text, color)

    def close_for_switch(self) -> bool:
        """Close for a profile switch: the device stays connected for the next window and the
        unsaved-data question is not asked (a switch is refused while data exists)."""
        self._keep_device = True
        try:
            return self.close()
        finally:
            self._keep_device = False

    def _layout_key(self, name: str) -> str:
        """Each profile keeps its own layout; the default profile uses the plain keys."""
        profile = self.config.profile
        return (
            f"window/{name}"
            if profile == DEFAULT_PROFILE
            else f"window/{profile}/{name}"
        )

    def _restore_layout(self) -> None:
        settings = layout_settings()
        geometry = settings.value(self._layout_key("geometry"))
        state = settings.value(self._layout_key("state"))
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)
        ui = self.ui  # a dock hidden by the restored state may not have announced it
        for dock, action in (
            (ui.dockControls, ui.actionToggleControls),
            (ui.dockLive, ui.actionToggleLive),
            (ui.dockLog, ui.actionToggleLog),
        ):
            action.setChecked(not dock.isHidden())

    def _save_layout(self) -> None:
        settings = layout_settings()
        settings.setValue(self._layout_key("geometry"), self.saveGeometry())
        settings.setValue(self._layout_key("state"), self.saveState())

    def show_initial(self, mode: str | None = None) -> None:
        """Show the window in ``mode`` (default: ``application.window_mode``)."""
        mode = mode or self.config.get("application.window_mode", WINDOW_MODES[0])
        if mode not in WINDOW_MODES:
            _log.warning("unknown window mode %r, using %r", mode, WINDOW_MODES[0])
            mode = WINDOW_MODES[0]
        if mode == "fullscreen":
            self.showFullScreen()
        elif mode == "maximized":
            self.showMaximized()
        else:
            self.show()
        self.ui.actionFullScreen.setChecked(self.isFullScreen())

    def _setup_full_screen(self) -> None:
        self.ui.actionFullScreen.triggered.connect(self.set_fullscreen)

    @Slot(bool)
    def set_fullscreen(self, on: bool) -> None:
        """Enter or leave full screen (leaving returns to maximised or normal as before)."""
        if on == self.isFullScreen():
            return
        if on:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        elif self._was_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self.ui.actionFullScreen.setChecked(self.isFullScreen())

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        """Keep the full-screen action in sync when the OS changes the window state."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self.ui.actionFullScreen.setChecked(self.isFullScreen())

    # ==================== Window lifecycle ====================

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if not self._keep_device and not self.session.confirm_close():
            event.ignore()
            return
        if self._persist:
            self._save_layout()
        self.ctrl.cleanup(disconnect=not self._keep_device)
        if self._owns_simulation and self.simulation is not None:
            self.simulation.stop()
        event.accept()
