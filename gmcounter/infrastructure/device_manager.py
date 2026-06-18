# Layer: infrastructure — Qt-free device manager.
# No QObject, no Signal, no QTimer — plain callbacks only.
# The ui layer (AppController) owns the DataAcquisitionThread and connects signals.
"""Qt-free GM counter connection lifecycle manager.

:class:`DeviceManager` manages the serial connection to one GM counter.
It uses plain Python callbacks so it can be tested without a running
``QApplication``.  :class:`~gmcounter.ui.controllers.app_controller.AppController`
subscribes to these callbacks and translates them into Qt signals.
"""

import logging
import time
from typing import Optional, Callable
import serial

from .devices.gm_counter import GMCounterAdapter
from ..core.services import MeasurementStateService
from ..core.models import DesiredState, DeviceSettings

_log = logging.getLogger(__name__)


class DeviceManager:
    """Manage the serial connection lifecycle for one GM counter.

    Plain callbacks — no Qt.  AppController subscribes to these and
    translates them into Qt signals for the UI.
    """

    STOP_SEQUENCE_DELAY_S = 0.2
    CLEAR_REGISTER_DELAY_S = 0.2

    def __init__(
        self,
        measurement_state: Optional[MeasurementStateService] = None,
    ) -> None:
        self.connected: bool = False
        self.port: str = "None"
        self.baudrate: int = 115200
        self.device: Optional[GMCounterAdapter] = None
        self._connection_lost_handled = False

        self.measurement_state = measurement_state or MeasurementStateService()

        # Plain callbacks — set by AppController
        self.on_status: Optional[Callable[[str, str], None]] = None
        self.on_data: Optional[Callable[[int, float], None]] = None
        self.on_connection_lost: Optional[Callable[[], None]] = None
        self.on_device_info: Optional[Callable[[dict], None]] = None

    # ------------------------------------------------------------------
    # Connection lifecycle

    def connect_device(
        self,
        port: str,
        baudrate: int,
        device_class=None,
    ) -> bool:
        """Connect to *port* at *baudrate*.

        *device_class* defaults to GMCounterAdapter but can be replaced
        with MockGMCounter for demo / test mode — both share the same
        command interface.
        """
        if device_class is None:
            device_class = GMCounterAdapter

        self.port = port
        self.baudrate = baudrate
        self.disconnect_device()

        try:
            self.device = device_class(port=port, baudrate=baudrate)
            self.connected = True
            self._connection_lost_handled = False
            _log.info("Connected to %s", port)

            if self.on_status:
                self.on_status(f"Verbunden mit {port}", "green")

            self._fetch_device_info()
            return True

        except serial.SerialException as exc:
            _log.error("Serial connection failed: %s", exc)
            self.connected = False
            if self.on_status:
                self.on_status(f"Verbindung fehlgeschlagen: {exc}", "red")
            return False
        except (OSError, ValueError) as exc:
            _log.error("Device initialization failed: %s", exc)
            self.connected = False
            if self.on_status:
                self.on_status(f"Verbindung fehlgeschlagen: {exc}", "red")
            return False

    def attempt_automatic_reconnect(
        self, desired: Optional[DesiredState] = None
    ) -> bool:
        """Attempt to reconnect to the last known port.

        Uses the stored baudrate (not hardcoded 115200) — this fixes the
        latent bug where reconnect always tried 1 000 000 baud.
        After a successful reconnect, re-applies *desired* state to the
        Arduino so voltage/counting-time/repeat are restored (§5 B5).
        """
        if not self.port or self.port == "None":
            _log.warning("No previous port for automatic reconnect")
            return False

        _log.info("Automatic reconnect to %s at %d baud", self.port, self.baudrate)
        self._connection_lost_handled = False

        success = self.connect_device(self.port, self.baudrate)
        if success and desired and self.device:
            settings = desired.to_device_settings()
            self._apply_device_settings(settings)

        return success

    def apply_device_settings(self, settings: DeviceSettings) -> dict:
        """Public API: push *settings* to hardware. See ``_apply_device_settings``."""
        return self._apply_device_settings(settings)

    def _apply_device_settings(self, settings: DeviceSettings) -> dict:
        """Push settings to the hardware with read-back confirmation.

        Each setting is sent with ``confirm=True``; on failure it is retried
        once.  Returns a dict of ``{setting_name: desired_value}`` for every
        setting whose final confirmed value still did not match.  An empty dict
        means all settings were confirmed.
        """
        if not self.device:
            return {}

        unconfirmed: dict = {}

        def _try(name: str, fn, desired) -> None:
            """Apply *fn* once with confirmation; retry once on failure."""
            try:
                ok = fn()
                if not ok:
                    # First attempt failed; pause briefly and retry.
                    time.sleep(0.15)
                    ok = fn()
                if not ok:
                    unconfirmed[name] = desired
                    _log.warning(
                        "Setting '%s' not confirmed after retry (desired=%s)",
                        name,
                        desired,
                    )
            except Exception as exc:
                unconfirmed[name] = desired
                _log.error("Error applying setting '%s': %s", name, exc)

        _try(
            "repeat",
            lambda: self.device.set_repeat(settings.repeat, confirm=True),
            settings.repeat,
        )
        stream_val = 4 if settings.auto_query else 1
        _try(
            "stream",
            lambda: self.device.set_stream(stream_val, confirm=True),
            stream_val,
        )
        _try(
            "counting_time",
            lambda: self.device.set_counting_time(settings.counting_time, confirm=True),
            settings.counting_time,
        )
        _try(
            "voltage",
            lambda: self.device.set_voltage(settings.voltage, confirm=True),
            settings.voltage,
        )

        # Brief settle time so the device can process all commands before
        # the next FETC:STAT? poll arrives.
        time.sleep(0.2)
        return unconfirmed

    def disconnect_device(self) -> None:
        """Close the device connection and reset state."""
        if self.device:
            try:
                self.device.close()
            except (serial.SerialException, OSError) as exc:
                _log.error("Error closing device: %s", exc)
        self.device = None
        self.connected = False
        self.measurement_state.stop_measurement()
        self._connection_lost_handled = False

    def fetch_device_info(self) -> None:
        """Public API: fetch device info and fire on_device_info callback."""
        self._fetch_device_info()

    def _fetch_device_info(self) -> None:
        if not self.device:
            return
        try:
            info = self.device.get_information()
            _log.info("Device info: %s", info)
            if self.on_device_info:
                self.on_device_info(info)
        except Exception as exc:
            _log.error("Failed to fetch device info: %s", exc)

    # ------------------------------------------------------------------
    # Measurement control

    def start_measurement(self) -> bool:
        """Send ``INIT`` to the device and mark the measurement as started.

        Returns:
            True on success; False if not connected or a serial error occurs.
        """
        if not (self.device and self.connected):
            _log.warning("Cannot start: device not connected")
            return False
        try:
            self.device.set_counting(True)
            self.measurement_state.start_measurement()
            _log.info("Measurement started")
            return True
        except serial.SerialException as exc:
            _log.error("Serial error starting measurement: %s", exc)
            self.measurement_state.stop_measurement()
            return False

    def stop_measurement(self) -> bool:
        """Send ``ABOR``, clear the event register, and drain the input buffer.

        Returns:
            True on success; False if not connected or a serial error occurs.
        """
        self.measurement_state.stop_measurement()
        if not (self.device and self.connected):
            _log.warning("Stop called but device not connected")
            return False
        try:
            self.device.set_counting(False)
            time.sleep(self.STOP_SEQUENCE_DELAY_S)
            self.device.clear_register()
            time.sleep(self.CLEAR_REGISTER_DELAY_S)
            if self.device.serial and self.device.serial.is_open:
                try:
                    self.device.serial.reset_input_buffer()
                except OSError:
                    pass
            _log.info("Measurement stopped")
            return True
        except (serial.SerialException, OSError) as exc:
            _log.error("Error stopping measurement: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Connection-loss handler (called by AppController from the Qt signal)

    def handle_connection_lost(self) -> None:
        """Perform cleanup when connection is detected as lost.

        Called by AppController when DataAcquisitionThread emits
        connection_lost — not called directly from the thread.
        """
        if self._connection_lost_handled:
            return
        self._connection_lost_handled = True
        _log.error("Connection lost — cleaning up")

        self.connected = False
        self.measurement_state.stop_measurement()

        if self.device:
            try:
                self.device.close()
            except Exception as exc:
                _log.error("Error closing device after loss: %s", exc)
            self.device = None

        if self.on_status:
            self.on_status("Verbindung unterbrochen", "red")
        if self.on_connection_lost:
            self.on_connection_lost()
