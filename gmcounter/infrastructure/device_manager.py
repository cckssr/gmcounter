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
