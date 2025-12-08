"""Device management with threaded acquisition for reuse."""

from typing import Optional
import time
from threading import Event

from PySide6.QtCore import QObject, QThread, Signal  # pylint: disable=no-name-in-module

from .arduino import GMCounter
from .debug_utils import Debug


class DataAcquisitionThread(QThread):
    """Background thread that pulls data from the device."""

    CONNECTION_TIMEOUT = 3.0  # seconds
    START_BYTE = 0xAA
    END_BYTE = 0x55
    PACKET_SIZE = 6  # 1 Start-Byte + 4 Daten-Bytes + 1 End-Byte
    PERFORMANCE_LOG_INTERVAL = 10.0  # seconds
    # Signal emitted when a new data point is acquired (index, value)
    data_point = Signal(int, float)
    connection_lost = Signal()  # Signal emitted when connection is lost

    def __init__(self, manager: "DeviceManager") -> None:
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
        if not self._skip_first_point:
            self._skip_first_point = True
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
        # Validate packet structure
        if not self._is_valid_packet(packet):
            return False

        # Skip first measurement
        if self._should_skip_first_measurement(packet):
            return True

        # Extract and emit value
        value = self._extract_value_from_packet(packet)
        if value is not None:
            self.data_point.emit(self._index, value)
            self._index += 1
            return True

        return False

    def _is_ready_for_acquisition(self) -> bool:
        """Check if device is ready for data acquisition.

        Returns:
            True if connected and measurement is active.
        """
        return (
            self.manager.device
            and self.manager.connected
            and self.manager.measurement_active
        ) or False

    def _process_buffer(self, byte_buffer: bytes) -> bytes:
        """Process all complete packets in the buffer.

        Args:
            byte_buffer: Current buffer with incoming data.

        Returns:
            Updated buffer with unprocessed data.
        """
        while len(byte_buffer) >= self.PACKET_SIZE:
            # Find start byte
            start_pos = self._find_packet_start(byte_buffer)

            if start_pos == -1:
                # No start byte found, clear buffer
                Debug.debug("No START_BYTE found in buffer, clearing buffer")
                return b""

            if start_pos > 0:
                # Start byte not at beginning, remove data before it
                Debug.debug(f"START_BYTE not at beginning, removing {start_pos} bytes")
                byte_buffer = byte_buffer[start_pos:]
                continue

            # Check if complete packet available
            if len(byte_buffer) < self.PACKET_SIZE:
                break

            # Extract 6-byte packet
            packet = byte_buffer[: self.PACKET_SIZE]
            byte_buffer = byte_buffer[self.PACKET_SIZE :]

            # Process packet
            if not self._process_packet(packet):
                # Invalid packet - remove only first byte and retry
                byte_buffer = packet[1:] + byte_buffer

        return byte_buffer

    def run(self) -> None:
        """Main loop for data acquisition from the device."""
        self._running = True
        self._skip_first_point = False  # Reset at each start
        Debug.info(
            f"Acquisition thread started with binary data acquisition mode "
            f"({self.START_BYTE:#04x} + 4 bytes + {self.END_BYTE:#04x})"
        )

        byte_buffer = b""
        last_process_time = time.time()

        while self._running and not self.isInterruptionRequested():
            # Check if ready for acquisition
            if not self._is_ready_for_acquisition():
                time.sleep(0.01)
                continue

            try:
                current_time = time.time()

                # Read data with high-speed method
                raw_data = self.manager.device.read_fast(
                    max_bytes=4096,
                    timeout_ms=1,
                )

                if raw_data:
                    # Add new data to buffer and process
                    byte_buffer += raw_data
                    byte_buffer = self._process_buffer(byte_buffer)
                else:
                    # Short pause when no data available
                    time.sleep(0.001)

                # Performance logging every x seconds
                if current_time - last_process_time > self.PERFORMANCE_LOG_INTERVAL:
                    Debug.debug(
                        f"Binary acquisition active, processed {self._index} packets, "
                        f"buffer: {len(byte_buffer)} bytes"
                    )
                    last_process_time = current_time

            except Exception as exc:
                Debug.error(f"Binary acquisition error: {exc}")
                time.sleep(0.05)  # Kürzere Pause bei Fehlern für binäre Daten

        Debug.info("Binary acquisition thread stopped")

    def reset_index(self) -> None:
        """Reset the data point index counter for a new measurement."""
        self._index = 0
        Debug.debug("Data acquisition index reset to 0")

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()
        self.wait(2000)


class DeviceManager(QObject):
    """Handle device connections and data acquisition."""

    # Signals for data and status updates
    status_update = Signal(str, str)  # (message, color)
    data_received = Signal(int, float)  # (index, value)
    device_info_received = Signal(dict)  # device info dictionary

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.connected = False
        self.port = "None"
        self.device: Optional[GMCounter] = None
        self.acquire_thread: Optional[DataAcquisitionThread] = None
        self.stop_event = Event()
        self.measurement_active = False

    def connect_device(self, port: str, baudrate: int) -> bool:
        """Connect to the given serial port and retrieve device information."""
        self.port = port
        self.disconnect_device()
        try:
            self.device = GMCounter(port=port, baudrate=baudrate)
            self.connected = True
            self.status_update.emit(f"Connected to {port}", "green")

            # Retrieve and report device information (version, openbis, etc.)
            self._fetch_device_info()

            self.start_acquisition()
            return True
        except Exception as exc:
            Debug.error(f"Connection failed: {exc}")
            self.connected = False
            self.status_update.emit(f"Connection failed: {exc}", "red")
            return False

    def _fetch_device_info(self) -> None:
        """Fetch device information and call the info callback."""
        if not self.device:
            return

        try:
            info = self.device.get_information()
            Debug.info(f"Device info retrieved: {info}")
            self.device_info_received.emit(info)
        except Exception as exc:
            Debug.error(f"Failed to fetch device info: {exc}")

    def disconnect_device(self) -> None:
        """Close existing connection and stop acquisition."""
        self.stop_acquisition()
        if self.device:
            try:
                self.device.close()
            except Exception as exc:  # pragma: no cover - close errors
                Debug.error(f"Error closing device: {exc}")
        self.device = None
        self.connected = False

    def start_acquisition(self) -> bool:
        """Start or (re)connect the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            # Thread already running, ensure signal is connected
            return True

        self.acquire_thread = DataAcquisitionThread(self)
        # Forward data_point signal from thread to our data_received signal
        self.acquire_thread.data_point.connect(self.data_received.emit)
        self.acquire_thread.start()
        return True

    def stop_acquisition(self) -> bool:
        """Stop the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            self.acquire_thread.stop()
        self.acquire_thread = None
        return True

    def start_measurement(self) -> bool:
        """Send start command to device and enable fast acquisition."""
        if not (self.device and self.connected):
            return False
        try:
            # Reset index counter for new measurement
            if self.acquire_thread:
                self.acquire_thread.reset_index()

            self.device.set_counting(True)
            self.measurement_active = True
            return True
        except Exception as exc:  # pragma: no cover - unexpected errors
            Debug.error(f"Failed to start measurement: {exc}")
            return False

    def stop_measurement(self) -> bool:
        """Stop counting and resume configuration polling."""
        if not (self.device and self.connected):
            self.measurement_active = False
            return False
        try:
            self.device.set_counting(False)
        except Exception as exc:  # pragma: no cover - unexpected errors
            Debug.error(f"Failed to stop measurement: {exc}")
        self.measurement_active = False
        return True
