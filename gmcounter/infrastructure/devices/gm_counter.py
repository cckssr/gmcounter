# Layer: infrastructure/devices — Qt-free GM counter adapter.
"""GM counter device adapter for the SCPI firmware protocol.

:class:`GMCounterAdapter` extends :class:`~gmcounter.infrastructure.serial_device.SerialDevice`
with the full SCPI command set supported by the firmware (v2+).  All methods
are synchronous and blocking; the acquisition thread calls
:meth:`~gmcounter.infrastructure.serial_device.SerialDevice.read_fast` to
drain the binary data stream.
"""

import logging
from time import sleep
from typing import Optional, Dict, Union

from ..serial_device import SerialDevice

_log = logging.getLogger(__name__)


class GMCounterAdapter(SerialDevice):
    """GM counter SCPI command set over serial.

    Communicates with the firmware (v2+) using SCPI commands::

        *IDN? / *RST / *CLS
        INIT / ABOR
        MEAS:STRT / MEAS:STP
        CONF:VOLT / CONF:TIME / CONF:REP / CONF:STR
        FETC:STAT? / SYST:CLR / CONF:SPKR / SYST:ERR?

    Binary timing data is streamed as ``0xAA [4-byte LE µs] 0x55`` packets,
    preceded by a ``0xFF×6`` start marker when ``INIT`` is sent.
    ``MEAS:STRT`` starts the counter without the streaming interrupt;
    ``FETC:STAT?`` can still be used to poll counts.  ``MEAS:STP`` or
    ``ABOR`` stops it.
    """

    is_mock_device: bool = False

    def __init__(
        self, port: str, baudrate: int = 1000000, timeout: float = 1.0
    ) -> None:
        super().__init__(port, baudrate, timeout)
        self._device_info_cache: Optional[Dict[str, str]] = None

        self.reconnect()
        _log.info("GMCounterAdapter initializing on %s", port)

        self.set_counting(False)
        self.set_stream(0)
        self.clear_register()
        sleep(0.5)

        # Drain any buffered data from a previous session
        for _ in range(3):
            val = self.read_value()
            if val is None or val == "":
                break
            self.set_stream(0)
            self.read_value()
            sleep(0.1)

    # ------------------------------------------------------------------
    # Data / info
    # Expected number of CSV fields in a FETC:STAT? response.
    # Field order: count, last_count, counting_time, repeat, progress, voltage
    _STAT_FIELD_COUNT = 6

    def get_data(self, request: bool = True) -> Dict[str, Union[int, bool]]:
        """Fetch current counter status and data.

        Args:
            request: If True, sends a FETC:STAT? command before reading.

        Returns:
            A dictionary with keys:
                - count: Total counts (int)
                - last_count: Counts since last request (int)
                - counting_time: Total counting time in seconds (int)
                - repeat: Whether repeat mode is on (bool)
                - progress: Progress of current counting time (0-100 int)
                - voltage: Current voltage setting (int)
                - error: If an error occurred (0 or 1 int)
        """
        template: Dict[str, Union[int, bool]] = {
            "count": 0,
            "last_count": 0,
            "counting_time": 0,
            "repeat": False,
            "progress": 0,
            "voltage": 0,
            "error": 0,
        }
        try:
            if request:
                # Flush first: any leftover binary bytes from a just-ended stream
                # would corrupt the CSV response if not discarded beforehand.
                self.flush_input_buffer()
                if not self.send_command("FETC:STAT?"):
                    template["error"] = 1
                    return template
                sleep(0.1)
            line = self.read_value(timeout=2.0, return_type="str")
            if not line or not isinstance(line, str):
                template["error"] = 1
                return template
            parts = line.split(",")
            if parts and parts[-1] == "":
                parts = parts[:-1]
            # Require exactly the expected number of fields; fewer means a
            # truncated / corrupted response — treat it as an error.
            if len(parts) < self._STAT_FIELD_COUNT:
                _log.debug(
                    "FETC:STAT? returned %d fields (expected %d): %r",
                    len(parts),
                    self._STAT_FIELD_COUNT,
                    line,
                )
                template["error"] = 1
                return template
            keys = [
                "count",
                "last_count",
                "counting_time",
                "repeat",
                "progress",
                "voltage",
            ]
            result = template.copy()
            for i, key in enumerate(keys):
                try:
                    result[key] = (
                        bool(int(parts[i])) if key == "repeat" else int(parts[i])
                    )
                except (ValueError, IndexError):
                    _log.debug("FETC:STAT? field '%s' parse error: %r", key, parts[i])
                    result["error"] = 1
            return result
        except Exception as exc:
            _log.error("Error in get_data: %s", exc)
            template["error"] = 1
            return template

    def get_information(self, use_cache: bool = True) -> Dict[str, str]:
        """Query ``*IDN?`` and return parsed device information.

        Args:
            use_cache: Return the cached result if available (avoids a serial
                round-trip on repeated calls).

        Returns:
            Dict with keys ``copyright`` (manufacturer), ``version``
            (firmware version), and ``openbis`` (device serial number).
        """
        if use_cache and self._device_info_cache is not None:
            return self._device_info_cache.copy()

        info = {"copyright": "", "version": "", "openbis": ""}
        try:
            self.flush_input_buffer()
            self.send_command("*IDN?")
            r = self.read_text_response(timeout=0.5)
            if r:
                # *IDN? returns: MFR,MODEL,SERIAL,VERSION
                parts = r.split(",", 3)
                info["copyright"] = parts[0].strip() if len(parts) > 0 else r
                info["version"] = parts[3].strip() if len(parts) > 3 else ""
                info["openbis"] = parts[2].strip() if len(parts) > 2 else ""
            self._device_info_cache = info.copy()
        except Exception as exc:
            _log.error("Error getting information: %s", exc)
        return info

    # Control commands
    def set_stream(self, value: int = 0, confirm: bool = False) -> bool:
        """Set the binary stream mode (``CONF:STR``).

        Args:
            value: Stream mode index (0 = off, 4 = continuous binary stream).
            confirm: If True, read back the value and verify it was accepted.

        Returns:
            True if the command was sent (and confirmed when requested).
        """
        self.send_command(f"CONF:STR {value}")
        if confirm:
            self.flush_input_buffer()
            self.send_command("CONF:STR?")
            r = self.read_text_response()
            if r is None or r.strip() != str(value):
                _log.debug(
                    "Stream setting confirmation failed: expected %d, got %s", value, r
                )
                return False
        return True

    def set_voltage(self, value: int = 500, confirm: bool = False) -> Optional[bool]:
        """Set the detector high voltage (``CONF:VOLT``).

        Args:
            value: Voltage in V; must be in the range 300–700.
            confirm: If True, read back and verify.

        Returns:
            True on success, False if confirmation failed, None if *value*
            is out of the allowed range.
        """
        if not 300 <= value <= 700:
            _log.error("Voltage must be between 300 and 700, got %d", value)
            return None
        self.send_command(f"CONF:VOLT {value}")
        if confirm:
            self.flush_input_buffer()
            self.send_command("CONF:VOLT?")
            r = self.read_value()
            if r is None or int(r) != value:
                _log.debug(
                    "Voltage setting confirmation failed: expected %d, got %s", value, r
                )
                return False
        return True

    def set_repeat(self, value: bool = False, confirm: bool = False) -> bool:
        """Enable or disable repeat mode (``CONF:REP``).

        Args:
            value: True to enable repeat mode.
            confirm: If True, read back and verify.

        Returns:
            True on success, False if confirmation failed.
        """
        self.send_command(f"CONF:REP {1 if value else 0}")
        if confirm:
            self.flush_input_buffer()
            self.send_command("CONF:REP?")
            r = self.read_value()
            if r is None or bool(int(r)) != value:
                _log.debug(
                    "Repeat setting confirmation failed: expected %s, got %s", value, r
                )
                return False
        return True

    def set_counting(self, value: bool = False) -> bool:
        """Start (``INIT``) or stop (``ABOR``) the binary acquisition stream.

        Args:
            value: True to send ``INIT``, False to send ``ABOR``.

        Returns:
            Always True (errors are logged but not re-raised).
        """
        self.send_command("INIT" if value else "ABOR")
        return True

    def start_counter_only(self) -> bool:
        """Start the counter without the binary-streaming interrupt routine."""
        self.send_command("MEAS:STRT")
        return True

    def stop_counter_only(self) -> bool:
        """Stop a counter-only measurement (also accepted: ABOR)."""
        self.send_command("MEAS:STP")
        return True

    def set_speaker(
        self, gm: bool = False, ready: bool = False, confirm: bool = False
    ) -> bool:
        """Configure the speaker output (``CONF:SPKR``).

        Args:
            gm: True to enable click on each GM event.
            ready: True to enable tone when the counting period is ready.
            confirm: If True, read back and verify.

        Returns:
            True on success, False if confirmation failed.
        """
        self.send_command(f"CONF:SPKR {int(gm) + 2 * int(ready)}")
        if confirm:
            self.send_command("CONF:SPKR?")
            r = self.read_value()
            if r is None or int(r) != int(gm) + 2 * int(ready):
                _log.debug(
                    "Speaker setting confirmation failed: expected %d, got %s",
                    int(gm) + 2 * int(ready),
                    r,
                )
                return False
        return True

    def set_counting_time(
        self, value: int = 0, confirm: bool = False
    ) -> Optional[bool]:
        """Set the counting time mode index (``CONF:TIME``).

        Args:
            value: Mode index 0–5 (0 = infinite, 1–5 map to device time modes).
            confirm: If True, read back and verify.

        Returns:
            True on success, False if confirmation failed, None if *value*
            is out of range.
        """
        if not 0 <= value <= 5:
            _log.error("Counting time key must be 0–5, got %d", value)
            return None
        self.send_command(f"CONF:TIME {value}")
        if confirm:
            self.flush_input_buffer()
            self.send_command("CONF:TIME?")
            r = self.read_value()
            if r is None or int(r) != value:
                _log.debug(
                    "Counting time setting confirmation failed: expected %d, got %s",
                    value,
                    r,
                )
                return False
        return True

    def clear_register(self) -> bool:
        """Send ``SYST:CLR`` to reset the GM counter's event register.

        Returns:
            Always True.
        """
        self.send_command("SYST:CLR")
        return True
