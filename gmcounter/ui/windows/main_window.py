# Layer: ui/windows — thin MainWindow.
# setupUi + subscribe to AppController signals → slot handlers touch widgets only.
# No reconnect/measurement/save business logic lives here.

from __future__ import annotations

import logging
from typing import Optional

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
from ..tabs.distance_law_tab import DistanceLawTab  # explicitly wired sweep tab
from ..tabs.voltage_response_tab import VoltageResponseTab  # explicitly wired sweep tab
from ..tabs.interval_repeat_tab import (
    IntervalRepeatTab,
)  # explicitly wired interval tab
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

        # Build AppController (needs status_bar for direct notifications)
        self._ctrl = AppController(
            device_manager, status_bar=self._status_bar, parent=self
        )

        # Instantiate the GM experiment tab and inject .ui containers
        self._gm_tab = GMTimingTab(parent=self)
        self._gm_tab.inject_ui_containers(
            plot_container=self.ui.timePlot,
            hist_container=self.ui.histWidget,
            table_view=self.ui.tableView,
            count_lcd=self.ui.currentCount,
            last_count_lcd=self.ui.lastCount,
            rate_lcd=self.ui.currentRate,
            tab_widget=self.ui.tabWidget,
        )
        self._gm_tab.build()

        # Register with AppController
        self._ctrl.set_active_tab(self._gm_tab)

        # ── Sweep tabs ────────────────────────────────────────────────────
        # The QWidget pages already live in .ui; inject widgets and build.
        # Sweep tabs are NOT registered in TabRegistry — they are wired here.

        # Distance-law sweep tab
        self._distance_tab = DistanceLawTab(parent=self)
        self._distance_tab.set_gm_tab(self._gm_tab)
        self._distance_tab.inject_ui(
            plot_container=self.ui.distancePlot,
            table_view=self.ui.distanceTable,
            status_label=self.ui.distanceStatus,
            param_input=self.ui.distanceInput,
        )
        self._distance_tab.build()

        # Voltage-response sweep tab — parameter comes from the device-control
        # panel (live cVoltage readback); no tab-local input spinbox.
        self._voltage_tab = VoltageResponseTab(parent=self)
        self._voltage_tab.set_gm_tab(self._gm_tab)
        self._voltage_tab.inject_ui(
            plot_container=self.ui.voltagePlot,
            table_view=self.ui.voltageTable,
            status_label=self.ui.voltageStatus,
            param_input=self.ui.sVoltage,
            param_provider=lambda: float(self.ui.cVoltage.value()),
        )
        self._voltage_tab.build()

        # Page → sweep-tab map: used by _current_sweep_tab() to resolve which
        # ParameterSweepTabBase object owns the currently-visible .ui page.
        self._sweep_tabs = {
            self.ui.distance: self._distance_tab,
            self.ui.voltage: self._voltage_tab,
        }

        # Sweep session state — True while any parameter sweep is running.
        # _active_sweep_tab holds the specific tab object for this session.
        self._sweep_session: bool = False
        self._active_sweep_tab = None  # type: ignore[assignment]

        # Interval tab
        self._interval_tab = IntervalRepeatTab(parent=self)
        self._interval_tab.inject_ui(
            plot_container=self.ui.intervalPlot,
            table_view=self.ui.intervalTable,
            width_input=self.ui.intervalWidthInput,
            repeat_input=self.ui.intervalRepeatInput,
            status_label=self.ui.intervalStatus,
        )
        self._interval_tab.build()

        # Interval session state — True while an interval measurement is active
        # (from Start until Save or Reset).
        self._interval_session: bool = False
        self._active_interval_tab: Optional[IntervalRepeatTab] = None

        # Measurement lifecycle is forwarded to the active sweep tab inside
        # _on_measurement_started / _on_measurement_stopped (below), which
        # fire after GMTimingTab via the AppController signal ordering.

        # Wire TabRegistry for any future experiments
        self._refresh_tab_visibility()

        # Connect AppController signals → MainWindow slots
        # (status_message is handled directly via StatusBarManager in AppController)
        self._ctrl.measurement_started.connect(self._on_measurement_started)
        self._ctrl.measurement_stopped.connect(self._on_measurement_stopped)
        self._ctrl.device_state_updated.connect(self._on_device_state_updated)
        self._ctrl.statistics_updated.connect(self._on_statistics_updated)
        self._ctrl.progress_updated.connect(self._on_progress_updated)
        self._ctrl.reconnect_succeeded.connect(self._on_reconnect_succeeded)
        self._ctrl.connection_lost.connect(self._on_connection_lost_terminal)

        # Connect GMTimingTab status signal to event log / status bar
        self._gm_tab.status_message.connect(self._on_tab_status)

        # Event log dock — give AppController a reference so _notify() can append
        self._event_log = EventLogPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._event_log)
        self._event_log.hide()
        self._ctrl.event_log = self._event_log

        # Wire buttons
        self._setup_buttons()
        self._setup_radioactive_sample_input()
        self._setup_detector_code_input()
        self._setup_voltage_warning()
        self._setup_global_distance_visibility()

        # Initial device info — set callback before fetch so it fires on initial connect
        device_manager.on_device_info = self._on_device_info
        if device_manager.device and device_manager.connected:
            device_manager._fetch_device_info()

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

        # Allow typing a custom duration in seconds directly into the combobox
        self.ui.sDuration.setEditable(True)

        # autoSave — gates incremental backup; reflect true initial state
        self.ui.autoSave.setChecked(False)
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

    def _setup_detector_code_input(self) -> None:
        codes = CONFIG.get("detektor_codes", [])
        self.ui.detectorCode.clear()
        self.ui.detectorCode.addItems(codes)
        self.ui.detectorCode.setCurrentIndex(-1)
        completer = QCompleter(codes)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ui.detectorCode.setCompleter(completer)

    def _setup_global_distance_visibility(self) -> None:
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed(self.ui.tabWidget.currentIndex())

    def _setup_voltage_warning(self) -> None:
        self.ui.sVoltage.valueChanged.connect(self._on_voltage_changed)

    # ------------------------------------------------------------------
    # AppController signal handlers

    def _on_tab_changed(self, index: int) -> None:
        current_page = self.ui.tabWidget.widget(index)
        on_distance_tab = current_page is self.ui.distance
        self.ui.lblDistance.setVisible(not on_distance_tab)
        self.ui.distanceGlobalDistance.setVisible(not on_distance_tab)
        if on_distance_tab:
            self.ui.distanceGlobalDistance.setValue(0.0)

        # Route frames to the interval tab when its page is selected;
        # otherwise the GM timing tab is the active receiver.
        if current_page is self.ui.interval:
            self._ctrl.set_active_tab(self._interval_tab)
        elif not self._interval_session:
            self._ctrl.set_active_tab(self._gm_tab)

    def _on_tab_status(self, level: str, text: str) -> None:
        color = {"info": "green", "warning": "orange", "error": "red"}.get(
            level, "white"
        )
        self._status_bar.show_message(text, backcolor=color)
        self._event_log.append(text, color)

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
        # Forward to the active sweep tab so it can record _session_start
        if self._active_sweep_tab is not None:
            self._active_sweep_tab.on_measurement_started()

    def _on_measurement_stopped(self) -> None:
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
        self._set_status_indicator("Gestoppt", "yellow")
        self.ui.progressBar.setMaximum(1)
        self.ui.progressBar.setValue(0)

        # Forward to the active sweep tab — GMTimingTab.on_measurement_stopped
        # fires first (connected via set_active_tab), so its export is ready.
        if self._active_sweep_tab is not None:
            self._active_sweep_tab.on_measurement_stopped()

        if self._sweep_session:
            # In a sweep session Start stays enabled so the user can fire the
            # next measurement point immediately; unsaved state is tracked by
            # the sweep tab, not _save_service.
            self.ui.buttonStart.setEnabled(True)
        elif self._interval_session:
            # Interval session: Start disabled until data is saved or reset.
            # interval_tab.on_measurement_stopped() fires via the ctrl signal.
            self.ui.buttonStart.setEnabled(False)
        else:
            # Normal mode: Start disabled until data is saved/reset.
            self.ui.buttonStart.setEnabled(False)
            self._save_service.mark_unsaved()

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
    #
    # The same Start / Stop / Speichern / Reset buttons serve both the normal
    # GM timing mode and any parameter-sweep tab (Abstandsgesetz, etc.).
    # _current_sweep_tab() returns the active sweep tab when one is selected;
    # None otherwise.  Button logic branches on that single check.

    def _current_sweep_tab(self):
        """Return the ParameterSweepTabBase for the currently-selected page, or None.

        Sweep tab objects are separate Python instances injected into plain .ui
        page widgets — the page widget itself is not a ParameterSweepTabBase.
        The _sweep_tabs dict maps each .ui page QWidget to its owner tab object.
        """
        return self._sweep_tabs.get(self.ui.tabWidget.currentWidget())

    def _current_interval_tab(self):
        """Return the IntervalRepeatTab if the interval page is active, else None."""
        return (
            self._interval_tab
            if self.ui.tabWidget.currentWidget() is self.ui.interval
            else None
        )

    def _parse_duration_s(self) -> int:
        """Parse the sDuration combobox to total seconds.

        Preset indices map directly; if the user typed a custom value
        (currentIndex == -1), it is parsed as a float and rounded.
        Returns 0 (infinite) for the 'unendlich' preset or invalid input.
        """
        seconds_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        idx = int(self.ui.sDuration.currentIndex())
        if idx in seconds_map:
            return seconds_map[idx]
        try:
            return max(0, int(round(float(self.ui.sDuration.currentText()))))
        except ValueError:
            return 0

    def _set_sweep_lock(self, locked: bool, active_page=None) -> None:
        """Lock or unlock tab navigation during a sweep session.

        When *locked*, every tab page is disabled except *active_page* (the
        sweep tab the user is currently running), so they cannot accidentally
        switch tabs mid-measurement.  When unlocked, all pages are re-enabled.
        """
        for idx in range(self.ui.tabWidget.count()):
            page = self.ui.tabWidget.widget(idx)
            self.ui.tabWidget.setTabEnabled(idx, (not locked) or page is active_page)

    def _handle_start(self) -> None:
        sweep = self._current_sweep_tab()
        interval = self._current_interval_tab()

        if interval is not None:
            # ── Interval/Repeat mode ─────────────────────────────────────
            total = int(interval.width_s * interval.repeat_count)

            self._interval_session = True
            self._active_interval_tab = interval
            active_page = self.ui.tabWidget.currentWidget()
            self._set_sweep_lock(True, active_page)
            self._gm_tab.set_high_speed_autoswitch(False)

            self._ctrl.start_measurement(total_seconds=total)

        elif sweep is not None:
            # ── Sweep mode ──────────────────────────────────────────────
            total = self._parse_duration_s()

            if total == 0 and not self._sweep_session:
                # Warn on infinite time only at the first measurement of a session
                if not MessageHelper.ask_question(
                    self,
                    "Die Messzeit ist auf 'unbegrenzt' eingestellt.\n\n"
                    "Für Sweep-Messungen empfiehlt sich eine feste Messzeit, "
                    "damit alle Messpunkte vergleichbar sind.\n\n"
                    "Trotzdem fortfahren?",
                    "Hinweis: unbegrenzte Messzeit",
                ):
                    return

            # Previous data already captured in on_measurement_stopped; bypass
            # the unsaved-data guard for repeat measurements in the same session.
            self._save_service.mark_saved()

            if not self._sweep_session:
                # First measurement of this sweep session: record which sweep
                # tab is active, lock other tabs, and suppress high-speed
                # auto-switch to Histogramm.
                self._sweep_session = True
                self._active_sweep_tab = sweep
                active_page = self.ui.tabWidget.currentWidget()
                self._set_sweep_lock(True, active_page)
                self._gm_tab.set_high_speed_autoswitch(False)

            # For tabs that require device voltage to be applied on each
            # measurement (e.g. VoltageResponseTab), push the current setpoint
            # to the device now so the live cVoltage readback is up-to-date.
            if sweep.applies_device_voltage_on_start:
                self._handle_apply_settings()

            self._gm_tab.set_measurement_metadata(
                rad_sample=self.ui.radSample.currentText(),
                group=self.ui.groupLetter.currentText(),
                subterm=self.ui.suffix.text().strip(),
            )
            self._ctrl.start_measurement(total_seconds=total)

        else:
            # ── Normal GM timing mode ────────────────────────────────────
            if self._save_service.has_unsaved():
                MessageHelper.show_warning(
                    self,
                    "Bitte speichern oder löschen Sie die vorhandenen Messdaten.",
                    "Warnung",
                )
                return

            total = self._parse_duration_s()
            self._gm_tab.set_measurement_metadata(
                rad_sample=self.ui.radSample.currentText(),
                group=self.ui.groupLetter.currentText(),
                subterm=self.ui.suffix.text().strip(),
            )
            self._ctrl.start_measurement(total_seconds=total)

    def _handle_stop(self) -> None:
        self._ctrl.stop_measurement()

    def _handle_save(self) -> None:
        from ...infrastructure.save_service import write_export

        interval = self._active_interval_tab
        if self._interval_session and interval is not None and interval.has_data():
            # ── Interval save: summary CSV + per-interval CSVs ────────────
            summary = interval.summary_export()
            if not summary:
                MessageHelper.show_info(
                    self, "Keine Intervalldaten vorhanden.", "Information"
                )
                return

            extra: dict = {}
            detector = self.ui.detectorCode.currentText().strip()
            if detector:
                extra["detector_code"] = detector
            if extra:
                summary.metadata.update(extra)

            saved = self._file_dialog_manager.manual_save_export(
                self,
                summary,
                self.ui.radSample.currentText(),
                self.ui.groupLetter.currentText(),
                self.ui.suffix.text().strip(),
            )
            if not saved or not saved.exists():
                return

            per_interval = interval.interval_exports
            ok_count = 0
            for exp in per_interval:
                if extra:
                    exp.metadata.update(extra)
                auto_name = f"{saved.stem}_{exp.filename_hint}.csv"
                try:
                    write_export(exp, saved.parent / auto_name)
                    ok_count += 1
                except Exception as exc:
                    _log.warning(
                        "Could not write interval export %s: %s", auto_name, exc
                    )

            interval.mark_saved()
            interval.reset()
            self._interval_session = False
            self._active_interval_tab = None
            self._set_sweep_lock(False)
            self._gm_tab.set_high_speed_autoswitch(True)
            self._save_service.mark_saved()
            self._ctrl.finalize_journal()

            self.ui.buttonSave.setEnabled(False)
            self.ui.buttonStart.setEnabled(True)
            n = len(per_interval)
            self._status_bar.show_message(
                f"Zusammenfassung gespeichert. {ok_count}/{n} Intervall-CSV(s) exportiert.",
                duration=5000,
            )
            self._set_status_indicator("Bereit", "green")
            return

        sweep = self._active_sweep_tab
        if self._sweep_session and sweep is not None and sweep.has_data():
            # ── Sweep save: summary CSV + auto-named individual timing CSVs ──
            summary = sweep.summary_export()
            if not summary:
                MessageHelper.show_info(
                    self, "Keine Zusammenfassungsdaten vorhanden.", "Information"
                )
                return

            # Inject shared metadata into the summary
            sweep_extra: dict = {}
            detector = self.ui.detectorCode.currentText().strip()
            if detector:
                sweep_extra["detector_code"] = detector
            global_dist = self.ui.distanceGlobalDistance.value()
            if global_dist > 0.0:
                sweep_extra["sample_distance_cm"] = global_dist
            if sweep_extra:
                summary.metadata.update(sweep_extra)

            saved = self._file_dialog_manager.manual_save_export(
                self,
                summary,
                self.ui.radSample.currentText(),
                self.ui.groupLetter.currentText(),
                self.ui.suffix.text().strip(),
            )
            if not saved or not saved.exists():
                return

            # Auto-write individual timing exports alongside the summary.
            # File name encodes the parameter value and measurement index.
            individual = sweep.individual_exports
            ok_count = 0
            for i, exp in enumerate(individual):
                if sweep_extra:
                    exp.metadata.update(sweep_extra)
                param_val = exp.metadata.get(sweep.param_metadata_key, "?")
                auto_name = (
                    f"{saved.stem}_p{param_val}{sweep.param_unit}_m{i + 1:02d}.csv"
                )
                try:
                    write_export(exp, saved.parent / auto_name)
                    ok_count += 1
                except Exception as exc:
                    _log.warning(
                        "Could not write individual export %s: %s", auto_name, exc
                    )

            # Tear down sweep session
            sweep.mark_saved()
            sweep.reset_summary()
            self._sweep_session = False
            self._active_sweep_tab = None
            self._set_sweep_lock(False)
            self._gm_tab.set_high_speed_autoswitch(True)
            self._gm_tab.on_reset()
            self._save_service.mark_saved()
            self._ctrl.finalize_journal()

            self.ui.buttonSave.setEnabled(False)
            self.ui.buttonStart.setEnabled(True)
            n = len(individual)
            self._status_bar.show_message(
                f"Zusammenfassung gespeichert. {ok_count}/{n} Einzelmessung(en) exportiert.",
                duration=5000,
            )
            self._set_status_indicator("Bereit", "green")

        else:
            # ── Normal single-measurement save ───────────────────────────
            if not self._save_service.has_unsaved():
                MessageHelper.show_info(
                    self, "Keine ungespeicherten Daten.", "Information"
                )
                return

            export = self._gm_tab.export()
            if not export:
                MessageHelper.show_error(
                    self, "Keine Messdaten zum Speichern.", "Fehler"
                )
                return

            extra = {"gui_version": gmcounter.__version__}
            openbis = self.ui.cOpenbis.text()
            if openbis and openbis != "unknown":
                extra["counter_openbis_code"] = openbis
            fw = self.ui.cVersion.text()
            if fw and fw != "unknown":
                extra["counter_firmware_version"] = fw
            if export.rows:
                extra["total_count"] = len(export.rows)
            detector = self.ui.detectorCode.currentText().strip()
            if detector:
                extra["detector_code"] = detector
            global_dist = self.ui.distanceGlobalDistance.value()
            if global_dist > 0.0:
                extra["sample_distance_cm"] = global_dist
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
                self._ctrl.finalize_journal()
                self.ui.buttonSave.setEnabled(False)
                self.ui.buttonStart.setEnabled(True)
                self._status_bar.show_message("Gespeichert.", duration=3000)
            else:
                MessageHelper.show_error(self, "Fehler beim Speichern.", "Fehler")

    def _handle_reset(self) -> None:
        if self._ctrl.is_measuring:
            MessageHelper.show_warning(self, "Messung läuft.", "Warnung")
            return

        if self._interval_session:
            interval = self._active_interval_tab
            if interval is not None and interval.has_data():
                if not MessageHelper.ask_question(
                    self,
                    CONFIG.get("messages", {}).get(
                        "unsaved_data", "Messdaten verwerfen?"
                    ),
                    "Warnung",
                ):
                    return
            if interval is not None:
                interval.reset()
            self._interval_session = False
            self._active_interval_tab = None
            self._set_sweep_lock(False)
            self._gm_tab.set_high_speed_autoswitch(True)
            self._save_service.mark_saved()
            self.ui.buttonSave.setEnabled(False)
            self.ui.buttonStart.setEnabled(True)
            self._set_status_indicator("Bereit", "green")
            return

        if self._sweep_session:
            # Discard the entire sweep session without saving
            sweep = self._active_sweep_tab
            if sweep is not None and sweep.has_data():
                if not MessageHelper.ask_question(
                    self,
                    CONFIG.get("messages", {}).get(
                        "unsaved_data", "Messdaten verwerfen?"
                    ),
                    "Warnung",
                ):
                    return
            if sweep is not None:
                sweep.reset_summary()
            self._sweep_session = False
            self._active_sweep_tab = None
            self._set_sweep_lock(False)
            self._gm_tab.set_high_speed_autoswitch(True)
        else:
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
            counting_time=0,  # always infinite — host controls duration via delta accumulation
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
