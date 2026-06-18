"""Integration test: MockGMCounter PTY server → raw pyserial → PacketParser.

Exercises the full wire-protocol stack end-to-end without any Qt components.
Uses a real PTY pair (Unix only) and pyserial.

Run with: pytest tests/integration/test_pty_pipeline.py -v
(Automatically included in `pytest` when not on Windows.)
"""

import sys
import os
import tempfile
import threading
import time

import pytest

if sys.platform == "win32":
    pytest.skip("PTY-based tests require Unix", allow_module_level=True)

pytestmark = pytest.mark.integration

try:
    import serial
except ImportError:
    pytest.skip("pyserial required for PTY pipeline tests", allow_module_level=True)

from gmcounter.infrastructure.mocks.mock_gm_counter import (
    MockGMCounter,
    run_pty_server,
    TICKS_PER_US,
)
from gmcounter.infrastructure.packet_parser import PacketParser


# ---------------------------------------------------------------------------
# Fixture


@pytest.fixture
def pty_port(request):
    """Start a MockGMCounter PTY server with 1 ms fixed pulses; yield the port path."""
    port_file = os.path.join(
        tempfile.gettempdir(), f"gm_pty_pipeline_{os.getpid()}_{id(request)}.txt"
    )
    if os.path.exists(port_file):
        os.remove(port_file)

    stop = threading.Event()
    server = threading.Thread(
        target=run_pty_server,
        kwargs={
            "device_class": MockGMCounter,
            "stop_event": stop,
            "port_file": port_file,
            "pulse_interval_us": 1000,  # 1 ms fixed pulses — deterministic + fast
        },
        daemon=True,
    )
    server.start()

    deadline = time.time() + 5.0
    while not os.path.exists(port_file):
        if time.time() > deadline:
            stop.set()
            pytest.fail("MockGMCounter PTY server did not start within 5 s")
        time.sleep(0.05)

    with open(port_file) as fh:
        port = fh.read().strip()

    yield port

    stop.set()
    server.join(timeout=2.0)


def _read_until_bytes(ser, target: bytes, timeout: float) -> bytes:
    """Read from serial until `target` appears or timeout expires."""
    collected = bytearray()
    deadline = time.time() + timeout
    while time.time() < deadline:
        chunk = ser.read(max(1, ser.in_waiting))
        if chunk:
            collected.extend(chunk)
            if target in collected:
                break
        else:
            time.sleep(0.002)
    return bytes(collected)


# ---------------------------------------------------------------------------
# Tests


def test_start_marker_after_init(pty_port):
    """Sending INIT must result in the 6-byte 0xFF start marker immediately."""
    with serial.Serial(pty_port, baudrate=9600, timeout=2.0) as ser:
        ser.write(b"INIT\n")
        ser.flush()
        data = _read_until_bytes(ser, b"\xff" * 6, timeout=2.0)
        ser.write(b"ABOR\n")
        ser.flush()

    assert b"\xff" * 6 in data, f"Start marker not found in: {data[:20]!r}"


def test_data_packets_decodable_by_packet_parser(pty_port):
    """Data packets from the PTY must be decodable by PacketParser."""
    with serial.Serial(pty_port, baudrate=9600, timeout=2.0) as ser:
        ser.write(b"INIT\n")
        ser.flush()
        # Read start marker + several packets (each 6 bytes; 10 packets = 60 bytes)
        raw = _read_until_bytes(ser, b"\xff" * 6, timeout=2.0)
        # Read more bytes after the start marker
        time.sleep(0.05)  # let a few packets accumulate
        raw += ser.read(ser.in_waiting or 60)
        ser.write(b"ABOR\n")
        ser.flush()

    parser = PacketParser()
    frames = parser.feed(raw)
    assert len(frames) >= 1, "Expected at least one decoded frame from PTY stream"
    for _, us in frames:
        # MockGMCounter was started with pulse_interval_us=1000
        assert 900.0 <= us <= 1100.0, f"Unexpected interval: {us:.1f} µs"


def test_end_of_period_marker_emitted(pty_port):
    """After the 1-second counting window expires, 0xEE×6 must appear in the stream."""
    with serial.Serial(pty_port, baudrate=9600, timeout=5.0) as ser:
        ser.write(b"CONF:TIME 1\n")  # mode 1 = 1 second
        ser.flush()
        ser.write(b"INIT\n")
        ser.flush()
        raw = _read_until_bytes(ser, b"\xee" * 6, timeout=3.0)

    assert b"\xee" * 6 in raw, "End-of-period marker not received within 3 s"


def test_end_of_period_marker_parsed_correctly(pty_port):
    """PacketParser.end_of_period must be True after the EOP sentinel is fed."""
    with serial.Serial(pty_port, baudrate=9600, timeout=5.0) as ser:
        ser.write(b"CONF:TIME 1\n")
        ser.flush()
        ser.write(b"INIT\n")
        ser.flush()
        raw = _read_until_bytes(ser, b"\xee" * 6, timeout=3.0)

    parser = PacketParser()
    parser.feed(raw)
    assert parser.end_of_period, "PacketParser did not detect end-of-period"


def test_scpi_query_returns_csv_response(pty_port):
    """FETC:STAT? over a real PTY must return a parseable CSV response."""
    with serial.Serial(pty_port, baudrate=9600, timeout=2.0) as ser:
        # Query without INIT so no binary data is flowing
        ser.write(b"FETC:STAT?\n")
        ser.flush()
        resp_bytes = ser.readline()

    resp = resp_bytes.decode(errors="ignore").strip()
    parts = resp.split(",")
    assert len(parts) == 7, f"Unexpected FETC:STAT? format: {resp!r}"
    assert parts[-1] == "", "Missing trailing comma in FETC:STAT? response"
    # All fields except the trailing empty must be numeric
    for field in parts[:-1]:
        assert field.lstrip("-").isdigit(), f"Non-numeric field: {field!r}"


def test_idn_query_returns_expected_format(pty_port):
    """*IDN? must return a 4-field comma-separated string."""
    with serial.Serial(pty_port, baudrate=9600, timeout=2.0) as ser:
        ser.write(b"*IDN?\n")
        ser.flush()
        resp = ser.readline().decode(errors="ignore").strip()

    parts = resp.split(",")
    assert len(parts) == 4, f"Unexpected *IDN? format: {resp!r}"
    assert "TU Berlin" in parts[0]
    assert "GM-Counter" in parts[1]
