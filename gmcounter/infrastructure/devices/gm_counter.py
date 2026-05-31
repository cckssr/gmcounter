# Layer: infrastructure/devices — Qt-free GM counter adapter.

import logging
from time import sleep
from typing import Optional, Dict, Union

from ..serial_device import SerialDevice

_log = logging.getLogger(__name__)


class GMCounterAdapter(SerialDevice):
    """GM counter SCPI command set over serial.

    Communicates with the firmware (v2+) using SCPI commands:
      *IDN? / *RST / *CLS
      INIT / ABOR
      CONF:VOLT / CONF:TIME / CONF:REP / CONF:STR
      FETC:STAT? / SYST:CLR / DIAG:SPKR / SYST:ERR?

    Binary timing data is streamed as 0xAA [4-byte LE µs] 0x55 packets,
    preceded by a 0xFF×6 start marker when INIT is sent.
    """

    is_mock_device: bool = False

    def __init__(self, port: str, baudrate: int = 1000000, timeout: float = 1.0) -> None:
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

    def get_data(self, request: bool = True) -> Dict[str, Union[int, bool]]:
        template: Dict[str, Union[int, bool]] = {
            "count": 0,
            "last_count": 0,
            "counting_time": 0,
            "repeat": False,
            "progress": 0,
            "voltage": 0,
        }
        try:
            if request:
                if not self.send_command("FETC:STAT?"):
                    return template
                sleep(0.1)
            line = self.read_value(timeout=2.0, return_type="str")
            if not line or not isinstance(line, str):
                return template
            parts = line.split(",")
            if parts and parts[-1] == "":
                parts = parts[:-1]
            keys = list(template.keys())
            result = template.copy()
            for i, part in enumerate(parts):
                if i >= len(keys):
                    break
                key = keys[i]
                try:
                    result[key] = bool(int(part)) if key == "repeat" else int(part)
                except (ValueError, IndexError):
                    pass
            return result
        except Exception as exc:
            _log.error("Error in get_data: %s", exc)
            return template

    def get_information(self, use_cache: bool = True) -> Dict[str, str]:
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

    # ------------------------------------------------------------------
    # Control commands

    def set_stream(self, value: int = 0) -> bool:
        self.send_command(f"CONF:STR {value}")
        return True

    def set_voltage(self, value: int = 500) -> Optional[bool]:
        if not 300 <= value <= 700:
            _log.error("Voltage must be between 300 and 700, got %d", value)
            return None
        self.send_command(f"CONF:VOLT {value}")
        return True

    def set_repeat(self, value: bool = False) -> bool:
        self.send_command(f"CONF:REP {1 if value else 0}")
        return True

    def set_counting(self, value: bool = False) -> bool:
        self.send_command("INIT" if value else "ABOR")
        return True

    def set_speaker(self, gm: bool = False, ready: bool = False) -> bool:
        self.send_command(f"DIAG:SPKR {int(gm) + 2 * int(ready)}")
        return True

    def set_counting_time(self, value: int = 0) -> Optional[bool]:
        if not 0 <= value <= 5:
            _log.error("Counting time key must be 0–5, got %d", value)
            return None
        self.send_command(f"CONF:TIME {value}")
        return True

    def clear_register(self) -> bool:
        self.send_command("SYST:CLR")
        return True
