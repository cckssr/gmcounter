# Layer: infrastructure/serial_device — Qt-free serial base class.
# This is a direct port of the Arduino class from arduino.py.

from typing import Optional, Union, Any
from time import sleep, time
import logging
import serial

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
