# Layer: infrastructure — Qt threading helpers.
# THIS IS THE ONLY FILE IN infrastructure/ ALLOWED TO IMPORT PySide6.

import threading
import time
import logging
from typing import Optional, Callable

from PySide6.QtCore import QThread, Signal  # pylint: disable=no-name-in-module

from .packet_parser import PacketParser

_log = logging.getLogger(__name__)


class DataAcquisitionThread(QThread):
    """Background thread that reads binary packets from the device.

    Protocol:
    - 6-byte packets: 0xAA + 4-byte LE tick value + 0x55
    - The tick value is an inter-event delta in firmware timer ticks; the host
      divides by ``ticks_per_us`` (config.json -> acquisition) to get µs.
    - Measurement start marker: 0xFF × 6 (discards all data before it)

    Performance: each read cycle parses *all* complete packets in one pass over a
    persistent ``bytearray`` (no per-packet reslicing) and emits a single
    ``data_batch`` signal carrying the whole list.  At 10 kHz this replaces ~10k
    queued cross-thread signals/s with a handful, which is the dominant host-side
    cost — see docs.
    """

    CONNECTION_TIMEOUT = 3.0
    START_MARKER_TIMEOUT = 2.0
    # Public signals
    data_batch = Signal(object)  # list[tuple[int index, float value_us]]
    connection_lost = Signal()

    def __init__(self, manager) -> None:
        """Initialize the data acquisition thread.

        Args:
        manager: DeviceManager (infrastructure layer, no Qt).
        """
        super().__init__()
        self.manager = manager
        self._running = False
        self._last_data_time = time.time()
        self._connection_lost_emitted = False
        self._first_data_received = False
        self._measurement_start_time: Optional[float] = None

        # Tick → microsecond conversion (firmware sends raw timer ticks).
        try:
            from .config import import_config

            acq = import_config().get("acquisition", {})
            ticks_per_us = float(acq.get("ticks_per_us", 48)) or 1.0
            self._read_chunk = int(acq.get("read_chunk_bytes", 8192))
            self._read_timeout_ms = int(acq.get("read_timeout_ms", 50))
        except Exception:  # pragma: no cover - config is best-effort here
            ticks_per_us = 48.0
            self._read_chunk = 8192
            self._read_timeout_ms = 50

        self._parser = PacketParser(ticks_per_us=ticks_per_us)

    # ------------------------------------------------------------------
    # Thread lifecycle

    def run(self) -> None:
        _log.info("DataAcquisitionThread started")
        self._running = True
        self._last_data_time = time.time()
        self._connection_lost_emitted = False
        self._first_data_received = False
        self._measurement_start_time = None
        self._parser.reset()

        while self._running:
            try:
                device = self.manager.device

                if not device or not device.connected:
                    if not self._connection_lost_emitted:
                        _log.error("Device not connected in acquisition thread")
                        self.connection_lost.emit()
                        self._connection_lost_emitted = True
                    time.sleep(0.1)
                    continue

                if not self.manager.measurement_state.measurement_active:
                    time.sleep(0.05)
                    continue

                if self._measurement_start_time is None:
                    self._measurement_start_time = time.time()

                # Start-marker timeout — longer for mock devices
                if not self._first_data_received:
                    elapsed = time.time() - self._measurement_start_time
                    is_mock = getattr(device, "is_mock_device", False)
                    timeout = 30.0 if is_mock else self.START_MARKER_TIMEOUT
                    if elapsed > timeout:
                        _log.error(
                            "Start marker not detected within %.0fs (mock=%s)",
                            timeout,
                            is_mock,
                        )
                        self.connection_lost.emit()
                        break

                raw = device.read_fast(
                    max_bytes=self._read_chunk, timeout_ms=self._read_timeout_ms
                )

                if raw:
                    self._last_data_time = time.time()
                    self._connection_lost_emitted = False
                    points = self._parser.feed(raw)
                    if not self._first_data_received and self._parser.synced:
                        self._first_data_received = True
                        _log.info("Start marker found — stream synced")
                    if points:
                        self.data_batch.emit(points)

                else:
                    if not self.manager.measurement_state.measurement_active:
                        if (
                            time.time() - self._last_data_time
                        ) > self.CONNECTION_TIMEOUT:
                            if not self._connection_lost_emitted:
                                _log.error("Connection timeout — no data")
                                self.connection_lost.emit()
                                self._connection_lost_emitted = True
                    # read_fast already blocked up to read_timeout_ms; only idle
                    # between measurements needs an explicit sleep.
                    if not self.manager.measurement_state.measurement_active:
                        time.sleep(0.01)

            except Exception as exc:
                _log.error("Error in acquisition thread: %s", exc, exc_info=True)
                if not self._connection_lost_emitted:
                    self.connection_lost.emit()
                    self._connection_lost_emitted = True
                time.sleep(0.1)

        _log.info("DataAcquisitionThread stopped")

    def reset_connection_lost(self) -> None:
        """Allow connection-loss detection to fire again after a successful reconnect."""
        self._connection_lost_emitted = False

    def reset_index(self) -> None:
        old = self._parser.index
        self._first_data_received = False
        self._measurement_start_time = None
        self._parser.reset()
        _log.info("Acquisition index reset from %d to 0", old)

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()
        _log.info("Stopping DataAcquisitionThread")
        if not self.wait(2000):
            _log.warning("Thread did not stop in time — terminating")
            self.terminate()
            self.wait()


