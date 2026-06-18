# Layer: infrastructure/mocks — wire-compatible MockGMCounter.
# Excluded from the wheel (pyproject.toml).
#
# PTY-based mock: starts a pseudo-terminal, writes the port path to
# /tmp/virtual_serial_port.txt, and responds to the GMCounter command set
# by emitting binary packets + start marker.

import logging
import os
import pty
import random
import select
import time
import tty
from tempfile import gettempdir
from typing import Optional, Dict, Union

_log = logging.getLogger(__name__)

PORT_FILE = os.path.join(gettempdir(), "virtual_serial_port.txt")

# Inter-event deltas are sent as raw firmware timer ticks; the host divides by
# this to recover microseconds.  MUST match config.json acquisition.ticks_per_us
# and the firmware TICKS_PER_US (RA4M1 @ 48 MHz).
TICKS_PER_US = 48


class MockGMCounter:
    """Wire-compatible mock for GMCounterAdapter.

    Simulates the GM counter binary protocol:
    - Start marker: 0xFF × 6 on measurement start
    - Data packets: 0xAA + 4-byte little-endian tick value + 0x55
      (ticks = µs × TICKS_PER_US, matching the firmware wire format)
    - End-of-period marker: 0xEE × 6 when counting time elapses
    - is_mock_device = True so the acquisition thread uses longer timeouts.

    Args:
        pulse_interval_us: When set, all pulses fire at this fixed interval (µs)
            instead of random intervals. Useful for deterministic testing.
    """

    is_mock_device: bool = True

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        max_tick: float = 1.0,
        pulse_interval_us: Optional[int] = None,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.max_tick = max_tick
        self._min_tick = 0.000_08  # 80 µs minimum
        self._pulse_interval_us = pulse_interval_us  # None = random

        self._voltage = 500
        self._repeat = False
        self._counting = False
        self._counting_time_mode = 2
        self._count = 0
        self._last_count = 0
        self._measurement_start_time = 0.0
        self._next_pulse_interval = 0.0
        self.next_pulse_time = 0.0
        self._stream_mode = 0
        self._start_marker_pending = False
        self._end_marker_pending = False  # True when period ends in streaming mode
        self._counting_only = False
        self._first_pulse_done = (
            False  # True after first pulse; suppresses start→first-pulse packet
        )
        self._speaker_gm = False
        self._speaker_ready = False

        _log.info("MockGMCounter initialized on port %s", port)

    # ------------------------------------------------------------------
    # Query methods (match GMCounterAdapter interface)

    def get_data(self) -> Optional[Dict[str, Union[int, bool]]]:
        ct_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        ct = ct_map.get(self._counting_time_mode, 0)
        progress = 0
        if self._counting and ct > 0:
            elapsed = time.time() - self._measurement_start_time
            progress = min(100, int((elapsed / ct) * 100))
        data = {
            "count": self._count,
            "last_count": self._last_count,
            "counting_time": ct,
            "repeat": self._repeat,
            "progress": progress,
            "voltage": self._voltage,
        }
        return data if data["voltage"] != 0 else None

    def get_information(self) -> Dict[str, str]:
        return {
            "copyright": "(C) 2024 TU Berlin - Mock GM Counter",
            "version": "Mock v1.0.0 (GMCounter Test Device)",
            "openbis": "MOCK-001",
        }

    # ------------------------------------------------------------------
    # Control commands

    def set_voltage(self, value: int = 500) -> None:
        if 300 <= value <= 700:
            self._voltage = value

    def set_repeat(self, value: bool = False) -> None:
        self._repeat = value

    def set_counting(self, value: bool = False) -> None:
        if value and not self._counting:
            self._counting = True
            self._counting_only = False
            self._last_count = self._count
            self._count = 0
            self._measurement_start_time = time.time()
            self._start_marker_pending = True
            self._end_marker_pending = False
            self._first_pulse_done = False  # reset so first packet is suppressed
            self._next_pulse_interval = (
                self._pulse_interval_us / 1_000_000
                if self._pulse_interval_us is not None
                else random.uniform(self._min_tick, self.max_tick)
            )
            self.next_pulse_time = time.time() + self._next_pulse_interval
            _log.info("MockGMCounter: counting started")
        elif not value and self._counting:
            self._counting = False
            self._counting_only = False
            _log.info("MockGMCounter: counting stopped (count=%d)", self._count)

    def set_counting_only(self, value: bool = False) -> None:
        """Start/stop counter without the streaming interrupt (no packet emission)."""
        if value and not self._counting:
            self._counting = True
            self._counting_only = True
            self._last_count = self._count
            self._count = 0
            self._measurement_start_time = time.time()
            self._next_pulse_interval = (
                self._pulse_interval_us / 1_000_000
                if self._pulse_interval_us is not None
                else random.uniform(self._min_tick, self.max_tick)
            )
            self.next_pulse_time = time.time() + self._next_pulse_interval
            _log.info("MockGMCounter: counter-only started")
        elif not value and self._counting:
            self._counting = False
            self._counting_only = False
            _log.info("MockGMCounter: counter-only stopped (count=%d)", self._count)

    def set_speaker(self, gm: bool = False, ready: bool = False) -> None:
        self._speaker_gm = gm
        self._speaker_ready = ready

    def set_counting_time(self, value: int = 0) -> None:
        if 0 <= value <= 5:
            self._counting_time_mode = value

    def set_stream(self, value: int = 0) -> None:
        self._stream_mode = value

    def clear_register(self) -> None:
        self._count = 0
        self._last_count = 0

    # ------------------------------------------------------------------
    # PTY protocol loop helpers

    def handle_command(self, command: str) -> Optional[str]:
        command = command.strip()
        upper = command.upper()

        # ── IEEE 488.2 ──
        if upper == "*IDN?":
            info = self.get_information()
            return f"TU Berlin,GM-Counter,MOCK-001,{info['version']}"
        if upper == "*RST":
            self.set_counting(False)
            self._counting_only = False
            self._voltage = 500
            self._repeat = False
            self._counting_time_mode = 2
            self._stream_mode = 0
            return None
        if upper in ("*CLS", "*TST?", "*OPC?"):
            return "0" if upper == "*TST?" else ("1" if upper == "*OPC?" else None)

        # ── SYSTem ──
        if upper in ("SYST:ERR?", "SYSTEM:ERROR?"):
            return '0,"No error"'
        if upper in ("SYST:CLR", "SYST:CLEAR", "SYSTEM:CLEAR"):
            self.clear_register()
            return None

        # ── INITiate / ABORt ──
        if upper in ("INIT", "INIT:IMM", "INITIATE:IMMEDIATE"):
            self.set_counting(True)
            return None
        if upper in ("ABOR", "ABORT"):
            self.set_counting(False)
            return None

        # ── MEASure (counter-only, no streaming interrupt) ──
        if upper in ("MEAS:STRT", "MEASURE:START"):
            self.set_counting_only(True)
            return None
        if upper in ("MEAS:STP", "MEASURE:STOP"):
            self.set_counting_only(False)
            return None

        # ── FETCh ──
        if upper in ("FETC:STAT?", "FETCH:STATUS?"):
            d = self.get_data()
            if d:
                return (
                    f"{d['count']},{d['last_count']},"
                    f"{d['counting_time']},{int(d['repeat'])},"
                    f"{d['progress']},{d['voltage']},"
                )
            return None

        # ── CONFigure ──
        if upper.startswith("CONF:VOLT") or upper.startswith("CONFIGURE:VOLTAGE"):
            parts = command.split(None, 1)
            if upper.endswith("?"):
                return str(self._voltage)
            if len(parts) == 2:
                try:
                    self.set_voltage(int(parts[1]))
                except ValueError:
                    pass
            return None
        if upper.startswith("CONF:TIME") or upper.startswith("CONFIGURE:TIME"):
            parts = command.split(None, 1)
            if upper.endswith("?"):
                return str(self._counting_time_mode)
            if len(parts) == 2:
                try:
                    self.set_counting_time(int(parts[1]))
                except ValueError:
                    pass
            return None
        if upper.startswith("CONF:REP") or upper.startswith("CONFIGURE:REPEAT"):
            parts = command.split(None, 1)
            if upper.endswith("?"):
                return "1" if self._repeat else "0"
            if len(parts) == 2:
                val = parts[1].upper()
                self.set_repeat(val in ("ON", "1"))
            return None
        if upper.startswith("CONF:STR") or upper.startswith("CONFIGURE:STREAM"):
            parts = command.split(None, 1)
            if upper.endswith("?"):
                return str(self._stream_mode)
            if len(parts) == 2:
                try:
                    self._stream_mode = int(parts[1])
                except ValueError:
                    pass
            return None

        # ── DIAGnostic ──
        if upper.startswith("CONF:SPKR") or upper.startswith("CONFIGURE:SPEAKER"):
            parts = command.split(None, 1)
            if upper.endswith("?"):
                return str(int(self._speaker_gm) + 2 * int(self._speaker_ready))
            if len(parts) == 2:
                try:
                    v = int(parts[1])
                    self.set_speaker(gm=bool(v & 1), ready=bool(v & 2))
                except ValueError:
                    pass
            return None

        _log.warning("MockGMCounter: unrecognised command: %s", command)
        return None

    def tick(self) -> Optional[int]:
        """Return inter-event time in µs if a packet-streaming pulse is due, else None.

        Returns None in counter-only mode (_counting_only=True) — the count still
        increments but no binary packet is emitted.
        """
        if not self._counting:
            return None

        ct_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        limit = ct_map.get(self._counting_time_mode, 0)
        if limit > 0 and (time.time() - self._measurement_start_time) >= limit:
            if self._counting_only:
                self.set_counting_only(False)
            else:
                # Streaming mode: emit the end-of-period sentinel before stopping.
                # The sentinel is queued here; run_pty_server() writes it to the PTY.
                if not self._end_marker_pending:
                    self._end_marker_pending = True
                    _log.info("MockGMCounter: period ended — end marker pending")
                self.set_counting(False)
            return None

        if time.time() >= self.next_pulse_time:
            interval_us = (
                self._pulse_interval_us
                if self._pulse_interval_us is not None
                else int(self._next_pulse_interval * 1_000_000)
            )
            self._count += 1
            self._next_pulse_interval = (
                self._pulse_interval_us / 1_000_000
                if self._pulse_interval_us is not None
                else random.uniform(self._min_tick, self.max_tick)
            )
            self.next_pulse_time = time.time() + self._next_pulse_interval
            if not self._first_pulse_done:
                # Suppress the start→first-pulse packet so the host receives pure
                # inter-event gaps. The "+1" convention on the host accounts for this
                # first event at t=0. Subsequent packets are first→second, second→third, …
                self._first_pulse_done = True
                return None
            return None if self._counting_only else interval_us

        return None


