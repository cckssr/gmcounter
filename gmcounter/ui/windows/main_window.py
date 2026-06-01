# Layer: ui/windows — thin MainWindow.
# setupUi + subscribe to AppController signals → slot handlers touch widgets only.
# No reconnect/measurement/save business logic lives here.

from __future__ import annotations

import logging

import gmcounter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QCompleter

from ...infrastructure.config import import_config
from ...infrastructure.device_manager import DeviceManager
from ...infrastructure.modules.registry import ModuleRegistry
from ...core.services import SaveService
from ..controllers.app_controller import AppController
from ..tabs.registry import TabRegistry
from ..tabs.gm_timing_tab import GMTimingTab  # registers at import time
from ..widgets.event_log_panel import EventLogPanel
from ..common import dialogs as MessageHelper
from ..common.file_dialogs import FileDialogManager
from ..common.statusbar import StatusBarManager
from ...pyqt.ui_mainwindow import Ui_MainWindow

_log = logging.getLogger(__name__)
CONFIG = import_config()

# Named color values for the status LED
_LED_COLORS = {
    "green": "rgb(50, 205, 50)",
    "blue": "rgb(30, 144, 255)",
    "orange": "rgb(255, 140, 0)",
    "yellow": "rgb(255, 215, 0)",
    "red": "rgb(255, 11, 3)",
    "gray": "rgb(128, 128, 128)",
}


