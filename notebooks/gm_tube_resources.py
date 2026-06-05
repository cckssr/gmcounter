# Layer: infrastructure/devices — Qt-free GM counter adapter.

from time import sleep
from typing import Optional, Dict, Union, Any, List, Tuple
from time import sleep, time
import serial
import logging

_log = logging.getLogger(__name__)


class SerialDevice:
    """Base class for serial-port device communication.

    Manages a pyserial connection: open/close, send command, read line/bytes.
    All methods are synchronous and blocking — callers that need non-blocking
    behaviour should run them in a thread (see infrastructure.qt_threads).
    """

    BINARY_PACKET_START_BYTE = 0xAA
    DEFAULT_PACKET_SIZE = 6
    DEFAULT_READ_TIMEOUT = 1.0
    FAST_READ_TIMEOUT_MS = 100

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self._config: dict[str, Any] = {}

    def reconnect(self) -> bool:
        if self.serial and self.serial.is_open:
            self.serial.close()
            _log.debug("Closed existing connection to %s", self.port)
            sleep(0.5)

        try:
            _log.info("Connecting to %s at %d baud", self.port, self.baudrate)
            is_pty = self.port.startswith("/dev/ttys") or self.port.startswith(
                "/dev/pts"
            )

            if is_pty:
                _log.debug("Detected PTY device, using raw serial access")
                self.serial = serial.Serial()
                self.serial.port = self.port
                self.serial.timeout = self.timeout
                self.serial.open()
            else:
                self.serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                )

            sleep(2.0)
            try:
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
            except OSError as exc:
                _log.debug("Could not reset buffers (non-critical): %s", exc)

            self.connected = True
            _log.info("Connected to %s", self.port)
            return True

        except (serial.SerialException, OSError) as exc:
            self.connected = False
            _log.error("Failed to connect to %s: %s", self.port, exc)
            raise serial.SerialException(str(exc)) from exc

    def close(self) -> None:
        if self.serial and self.serial.is_open:
            self.serial.close()
            _log.debug("Connection to %s closed", self.port)
        self.connected = False

    def send_command(self, command: str, add_newline: bool = True) -> bool:
        if not self.serial or not self.serial.is_open:
            _log.error("Cannot send command: serial not open")
            return False
        try:
            cmd = (
                command + "\n"
                if add_newline and not command.endswith("\n")
                else command
            )
            self.serial.write(cmd.encode("utf-8"))
            self.serial.flush()
            _log.debug("Sent: %r", cmd.strip())
            return True
        except (serial.SerialException, OSError) as exc:
            _log.error("Serial error sending command: %s", exc, exc_info=True)
            if "Device not configured" in str(exc) or "Errno 6" in str(exc):
                self.connected = False
            return False
        except Exception as exc:
            _log.error("Unexpected error sending command: %s", exc, exc_info=True)
            return False

    def _wait_for_data(self, timeout: float) -> bool:
        if not self.serial:
            return False
        start = time()
        while (time() - start) < timeout:
            if self.serial.in_waiting > 0:
                return True
            sleep(0.01)
        return False

    def read_value(
        self,
        timeout: float = 1.0,
        return_type: str = "auto",
        strip_whitespace: bool = True,
    ) -> Union[str, bytes, None]:
        if not self.serial or not self.serial.is_open:
            _log.error("Serial not open")
            return None
        try:
            if not self._wait_for_data(timeout):
                _log.debug("Timeout: no data available")
                return None
            raw = self.serial.readline()
            if not raw:
                return None
            if return_type == "bytes":
                return raw
            try:
                decoded = raw.decode("utf-8")
                if strip_whitespace:
                    decoded = decoded.strip()
                if decoded.lower() == "invalid" or not decoded:
                    return None
                return decoded
            except UnicodeDecodeError:
                if return_type == "auto":
                    return raw
                return None
        except serial.SerialException as exc:
            _log.error("Serial read error: %s", exc)
            return None

    def read_fast(
        self,
        max_bytes: int = 1024,
        timeout_ms: int = FAST_READ_TIMEOUT_MS,
        delimiter: Optional[bytes] = None,
    ) -> Optional[bytes]:
        if not self.serial or not self.serial.is_open:
            return None
        original = self.serial.timeout
        try:
            self.serial.timeout = timeout_ms * 0.001
            if delimiter:
                buf = bytearray()
                while len(buf) < max_bytes:
                    chunk = self.serial.read(1)
                    if not chunk:
                        break
                    buf.extend(chunk)
                    if delimiter in bytes(buf):
                        pos = buf.find(delimiter)
                        return bytes(buf[: pos + len(delimiter)])
                return bytes(buf)
            buf = self.serial.read(max_bytes)
            return buf if buf else b""
        except serial.SerialException as exc:
            _log.error("Serial error in fast read: %s", exc)
            return None
        finally:
            self.serial.timeout = original

    def read_text_response(self, timeout: float = DEFAULT_READ_TIMEOUT) -> str:
        if not self.serial or not self.serial.is_open:
            return ""
        parts: list[str] = []
        start = time()
        try:
            while (time() - start) < timeout:
                if not self._wait_for_data(min(0.1, timeout - (time() - start))):
                    if parts:
                        break
                    continue
                chunk = self.serial.readline()
                if not chunk:
                    break
                decoded = chunk.decode("utf-8", errors="ignore").strip()
                if decoded and decoded.lower() != "invalid":
                    parts.append(decoded)
                if chunk.endswith(b"\n"):
                    sleep(0.05)
                    if self.serial.in_waiting == 0:
                        break
            return "".join(parts).strip()
        except Exception as exc:
            _log.error("Error in read_text_response: %s", exc)
            return ""

    def flush_input_buffer(self) -> bool:
        if not self.serial or not self.serial.is_open:
            return False
        try:
            discarded = 0
            while self.serial.in_waiting > 0:
                discarded += len(self.serial.read(min(self.serial.in_waiting, 256)))
                sleep(0.001)
            try:
                self.serial.reset_input_buffer()
            except (OSError, serial.SerialException):
                pass
            if discarded:
                _log.debug("Flushed %d bytes", discarded)
            return True
        except Exception as exc:
            _log.error("Error flushing buffer: %s", exc)
            return False


