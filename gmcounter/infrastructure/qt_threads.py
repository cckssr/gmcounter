# Layer: infrastructure — Qt threading helpers.
# THIS IS THE ONLY FILE IN infrastructure/ ALLOWED TO IMPORT PySide6.

import time
import logging
from typing import Optional, Callable

from PySide6.QtCore import QThread, Signal  # pylint: disable=no-name-in-module

_log = logging.getLogger(__name__)


class DataAcquisitionThread(QThread):
    """Background thread that reads binary packets from the device.

    Protocol:
    - 6-byte packets: 0xAA + 4-byte LE µs value + 0x55
    - Measurement start marker: 0xFF × 6 (discards all data before it)
    - Adaptive sleep: 0.1 ms during active measurement, 10 ms otherwise
    """

    CONNECTION_TIMEOUT = 3.0
    START_MARKER_TIMEOUT = 2.0
    START_BYTE = 0xAA
    END_BYTE = 0x55
    PACKET_SIZE = 6

    # Public signals
    data_point = Signal(int, float)  # (index, value_us)
    connection_lost = Signal()

    def __init__(self, manager) -> None:
        """Initialize the data acquisition thread.

        Args:
        manager: DeviceManager (infrastructure layer, no Qt).
        """
        super().__init__()
        self.manager = manager
        self._running = False
        self._index = 0
        self._last_data_time = time.time()
        self._connection_lost_emitted = False
        self._first_data_received = False
        self._measurement_start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Thread lifecycle

    def run(self) -> None:
        _log.info("DataAcquisitionThread started")
        self._running = True
        self._index = 0
        self._last_data_time = time.time()
        self._connection_lost_emitted = False
        self._first_data_received = False
        self._measurement_start_time = None

        byte_buffer = b""

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

                raw = device.read_fast(max_bytes=4096, timeout_ms=1500)

                if raw:
                    self._last_data_time = time.time()
                    self._connection_lost_emitted = False
                    byte_buffer += raw

                    # Detect start marker (0xFF × 6)
                    marker = b"\xff\xff\xff\xff\xff\xff"
                    pos = byte_buffer.find(marker)
                    if pos != -1:
                        discarded = pos + len(marker)
                        _log.info("Start marker found — discarding %d bytes", discarded)
                        byte_buffer = byte_buffer[discarded:]
                        self._first_data_received = True

                    # Process complete packets
                    while len(byte_buffer) >= self.PACKET_SIZE:
                        start = byte_buffer.find(self.START_BYTE)
                        if start == -1:
                            byte_buffer = b""
                            break
                        if start > 0:
                            byte_buffer = byte_buffer[start:]
                        if len(byte_buffer) < self.PACKET_SIZE:
                            break

                        packet = byte_buffer[: self.PACKET_SIZE]
                        byte_buffer = byte_buffer[self.PACKET_SIZE :]
                        self._process_packet(packet)

                else:
                    if not self.manager.measurement_state.measurement_active:
                        if (
                            time.time() - self._last_data_time
                        ) > self.CONNECTION_TIMEOUT:
                            if not self._connection_lost_emitted:
                                _log.error("Connection timeout — no data")
                                self.connection_lost.emit()
                                self._connection_lost_emitted = True

                sleep_s = (
                    0.0001
                    if self.manager.measurement_state.measurement_active
                    else 0.01
                )
                time.sleep(sleep_s)

            except Exception as exc:
                _log.error("Error in acquisition thread: %s", exc, exc_info=True)
                if not self._connection_lost_emitted:
                    self.connection_lost.emit()
                    self._connection_lost_emitted = True
                time.sleep(0.1)

        _log.info("DataAcquisitionThread stopped")

    def _process_packet(self, packet: bytes) -> None:
        if packet[0] != self.START_BYTE or packet[5] != self.END_BYTE:
            _log.debug("Invalid packet: %s", packet.hex())
            return
        try:
            value = float(int.from_bytes(packet[1:5], byteorder="little", signed=False))
            self._index += 1
            self.data_point.emit(self._index, value)
            self._last_data_time = time.time()
            self._connection_lost_emitted = False
        except Exception as exc:
            _log.error("Error processing packet %s: %s", packet.hex(), exc)

    def reset_index(self) -> None:
        old = self._index
        self._index = 0
        self._first_data_received = False
        self._measurement_start_time = None
        _log.info("Acquisition index reset from %d to 0", old)

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()
        _log.info("Stopping DataAcquisitionThread")
        if not self.wait(2000):
            _log.warning("Thread did not stop in time — terminating")
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
