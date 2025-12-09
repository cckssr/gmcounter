# -*- coding: utf-8 -*-
from datetime import datetime
import time
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QMainWindow,
    QVBoxLayout,
    QCompleter,
)
from PySide6.QtCore import QTimer, Qt  # pylint: disable=no-name-in-module
import gmcounter
from ...infrastructure.device_manager import DeviceManager
from ...core.reconnect_service import ConnectionRetryService
from ...ui.controllers.control import ControlWidget
from ..widgets.plot import GeneralPlot, HistogramWidget, PlotConfig
from ...infrastructure.logging import Debug
from ...infrastructure.config import import_config
from ...helper_classes_compat import Statusbar
from ...core.services import SaveService
from ..common import dialogs as MessageHelper
from ..common.file_dialogs import FileDialogManager
from ...pyqt.ui_mainwindow import Ui_MainWindow
from ..controllers.data_controller import DataController


# Import settings and messages
CONFIG = import_config()


class MainWindow(QMainWindow):
    """Main window of the GMCounter application.

    It handles the user interface, the device connection and the
    processing of the recorded data.  The implementation is split
    into several functional sections:

    1. Initialization and setup
    2. Data processing and statistics
    3. Measurement management
    4. UI event handlers
    5. Device control
    6. Helper functions
    """

    def __init__(self, device_manager: DeviceManager, parent=None):
        """Initialise the main window and all components.

        Args:
            device_manager: The connected device manager.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Measurement status
        self.is_measuring = False
        self.data_saved = True
        self.save_service = SaveService(
            base_dir=CONFIG.get("save", {}).get("base_folder", "GMCounter"),
            tk_designation=CONFIG.get("save", {}).get("tk_designation", "TK47"),
        )
        # FileDialogManager is only used for UI dialogs (file picker)
        self.file_dialog_manager = FileDialogManager(self.save_service)
        self.measurement_start = None
        self.measurement_end = None
        self._elapsed_seconds = 0
        self._measurement_timer: QTimer | None = None

        # Reconnection service
        self.reconnect_service = ConnectionRetryService(
            max_attempts=CONFIG.get("connection", {}).get("max_retry_attempts", 5),
            initial_delay_ms=CONFIG.get("connection", {}).get(
                "initial_retry_delay_ms", 500
            ),
        )

        # Initialize status bar for user feedback
        self.statusbar = Statusbar(self.ui.statusBar)
        self.statusbar.temp_message(CONFIG["messages"]["app_init"])

        # Set up device manager
        self._setup_device_manager(device_manager)

        # Initialise UI components
        self._setup_plot()
        self._setup_data_controller()
        self._setup_controls()
        self._setup_buttons()
        self._setup_radioactive_sample_input()
        self._setup_timers()

        # Initial update of the UI
        self._update_control_display()

        # Show success message
        self.statusbar.temp_message(
            CONFIG["messages"]["connected"].format(self.device_manager.port),
            CONFIG["colors"]["green"],
        )

        # Set initial status indicator
        self._update_status_indicator("Bereit", "green")

        # Maximize window on startup
        self.showMaximized()

    #
    # 1. INITIALIZATION AND SETUP
    #

    def _setup_device_manager(self, device_manager: DeviceManager):
        """Configure the device manager and connect signals.

        Args:
            device_manager: The device manager instance to use.
        """
        self.device_manager = device_manager

        # Connect DeviceManager signals to MainWindow slots
        # CRITICAL: Use Qt.QueuedConnection to ensure thread-safe signal delivery
        # The data_received signal comes from DataAcquisitionThread (background)
        # and MUST be queued to avoid blocking the acquisition thread
        self.device_manager.data_received.connect(
            self.handle_data, Qt.ConnectionType.QueuedConnection
        )
        self.device_manager.status_update.connect(self.statusbar.temp_message)
        self.device_manager.device_info_received.connect(self._update_device_info)

        # Connect connection loss signal to handle unexpected disconnections
        self.device_manager.connection_lost.connect(
            self._handle_connection_lost, Qt.ConnectionType.QueuedConnection
        )

        # Ensure the acquisition thread forwards data to this window. When the
        # connection dialog created the DeviceManager the acquisition thread may
        # already be running without our callback connected.
        self.device_manager.start_acquisition()

        # Request device info again since it may have been emitted before we connected the signal
        if self.device_manager.device and self.device_manager.connected:
            self.device_manager._fetch_device_info()

    def _update_device_info(self, info: dict):
        """Update the UI with device information.

        Args:
            info: Dictionary containing 'version', 'copyright', and 'openbis' keys.
        """
        Debug.info(f"Updating device info in UI: {info}")

        version = info.get("version", "unknown")
        openbis = info.get("openbis", "unknown")

        # Update UI labels
        self.ui.cVersion.setText(version)
        self.ui.cOpenbis.setText(openbis)

    def _setup_controls(self):
        self.control = ControlWidget(
            device_manager=self.device_manager,
        )

    def _setup_plot(self):
        """Initialise the plot widget."""
        background_color = (
            self.ui.timePlot.palette().color(self.ui.timePlot.backgroundRole()).name()
        )
        # Time plot
        time_plot_config = PlotConfig(
            xlabel=CONFIG["plot"]["x_label"],
            ylabel=CONFIG["plot"]["y_label"],
            max_plot_points=CONFIG["plot"]["max_points"],
            background_color=background_color,
            fontsize=self.ui.timePlot.fontInfo().pixelSize() + 1,
        )

        self.plot = GeneralPlot(
            config=time_plot_config,
        )
        QVBoxLayout(self.ui.timePlot).addWidget(self.plot)

        hist_plot_config = PlotConfig(
            xlabel=CONFIG["histogram"]["x_label"],
            ylabel=CONFIG["histogram"]["y_label"],
            background_color=background_color,
            fontsize=self.ui.timePlot.fontInfo().pixelSize(),
        )
        # Histogram plot
        self.histogram = HistogramWidget(
            xlabel=CONFIG["histogram"]["x_label"],
            ylabel=CONFIG["histogram"]["y_label"],
        )
        QVBoxLayout(self.ui.histWidget).addWidget(self.histogram)

    def _setup_data_controller(self):
        """Initialise the data controller."""
        self.data_controller = DataController(
            plot_widget=self.plot,
            display_widget=self.ui.currentCount,
            histogram_widget=self.histogram,
            table_widget=self.ui.tableView,
            max_history=CONFIG["data_controller"]["max_history_size"],
        )

        # Connect HIGH_SPEED_MODE signal
        self.data_controller.high_speed_mode_changed.connect(
            self._handle_high_speed_mode_change
        )

    def _setup_buttons(self):
        """Connect buttons to their respective callbacks."""
        # Connect measurement buttons
        self.ui.buttonStart.clicked.connect(self._start_measurement)
        self.ui.buttonStop.clicked.connect(self._stop_measurement)
        self.ui.buttonSave.clicked.connect(self._save_measurement)
        self.ui.buttonReset.clicked.connect(self._clear_data)
        self.ui.buttonSetting.clicked.connect(self._apply_settings)

        # Initial state of buttons
        self.ui.buttonStart.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonReset.setEnabled(False)

        # Check auto-save setting (checkbox is for UI only, backup always runs)
        self.ui.autoSave.setChecked(
            True
        )  # Show as enabled since backup is always active
        self.ui.autoSave.toggled.connect(self._change_auto_save)

        # Connect autoScroll checkbox
        self.ui.autoScroll.toggled.connect(self._handle_auto_scroll)

        # Connect sPlotpoints spinbox
        self.ui.sPlotpoints.valueChanged.connect(self._handle_plot_points_changed)

        # Connect buttonAutoRange
        self.ui.buttonAutoRange.clicked.connect(self._handle_auto_range_button)

        # Connect plot's user interaction signal
        self.plot.user_interaction_detected.connect(self._handle_plot_user_interaction)

        # Initialize auto-scroll if checkbox is already checked
        if self.ui.autoScroll.isChecked():
            self._handle_auto_scroll(True)

    def _setup_radioactive_sample_input(self):
        """Initialise the input field for radioactive samples."""
        samples = CONFIG["radioactive_samples"]
        rad_dropdown = self.ui.radSample
        rad_dropdown.clear()
        rad_dropdown.addItems(samples)
        Debug.debug(
            f"Radioaktive Proben geladen: {len(samples)} Proben",
        )
        rad_dropdown.setCurrentIndex(-1)  # No default selection

        # QCompleter for radioactive samples
        completer = QCompleter(samples)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        rad_dropdown.setCompleter(completer)

    def _setup_timers(self):
        """Initialise timers used by the application.

        Measurement data are acquired in the background by ``DeviceManager``
        while configuration polling happens only when no measurement is running.
        This keeps the acquisition loop free of ``sleep`` calls and the GUI
        responsive.
        """
        # Timer for control updates
        self.control_update_timer = QTimer(self)
        self.control_update_timer.timeout.connect(self._update_control_display)
        self.control_update_timer.start(CONFIG["timers"]["control_update_interval"])

        # Timer for statistics updates (UI only)
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(CONFIG["timers"]["statistics_update_interval"])

        # Timer for auto-backup every 30 seconds during measurement
        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self._auto_backup_measurement)
        # Timer wird nur während der Messung gestartet

    #
    # 2a. MEASUREMENT CONTROL
    #

    def _set_ui_measuring_state(self) -> None:
        """Put the UI into measurement mode."""
        self.control_update_timer.stop()
        self.ui.buttonStart.setEnabled(False)
        self.ui.buttonSetting.setEnabled(False)
        self.ui.buttonStop.setEnabled(True)
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonReset.setEnabled(False)
        Debug.debug("UI in Messmodus gesetzt")

    def _set_ui_idle_state(self) -> None:
        """Return the UI to idle mode after a measurement."""
        # Verzögere Timer-Start um 500ms, damit Device Zeit hat, den Stopp-Befehl zu verarbeiten
        QTimer.singleShot(
            500,
            lambda: self.control_update_timer.start(
                CONFIG["timers"]["control_update_interval"]
            ),
        )

        # Start nur aktivieren wenn keine ungespeicherten Daten vorhanden
        has_unsaved = self.save_service.has_unsaved()
        self.ui.buttonStart.setEnabled(not has_unsaved)
        self.ui.buttonSetting.setEnabled(True)
        self.ui.buttonStop.setEnabled(False)
        self.ui.buttonReset.setEnabled(True)
        self.ui.buttonSave.setEnabled(has_unsaved)
        Debug.debug(
            f"UI in Ruhemodus gesetzt "
            f"(Start: {'deaktiviert' if has_unsaved else 'aktiviert'}, "
            f"Save: {'aktiviert' if has_unsaved else 'deaktiviert'})"
        )

    def _setup_progress_bar(self, duration_seconds: int) -> None:
        """Configure the progress bar for the given duration.

        Args:
            duration_seconds: Duration in seconds (``999`` means infinite).
        """
        # Reset elapsed time counter FIRST
        self._elapsed_seconds = 0
        self.ui.progressTimer.setText("0s")

        if duration_seconds != 999:
            # Finite duration - progress bar with timer
            self.ui.progressBar.setMaximum(duration_seconds)
            self.ui.progressBar.setValue(0)
            Debug.debug(f"ProgressBar konfiguriert für {duration_seconds} Sekunden")
        else:
            # Infinite duration - indeterminate progress bar (animiert hin und her)
            self.ui.progressBar.setMaximum(0)
            self.ui.progressBar.setValue(0)
            Debug.debug(
                "ProgressBar konfiguriert für unendliche Messdauer (indeterminate mode)"
            )

        # Start timer to update progressTimer label for both finite and infinite measurements
        self._measurement_timer = QTimer(self)
        self._measurement_timer.timeout.connect(self._update_progress)
        self._measurement_timer.start(1000)  # Update every second
        Debug.debug(
            f"Timer started: isActive={self._measurement_timer.isActive()}, "
            f"duration={duration_seconds}s"
        )

    def _stop_progress_bar(self) -> None:
        """Stop the progress bar and its timer."""
        if self._measurement_timer:
            self._measurement_timer.stop()
            self._measurement_timer = None

        # Reset progress bar and timer display to idle state
        self.ui.progressBar.setMaximum(100)
        self.ui.progressBar.setValue(0)
        self.ui.progressTimer.setText("0s")
        self._elapsed_seconds = 0
        Debug.debug("ProgressBar und Timer gestoppt und zurückgesetzt")

    def _start_measurement(self):
        """Start measurement and adjust UI."""
        # Button sollte bereits deaktiviert sein wenn ungespeicherte Daten vorliegen
        # Aber zur Sicherheit nochmal prüfen
        if self.save_service.has_unsaved():
            MessageHelper.show_warning(
                self,
                "Bitte speichern oder löschen Sie die vorhandenen Messdaten, bevor Sie eine neue Messung starten.",
                "Warnung",
            )
            return

        self.data_controller.clear_data()
        self.save_service.mark_saved()  # Neue Messung hat keine ungespeicherten Daten

        if self.device_manager.start_measurement():
            self.is_measuring = True
            self._set_ui_measuring_state()
            self.measurement_start = datetime.now()
            seconds = int(self.ui.cDuration.value())
            if seconds == 0:
                seconds = 999
            self._setup_progress_bar(seconds)

            # Starte automatisches Backup alle 30 Sekunden
            self.backup_timer.start(30000)  # 30000ms = 30s

            self.statusbar.temp_message(
                "Messung läuft...",
                CONFIG["colors"]["blue"],
                duration=0,  # Persistent during measurement
            )
            self._update_status_indicator("Messung", "blue")
            Debug.info("Measurement started, statusbar updated")

    def _stop_measurement(self):
        """Stop measurement and resume config polling."""
        self.device_manager.stop_measurement()
        self.is_measuring = False
        self.measurement_end = datetime.now()
        self._stop_progress_bar()

        # Stoppe automatisches Backup
        self.backup_timer.stop()

        # ✅ FIX: Stoppe GUI Update Timer nach Messung
        # Dies verhindert, dass die Queue noch nach Stop
        # geleert wird und unnötige GUI-Updates erfolgen
        if (
            hasattr(self.data_controller, "gui_update_timer")
            and self.data_controller.gui_update_timer is not None
        ):
            was_running = self.data_controller.gui_update_timer.isActive()
            if was_running:
                self.data_controller.gui_update_timer.stop()
                Debug.info(
                    "GUI update timer stopped after measurement - "
                    "queue processing suspended"
                )

        # Markiere Messung als ungespeichert, wenn Daten vorhanden sind
        if self.data_controller.get_csv_data():
            self.save_service.mark_unsaved()

        self._set_ui_idle_state()
        self.statusbar.temp_message(
            "Messung gestoppt. Daten bereit zum Speichern.",
            CONFIG["colors"]["green"],
            duration=0,  # Persistent
        )
        self._update_status_indicator("Gestoppt", "yellow")
        Debug.info("Measurement stopped, statusbar updated")
        # Auto-save is handled by backup timer, not here
        # The periodic auto_backup via SaveService takes care of incremental backups

    def _handle_connection_lost(self):
        """Handle unexpected device disconnection.

        Automatically attempts reconnection, then shows connection dialog if needed.
        This slot is called from the acquisition thread (via QueuedConnection).
        """
        Debug.error("MainWindow: handling connection loss")

        # Stop measurement if active
        was_measuring = self.is_measuring
        if self.is_measuring:
            self._stop_measurement()

        # ✅ FIX: Stop control update timer immediately on disconnect
        # This prevents config polling (which tries to read from disconnected device)
        # and stops the queue from being refilled
        if (
            hasattr(self, "control_update_timer")
            and self.control_update_timer is not None
        ):
            if self.control_update_timer.isActive():
                self.control_update_timer.stop()
                Debug.info(
                    "Control update timer stopped - no config polling during disconnect"
                )

        # Update UI to show disconnection
        self._set_ui_idle_state()
        self.statusbar.temp_message(
            "Gerät wurde unerwartet getrennt! Versuche automatische Wiederverbindung...",
            CONFIG["colors"]["orange"],
            duration=0,
        )
        self._update_status_indicator("Wiederverbindung...", "orange")

        # Attempt automatic reconnection after brief delay to let UI update
        QTimer.singleShot(500, self._attempt_automatic_reconnection)

    def _attempt_automatic_reconnection(self):
        """Attempt automatic reconnection to the previously connected device.

        If automatic reconnection fails, shows the connection dialog
        to allow the user to manually reconnect.
        """
        Debug.info("Attempting automatic reconnection...")

        try:
            # ✅ FIX: Use reconnect service with exponential backoff
            # This ensures proper delays between retry attempts (500ms → 750ms → 1125ms → etc.)
            def reconnect_callback(message: str, color: str):
                self.statusbar.temp_message(
                    message, CONFIG["colors"].get(color, "orange"), duration=0
                )

            if self.reconnect_service.attempt_reconnect(
                reconnect_fn=self.device_manager.attempt_automatic_reconnect,
                status_callback=reconnect_callback,
            ):
                # Success!
                Debug.info("Automatic reconnection successful")

                # ✅ CRITICAL FIX: Re-initialize control widget with the (already updated) device_manager
                # This ensures control.get_settings() uses the newly connected device
                self.control = ControlWidget(device_manager=self.device_manager)
                Debug.info(
                    "Control widget re-initialized with reconnected device manager"
                )

                # ✅ FIX: Restart control update timer after successful reconnection
                if (
                    hasattr(self, "control_update_timer")
                    and self.control_update_timer is not None
                ):
                    if not self.control_update_timer.isActive():
                        self.control_update_timer.start(
                            CONFIG["timers"]["control_update_interval"]
                        )
                        Debug.info(
                            "Control update timer restarted after automatic reconnection"
                        )

                self.statusbar.temp_message(
                    f"Wiederverbunden mit {self.device_manager.port}",
                    CONFIG["colors"]["green"],
                    duration=3000,
                )
                self._update_status_indicator("Verbunden", "green")
                return
        except Exception as e:
            Debug.error(f"Exception during automatic reconnection: {e}")

        # Automatic reconnection failed - show connection dialog
        Debug.warning("Automatic reconnection failed - showing connection dialog")

        # Show dialog with slight delay to ensure UI has processed previous updates
        QTimer.singleShot(300, self._show_connection_dialog_on_disconnect)

    def _show_connection_dialog_on_disconnect(self):
        """Show the connection dialog after a disconnection.

        Disables the main window and allows user to reconnect to the device.
        """
        Debug.info("Showing connection dialog for manual reconnection")

        # Only show dialog if we're not measuring (measurement should have been stopped already)
        if self.is_measuring:
            Debug.warning(
                "Measurement still active - waiting for it to complete before showing dialog"
            )
            QTimer.singleShot(200, self._show_connection_dialog_on_disconnect)
            return

        # Disable main window to prevent interaction while reconnecting
        self.setEnabled(False)

        # Update status message
        self.statusbar.temp_message(
            "Bitte überprüfen Sie die USB-Verbindung und versuchen Sie erneut, sich zu verbinden.",
            CONFIG["colors"]["orange"],
            duration=0,
        )

        # Create and show connection dialog for the same port
        from ...ui.dialogs.connection import ConnectionWindow

        connection_dialog = ConnectionWindow(
            parent=self,
            demo_mode=CONFIG["gm_counter"]["demo_mode"],
            default_device=self.device_manager.port,  # Try to reconnect to same port
            measurement_state=self.device_manager.measurement_state,  # Reuse measurement state
        )

        if connection_dialog.exec():
            if connection_dialog.connection_successful:
                # Reconnection successful - update device manager
                new_device_manager = connection_dialog.device_manager
                Debug.info(f"Reconnected to {new_device_manager.port}")

                # ✅ FIX: Disconnect old signals BEFORE replacing device_manager
                # Dies verhindert mehrfache Signal-Verbindungen
                self.device_manager.data_received.disconnect(self.handle_data)
                self.device_manager.connection_lost.disconnect(
                    self._handle_connection_lost
                )

                # Update our device manager reference
                self.device_manager = new_device_manager

                # Reconnect signals (fresh start ohne Duplikate)
                self.device_manager.data_received.connect(
                    self.handle_data, Qt.ConnectionType.QueuedConnection
                )
                self.device_manager.status_update.connect(self.statusbar.temp_message)
                self.device_manager.device_info_received.connect(
                    self._update_device_info
                )
                self.device_manager.connection_lost.connect(
                    self._handle_connection_lost, Qt.ConnectionType.QueuedConnection
                )

                # ✅ CRITICAL FIX: Re-initialize control widget with NEW device_manager
                # This ensures control.get_settings() uses the newly connected device,
                # not the old dead connection
                self.control = ControlWidget(device_manager=self.device_manager)
                Debug.info("Control widget re-initialized with new device manager")

                # ✅ FIX: Restart control update timer after successful reconnection
                if (
                    hasattr(self, "control_update_timer")
                    and self.control_update_timer is not None
                ):
                    if not self.control_update_timer.isActive():
                        self.control_update_timer.start(
                            CONFIG["timers"]["control_update_interval"]
                        )
                        Debug.info("Control update timer restarted after reconnection")

                # Re-enable main window
                self.setEnabled(True)
                self.statusbar.temp_message(
                    f"Wiederverbunden mit {self.device_manager.port}",
                    CONFIG["colors"]["green"],
                    duration=3000,
                )
                self._update_status_indicator("Verbunden", "green")
                Debug.info("Reconnection dialog completed successfully")
            else:
                # Reconnection failed in dialog
                self.setEnabled(True)
                self.statusbar.temp_message(
                    "Wiederverbindung fehlgeschlagen.",
                    CONFIG["colors"]["red"],
                    duration=0,
                )
                self._update_status_indicator("Getrennt", "red")
                MessageHelper.show_error(
                    self,
                    "Wiederverbindung fehlgeschlagen.\n\n"
                    "Die Anwendung kann ohne Geräteverbindung nicht fortgesetzt werden.",
                    "Verbindungsfehler",
                )
                Debug.warning("Reconnection failed in dialog")
        else:
            # User cancelled dialog
            self.setEnabled(True)
            self.statusbar.temp_message(
                "Wiederverbindung abgebrochen.",
                CONFIG["colors"]["red"],
                duration=0,
            )
            self._update_status_indicator("Getrennt", "red")
            MessageHelper.show_error(
                self,
                "Wiederverbindung abgebrochen.\n\n"
                "Die Anwendung kann ohne Geräteverbindung nicht fortgesetzt werden.",
                "Verbindung erforderlich",
            )
            Debug.info("User cancelled reconnection dialog")

    def _attempt_reconnection(self):
        """[DEPRECATED] Use _attempt_automatic_reconnection instead."""
        Debug.warning(
            "_attempt_reconnection called - delegating to _attempt_automatic_reconnection"
        )
        self._attempt_automatic_reconnection()

    def _run_reconnection_with_retry(self, reconnect_fn, status_callback):
        """[DEPRECATED] Old retry logic - no longer used."""
        Debug.debug("_run_reconnection_with_retry called but is deprecated")

    def _save_measurement(self):
        """Manually save the current measurement data using a file dialog."""
        try:
            # Check if there is data to save
            if not self.save_service.has_unsaved():
                MessageHelper.show_info(
                    self,
                    "Keine ungespeicherten Daten vorhanden.",
                    "Information",
                )
                return

            data = self.data_controller.get_csv_data()
            rad_sample = self.ui.radSample.currentText()
            group_letter = self.ui.groupLetter.currentText()
            subterm = self.ui.suffix.text().strip()

            # Erstelle erweiterte Metadaten über SaveService (core layer)
            extra_metadata = self._get_extended_metadata()

            # Use FileDialogManager for UI file dialog interaction
            # SaveService handles the actual saving logic
            saved_path = self.file_dialog_manager.manual_save_measurement(
                self,
                rad_sample,
                group_letter,
                data,
                self.measurement_start or datetime.now(),
                self.measurement_end or datetime.now(),
                subterm,
                extra_metadata=extra_metadata,
            )

            if saved_path and saved_path.exists():
                self.data_saved = True
                self.save_service.mark_saved()  # Markiere als gespeichert

                # Update UI - Start aktivieren, Save deaktivieren
                self.ui.buttonSave.setEnabled(False)
                self.ui.buttonStart.setEnabled(True)

                self.statusbar.temp_message(
                    f"Messung erfolgreich gespeichert. Bereit für neue Messung.",
                    CONFIG["colors"]["green"],
                    duration=0,  # Persistent
                )
                Debug.info(f"Messung manuell gespeichert: {saved_path}")
            else:
                MessageHelper.show_error(
                    self,
                    "Fehler beim Speichern der Messung. Siehe Log für Details.",
                    "Fehler",
                )

        except Exception as e:
            Debug.error(f"Fehler beim manuellen Speichern: {e}")
            MessageHelper.show_error(
                self,
                f"Unerwarteter Fehler beim Speichern: {str(e)}",
                "Fehler",
            )

    def _clear_data(self):
        """Clear all recorded data from the data controller."""
        if self.is_measuring:
            MessageHelper.show_warning(
                self,
                "Daten können während einer Messung nicht gelöscht werden.",
                "Warnung",
            )
            return

        if self.save_service.has_unsaved():
            if not MessageHelper.ask_question(
                self,
                CONFIG["messages"]["unsaved_data"],
                "Warnung",
            ):
                return

        self.data_controller.clear_data()
        self.data_saved = True
        self.save_service.mark_saved()  # Markiere als gespeichert

        # Update UI - Start aktivieren, Save deaktivieren
        self.ui.buttonSave.setEnabled(False)
        self.ui.buttonStart.setEnabled(True)

        self.statusbar.temp_message(
            "Alle Messdaten wurden gelöscht. Bereit für neue Messung.",
            CONFIG["colors"]["green"],
            duration=0,  # Persistent
        )
        self._update_status_indicator("Bereit", "green")
        Debug.info("All measurement data cleared, statusbar updated")

    #
    # 2. DATA PROCESSING AND STATISTICS
    #

    def handle_data(self, index, value):
        """Handle incoming data from the device.

        The values are forwarded to ``DataController`` using the fast
        queue-based API.

        Args:
            index: Index of the data point.
            value: Measured value.
        """
        # CRITICAL: Only process data if measurement is active OR if we're still
        # processing a batch from the end of the measurement
        # Device may continue sending data briefly after measurement stop,
        # but we should still accept data that belongs to the same batch
        if not self.is_measuring:
            # Measurement has stopped - only accept data if we're still processing the batch
            # (queue is not empty = data belongs to the same batch)
            if self.data_controller.data_queue.empty():
                return

        # Use the fast queue-based method for better performance
        self.data_controller.add_data_point_fast(index, value)

        # Mark data as unsaved
        self.data_saved = False
        self.save_service.mark_unsaved()

        # Update buttons: Start deaktivieren (wegen ungespeicherter Daten), Save aktivieren
        if not self.is_measuring:
            self.ui.buttonSave.setEnabled(True)
            self.ui.buttonStart.setEnabled(
                False
            )  # Start deaktiviert bei ungespeicherten Daten

    def _handle_high_speed_mode_change(self, activated: bool):
        """Handle HIGH_SPEED_MODE activation/deactivation from DataController.

        Args:
            activated: True if HIGH_SPEED_MODE was activated, False if deactivated
        """
        if activated:
            # Calculate minimum frequency from config parameters
            # batch_threshold points per batch, gui_update_interval in ms
            batch_threshold = CONFIG["data_controller"]["high_speed_mode"][
                "batch_threshold"
            ]
            gui_interval_ms = CONFIG["timers"]["gui_update_interval"]
            min_freq_hz = int((batch_threshold * 1000) / gui_interval_ms)

            # HIGH_SPEED_MODE activated
            self.statusbar.temp_message(
                f"⚡ HIGH-SPEED MODE aktiviert - Plot/Table deaktiviert",
                CONFIG["colors"]["orange"],
                duration=0,  # Permanent until deactivated
            )

            # Switch to Histogram tab (index 1) since plot is disabled
            self.ui.tabWidget.setCurrentIndex(1)

            self._update_status_indicator("High-Speed", "orange")

            Debug.info(
                "MainWindow: HIGH_SPEED_MODE UI updated, switched to Histogram tab"
            )
        else:
            # HIGH_SPEED_MODE deactivated - restore normal status
            if self.is_measuring:
                self.statusbar.temp_message(
                    "Messung läuft (Normal-Modus)...",
                    CONFIG["colors"]["blue"],
                    duration=0,  # Persistent during measurement
                )
                self._update_status_indicator("Messung", "blue")
            else:
                self.statusbar.temp_message(
                    "Bereit für Messungen.", CONFIG["colors"]["green"], duration=0
                )
                self._update_status_indicator("Bereit", "green")
            Debug.info("MainWindow: Normal mode UI restored")

    def _update_status_indicator(self, status: str, color: str = None):
        """Update statusLED and statusText to reflect current state.

        Args:
            status: Status text to display ("Bereit", "Messung", "High-Speed", "Gestoppt")
            color: LED color ("green", "blue", "orange", "red", "yellow")
        """
        # Map status to colors if not explicitly provided
        status_colors = {
            "Bereit": "rgb(50, 205, 50)",  # Green
            "Messung": "rgb(30, 144, 255)",  # Blue
            "High-Speed": "rgb(255, 140, 0)",  # Orange
            "Gestoppt": "rgb(255, 215, 0)",  # Yellow
            "Fehler": "rgb(255, 11, 3)",  # Red
        }

        if color is None:
            led_color = status_colors.get(status, "rgb(128, 128, 128)")  # Gray default
        else:
            # Convert color name to RGB
            color_map = {
                "green": "rgb(50, 205, 50)",
                "blue": "rgb(30, 144, 255)",
                "orange": "rgb(255, 140, 0)",
                "yellow": "rgb(255, 215, 0)",
                "red": "rgb(255, 11, 3)",
                "gray": "rgb(128, 128, 128)",
            }
            led_color = color_map.get(color, "rgb(128, 128, 128)")

        # Update LED
        self.ui.statusLED.setStyleSheet(
            f"background-color: {led_color}; border: 0px; padding: 4px; border-radius: 10px"
        )

        # Update text
        self.ui.statusText.setText(status)

        Debug.debug(f"Status indicator updated: {status} ({led_color})")

    def _update_statistics(self):
        """Update statistics shown in the user interface."""
        try:
            # Retrieve statistics from DataController
            stats = self.data_controller.get_statistics()

            # Only update when data points are available
            if stats["count"] > 1:
                self.ui.cStatPoints.setText(f"{stats['count']:.0f}")
                self.ui.cStatMin.setText(f"{stats['min']:.0f}")
                self.ui.cStatMax.setText(f"{stats['max']:.0f}")
                self.ui.cStatAvg.setText(f"{stats['avg']:.0f}")
                self.ui.cStatSD.setText(f"{stats['stdev']:.0f}")

        except Exception as e:
            Debug.error(
                f"Fehler beim Aktualisieren der Statistiken: {e}", exc_info=True
            )

    def _update_progress(self) -> None:
        """Update progress bar during measurements.

        For finite measurements: increment progress and stop when done.
        For infinite measurements: just increment elapsed time counter.
        """
        self._elapsed_seconds += 1

        # Update progressTimer label (for both finite and infinite measurements)
        self.ui.progressTimer.setText(f"{self._elapsed_seconds}s")
        Debug.debug(f"Progress timer tick: elapsed={self._elapsed_seconds}s")

        # For finite measurements: update progress bar and check if done
        if self.ui.progressBar.maximum() > 0:
            self.ui.progressBar.setValue(self._elapsed_seconds)
            if self._elapsed_seconds >= self.ui.progressBar.maximum():
                self._stop_measurement()
        # For infinite measurements: progressBar stays in indeterminate mode (animates automatically)

    #
    # 3. DEVICE CONTROL
    #

    def _update_control_display(self):
        """Update the displayed configuration values from the GM counter."""
        if self.is_measuring:
            Debug.info(
                "Control update timer fired during measurement - should not happen!"
            )
            return

        try:
            # Request fresh data from the GM counter
            data = self.control.get_settings()
            if not data:
                Debug.error("Keine Daten vom GM-Counter erhalten.")
                # Möglicherweise ist Arduino noch im Streaming-Modus
                # Dies sollte nicht passieren wenn stop_measurement() korrekt war
                if self.device_manager.device and self.device_manager.connected:
                    Debug.warning("Versuche Arduino-Reset...")
                    self.device_manager.device.set_counting(False)

                    time.sleep(0.5)
                    try:
                        self.device_manager.device.serial.reset_input_buffer()
                    except (OSError, AttributeError):
                        pass
                return

            # Update UI elements
            label = CONFIG["gm_counter"]["label_map"]

            self.ui.currentCount.display(data["count"])
            self.ui.lastCount.display(
                data["last_count"]
            )  # TODO: last_count implementieren mit check

            self.ui.cVoltage.display(data["voltage"])
            self.ui.cDuration.display(data["counting_time"])
            self.ui.cMode.setText(
                label["repeat_on"] if data["repeat"] else label["repeat_off"]
            )
            # self.ui.cQueryMode.setText(label["auto_on"] if data["auto_query"] else label["auto_off"])
            # FEAT: auto_query implementieren

        except Exception as e:
            Debug.error(f"Fehler bei der Aktualisierung der Anzeige: {e}")

    def _apply_settings(self):
        """
        Applies the current settings from the UI to the GM-Counter.
        """
        try:
            settings = {
                "voltage": int(self.ui.sVoltage.value()),
                "counting_time": int(self.ui.sDuration.currentIndex()),
                "repeat": self.ui.cMode.text() == "Repeat On",
                # "auto_query": self.ui.cQueryMode.text() == "Auto On",
            }
            self.control.apply_settings(settings)
            self.statusbar.temp_message(
                CONFIG["messages"]["settings_applied"],
                CONFIG["colors"]["green"],
            )
            Debug.info(
                "Einstellungen erfolgreich angewendet: " + str(settings.values())
            )
        except Exception as e:
            Debug.error(f"Fehler beim Anwenden der Einstellungen: {e}")

    def _change_auto_save(self, checked: bool) -> None:
        """Handle a change of the auto-save option.

        Args:
            checked: ``True`` if auto save is enabled.
        """
        # Note: Auto-backup via SaveService is always active during measurements.
        # This checkbox is kept for UI compatibility but doesn't affect backup behavior.
        if checked:
            self.statusbar.temp_message(
                CONFIG["messages"]["auto_save_enabled"],
                CONFIG["colors"]["green"],
                1000,
            )
        else:
            self.statusbar.temp_message(
                CONFIG["messages"]["auto_save_disabled"],
                CONFIG["colors"]["green"],
                1000,
            )

    def _handle_auto_scroll(self, checked: bool):
        """Handle autoScroll checkbox state change.

        When autoScroll is enabled, activate auto-scroll in the plot and use
        the configured max_plot_points value.
        """
        if checked:
            # Enable auto-scroll mode
            max_points = self.ui.sPlotpoints.value()
            self.plot.set_auto_scroll(True, max_points)
            Debug.debug(f"Auto-Scroll aktiviert mit {max_points} Punkten")
        else:
            # Disable auto-scroll mode
            self.plot.set_auto_scroll(False)
            Debug.debug("Auto-Scroll deaktiviert")

    def _handle_plot_points_changed(self, value: int):
        """Handle changes to the max plot points spinbox.

        Update the plot's max_plot_points if auto-scroll is enabled.
        """
        if self.ui.autoScroll.isChecked():
            self.plot.set_auto_scroll(True, value)
            Debug.debug(f"Max Plot Points aktualisiert auf: {value}")

    def _handle_auto_range_button(self):
        """Handle buttonAutoRange click.

        Enable auto-range in the timePlot when clicked.
        """
        self.plot.enable_auto_range(True)
        self.ui.autoScroll.setChecked(True)  # Also enable autoScroll checkbox
        Debug.debug("Auto-Range durch Button aktiviert")

    def _handle_plot_user_interaction(self):
        """Handle manual user interaction in the plot.

        Deactivates autoScroll checkbox when user manually pans or zooms.
        """
        # Deactivate autoScroll checkbox (this will trigger _handle_auto_scroll)
        if self.ui.autoScroll.isChecked():
            self.ui.autoScroll.setChecked(False)
            Debug.info("Auto-Scroll durch manuelle Plot-Interaktion deaktiviert")

    def _auto_backup_measurement(self):
        """Automatically backup measurement data to temporary file every 30 seconds.

        Delegates to SaveService (core layer) for the actual backup logic.
        MainWindow only collects UI-specific data and calls the service.
        """
        if not self.is_measuring:
            return

        data = self.data_controller.get_csv_data()
        if not data or len(data) <= 1:  # Only header present
            return

        # Collect UI-specific extended metadata
        extra_metadata = self._get_extended_metadata()

        # Get UI values
        rad_sample = self.ui.radSample.currentText() or "unknown"
        group_letter = self.ui.groupLetter.currentText() or "unknown"
        subterm = self.ui.suffix.text().strip()

        # Delegate to SaveService (core layer)
        self.save_service.auto_backup(
            data=data,
            start=self.measurement_start or datetime.now(),
            rad_sample=rad_sample,
            group_letter=group_letter,
            subterm=subterm,
            extra_metadata=extra_metadata,
        )

    def _get_extended_metadata(self) -> dict:
        """Collect extended metadata from UI elements.

        This method is UI-specific and belongs in MainWindow.
        It collects data from UI widgets that the SaveManager doesn't have access to.

        Returns:
            dict: Extended metadata including sampleDistance, OpenBIS code,
                  firmware versions, and total count
        """

        extra = {}

        # Sample Distance (nur wenn != 0)
        sample_distance = self.ui.sampleDistance.value()
        if sample_distance != 0:
            extra["sample_distance_cm"] = sample_distance

        # OpenBIS Code des Zählers
        openbis_code = self.ui.cOpenbis.text()
        if openbis_code and openbis_code != "unknown":
            extra["counter_openbis_code"] = openbis_code

        # Firmware Version des Zählers
        firmware_version = self.ui.cVersion.text()
        if firmware_version and firmware_version != "unknown":
            extra["counter_firmware_version"] = firmware_version

        # GUI Version
        extra["gui_version"] = gmcounter.__version__

        # Gesamtzählung der aktuellen Messung
        data = self.data_controller.get_csv_data()
        if data and len(data) > 1:  # Header + Daten
            extra["total_count"] = len(data) - 1  # Ohne Header

        return extra

    def closeEvent(self, event):
        """Handle the window close event and shut down all components cleanly.

        Args:
            event: The close event from Qt.
        """
        Debug.info("Anwendung wird geschlossen, fahre Komponenten herunter...")

        # Check if unsaved data is present FIRST, before stopping anything
        if hasattr(self, "save_service"):
            try:
                if self.save_service.has_unsaved():
                    # ask_question returns True for "Yes", False for "No"
                    if MessageHelper.ask_question(
                        self,
                        CONFIG["messages"]["unsaved_data_end"],
                        "Warnung",
                    ):
                        # User clicked "Yes" - proceed with closing
                        Debug.info(
                            "Benutzer hat bestätigt: Schließen mit ungespeicherten Daten"
                        )
                    else:
                        # User clicked "No" - abort closing
                        Debug.info("Benutzer hat das Schließen abgebrochen")
                        event.ignore()
                        return
            except Exception as e:
                Debug.error(f"Fehler beim SaveService Cleanup: {e}")

        # User confirmed closing, now stop everything
        # Stop data acquisition in the DeviceManager
        if hasattr(self, "device_manager"):
            try:
                Debug.info("Stoppe Datenerfassung...")
                self.device_manager.stop_acquisition()

                # Close the connection if a real device is connected
                if (
                    hasattr(self.device_manager, "device")
                    and self.device_manager.device
                ):
                    Debug.info("Schließe Geräteverbindung...")
                    self.device_manager.device.close()
            except Exception as e:
                Debug.error(f"Fehler beim Herunterfahren des DeviceManagers: {e}")

        # Stop all timers
        for timer_attr in ["control_update_timer", "stats_timer"]:
            if hasattr(self, timer_attr):
                timer = getattr(self, timer_attr)
                if timer.isActive():
                    Debug.debug(f"Stoppe Timer: {timer_attr}")
                    timer.stop()

        # Stop the DataController GUI update timer
        if hasattr(self, "data_controller"):
            try:
                Debug.info("DataController Cleanup...")
                # Daten können noch geleert werden, falls gewünscht
                # self.data_controller.clear_data()  # Optional
            except Exception as e:
                Debug.error(f"Fehler beim DataController Cleanup: {e}")

        # Pass event to base class
        Debug.info("Anwendung wird geschlossen")
        event.accept()