class GMCounterAdapter(SerialDevice):
    """GM counter SCPI command set over serial.

    Communicates with the firmware (v2+) using SCPI commands:
      *IDN? / *RST / *CLS
      INIT / ABOR
      CONF:VOLT / CONF:TIME / CONF:REP / CONF:STR
      FETC:STAT? / SYST:CLR / CONF:SPKR / SYST:ERR?

    Binary timing data is streamed as 0xAA [4-byte LE µs] 0x55 packets,
    preceded by a 0xFF×6 start marker when INIT is sent.
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
            keys = list(template.keys())
            result = template.copy()
            for i, part in enumerate(parts):
                if i >= len(keys):
                    break
                key = keys[i]
                try:
                    result[key] = bool(int(part)) if key == "repeat" else int(part)
                except (ValueError, IndexError):
                    result["error"] = 1
                    pass
            return result
        except Exception as exc:
            _log.error("Error in get_data: %s", exc)
            template["error"] = 1
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

    # Control commands
    def set_stream(self, value: int = 0, confirm: bool = False) -> bool:
        self.send_command(f"CONF:STR {value}")
        if confirm:
            self.send_command("CONF:STR?")
            r = self.read_text_response()
            if r is None or r.strip() != str(value):
                _log.debug(
                    "Stream setting confirmation failed: expected %d, got %s", value, r
                )
                return False
        return True

    def set_voltage(self, value: int = 500, confirm: bool = False) -> Optional[bool]:
        if not 300 <= value <= 700:
            _log.error("Voltage must be between 300 and 700, got %d", value)
            return None
        self.send_command(f"CONF:VOLT {value}")
        if confirm:
            self.send_command("CONF:VOLT?")
            r = self.read_value()
            if r is None or int(r) != value:
                _log.debug(
                    "Voltage setting confirmation failed: expected %d, got %s", value, r
                )
                return False
        return True

    def set_repeat(self, value: bool = False, confirm: bool = False) -> bool:
        self.send_command(f"CONF:REP {1 if value else 0}")
        if confirm:
            self.send_command("CONF:REP?")
            r = self.read_value()
            if r is None or bool(int(r)) != value:
                _log.debug(
                    "Repeat setting confirmation failed: expected %s, got %s", value, r
                )
                return False
        return True

    def set_counting(self, value: bool = False) -> bool:
        self.send_command("INIT" if value else "ABOR")
        return True

    def set_speaker(
        self, gm: bool = False, ready: bool = False, confirm: bool = False
    ) -> bool:
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
        if not 0 <= value <= 5:
            _log.error("Counting time key must be 0–5, got %d", value)
            return None
        self.send_command(f"CONF:TIME {value}")
        if confirm:
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
        self.send_command("SYST:CLR")
        return True


class PacketParser:
    """Incremental decoder for the GM counter binary protocol.

    Wire format (little-endian):
        start marker : 0xFF × 6   (everything before it is discarded)
        data packet  : 0xAA [b0 b1 b2 b3] 0x55   — b0..b3 = inter-event delta
                       in firmware timer ticks

    ``feed()`` appends a chunk and returns every newly completed point as
    ``(index, value_us)`` where ``value_us = ticks / ticks_per_us``.  Partial
    packets and a start marker split across two chunks are carried over.
    The whole thing is a single O(n) pass — no per-packet reslicing.
    """

    START_BYTE = 0xAA
    END_BYTE = 0x55
    PACKET_SIZE = 6
    START_MARKER = b"\xff\xff\xff\xff\xff\xff"

    def __init__(self, ticks_per_us: float = 48.0) -> None:
        self._scale = float(ticks_per_us) or 1.0
        self._buf = bytearray()
        self._index = 0
        self._synced = False  # True once the 0xFF×6 marker has been seen

    @property
    def index(self) -> int:
        return self._index

    @property
    def synced(self) -> bool:
        return self._synced

    def reset(self) -> None:
        """Clear buffer, index and sync state (between measurements)."""
        self._buf.clear()
        self._index = 0
        self._synced = False

    def feed(self, raw: bytes) -> List[Tuple[int, float]]:
        """Append *raw* and return newly decoded ``(index, value_us)`` points."""
        buf = self._buf
        buf += raw

        if not self._synced:
            pos = buf.find(self.START_MARKER)
            if pos == -1:
                # Keep a marker-length tail in case it straddles two chunks.
                if len(buf) > len(self.START_MARKER):
                    del buf[: -len(self.START_MARKER)]
                return []
            del buf[: pos + len(self.START_MARKER)]
            self._synced = True

        points: List[Tuple[int, float]] = []
        scale = self._scale
        i = 0
        n = len(buf)
        while n - i >= self.PACKET_SIZE:
            if buf[i] != self.START_BYTE or buf[i + 5] != self.END_BYTE:
                i += 1  # resync: slide one byte and retry framing
                continue
            ticks = buf[i + 1] | buf[i + 2] << 8 | buf[i + 3] << 16 | buf[i + 4] << 24
            self._index += 1
            points.append((self._index, ticks / scale))
            i += self.PACKET_SIZE

        if i:
            del buf[:i]
        return points
