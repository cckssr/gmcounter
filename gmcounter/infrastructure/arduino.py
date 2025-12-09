#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
arduino.py

This module provides a class to manage a serial connection to an Arduino device.

Classes:
    Arduino: A class to represent an Arduino connection, providing methods to
             reconnect, check status, close the connection, read from, and write to the Arduino.

Usage example:
    arduino = Arduino(port='/dev/ttyUSB0')
    if arduino.connected:
        arduino.send_command('Hello, Arduino!')
        print(arduino.read_value())
"""
from typing import Optional, Union, Dict, Any
from time import sleep, time
import serial
from .logging import Debug


class Arduino:
    """
    Class for communication with Arduino-based devices.
    Manages serial connection and data exchange with hardware.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize Arduino connection.

        Args:
            port (str): Serial port identifier
            baudrate (int, optional): Communication speed. Defaults to 9600.
            timeout (float, optional): Read timeout in seconds. Defaults to 1.0.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self._config: Dict[str, Any] = {}

    def reconnect(self) -> bool:
        """
        (Re-)establishes connection with the Arduino.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            serial.SerialException: If connection fails
        """
        # Close existing connection if any
        if self.serial and self.serial.is_open:
            self.serial.close()
            Debug.debug(f"Closed existing connection to {self.port}")
            sleep(0.5)  # Give the port time to close properly

        try:
            Debug.info(f"Attempting to connect to {self.port} at {self.baudrate} baud")

            # Check if this is a PTY (pseudo-terminal) - used by mock devices
            # PTYs don't support baudrate setting via ioctl
            is_pty = self.port.startswith("/dev/ttys") or self.port.startswith(
                "/dev/pts"
            )

            if is_pty:
                # For PTYs, open without baudrate configuration
                Debug.debug("Detected PTY device, using raw serial access")
                self.serial = serial.Serial()
                self.serial.port = self.port
                self.serial.timeout = self.timeout
                # Don't set baudrate for PTYs - it causes ioctl errors
                self.serial.open()
            else:
                # Normal serial port with full configuration
                self.serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                )

            sleep(2.0)  # Allow Arduino to reset after connection
            # Clear buffers - wrapped in try/except for compatibility with
            # virtual ports and some USB-Serial adapters that don't support
            # certain ioctl operations
            try:
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
            except OSError as e:
                Debug.debug(f"Could not reset buffers (non-critical): {e}")
            self.connected = True
            Debug.info(f"Successfully connected to {self.port}")
            return True
        except (serial.SerialException, OSError) as e:
            self.connected = False
            Debug.error(f"Failed to connect to {self.port}: {e}")
            raise serial.SerialException(str(e)) from e

    def close(self) -> None:
        """
        Closes the connection to the Arduino.
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
            Debug.debug(f"Connection to {self.port} closed")
        self.connected = False

    def send_command(self, command: str, add_newline: bool = True) -> bool:
        """
        Sends a command to the Arduino.

        Args:
            command (str): Command to send
            add_newline (bool): If True, append newline if not present. Default True.

        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Cannot send command: Serial connection not open")
            return False

        try:
            # Prepare command
            cmd = command
            if add_newline and not cmd.endswith("\n"):
                cmd += "\n"

            # Encode and send
            self.serial.write(cmd.encode("utf-8"))
            self.serial.flush()  # Ensure data is sent immediately
            Debug.debug(f"Sent command: {repr(cmd.strip())}")
            return True

        except (serial.SerialException, OSError) as e:
            Debug.error(f"Serial error sending command: {e}", exc_info=True)

            # Check if it's a "Device not configured" error - connection lost
            if "Device not configured" in str(e) or "Errno 6" in str(e):
                Debug.warning("Device disconnected! Attempting to reconnect...")
                self.connected = False

                # Try to reconnect
                try:
                    if self.reconnect():
                        Debug.info("Reconnection successful! Retrying command...")
                        # Retry the command after successful reconnection
                        try:
                            cmd_to_send = command
                            if add_newline and not cmd_to_send.endswith("\n"):
                                cmd_to_send += "\n"
                            self.serial.write(cmd_to_send.encode("utf-8"))
                            self.serial.flush()
                            Debug.debug(
                                f"Command resent after reconnect: {repr(cmd_to_send.strip())}"
                            )
                            return True
                        except Exception as retry_error:
                            Debug.error(
                                f"Failed to resend command after reconnect: {retry_error}"
                            )
                            return False
                    else:
                        Debug.error("Reconnection failed")
                        return False
                except Exception as reconnect_error:
                    Debug.error(f"Error during reconnection attempt: {reconnect_error}")
                    return False

            return False
        except Exception as e:
            Debug.error(f"Unexpected error sending command: {e}", exc_info=True)
            return False

    def _wait_for_data(self, timeout: float) -> bool:
        """Wait for data to arrive in the serial buffer."""
        if not self.serial:
            return False
        start_time = time()
        while (time() - start_time) < timeout:
            if self.serial.in_waiting > 0:
                return True
            sleep(0.01)
        return False

    def _decode_bytes_to_string(self, raw_data: bytes, strip: bool) -> Optional[str]:
        """Decode bytes to UTF-8 string, filtering invalid responses."""
        decoded = raw_data.decode("utf-8")
        if strip:
            decoded = decoded.strip()

        if decoded.lower() == "invalid":
            Debug.info("'invalid' response received")
            return None

        if not decoded:
            Debug.debug("Empty string after decoding")
            return None

        return decoded

    def read_value(
        self,
        timeout: float = 1.0,
        return_type: str = "auto",
        strip_whitespace: bool = True,
    ) -> Union[str, bytes, None]:
        """
        Unified method to read a single value from the Arduino.

        This is the standard read method. It automatically handles both text and binary
        data. Use this for general-purpose reading unless you need extreme speed.

        Args:
            timeout (float): Maximum time to wait for a complete line in seconds. Default 1.0.
            return_type (str): One of "auto", "str", or "bytes":
                - "auto": Attempt to decode as UTF-8 string; return bytes if decode fails.
                - "str": Force string return; discard non-UTF-8 data.
                - "bytes": Return raw bytes without decoding.
            strip_whitespace (bool): If True and return_type is "str", strip whitespace.

        Returns:
            Union[str, bytes, None]: The value read, or None if reading failed or no data available.
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Serial connection not open")
            return None

        try:
            # Wait for data with timeout
            if not self._wait_for_data(timeout):
                Debug.debug("Timeout: No data available to read")
                return None

            # Read raw data
            raw_data = self.serial.readline()
            if not raw_data:
                Debug.debug("Empty data read")
                return None

            # Return bytes directly if requested
            if return_type == "bytes":
                Debug.debug(f"Received {len(raw_data)} bytes")
                return raw_data

            # Try to decode as string
            try:
                decoded = self._decode_bytes_to_string(raw_data, strip_whitespace)
                if decoded:
                    Debug.debug(f"Received string: '{decoded}'")
                return decoded

            except UnicodeDecodeError:
                if return_type == "auto":
                    Debug.debug(
                        f"Could not decode as UTF-8, returning {len(raw_data)} raw bytes"
                    )
                    return raw_data
                Debug.info(
                    "Could not decode as UTF-8 (return_type='str'), returning None"
                )
                return None

        except serial.SerialException as e:
            Debug.error(f"Serial read error: {e}", exc_info=True)
            return None
        except Exception as e:
            Debug.error(f"Unexpected error in read_value: {e}", exc_info=True)
            return None

    def _skip_binary_packets(
        self, timeout_remaining: float, packet_size: int = 6, start_byte: int = 0xAA
    ) -> Optional[str]:
        """Skip binary packets and return the first text character found.

        Args:
            timeout_remaining (float): Remaining timeout in seconds.
            packet_size (int): Size of binary packets to skip (default 6 bytes).
            start_byte (int): Start byte of binary packets (default 0xAA).
        Returns:
            Optional[str]: The first text character found, or None if none found.
        """
        if not self.serial:
            return None

        # Quick check - if no data available immediately, return early
        initial_wait = min(0.1, timeout_remaining)
        if not self._wait_for_data(initial_wait):
            return None

        start_time = time()
        while (time() - start_time) < timeout_remaining and self.serial.in_waiting > 0:
            peek = self.serial.read(1)
            if not peek:
                return None

            # Skip binary packet start byte (0xAA)
            if peek[0] == start_byte:
                try:
                    self.serial.read(packet_size - 1)
                except Exception:
                    pass
                continue

            # Try to decode as text
            try:
                char = peek.decode("utf-8")
                if char.isprintable() or char in "\r\n\t":
                    return char
            except UnicodeDecodeError:
                continue
        return None

    def _try_read_single_line(self, result_parts: list) -> bool:
        """Try to read a single line. Returns True if data was read.

        Args:
            result_parts (list): List to append read lines to.
        Returns:
            bool: True if data was read, False otherwise.
        """
        if not self.serial or self.serial.in_waiting == 0:
            return False

        try:
            line = self.serial.readline()
            if not line:
                return False

            decoded = line.decode("utf-8", errors="ignore").strip()
            if decoded and decoded.lower() != "invalid":
                result_parts.append(decoded)

                # Check if we should wait for more
                if line.endswith(b"\n") or line.endswith(b"\r"):
                    sleep(0.05)
                    return self.serial.in_waiting > 0
            return True

        except (UnicodeDecodeError, serial.SerialException) as e:
            Debug.debug(f"Error reading line: {e}")
            return False

    def _read_text_lines(self, timeout_remaining: float, result_parts: list) -> None:
        """Read text lines until timeout or no more data.

        Args:
            timeout_remaining (float): Remaining timeout in seconds.
            result_parts (list): List to append read lines to.
        """
        if not self.serial:
            return

        start_time = time()
        while (time() - start_time) < timeout_remaining:
            if not self._try_read_single_line(result_parts):
                # No data available, check if we're done
                sleep(0.05)
                if result_parts and self.serial.in_waiting == 0:
                    sleep(0.1)  # Extra wait
                    if self.serial.in_waiting == 0:
                        break

    def read_text_response(self, timeout: float = 1.0, packet_size: int = 6) -> str:
        """
        Reads a complete text response from the Arduino, handling multiple lines
        and filtering out binary data.

        This method is more lenient than read_value() and is designed for
        multi-line text responses (copyright, version information, etc.).
        It automatically skips binary packets and waits for a complete response.

        Args:
            timeout (float): Maximum time to wait for response in seconds. Default 1.0.
            packet_size (int): Size of binary packets to skip (default 6 bytes).

        Returns:
            str: The collected response string, or empty string if nothing received or
                 if only binary data was found.
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Serial connection not open")
            return ""

        result_parts = []
        start_time = time()

        try:
            # Skip binary packets and get first text character
            first_char = self._skip_binary_packets(timeout, packet_size)
            if first_char:
                result_parts.append(first_char)

            # Read remaining text data
            remaining_time = timeout - (time() - start_time)
            if remaining_time > 0:
                self._read_text_lines(remaining_time, result_parts)

            # Join without spaces - data comes from Arduino without spaces
            response = "".join(result_parts).strip()
            Debug.debug(f"Text response: '{response}'")
            return response

        except Exception as e:
            Debug.error(f"Error in read_text_response: {e}", exc_info=True)
            return ""

    def _read_with_delimiter(self, max_bytes: int, delimiter: bytes) -> bytes:
        """Read bytes until delimiter found or max_bytes reached.

        Args:
            max_bytes (int): Maximum number of bytes to read.
            delimiter (bytes): Byte sequence marking end of message.
        Returns:
            bytes: The bytes read including the delimiter, or empty bytes if none.
        """
        if not self.serial:
            return b""

        buffer = bytearray()
        while len(buffer) < max_bytes:
            chunk = self.serial.read(1)
            if not chunk:
                break

            buffer.extend(chunk)

            # Check if delimiter found
            if delimiter in bytes(buffer):
                pos = buffer.find(delimiter)
                result = bytes(buffer[: pos + len(delimiter)])
                Debug.debug(f"Fast read complete: {len(result)} bytes with delimiter")
                return result

        # No delimiter found
        if buffer:
            Debug.debug(f"Fast read timeout: {len(buffer)} bytes without delimiter")
        return bytes(buffer)

    def read_fast(
        self,
        max_bytes: int = 1024,
        timeout_ms: int = 100,
        delimiter: Optional[bytes] = None,
    ) -> Optional[bytes]:
        """
        Read raw bytes at very high speed with minimal overhead.

        This is optimized for bulk data transfer and high-frequency sampling.
        Use this instead of read_value() when you need maximum performance.

        Args:
            max_bytes (int): Maximum number of bytes to read. Default 1024.
            timeout_ms (int): Timeout in milliseconds. Default 100.
            delimiter (Optional[bytes]): If provided, read until this byte sequence
                                         is found (e.g., b"\\n"). Default None.

        Returns:
            Optional[bytes]: The raw bytes read, or None on error.
                            Empty bytes if no data and no delimiter found.
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Serial connection not open")
            return None

        original_timeout = self.serial.timeout

        try:
            self.serial.timeout = timeout_ms * 0.001

            # Read with delimiter if specified
            if delimiter:
                return self._read_with_delimiter(max_bytes, delimiter)

            # Simple read without delimiter
            buffer = self.serial.read(max_bytes)
            return buffer if buffer else b""

        except serial.SerialException as e:
            Debug.error(f"Serial error in fast read: {e}", exc_info=True)
            return None
        except Exception as e:
            Debug.error(f"Unexpected error in fast read: {e}", exc_info=True)
            return None
        finally:
            self.serial.timeout = original_timeout

    def _check_delimiter_in_buffer(
        self, buffer: bytearray, delimiter: bytes
    ) -> Optional[bytes]:
        """Check if delimiter is in buffer and extract message if found."""
        delimiter_pos = buffer.find(delimiter)
        if delimiter_pos == -1:
            return None

        message = bytes(buffer[:delimiter_pos])
        remaining = buffer[delimiter_pos + len(delimiter) :]

        if remaining:
            Debug.debug(f"Found delimiter, {len(remaining)} bytes remain in buffer")

        Debug.debug(f"Read complete message: {len(message)} bytes")
        return message

    def read_until_delimiter(
        self,
        delimiter: bytes = b"\n",
        max_buffer: int = 4096,
        timeout: float = 2.0,
    ) -> Optional[bytes]:
        """
        Read bytes until a delimiter is encountered.

        Optimized for streaming data where you need to read complete messages
        separated by a delimiter (e.g., newline).

        Args:
            delimiter (bytes): Byte sequence marking end of message. Default b"\\n".
            max_buffer (int): Maximum buffer size before giving up. Default 4096.
            timeout (float): Total timeout in seconds. Default 2.0.

        Returns:
            Optional[bytes]: Complete message excluding the delimiter, or None on error.
                            Empty bytes if no data received.
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Serial connection not open")
            return None

        buffer = bytearray()
        start_time = time()

        try:
            while len(buffer) < max_buffer:
                # Check timeout
                if (time() - start_time) > timeout:
                    Debug.info(
                        f"Timeout reading until delimiter (collected {len(buffer)} bytes)"
                    )
                    return bytes(buffer) if buffer else None

                # Read available data
                chunk = self.read_fast(max_bytes=64, timeout_ms=50)
                if chunk is None:
                    Debug.error("read_fast() returned None")
                    return None

                if not chunk:
                    sleep(0.01)
                    continue

                buffer.extend(chunk)

                # Check if delimiter found
                message = self._check_delimiter_in_buffer(buffer, delimiter)
                if message is not None:
                    return message

            # Buffer full without finding delimiter
            Debug.info(
                f"Buffer limit ({max_buffer} bytes) reached without finding delimiter"
            )
            return bytes(buffer) if buffer else None

        except Exception as e:
            Debug.error(f"Error reading until delimiter: {e}", exc_info=True)
            return None

    def flush_input_buffer(self) -> bool:
        """
        Clear the serial input buffer for a clean restart.

        Reads and discards all pending data in the buffer. Useful before
        expecting a specific response.

        Returns:
            bool: True on success, False on error.
        """
        if not self.serial or not self.serial.is_open:
            Debug.error("Serial connection not open")
            return False

        try:
            discarded_bytes = 0

            # Read and discard all available data
            while self.serial.in_waiting > 0:
                try:
                    chunk = self.serial.read(min(self.serial.in_waiting, 256))
                    discarded_bytes += len(chunk)
                    sleep(0.001)  # Brief wait for more data to arrive
                except serial.SerialException:
                    break

            # Reset input buffer
            try:
                self.serial.reset_input_buffer()
            except (OSError, serial.SerialException):
                # Some virtual ports don't support this
                pass

            if discarded_bytes > 0:
                Debug.debug(f"Flushed {discarded_bytes} bytes from input buffer")

            return True

        except Exception as e:
            Debug.error(f"Error flushing input buffer: {e}", exc_info=True)
            return False

    def set_config(self, key: str, value: Any) -> bool:
        """
        Sets a configuration parameter for the Arduino.

        Args:
            key (str): Configuration parameter name
            value (Any): Configuration parameter value

        Returns:
            bool: True if configuration was set successfully, False otherwise
        """
        self._config[key] = value
        return self.send_command(f"CONFIG {key}={value}")

    def get_config(self, key: str) -> Any:
        """
        Retrieves a configuration parameter.

        Args:
            key (str): Configuration parameter name

        Returns:
            Any: The configuration parameter value
        """
        return self._config.get(key, None)