class StatePollerThread(QThread):
    """Polls device state (FETC:STAT?) in a background thread.

    Mutually exclusive with DataAcquisitionThread — pause() must be called
    before any measurement starts so no SCPI command is in-flight when INIT
    is sent.  pause() blocks until the current get_data() call finishes,
    guaranteeing the serial port is fully idle before returning.
    """

    data_ready = Signal(dict)

    _POLL_INTERVAL_S = 1.0

    def __init__(self, manager) -> None:
        super().__init__()
        self.manager = manager
        self._running = False
        self._poll_lock = threading.Lock()
        self._enabled = True
        self._wake_event = threading.Event()

    def pause(self) -> None:
        """Disable polling and wait for any in-flight get_data() to complete."""
        with self._poll_lock:
            self._enabled = False

    def resume(self) -> None:
        """Re-enable polling after a measurement has stopped."""
        with self._poll_lock:
            self._enabled = True

    def force_poll_soon(self) -> None:
        """Wake the poller immediately so a fresh state is fetched without waiting."""
        self._wake_event.set()

    def run(self) -> None:
        _log.info("StatePollerThread started")
        self._running = True
        while self._running:
            with self._poll_lock:
                if (
                    self._enabled
                    and self.manager.device
                    and self.manager.connected
                    and not self.manager.measurement_state.measurement_active
                ):
                    try:
                        data = self.manager.device.get_data()
                        if data:
                            self.data_ready.emit(data)
                    except Exception as exc:
                        _log.debug("State poller error: %s", exc)
            time.sleep(self._POLL_INTERVAL_S)
        _log.info("StatePollerThread stopped")

    def stop(self) -> None:
        self._running = False
        self._wake_event.set()  # unblock wait() so the thread exits promptly
        self.requestInterruption()
        _log.info("Stopping StatePollerThread")
        if not self.wait(3000):
            _log.warning("StatePollerThread did not stop in time — terminating")
            self.terminate()
            self.wait()


class ReconnectWorker(QThread):
    """Non-blocking exponential-backoff reconnect loop (§4).

    Runs ConnectionRetryService.attempt_reconnect in a background thread
    so the GUI remains responsive during reconnection attempts.

    Signals:
        succeeded: Emitted when reconnect_fn returns True.
        failed: Emitted after all retry attempts are exhausted.
        status_update: (message, color) progress messages.
    """

    succeeded = Signal()
    failed = Signal()
    status_update = Signal(str, str)

    def __init__(
        self,
        reconnect_fn: Callable[[], bool],
        max_attempts: int = 5,
        initial_delay_ms: float = 500,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._reconnect_fn = reconnect_fn
        self._max_attempts = max_attempts
        self._initial_delay_ms = initial_delay_ms
        self._abort = False

    def abort(self) -> None:
        self._abort = True

    def run(self) -> None:
        from ..core.reconnect_service import ConnectionRetryService

        svc = ConnectionRetryService(
            max_attempts=self._max_attempts,
            initial_delay_ms=self._initial_delay_ms,
        )

        def _status(msg: str, color: str) -> None:
            self.status_update.emit(msg, color)

        result = svc.attempt_reconnect(
            self._reconnect_fn,
            status_callback=_status,
            abort_flag=lambda: self._abort,
        )

        if result:
            self.succeeded.emit()
        else:
            self.failed.emit()
