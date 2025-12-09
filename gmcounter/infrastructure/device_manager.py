"""Device management with threaded acquisition for reuse."""

from typing import Optional
import time
from threading import Event
import serial

from PySide6.QtCore import QObject, Signal, QTimer  # pylint: disable=no-name-in-module

from .arduino import GMCounter
from .logging import Debug
from .qt_threads import DataAcquisitionThread


class DeviceManager(QObject):
    """Handle device connections and data acquisition.

    This class manages the hardware interface layer only:
    - Device connection/disconnection
    - Data acquisition thread lifecycle
    - Hardware command execution

    Domain state (measurement_active) should be managed by core/services.
    """

    # Timing constants for hardware operations (milliseconds)
    STOP_SEQUENCE_DELAY_MS = 200
    CLEAR_REGISTER_DELAY_MS = 200

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
        except serial.SerialException as exc:
            Debug.error(f"Serial connection failed: {exc}")
            self.connected = False
            self.status_update.emit(f"Connection failed: {exc}", "red")
            return False
        except (OSError, ValueError) as exc:
            Debug.error(f"Device initialization failed: {exc}")
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
        except Exception as exc:  # pylint: disable=broad-except
            Debug.error(f"Failed to fetch device info: {exc}")

    def disconnect_device(self) -> None:
        """Close existing connection and stop acquisition."""
        self.stop_acquisition()
        if self.device:
            try:
                self.device.close()
            except (serial.SerialException, OSError) as exc:
                Debug.error(f"Error closing device: {exc}")
        self.device = None
        self.connected = False
        self.measurement_active = False

    def start_acquisition(self) -> bool:
        """Start or (re)connect the acquisition thread."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            # Thread already running, ensure signal is connected
            return True

        try:
            self.acquire_thread = DataAcquisitionThread(self)
            # Forward data_point signal from thread to our data_received signal
            self.acquire_thread.data_point.connect(self.data_received.emit)
            # Connect connection_lost signal to handle disconnections
            self.acquire_thread.connection_lost.connect(self._handle_connection_lost)
            self.acquire_thread.start()

            # Verify thread started successfully
            if not self.acquire_thread.isRunning():
                Debug.error("Failed to start acquisition thread")
                return False

            return True
        except Exception as exc:  # pylint: disable=broad-except
            Debug.error(f"Failed to start acquisition thread: {exc}")
            return False

    def stop_acquisition(self) -> None:
        """Stop the acquisition thread if running."""
        if self.acquire_thread and self.acquire_thread.isRunning():
            try:
                self.stop_event.set()
                self.acquire_thread.stop()
                self.acquire_thread.wait(2000)  # Wait up to 2 seconds
                if self.acquire_thread.isRunning():
                    Debug.warning("Acquisition thread did not stop in time")
            except Exception as exc:  # pylint: disable=broad-except
                Debug.error(f"Error stopping acquisition thread: {exc}")
            finally:
                self.stop_event.clear()

    def start_measurement(self) -> bool:
        """Send start command to device and enable fast acquisition.

        The Arduino firmware now handles buffer clearing internally when receiving s1.
        """
        if not (self.device and self.connected):
            Debug.warning("Cannot start measurement: device not connected")
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
            # NOTE: This is domain state and should eventually move to core/services
            self.measurement_active = True

            total_time = time.time() - start_time
            Debug.info(f"Total start sequence: {total_time*1000:.1f} ms")
            Debug.debug(
                f"DeviceManager: measurement_active = {self.measurement_active}"
            )
            Debug.info("=== MEASUREMENT STARTED ===")

            return True
        except serial.SerialException as exc:
            Debug.error(f"Serial error during start measurement: {exc}")
            self.measurement_active = False
            return False
        except (OSError, ValueError) as exc:
            Debug.error(f"Failed to start measurement: {exc}")
            self.measurement_active = False
            return False

    def stop_measurement(self) -> bool:
        """Stop counting and ensure Arduino returns to command mode.

        Approach:
        1. Set measurement_active = False FIRST (stops timeout checking)
        2. Send stop command to Arduino
        3. Clear GM counter register to reset state
        4. Wait briefly for processing (using QTimer callbacks)
        5. Clear serial buffers

        Note: Uses sequential QTimer.singleShot calls to avoid blocking.
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
            Debug.debug(
                f"Sent set_counting(False) at t={((t1 - start_time)*1000):.1f} ms"
            )

            # Schedule the rest of the stop sequence with QTimer to avoid blocking
            QTimer.singleShot(self.STOP_SEQUENCE_DELAY_MS, self._continue_stop_sequence)

            return True

        except serial.SerialException as exc:
            Debug.error(f"Serial error during stop measurement: {exc}")
            return False
        except (OSError, ValueError) as exc:
            Debug.error(f"Failed to stop measurement: {exc}")
            return False

    def _continue_stop_sequence(self) -> None:
        """Continue stop sequence after initial delay (called by QTimer)."""
        if not (self.device and self.connected):
            return

        try:
            # Clear GM counter register to reset its state
            self.device.clear_register()
            Debug.debug("Sent clear_register()")

            # Schedule buffer clearing after another delay
            QTimer.singleShot(
                self.CLEAR_REGISTER_DELAY_MS, self._finalize_stop_sequence
            )

        except serial.SerialException as exc:
            Debug.error(f"Serial error during stop sequence: {exc}")
        except (OSError, ValueError) as exc:
            Debug.error(f"Error during stop sequence: {exc}")

    def _finalize_stop_sequence(self) -> None:
        """Finalize stop sequence by clearing buffers (called by QTimer)."""
        if not (self.device and self.connected):
            return

        try:
            # Clear any remaining buffered data
            if self.device.serial and self.device.serial.is_open:
                bytes_waiting = self.device.serial.in_waiting
                Debug.debug(f"Buffer status: {bytes_waiting} bytes waiting")

                try:
                    self.device.serial.reset_input_buffer()
                    Debug.debug("Cleared remaining serial buffer")
                except OSError as e:
                    Debug.warning(f"Could not reset buffer: {e}")

            Debug.info("=== MEASUREMENT STOPPED ===")

        except serial.SerialException as exc:
            Debug.error(f"Serial error finalizing stop: {exc}")
        except (OSError, ValueError) as exc:
            Debug.error(f"Error finalizing stop: {exc}")

    def _handle_connection_lost(self) -> None:
        """Handle connection loss from acquisition thread.

        Performs cleanup and notifies UI of disconnection.
        """
        Debug.error("Connection lost during acquisition")

        # Update state flags
        self.connected = False
        self.measurement_active = False

        # Stop acquisition thread
        if self.acquire_thread and self.acquire_thread.isRunning():
            try:
                self.acquire_thread.stop()
            except Exception as exc:  # pylint: disable=broad-except
                Debug.error(f"Error stopping acquisition thread: {exc}")

        # Close device connection
        if self.device:
            try:
                self.device.close()
            except Exception as exc:  # pylint: disable=broad-except
                Debug.error(f"Error closing device after connection loss: {exc}")
            self.device = None

        # Notify UI
        self.status_update.emit("Connection lost", "red")
        Debug.debug("Connection cleanup completed")