class MainWindow(QMainWindow):
    """Main application window — chrome only.

    Business logic lives in:
    - AppController: timers, reconnect FSM, measurement start/stop
    - GMTimingTab: data accumulation, plots, export
    """

    def __init__(self, device_manager: DeviceManager, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._status_bar = StatusBarManager(self.ui.statusBar)

        self._save_service = SaveService(
            base_dir=CONFIG.get("save", {}).get("base_folder", "GMCounter"),
            tk_designation=CONFIG.get("save", {}).get("tk_designation", "TK47"),
        )
        self._file_dialog_manager = FileDialogManager(self._save_service)

        # Build AppController
        self._ctrl = AppController(device_manager, parent=self)

        # Instantiate the GM experiment tab and inject .ui containers
        self._gm_tab = GMTimingTab(parent=self)
        self._gm_tab.inject_ui_containers(
            plot_container=self.ui.timePlot,
            hist_container=self.ui.histWidget,
            table_view=self.ui.tableView,
            count_lcd=self.ui.currentCount,
            last_count_lcd=self.ui.lastCount,
            tab_widget=self.ui.tabWidget,
        )
        self._gm_tab.build()

        # Register with AppController
        self._ctrl.set_active_tab(self._gm_tab)

        # Wire TabRegistry for any future experiments
        self._refresh_tab_visibility()

        # Connect AppController signals → MainWindow slots
        self._ctrl.status_message.connect(self._on_status_message)
        self._ctrl.measurement_started.connect(self._on_measurement_started)
        self._ctrl.measurement_stopped.connect(self._on_measurement_stopped)
        self._ctrl.device_state_updated.connect(self._on_device_state_updated)
        self._ctrl.statistics_updated.connect(self._on_statistics_updated)
        self._ctrl.progress_updated.connect(self._on_progress_updated)
        self._ctrl.reconnect_succeeded.connect(self._on_reconnect_succeeded)
        self._ctrl.connection_lost.connect(self._on_connection_lost_terminal)

        # Connect GMTimingTab status signal to event log / status bar
        self._gm_tab.status_message.connect(self._on_tab_status)

        # Event log dock
        self._event_log = EventLogPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._event_log)
        self._event_log.hide()

        # Wire buttons
        self._setup_buttons()
        self._setup_radioactive_sample_input()
        self._setup_voltage_warning()

        # Initial device info
        if device_manager.device and device_manager.connected:
            device_manager._fetch_device_info()
        device_manager.on_device_info = self._on_device_info

        # Initial status
        self._set_status_indicator("Bereit", "green")
        self._status_bar.show_message(
            CONFIG.get("messages", {})
            .get("connected", "Verbunden mit {0}")
            .format(device_manager.port),
            duration=3000,
        )

        # Maximize
        self.setGeometry(self.screen().availableGeometry())
        self.show()

    # ------------------------------------------------------------------
    # Tab registry

    def _refresh_tab_visibility(self) -> None:
        """Show/hide module-gated experiment tabs based on the ModuleRegistry."""
        modules = ModuleRegistry.all()
        for tab_class in TabRegistry.available(modules):
            if tab_class is GMTimingTab:
                continue  # Already contributed via setupUi + inject
            # Future experiments contribute their own tabs
            tab_class().contribute_tabs(self.ui.tabWidget)

    # ------------------------------------------------------------------
    # Button wiring

    def _setup_buttons(self) -> None:
        self.ui.buttonStart.clicked.connect(self._handle_start)
        self.ui.buttonStop.clicked.connect(self._handle_stop)
        self.ui.buttonSave.clicked.connect(self._handle_save)
        self.ui.buttonReset.clicked.connect(self._handle_reset)
        self.ui.buttonSetting.clicked.connect(self._handle_apply_settings)

        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonReset.setEnabled(False)

        # autoSave — gates incremental backup; reflect true initial state
        self.ui.autoSave.setChecked(True)
        self.ui.autoSave.toggled.connect(self._on_auto_save_toggled)

        self.ui.autoScroll.toggled.connect(self._on_auto_scroll_toggled)
        self.ui.sPlotpoints.valueChanged.connect(self._on_plot_points_changed)
        self.ui.buttonAutoRange.clicked.connect(self._on_auto_range)

        if self._gm_tab._plot:
            self._gm_tab._plot.user_interaction_detected.connect(
                self._on_plot_user_interaction
            )

        # Bug fix §6: enable auto-query radios (were disabled in .ui)
        if hasattr(self.ui, "sQModeMan"):
            self.ui.sQModeMan.setEnabled(True)
        if hasattr(self.ui, "sQModeAuto"):
            self.ui.sQModeAuto.setEnabled(True)

        if self.ui.autoScroll.isChecked():
            self._on_auto_scroll_toggled(True)

    def _setup_radioactive_sample_input(self) -> None:
        samples = CONFIG.get("radioactive_samples", [])
        self.ui.radSample.clear()
        self.ui.radSample.addItems(samples)
        self.ui.radSample.setCurrentIndex(-1)
        completer = QCompleter(samples)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ui.radSample.setCompleter(completer)

    def _setup_voltage_warning(self) -> None:
        self.ui.sVoltage.valueChanged.connect(self._on_voltage_changed)

    # ------------------------------------------------------------------
    # AppController signal handlers

    def _on_status_message(self, text: str, color: str) -> None:
        self._status_bar.show_message(text)
        self._event_log.append(text, color)

    def _on_tab_status(self, level: str, text: str) -> None:
        color = {"info": "green", "warning": "orange", "error": "red"}.get(
            level, "white"
        )
        self._on_status_message(text, color)

    def _on_measurement_started(self) -> None:
        self.ui.buttonStart.setEnabled(False)
        self.ui.buttonStop.setEnabled(True)
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonReset.setEnabled(False)
        # Lock all device-settings controls — only binary acquisition runs now
        self.ui.buttonSetting.setEnabled(False)
        self.ui.sVoltage.setEnabled(False)
        self.ui.sDuration.setEnabled(False)
        self.ui.sModeMulti.setEnabled(False)
        if hasattr(self.ui, "sQModeAuto"):
            self.ui.sQModeAuto.setEnabled(False)
        if hasattr(self.ui, "sQModeMan"):
            self.ui.sQModeMan.setEnabled(False)
        self._set_status_indicator("Messung", "blue")

    def _on_measurement_stopped(self) -> None:
        self.ui.buttonStart.setEnabled(False)  # disabled until data saved/reset
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(True)
        self.ui.buttonReset.setEnabled(True)
        # Restore all device-settings controls
        self.ui.buttonSetting.setEnabled(True)
        self.ui.sVoltage.setEnabled(True)
        self.ui.sDuration.setEnabled(True)
        self.ui.sModeMulti.setEnabled(True)
        if hasattr(self.ui, "sQModeAuto"):
            self.ui.sQModeAuto.setEnabled(True)
        if hasattr(self.ui, "sQModeMan"):
            self.ui.sQModeMan.setEnabled(True)
        self._save_service.mark_unsaved()
        self._set_status_indicator("Gestoppt", "yellow")

    def _on_device_state_updated(self, data: dict) -> None:
        label_map = CONFIG.get("gm_counter", {}).get("label_map", {})
        self.ui.currentCount.display(data.get("count", 0))
        self.ui.lastCount.display(data.get("last_count", 0))
        self.ui.cVoltage.display(data.get("voltage", 0))
        self.ui.cDuration.display(data.get("counting_time", 0))
        repeat = data.get("repeat", False)
        self.ui.cMode.setText(
            label_map.get("repeat_on", "Repeat On")
            if repeat
            else label_map.get("repeat_off", "Repeat Off")
        )

    def _on_statistics_updated(self, stats: dict) -> None:
        if stats.get("count", 0) > 1:
            self.ui.cStatPoints.setText(f"{stats.get('count', 0):.0f}")
            self.ui.cStatMin.setText(f"{stats.get('min', 0):.0f}")
            self.ui.cStatMax.setText(f"{stats.get('max', 0):.0f}")
            self.ui.cStatAvg.setText(f"{stats.get('avg', 0):.0f}")
            self.ui.cStatSD.setText(f"{stats.get('stdev', 0):.0f}")

    def _on_progress_updated(self, elapsed: int, total: int) -> None:
        self.ui.progressTimer.setText(f"{elapsed}s")
        if total > 0:
            self.ui.progressBar.setMaximum(total)
            self.ui.progressBar.setValue(elapsed)
        else:
            self.ui.progressBar.setMaximum(0)  # indeterminate

    def _on_reconnect_succeeded(self) -> None:
        self.ui.buttonStart.setEnabled(True)
        self._set_status_indicator("Verbunden", "green")

    def _on_connection_lost_terminal(self) -> None:
        self._set_status_indicator("Getrennt", "red")
        MessageHelper.show_error(
            self,
            "Verbindung verloren.\n\nAlle Wiederverbindungsversuche fehlgeschlagen.",
            "Verbindungsfehler",
        )

    def _on_device_info(self, info: dict) -> None:
        self.ui.cVersion.setText(info.get("version", ""))
        self.ui.cOpenbis.setText(info.get("openbis", ""))

    # ------------------------------------------------------------------
    # Measurement button handlers

    def _handle_start(self) -> None:
        if self._save_service.has_unsaved():
            MessageHelper.show_warning(
                self,
                "Bitte speichern oder löschen Sie die vorhandenen Messdaten.",
                "Warnung",
            )
            return

        seconds_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        idx = int(self.ui.sDuration.currentIndex())
        total = seconds_map.get(idx, 0)
        if total == 0:
            total = 0  # indeterminate

        self._gm_tab.set_measurement_metadata(
            rad_sample=self.ui.radSample.currentText(),
            group=self.ui.groupLetter.currentText(),
            subterm=self.ui.suffix.text().strip(),
        )
        self._ctrl.start_measurement(total_seconds=total)

    def _handle_stop(self) -> None:
        self._ctrl.stop_measurement()

    def _handle_save(self) -> None:
        if not self._save_service.has_unsaved():
            MessageHelper.show_info(self, "Keine ungespeicherten Daten.", "Information")
            return

        export = self._gm_tab.export()
        if not export:
            MessageHelper.show_error(self, "Keine Messdaten zum Speichern.", "Fehler")
            return

        # Collect extended metadata
        extra = {
            "gui_version": gmcounter.__version__,
        }
        dist = self.ui.sampleDistance.value()
        if dist != 0:
            extra["sample_distance_cm"] = dist
        openbis = self.ui.cOpenbis.text()
        if openbis and openbis != "unknown":
            extra["counter_openbis_code"] = openbis
        fw = self.ui.cVersion.text()
        if fw and fw != "unknown":
            extra["counter_firmware_version"] = fw
        if export.rows:
            extra["total_count"] = len(export.rows)

        export.metadata.update(extra)

        saved = self._file_dialog_manager.manual_save_export(
            self,
            export,
            self.ui.radSample.currentText(),
            self.ui.groupLetter.currentText(),
            self.ui.suffix.text().strip(),
        )

        if saved and saved.exists():
            self._save_service.mark_saved()
            self.ui.buttonSave.setEnabled(False)
            self.ui.buttonStart.setEnabled(True)
            self._status_bar.show_message("Gespeichert.", duration=3000)
        else:
            MessageHelper.show_error(self, "Fehler beim Speichern.", "Fehler")

    def _handle_reset(self) -> None:
        if self._ctrl.is_measuring:
            MessageHelper.show_warning(self, "Messung läuft.", "Warnung")
            return
        if self._save_service.has_unsaved():
            if not MessageHelper.ask_question(
                self,
                CONFIG.get("messages", {}).get("unsaved_data", "Daten verwerfen?"),
                "Warnung",
            ):
                return
        self._gm_tab.on_reset()
        self._save_service.mark_saved()
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonStart.setEnabled(True)
        self._set_status_indicator("Bereit", "green")

    def _handle_apply_settings(self) -> None:
        # Bug fix §6: read repeat from sModeMulti radio (not the broken cMode.text() check)
        repeat = self.ui.sModeMulti.isChecked()
        # Bug fix §6: auto-query enabled end-to-end via sQModeAuto radio
        auto_query = hasattr(self.ui, "sQModeAuto") and self.ui.sQModeAuto.isChecked()
        self._ctrl.apply_settings(
            voltage=int(self.ui.sVoltage.value()),
            counting_time=int(self.ui.sDuration.currentIndex()),
            repeat=repeat,
            auto_query=auto_query,
        )

    # ------------------------------------------------------------------
    # Plot / scroll handlers

    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        if self._gm_tab._plot:
            if checked:
                self._gm_tab._plot.set_auto_scroll(True, self.ui.sPlotpoints.value())
            else:
                self._gm_tab._plot.set_auto_scroll(False)

    def _on_plot_points_changed(self, value: int) -> None:
        if self.ui.autoScroll.isChecked() and self._gm_tab._plot:
            self._gm_tab._plot.set_auto_scroll(True, value)

    def _on_auto_range(self) -> None:
        if self._gm_tab._plot:
            self._gm_tab._plot.enable_auto_range(True)
        self.ui.autoScroll.setChecked(True)

    def _on_plot_user_interaction(self) -> None:
        if self.ui.autoScroll.isChecked():
            self.ui.autoScroll.setChecked(False)

    def _on_auto_save_toggled(self, checked: bool) -> None:
        msg = (
            CONFIG.get("messages", {}).get("auto_save_enabled", "Auto-Backup aktiviert")
            if checked
            else CONFIG.get("messages", {}).get(
                "auto_save_disabled", "Auto-Backup deaktiviert"
            )
        )
        self._status_bar.show_message(msg, duration=1000)

    def _on_voltage_changed(self, value: int) -> None:
        threshold = CONFIG.get("gm_counter", {}).get("voltage_warning_threshold", 650)
        if value > threshold:
            self.ui.sVoltage.setStyleSheet("background-color: orange;")
            self._status_bar.show_message(
                CONFIG.get("messages", {})
                .get("voltage_warning", "Achtung: {0} V")
                .format(value),
                duration=3000,
            )
        else:
            self.ui.sVoltage.setStyleSheet("")

    # ------------------------------------------------------------------
    # Status indicator

    def _set_status_indicator(self, status: str, color: str) -> None:
        led_color = _LED_COLORS.get(color, _LED_COLORS["gray"])
        self.ui.statusLED.setStyleSheet(
            f"background-color: {led_color}; border: 0px; padding: 4px; border-radius: 10px"
        )
        self.ui.statusText.setText(status)

    # ------------------------------------------------------------------
    # Window lifecycle

    def closeEvent(self, event) -> None:
        if self._save_service.has_unsaved():
            if not MessageHelper.ask_question(
                self,
                CONFIG.get("messages", {}).get(
                    "unsaved_data_end", "Daten nicht gespeichert. Trotzdem schließen?"
                ),
                "Warnung",
            ):
                event.ignore()
                return
        self._ctrl.cleanup()
        event.accept()
