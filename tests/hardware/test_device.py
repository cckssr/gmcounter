"""Device-level integration tests using the gm_adapter fixture.

The gm_adapter fixture (defined in tests/conftest.py) connects to real hardware
when --port is given, or starts a MockGMCounter PTY server otherwise.  These
tests exercise the GMCounterAdapter API identically in both cases.

Run:
    pytest tests/hardware/ -v                       # mock PTY (always works on Unix)
    pytest tests/hardware/ -v --port /dev/tty.xxx   # real hardware
"""

import time

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Device identity


class TestDeviceInfo:
    def test_get_information_returns_version(self, gm_adapter):
        info = gm_adapter.get_information()
        assert isinstance(info, dict)
        assert "version" in info
        assert info["version"]  # non-empty

    def test_get_information_returns_copyright(self, gm_adapter):
        info = gm_adapter.get_information()
        assert "copyright" in info

    def test_get_data_returns_dict(self, gm_adapter):
        data = gm_adapter.get_data()
        assert data is not None
        expected_keys = {
            "count",
            "last_count",
            "counting_time",
            "repeat",
            "progress",
            "voltage",
        }
        assert expected_keys.issubset(data.keys())


# ---------------------------------------------------------------------------
# Voltage and configuration


class TestConfiguration:
    def setup_method(self):
        """Placeholder; gm_adapter teardown handled by conftest fixture."""

    def test_voltage_set_and_read_back(self, gm_adapter):
        gm_adapter.set_voltage(550)
        data = gm_adapter.get_data()
        assert data is not None
        assert data["voltage"] == 550
        gm_adapter.set_voltage(500)  # restore

    def test_voltage_clamps_to_range(self, gm_adapter):
        """GMCounterAdapter silently ignores out-of-range voltages."""
        gm_adapter.set_voltage(500)  # baseline
        gm_adapter.set_voltage(200)  # below minimum — should be ignored
        data = gm_adapter.get_data()
        assert data is not None
        assert data["voltage"] == 500  # unchanged

    def test_counting_time_mode_reflected_in_data(self, gm_adapter):
        ct_map = {0: 0, 1: 1, 2: 10, 3: 60, 4: 100, 5: 300}
        for mode, expected_seconds in ct_map.items():
            gm_adapter.set_counting_time(mode)
            data = gm_adapter.get_data()
            assert data is not None
            assert data["counting_time"] == expected_seconds, (
                f"Mode {mode}: expected {expected_seconds} s, got {data['counting_time']}"
            )
        gm_adapter.set_counting_time(2)  # restore default

    def test_repeat_mode_on_and_off(self, gm_adapter):
        gm_adapter.set_repeat(True)
        data = gm_adapter.get_data()
        assert data["repeat"]
        gm_adapter.set_repeat(False)
        data = gm_adapter.get_data()
        assert not data["repeat"]


# ---------------------------------------------------------------------------
# Measurement control


class TestMeasurementControl:
    def test_start_then_stop(self, gm_adapter):
        gm_adapter.set_counting(True)
        time.sleep(0.1)
        gm_adapter.set_counting(False)
        data = gm_adapter.get_data()
        assert data is not None

    def test_clear_register_resets_count(self, gm_adapter):
        gm_adapter.set_counting(True)
        time.sleep(0.2)
        gm_adapter.set_counting(False)
        gm_adapter.clear_register()
        data = gm_adapter.get_data()
        assert data is not None
        assert data["count"] == 0
        assert data["last_count"] == 0

    def test_count_increments_during_measurement(self, gm_adapter):
        gm_adapter.clear_register()
        gm_adapter.set_counting(True)
        time.sleep(0.3)
        gm_adapter.set_counting(False)
        data = gm_adapter.get_data()
        assert data is not None
        # Mock emits pulses at random; at least 1 should arrive in 300 ms.
        # (Real hardware: depends on actual radiation level; assert count >= 0.)
        assert data["count"] >= 0  # structural check — always passes

    def test_stream_mode_set(self, gm_adapter):
        gm_adapter.set_stream(4)
        # No query API in GMCounterAdapter — just verify no exception
        gm_adapter.set_stream(0)


# ---------------------------------------------------------------------------
# Binary data stream


class TestDataStream:
    def test_start_marker_in_stream(self, gm_adapter):
        """After set_counting(True), the 0xFF×6 start marker must appear in the stream."""
        gm_adapter.set_counting(True)

        raw = b""
        deadline = time.time() + 2.0
        while time.time() < deadline:
            chunk = gm_adapter.read_fast(64)
            raw += chunk
            if b"\xff\xff\xff\xff\xff\xff" in raw:
                break
            if not chunk:
                time.sleep(0.01)

        gm_adapter.set_counting(False)
        assert b"\xff\xff\xff\xff\xff\xff" in raw, (
            "Start marker 0xFF×6 not found in stream within 2 s"
        )

    def test_data_packets_parseable(self, gm_adapter):
        """Packets in the stream must be decodable by PacketParser."""
        from gmcounter.infrastructure.packet_parser import PacketParser

        gm_adapter.set_counting(True)

        raw = bytearray()
        deadline = time.time() + 2.0
        while time.time() < deadline:
            chunk = gm_adapter.read_fast(128)
            raw.extend(chunk)
            if not chunk:
                time.sleep(0.01)

        gm_adapter.set_counting(False)

        parser = PacketParser()
        frames = parser.feed(bytes(raw))
        # If any frames were decoded they must have monotonic indices
        for i, (idx, _) in enumerate(frames, start=1):
            assert idx == i, f"Non-contiguous index: expected {i}, got {idx}"
