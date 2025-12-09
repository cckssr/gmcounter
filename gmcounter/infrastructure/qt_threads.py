"""Qt threading helpers for background tasks."""

import time
from typing import Optional
from PySide6.QtCore import QThread, Signal  # pylint: disable=no-name-in-module

from .logging import Debug


class DataAcquisitionThread(QThread):
    """Background thread that pulls data from the device."""

    CONNECTION_TIMEOUT = 3.0  # seconds
    START_MARKER_TIMEOUT = 2.0  # seconds - timeout for detecting start marker
    START_BYTE = 0xAA
    END_BYTE = 0x55
    PACKET_SIZE = 6  # 1 Start-Byte + 4 Daten-Bytes + 1 End-Byte
    PERFORMANCE_LOG_INTERVAL = 10.0  # seconds

    # Signal emitted when a new data point is acquired (index, value)
    data_point = Signal(int, float)
    connection_lost = Signal()  # Signal emitted when connection is lost

    def __init__(self, manager) -> None:
        """Initialize the acquisition thread.

        Args:
            manager: DeviceManager instance from infrastructure layer
        """
        super().__init__()
        self.manager = manager
        self._running = False
        self._index = 0  # Index counter for data points
        self._skip_first_point = False  # Flag to discard first measurement
        self._last_data_time = time.time()
        self._connection_lost_emitted = False

    def _find_packet_start(self, byte_buffer: bytes) -> int:
        """Find the position of the start byte in the buffer.

        Returns:
            Position of START_BYTE, or -1 if not found.
        """
        return byte_buffer.find(self.START_BYTE)

    def _is_valid_packet(self, packet: bytes) -> bool:
        """Check if a packet has valid start and end bytes.

        Args:
            packet: 6-byte packet to validate.

        Returns:
            True if packet has correct START_BYTE and END_BYTE.
        """
        if packet[0] != self.START_BYTE:
            Debug.debug(f"Invalid START_BYTE in packet: 0x{packet.hex()}")
            return False
        if packet[5] != self.END_BYTE:
            Debug.debug(f"Invalid END_BYTE in packet: 0x{packet.hex()}")
            return False
        return True

    def _should_skip_first_measurement(self, packet: bytes) -> bool:
        """Check if this is the first measurement and should be discarded.

        Args:
            packet: The packet to potentially discard.

        Returns:
            True if packet should be skipped.
        """
        if self._skip_first_point:
            Debug.info(f"Discarding first measurement: 0x{packet.hex()}")
            return True
        return False

    def _extract_value_from_packet(self, packet: bytes) -> Optional[float]:
        """Extract the 32-bit value from a valid packet.

        Args:
            packet: 6-byte packet with format [START, data[4], END].

        Returns:
            Extracted value as float, or None on error.
        """
        try:
            value_bytes = packet[1:5]
            value = int.from_bytes(value_bytes, byteorder="little", signed=False)
            Debug.debug(f"Valid packet: 0x{packet.hex()} -> value: {value}")
            return float(value)
        except Exception as e:
            Debug.error(f"Error processing valid packet 0x{packet.hex()}: {e}")
            return None

    def _process_packet(self, packet: bytes) -> bool:
        """Process a single validated packet and emit data if valid.

        Args:
            packet: 6-byte packet to process.

        Returns:
            True if packet was processed successfully, False otherwise.
        """
        if not self._is_valid_packet(packet):
            return False

        if self._should_skip_first_measurement(packet):
            return True

        value = self._extract_value_from_packet(packet)
        if value is None:
            return False

        self._index += 1
        self.data_point.emit(self._index, value)
        self._last_data_time = time.time()
        self._connection_lost_emitted = False

        return True

    def run(self):
        """Main thread loop for continuous data acquisition."""
        Debug.info("Data acquisition thread started")
        self._running = True
        self._index = 0
        self._skip_first_point = False
        self._last_data_time = time.time()
        self._connection_lost_emitted = False
        self._first_data_received = False  # Track first data batch
        self._measurement_start_time = (
            None  # Track when measurement started for marker timeout
        )

        byte_buffer = b""

        while self._running:
            try:
                device = self.manager.device

                # Check if device is connected
                if not device or not device.connected:
                    Debug.error("Device not connected in acquisition thread")
                    if not self._connection_lost_emitted:
                        self.connection_lost.emit()
                        self._connection_lost_emitted = True
                    time.sleep(0.1)
                    continue

                # Only acquire data if measurement is active
                if not self.manager.measurement_active:
                    time.sleep(0.05)  # Wait longer when not measuring
                    continue

                # Set measurement start time on first iteration
                if self._measurement_start_time is None:
                    self._measurement_start_time = time.time()

                # Check if start marker timeout has been reached
                if not self._first_data_received:
                    elapsed = time.time() - self._measurement_start_time
                    if elapsed > self.START_MARKER_TIMEOUT:
                        Debug.error(
                            f"Start marker not detected within {self.START_MARKER_TIMEOUT}s \
                                - aborting measurement"
                        )
                        self.connection_lost.emit()
                        break

                # Read available bytes using read_fast method
                raw_data = device.read_fast(max_bytes=4096, timeout_ms=1500)
                Debug.debug(
                    f"Thread: read_fast() returned: {type(raw_data)} \
                        with length {len(raw_data) if raw_data else 0}"
                )

                if raw_data:
                    Debug.debug(f"Thread received {len(raw_data)} bytes")
                    # Reset connection timeout
                    self._last_data_time = time.time()
                    self._connection_lost_emitted = False

                    # Add new data to buffer
                    byte_buffer += raw_data

                    # Check for measurement start marker (0xFF 0xFF 0xFF 0xFF 0xFF 0xFF)
                    # This marker cannot be confused with normal packets (which start with 0xAA)
                    start_marker = b"\xff\xff\xff\xff\xff\xff"
                    marker_pos = byte_buffer.find(start_marker)
                    if marker_pos != -1:
                        # Found start marker - discard everything before and including it
                        discarded_bytes = marker_pos + len(start_marker)
                        Debug.info(
                            f">>> MEASUREMENT START MARKER detected, discarding \
                                {discarded_bytes} bytes of accumulated data"
                        )
                        byte_buffer = byte_buffer[discarded_bytes:]
                        self._first_data_received = True

                    # Process complete packets
                    packets_processed = 0
                    while len(byte_buffer) >= self.PACKET_SIZE:
                        start_pos = self._find_packet_start(byte_buffer)
                        if start_pos == -1:
                            byte_buffer = b""
                            break

                        # Remove bytes before start
                        if start_pos > 0:
                            byte_buffer = byte_buffer[start_pos:]

                        # Check if we have a complete packet
                        if len(byte_buffer) < self.PACKET_SIZE:
                            break

                        packet = byte_buffer[: self.PACKET_SIZE]
                        self._process_packet(packet)
                        packets_processed += 1
                        byte_buffer = byte_buffer[self.PACKET_SIZE :]

                    if packets_processed > 0:
                        Debug.debug(
                            f"Processed {packets_processed} packets, total index now: {self._index}"
                        )
                else:
                    # No data - check for timeout only if NOT measuring
                    # (during measurement, pulses can be slow and shouldn't trigger timeout)
                    if not self.manager.measurement_active:
                        time_since_last = time.time() - self._last_data_time
                        if time_since_last > self.CONNECTION_TIMEOUT:
                            if not self._connection_lost_emitted:
                                Debug.error("Connection timeout - no data received")
                                self.connection_lost.emit()
                                self._connection_lost_emitted = True

                # Adaptive sleep: shorter during active measurement for better response
                # At 10kHz, packets arrive every 0.1ms, so 0.0001s sleep is appropriate
                if self.manager.measurement_active:
                    time.sleep(0.0001)  # 0.1ms - minimal delay during measurement
                else:
                    time.sleep(0.01)  # 10ms - longer when idle to save CPU

            except Exception as e:
                Debug.error(f"Error in acquisition thread: {e}", exc_info=True)
                if not self._connection_lost_emitted:
                    self.connection_lost.emit()
                    self._connection_lost_emitted = True
                time.sleep(0.1)

        Debug.info("Data acquisition thread stopped")

    def reset_index(self):
        """Reset the measurement index counter."""
        old_index = self._index
        self._index = 0
        self._skip_first_point = False
        self._first_data_received = False  # Reset first data flag
        self._measurement_start_time = None  # Reset measurement start time
        Debug.info(
            f"Data acquisition index reset from {old_index} to 0 (ready for new measurement)"
        )

    def stop(self):
        """Stop the acquisition thread and wait for it to finish."""
        self._running = False
        self.requestInterruption()
        Debug.info("Stopping data acquisition thread")

        # Wait for thread to finish (max 2 seconds)
        if not self.wait(2000):
            Debug.info("Thread did not stop within timeout, terminating...")
            self.terminate()
            self.wait()