def run_pty_server(
    device_class=MockGMCounter,
    stop_event=None,
    port_file: Optional[str] = None,
    **device_kwargs,
) -> None:
    """Run a PTY-based mock GM counter server.

    Writes the slave port path to ``port_file`` (defaults to PORT_FILE) so
    the caller can read it.  Stop by setting ``stop_event`` (threading.Event)
    or pressing Ctrl-C.

    Pass a unique ``port_file`` path when running multiple instances in the
    same process (e.g. parallel test fixtures) to avoid collisions.
    """
    actual_port_file = port_file if port_file is not None else PORT_FILE

    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    _log.info("Virtual serial port: %s", slave_name)

    tmp_path = actual_port_file + ".tmp"
    try:
        with open(actual_port_file, "w", encoding="utf-8") as fh:
            fh.write(slave_name)
        os.replace(
            tmp_path, actual_port_file
        )  # atomic on Unix — file appears fully written
    except IOError as exc:
        _log.error("Could not write port file: %s", exc)

    tty.setraw(master)
    device = device_class(port=slave_name, **device_kwargs)

    try:
        while not (stop_event and stop_event.is_set()):
            r, _, _ = select.select([master], [], [], 0.01)
            if r:
                try:
                    raw = os.read(master, 1024)
                    if not raw:
                        break
                    for cmd in raw.decode(errors="ignore").split("\n"):
                        cmd = cmd.strip()
                        if not cmd:
                            continue
                        response = device.handle_command(cmd)
                        if response:
                            os.write(master, (response + "\n").encode("utf-8"))
                except (OSError, ValueError):
                    break

            if device._start_marker_pending:
                os.write(master, b"\xff\xff\xff\xff\xff\xff")
                device._start_marker_pending = False

            if device._end_marker_pending:
                os.write(master, b"\xee\xee\xee\xee\xee\xee")
                device._end_marker_pending = False
                _log.info("MockGMCounter: end-of-period sentinel written to PTY")

            value = device.tick()
            if value is not None:
                # tick() returns µs; the wire protocol carries firmware ticks.
                ticks = min(int(value) * TICKS_PER_US, 0xFFFFFFFF)
                packet = (
                    bytes([0xAA])
                    + ticks.to_bytes(4, byteorder="little")
                    + bytes([0x55])
                )
                os.write(master, packet)

    except KeyboardInterrupt:
        pass
    finally:
        os.close(master)
        os.close(slave)
        if os.path.exists(actual_port_file):
            os.remove(actual_port_file)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pty_server()