class GMCounter(Arduino):
    """
    A class to represent a GM counter connected to an Arduino.
    Class only for communication with GM counters and basic validity checks.

    Inherits from the Arduino class and provides additional functionality specific to GM counters.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        super().__init__(port, baudrate, timeout)
        self._device_info_cache: Optional[Dict[str, str]] = (
            None  # Cache for device info
        )
        # Establish single connection
        self.reconnect()
        Debug.info("Initializing GMCounter...")

        # Stop any ongoing measurement immediately after connection
        self.set_counting(False)  # Send "s0" to stop measurement
        self.set_stream(0)  # Stop any streaming by default
        self.clear_register()
        sleep(0.5)  # Allow time for the Arduino to process commands

        # Clear any buffered data (limit iterations to avoid blocking)
        max_attempts = 3
        attempt = 0
        init_value = self.read_value()
        while init_value != "" and init_value is not None and attempt < max_attempts:
            Debug.debug(f"Clearing initial buffer: {init_value}")
            self.set_stream(0)  # Ensure streaming is stopped
            init_value = self.read_value()
            attempt += 1
            sleep(0.1)  # Reduced sleep time

    def _parse_data_field(self, key: str, value: str) -> Union[int, bool]:
        """Parse a single data field."""
        if key == "repeat":
            return bool(int(value))
        return int(value)

    def _parse_csv_line(self, line: str, data_template: dict) -> dict:
        """Parse comma-separated data line into dictionary."""
        parts = line.split(",")

        # Remove empty trailing parts
        if parts and parts[-1] == "":
            parts = parts[:-1]

        # Validate field count
        if len(parts) != len(data_template):
            Debug.info(f"Expected {len(data_template)} fields, got {len(parts)}")
            if not parts:
                return data_template

        # Parse each field
        result = data_template.copy()
        for i, part in enumerate(parts):
            if i >= len(data_template):
                break
            key = list(data_template.keys())[i]
            try:
                result[key] = self._parse_data_field(key, part)
            except (ValueError, IndexError) as e:
                Debug.info(f"Could not parse field '{key}': '{part}' ({e})")

        return result

    def get_data(self, request: bool = True) -> Dict[str, Union[int, bool]]:
        """
        Extracts data from the GM counter data string stream.

        Sends a request to the device (if requested) and reads a single
        data line containing comma-separated values.

        Args:
            request (bool): If True, send a data request command first. Default True.

        Returns:
            dict: A dictionary with keys:
                - 'count': Current count value
                - 'last_count': Last count value
                - 'counting_time': Counting time setting
                - 'repeat': Repeat mode (bool)
                - 'progress': Progress value
                - 'voltage': Current voltage setting
                All values default to 0/False if parsing fails.
        """
        data_template = {
            "count": 0,
            "last_count": 0,
            "counting_time": 0,
            "repeat": False,
            "progress": 0,
            "voltage": 0,
        }

        try:
            if request:
                Debug.info("Requesting data from GMCounter...")
                if not self.send_command("b2"):
                    Debug.error("Failed to send data request command")
                    return data_template
                sleep(0.1)

            # Read single line of data
            Debug.debug("Reading data from GMCounter...")
            line = self.read_value(timeout=2.0, return_type="str")

            if not line:
                Debug.info("No data received from GMCounter")
                return data_template

            # Parse comma-separated values
            Debug.debug(f"Parsing data line: '{line}'")
            data = self._parse_csv_line(line, data_template)
            Debug.debug(f"Parsed data: {data}")
            return data

        except Exception as e:
            Debug.error(f"Error in get_data: {e}", exc_info=True)
            return data_template

    def set_stream(self, value: int = 0):
        """
        Sets the stream value for the GM counter.

        Args:
            value (int): The stream value to set.
                '0': Stop streaming.
                '1': Send streaming data when the measurement is ready.
                '2': Send streaming data now.
                '3': Send data now and continue when ready ('2' + '1').
                '4': Send data every 50 ms.
                '5': Use a comma as a separator between values.
                '6': Use a semicolon as a separator between values.
                '7': Use a space as a separator between values.
                '8': Use a tab as a separator between values.
        """
        self.send_command(f"b{value}")
        return True

    def get_information(self, use_cache: bool = True) -> Dict[str, str]:
        """
        Gets information from the GM counter.

        Queries the device for copyright, version, and OpenBIS code information.
        Uses read_text_response() with optimized timeouts for fast handshake.
        Results are cached to avoid repeated queries.

        Args:
            use_cache (bool): If True and info was previously fetched, return cached value.
                             Set to False to force a fresh query. Default True.

        Returns:
            dict: A dictionary containing:
                - 'copyright': Copyright/device information
                - 'version': Software version information
                - 'openbis': OpenBIS code identifier
        """
        # Return cached info if available and cache is enabled
        if use_cache and self._device_info_cache is not None:
            Debug.debug("Returning cached device information")
            return self._device_info_cache.copy()

        info = {"copyright": "", "version": "", "openbis": ""}

        try:
            # Flush buffer before starting to avoid reading stale data
            self.flush_input_buffer()

            # Use shorter timeout (0.3s) for faster handshake when no response expected
            Debug.info("Requesting copyright information...")
            self.send_command("oc")
            response = self.read_text_response(timeout=0.3)
            if response:
                info["copyright"] = response
                Debug.info(f"Copyright info: {info['copyright']}")
            else:
                Debug.debug("No copyright information received")

            Debug.info("Requesting version information...")
            self.send_command("sv")
            response = self.read_text_response(timeout=0.3)
            if response:
                info["version"] = response
                Debug.info(f"Version info: {info['version']}")
            else:
                Debug.debug("No version information received")

            Debug.info("Requesting OpenBIS code...")
            self.send_command("info")
            response = self.read_text_response(timeout=0.3)
            if response:
                # Parse response format: "OpenBIS code: XXXXX" or similar
                if ":" in response:
                    info["openbis"] = response.split(":", 1)[1].strip()
                else:
                    info["openbis"] = response.strip()
                Debug.info(f"OpenBIS code: {info['openbis']}")
            else:
                Debug.debug("No OpenBIS code received")

            # Cache the result
            self._device_info_cache = info.copy()

        except Exception as e:
            Debug.error(f"Error getting information: {e}", exc_info=True)

        return info

    def set_voltage(self, value: int = 500):
        """
        Sets the voltage for the GM counter.

        Args:
            value (int): The voltage value in volt to set (default is 500).
        """
        if not 300 <= value <= 700:
            Debug.error("Error: Voltage must be between 300 and 700.")
            return None
        self.send_command(f"j{value}")
        return True

    def set_repeat(self, value: bool = False):
        """
        Sets the repeat mode for the GM counter.

        Args:
            value (bool): True to enable repeat mode, False to disable it.
        """
        self.send_command(f"o{int(value)}")
        return True

    def set_counting(self, value: bool = False):
        """
        Starts or stops the counting process of the GM counter.

        Args:
            value (bool): True to start counting, False to stop it.
        """
        self.send_command(f"s{int(value)}")
        return True

    def set_speaker(self, gm: bool = False, ready: bool = False):
        """
        Sets the speaker settings for the GM counter.
        The speaker settings are represented by a combination of two binary values:
        - 'U0': GM sound off - Ready sound off
        - 'U1': GM sound on - Ready sound off
        - 'U2': GM sound off - Ready sound on
        - 'U3': GM sound on - Ready sound on

        Args:
            gm (bool): True to enable GM sound, False to disable it.
            ready (bool): True to enable ready sound, False to disable it.
        """
        self.send_command(f"U{int(gm) + 2 * int(ready)}")
        return True

    def set_counting_time(self, value: int = 0):
        """
        Sets the counting time for the GM counter.

        Args:
            value (int): The counting time in seconds (default is 0).

        Possible settings:
            'f0': Infinite
            'f1': 1 second
            'f2': 10 seconds
            'f3': 60 seconds
            'f4': 100 seconds
            'f5': 300 seconds
        """
        if not 0 <= value <= 5:
            Debug.error("Error: Counting time key must be between 0 and 5.")
            return None
        self.send_command(f"f{value}")
        return True

    def clear_register(self):
        """
        Clears the register of the GM counter.
        This is typically used to reset the count.
        """
        self.send_command("w")
        return True
