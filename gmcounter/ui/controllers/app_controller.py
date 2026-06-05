# Layer: ui — AppController bridges device ↔ experiment tab ↔ main window.
# All QTimers live here; no business logic in MainWindow.

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import (  # pylint: disable=no-name-in-module
    QObject,
    QTimer,
    Signal,
    Qt,
)

from ...infrastructure.device_manager import DeviceManager
from ...infrastructure.qt_threads import (
    DataAcquisitionThread,
    ReconnectWorker,
    StatePollerThread,
)
from ...infrastructure.config import import_config
from ...infrastructure.session_journal import SessionJournal, find_orphan_journals
from ...core.models import DesiredState, Frame
from ...core.duration import accumulate_and_trim
from ..common.statusbar import StatusBarManager

if TYPE_CHECKING:
    from ..tabs.base import PlotTabBase
    from ..widgets.event_log_panel import EventLogPanel

_log = logging.getLogger(__name__)
CONFIG = import_config()


class AppController(QObject):
    """Central coordinator: owns all timers, acquisition thread, and reconnect FSM.

    Signal contract (public API for MainWindow / tabs):
    ─────────────────────────────────────────────────
    frames_ready(list[Frame])     — a batch of acquired data points
    statistics_updated(dict)      — {count, min, max, avg, stdev}
    device_state_updated(dict)    — raw get_data() response (count/voltage/…)
    measurement_started()
    measurement_stopped()
    high_speed_mode_changed(bool) — from active tab
    progress_updated(int, int)    — (elapsed_s, total_s; total=0 → indeterminate)
    status_message(str, str)      — (text, color)
    retry_connecting(int, float)  — (attempt_no, delay_ms)
    reconnect_succeeded()
    connection_lost()             — terminal; all retries exhausted
    """

    frames_ready = Signal(object)  # list[Frame] (frozen dataclasses)
    statistics_updated = Signal(dict)
    device_state_updated = Signal(dict)
    measurement_started = Signal()
    measurement_stopped = Signal()
    high_speed_mode_changed = Signal(bool)
    progress_updated = Signal(int, int)
    status_message = Signal(str, str)
    retry_connecting = Signal(int, float)
    reconnect_succeeded = Signal()
    connection_lost = Signal()

    # ------------------------------------------------------------------
    # Reconnect state-machine states
    _CONNECTED = "connected"
    _RECONNECTING = "reconnecting"
    _DISCONNECTED = "disconnected"

    def __init__(
        self,
        device_manager: DeviceManager,
        status_bar: StatusBarManager,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self.device_manager = device_manager
        self._status_bar = status_bar
        self.event_log: Optional["EventLogPanel"] = None
        self._active_tab: Optional["PlotTabBase"] = None

        # Measurement tracking
        self._is_measuring = False
        self._measurement_start: Optional[datetime] = None
        self._elapsed_s = 0
        self._total_s = 0  # 0 = indeterminate

        # Delta-based duration: device-time accumulator and target (in µs)
        self._accum_us: float = 0.0
        self._target_us: float = 0.0

        # Reconnect state machine
        self._reconnect_state = self._CONNECTED
        self._reconnect_worker: Optional[ReconnectWorker] = None
        self._desired_state = DesiredState()  # Saved before disconnect for B5 replay

        # Journal
        self._journal: Optional[SessionJournal] = None

        # Acquisition thread
        self._acquire_thread: Optional[DataAcquisitionThread] = None
        self._wire_device_manager()
        self._start_acquisition()

        # Background state poller — replaces the old main-thread _control_timer.
        # get_data() blocks for up to 2 s; running it off the main thread keeps
        # the UI responsive.
        self._state_poller = StatePollerThread(device_manager)
        self._state_poller.data_ready.connect(
            self.device_state_updated, Qt.ConnectionType.QueuedConnection
        )
        self._state_poller.start()

        # QTimers
        cfg_t = CONFIG.get("timers", {})
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._emit_statistics)
        self._stats_timer.start(cfg_t.get("statistics_update_interval", 1000))

        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._tick_progress)

        # Check for orphan journals from previous crashes
        QTimer.singleShot(5000, self._check_orphan_journals)

    # ------------------------------------------------------------------
    # Status notification

    def _notify(self, text: str, color: str = "") -> None:
        """Show text on the status bar and append to the event log."""
        self._status_bar.show_message(text, backcolor=color)
        if self.event_log is not None:
            self.event_log.append(text, color)

    # ------------------------------------------------------------------
    # Active-tab management

    def set_active_tab(self, tab: "PlotTabBase") -> None:
        if self._active_tab is not None:
            try:
                self.frames_ready.disconnect(self._active_tab.on_frames)
                self.measurement_started.disconnect(
                    self._active_tab.on_measurement_started
                )
                self.measurement_stopped.disconnect(
                    self._active_tab.on_measurement_stopped
                )
            except RuntimeError:
                pass
        self._active_tab = tab
        if tab is not None:
            self.frames_ready.connect(tab.on_frames)
            self.measurement_started.connect(tab.on_measurement_started)
            self.measurement_stopped.connect(tab.on_measurement_stopped)

    # ------------------------------------------------------------------
    # Measurement control (called by MainWindow)

    def start_measurement(self, total_seconds: int = 0) -> bool:
        """Start a measurement.  total_seconds=0 → indeterminate."""
        if not (self.device_manager.connected and self.device_manager.device):
            self._notify("Kein Gerät verbunden", "red")
            return False

        if self._active_tab is not None:
            self._active_tab.on_reset()

        if self._acquire_thread:
            self._acquire_thread.reset_index()

        # Pause state polling before sending INIT so no FETC:STAT? is
        # in-flight when binary streaming starts.  pause() blocks until
        # any ongoing get_data() call finishes, guaranteeing a clean port.
        self._state_poller.pause()

        if self.device_manager.start_measurement():
            self._is_measuring = True
            self._measurement_start = datetime.now()
            self._elapsed_s = 0
            self._total_s = total_seconds
            self._target_us = total_seconds * 1_000_000.0
            self._accum_us = 0.0

            # Open journal
            self._journal = SessionJournal()

            self._progress_timer.start(1000)
            self.measurement_started.emit()
            self._notify(
                "Messung läuft...", CONFIG.get("colors", {}).get("blue", "blue")
            )
            return True

        # start failed — restore polling so the idle state display still works
        self._state_poller.resume()
        return False

    def stop_measurement(self) -> None:
        self._is_measuring = False
        self._progress_timer.stop()
        self.device_manager.stop_measurement()
        self._state_poller.resume()
        self.measurement_stopped.emit()
        self._notify(
            "Messung gestoppt.", CONFIG.get("colors", {}).get("green", "green")
        )

    def finalize_journal(self) -> None:
        """Mark the current session journal as cleanly saved."""
        if self._journal:
            self._journal.finalize()

    @property
    def is_measuring(self) -> bool:
        return self._is_measuring

    # ------------------------------------------------------------------
    # Settings

    def apply_settings(
        self,
        voltage: int,
        counting_time: int,
        repeat: bool,
        auto_query: bool = False,
    ) -> None:
        """Push settings to device and save as DesiredState for reconnect replay."""
        self._desired_state = DesiredState(
            voltage=voltage,
            counting_time=counting_time,
            repeat=repeat,
            stream=4 if auto_query else 1,
        )
        if self.device_manager.device:
            # Pause the poller first so no FETC:STAT? is in-flight while the
            # CONF:* commands are being written — both share the same serial port.
            self._state_poller.pause()
            try:
                self.device_manager._apply_device_settings(
                    self._desired_state.to_device_settings()
                )
            finally:
                self._state_poller.resume()
        self._notify(
            CONFIG.get("messages", {}).get("settings_applied", "Einstellungen gesetzt"),
            CONFIG.get("colors", {}).get("green", "green"),
        )
        # Trigger a fresh state poll ~300 ms after the device processes the commands.
        QTimer.singleShot(300, self._state_poller.force_poll_soon)

    # ------------------------------------------------------------------
    # Cleanup

    def cleanup(self) -> None:
        """Call from MainWindow.closeEvent() — stop all timers and threads."""
        for timer in (self._stats_timer, self._progress_timer):
            if timer.isActive():
                timer.stop()

        if self._state_poller and self._state_poller.isRunning():
            self._state_poller.stop()

        if self._reconnect_worker and self._reconnect_worker.isRunning():
            self._reconnect_worker.abort()
            self._reconnect_worker.wait(2000)

        if self._acquire_thread and self._acquire_thread.isRunning():
            self._acquire_thread.stop()

        if self._journal:
            self._journal.close()

        self.device_manager.disconnect_device()

    # ------------------------------------------------------------------
    # Internal wiring

    def _wire_device_manager(self) -> None:
        self.device_manager.on_status = self._notify
        self.device_manager.on_connection_lost = self._on_connection_lost_cb

    def _start_acquisition(self) -> None:
        if self._acquire_thread and self._acquire_thread.isRunning():
            return
        self._acquire_thread = DataAcquisitionThread(self.device_manager)
        self._acquire_thread.data_batch.connect(
            self._on_data_batch, Qt.ConnectionType.QueuedConnection
        )
        self._acquire_thread.connection_lost.connect(
            self._on_acquire_connection_lost, Qt.ConnectionType.QueuedConnection
        )
        self._acquire_thread.start()

    def _stop_acquisition(self) -> None:
        if self._acquire_thread and self._acquire_thread.isRunning():
            self._acquire_thread.stop()

    # ------------------------------------------------------------------
    # Data batch handler

    def _on_data_batch(self, points: list) -> None:
        """Handle a batch of (index, value_us) tuples from the acquisition thread.

        Runs on the GUI thread (QueuedConnection).  Trims the batch to the
        device-time target via accumulate_and_trim, journals and fans out
        only the kept points, then stops if the target was crossed.
        """
        if not self._is_measuring or not points:
            return

        kept, self._accum_us, reached = accumulate_and_trim(
            points, self._accum_us, self._target_us
        )

        if kept:
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            journal = self._journal
            frames = []
            for index, value in kept:
                if journal:
                    journal.record(index, value)
                frames.append(Frame(index=index, value=value, timestamp=ts))
            self.frames_ready.emit(frames)

        if reached:
            self.stop_measurement()

    # ------------------------------------------------------------------
    # Timers

    def _emit_statistics(self) -> None:
        if self._active_tab is None:
            return
        try:
            stats = self._active_tab.get_statistics()
            if stats:
                self.statistics_updated.emit(stats)
        except Exception as exc:
            _log.debug("Error emitting statistics: %s", exc)

    def _tick_progress(self) -> None:
        # Pure heartbeat: emit device-time progress from the delta accumulator so
        # the progress bar stays live during quiet periods.  Stop decisions are made
        # in _on_data_batch (delta-driven) — never here.
        elapsed = int(self._accum_us / 1e6)
        total = int(self._target_us / 1e6)
        self.progress_updated.emit(elapsed, total)

    # ------------------------------------------------------------------
    # Reconnect state machine (§5 B1–B7)

    def _on_acquire_connection_lost(self) -> None:
        """Called (via QueuedConnection) when the acquisition thread detects loss."""
        if self._reconnect_state != self._CONNECTED:
            return  # Already handling

        # Set state immediately — handle_connection_lost() calls on_connection_lost
        # which re-enters here, so the guard must be up before any callback fires.
        self._reconnect_state = self._RECONNECTING

        # B1: if measuring, stop cleanly first
        if self._is_measuring:
            self.stop_measurement()

        self.device_manager.handle_connection_lost()

        self._notify(
            "Verbindung unterbrochen — Wiederverbindung...",
            CONFIG.get("colors", {}).get("orange", "orange"),
        )

        # Save desired state for replay after reconnect (B5)
        # B2: start non-blocking reconnect worker
        cfg_conn = CONFIG.get("connection", {})
        delays = cfg_conn.get("backoff_delays_ms", [500, 750, 1125, 1688, 2531])
        max_att = len(delays)
        init_ms = delays[0] if delays else 500

        self._reconnect_worker = ReconnectWorker(
            reconnect_fn=lambda: self.device_manager.attempt_automatic_reconnect(
                desired=self._desired_state
            ),
            max_attempts=max_att,
            initial_delay_ms=init_ms,
            parent=self,
        )
        self._reconnect_worker.succeeded.connect(self._on_reconnect_succeeded)
        self._reconnect_worker.failed.connect(self._on_reconnect_failed)
        self._reconnect_worker.status_update.connect(self._notify)
        self._reconnect_worker.start()

    def _on_connection_lost_cb(self) -> None:
        """DeviceManager callback — route to the Qt signal handler."""
        self._on_acquire_connection_lost()

    def _on_reconnect_succeeded(self) -> None:
        """Reconnect worker reports success (B5)."""
        self._reconnect_state = self._CONNECTED
        self._start_acquisition()

        if self._journal:
            self._journal.mark_gap()

        self.reconnect_succeeded.emit()
        self._notify("Wiederverbunden", CONFIG.get("colors", {}).get("green", "green"))

    def _on_reconnect_failed(self) -> None:
        """All retry attempts exhausted (B7) — notify UI and offer journal export."""
        self._reconnect_state = self._DISCONNECTED
        self.connection_lost.emit()

        if self._journal:
            self._journal.close()
            self._notify(
                f"Verbindung verloren. Journal gespeichert: {self._journal.path}",
                CONFIG.get("colors", {}).get("red", "red"),
            )
        else:
            self._notify(
                "Verbindung verloren. Alle Wiederverbindungsversuche fehlgeschlagen.",
                CONFIG.get("colors", {}).get("red", "red"),
            )

    # ------------------------------------------------------------------
    # Orphan journal check

    def _check_orphan_journals(self) -> None:
        orphans = find_orphan_journals()
        if orphans:
            paths = "\n".join(str(p) for p in orphans)
            _log.warning("Found %d orphan journal(s):\n%s", len(orphans), paths)
            self._notify(
                f"{len(orphans)} ungespeichertes Journal gefunden. Daten unter ~/.gmcounter/sessions/",
                CONFIG.get("colors", {}).get("orange", "orange"),
            )
