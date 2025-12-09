"""Device management with threaded acquisition for reuse."""

from typing import Optional
import time
from threading import Event

from PySide6.QtCore import QObject, Signal  # pylint: disable=no-name-in-module

from .arduino import GMCounter
from .logging import Debug
from .qt_threads import DataAcquisitionThread


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
        # Connect connection_lost signal to handle disconnections
        self.acquire_thread.connection_lost.connect(self._handle_connection_lost)
        self.acquire_thread.start()
        return True

    def stop_acquisition(self) -> bool:
        """Stop the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            self.acquire_thread.stop()
        self.acquire_thread = None
        return True

    def start_measurement(self) -> bool:
        """Send start command to device and enable fast acquisition.

        The Arduino firmware now handles buffer clearing internally when receiving s1.
        """
        if not (self.device and self.connected):
            return False
        try:
            start_time = time.time()

            # Reset index counter for new measurement
            if self.acquire_thread:
                self.acquire_thread.reset_index()

            Debug.debug("=== MEASUREMENT START SEQUENCE ===")

            # Send start command to Arduino (s1)
            # Arduino firmware will:
            # 1. Reset buffer indices (discard old ISR data)
            # 2. Send start marker (0xFF x 6)
            # 3. Activate measurement mode
            self.device.set_counting(True)
            Debug.debug("Sent set_counting(True) to Arduino")

            # Activate measurement mode in Python
            self.measurement_active = True

            total_time = time.time() - start_time
            Debug.info(f"Total start sequence: {total_time*1000:.1f} ms")
            Debug.debug(
                f"DeviceManager: measurement_active = {self.measurement_active}"
            )
            Debug.debug("=== MEASUREMENT STARTED ===")

            return True
        except Exception as exc:  # pragma: no cover - unexpected errors
            Debug.error(f"Failed to start measurement: {exc}")
            return False

    def stop_measurement(self) -> bool:
        """Stop counting and ensure Arduino returns to command mode.

        Approach:
        1. Set measurement_active = False FIRST (stops timeout checking)
        2. Send stop command to Arduino
        3. Clear GM counter register to reset state
        4. Wait briefly for processing
        5. Clear serial buffers
        """
        start_time = time.time()

        Debug.debug("=== MEASUREMENT STOP SEQUENCE ===")

        # Set flag FIRST to prevent timeout during stop sequence
        self.measurement_active = False
        Debug.debug("Set measurement_active = False at t=0.0 ms")

        if not (self.device and self.connected):
            Debug.warning("Stop called but device not connected")
            return False

        try:
            # Send stop command to Arduino
            self.device.set_counting(False)
            t1 = time.time()
            Debug.info(
                f"Sent set_counting(False) at t={((t1 - start_time)*1000):.1f} ms"
            )

            # Give Arduino brief moment to stop streaming
            time.sleep(0.2)
            t2 = time.time()
            Debug.info(f"Waited 200ms, now at t={((t2 - start_time)*1000):.1f} ms")

            # Clear GM counter register to reset its state
            self.device.clear_register()
            t3 = time.time()
            Debug.info(f"Sent clear_register() at t={((t3 - start_time)*1000):.1f} ms")

            # Wait for GM counter to process reset
            time.sleep(0.2)
            t4 = time.time()
            Debug.info(f"Waited 200ms, now at t={((t4 - start_time)*1000):.1f} ms")

            # Clear any remaining buffered data
            if self.device.serial and self.device.serial.is_open:
                bytes_waiting = self.device.serial.in_waiting
                Debug.info(f"Buffer status: {bytes_waiting} bytes waiting")

                try:
                    self.device.serial.reset_input_buffer()
                    Debug.info("Cleared remaining serial buffer")
                except OSError as e:
                    Debug.debug(f"Could not reset buffer: {e}")

            total_time = time.time() - start_time
            Debug.info(f"Total stop sequence: {total_time*1000:.1f} ms")
            Debug.info("=== MEASUREMENT STOPPED ===")

        except Exception as exc:  # pragma: no cover - unexpected errors
            Debug.error(f"Failed to stop measurement: {exc}")

        return True

    def _handle_connection_lost(self) -> None:
        """Handle connection loss from acquisition thread."""
        Debug.error("Connection lost during acquisition")
        self.connected = False
        self.measurement_active = False
        self.status_update.emit("Connection lost", "red")
