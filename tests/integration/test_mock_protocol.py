"""Integration tests for MockGMCounter: SCPI command handling and wire-protocol encoding.

All tests run entirely in-process (no PTY, no serial port, no Qt).
They verify that MockGMCounter is a faithful stand-in for the real firmware,
covering SCPI commands, packet encoding, start/end markers, and first-pulse
suppression.  These are fast enough to be part of the normal test suite.
"""

import time

import pytest

from gmcounter.infrastructure.mocks.mock_gm_counter import MockGMCounter, TICKS_PER_US
from gmcounter.infrastructure.packet_parser import PacketParser


# ---------------------------------------------------------------------------
# In-process PTY-loop simulation helpers


def _collect_bytes(mock: MockGMCounter, max_steps: int = 2000) -> bytes:
    """Simulate run_pty_server() and collect every byte it would write to the PTY."""
    out = bytearray()
    for _ in range(max_steps):
        if mock._start_marker_pending:
            out += b"\xff" * 6
            mock._start_marker_pending = False
        if mock._end_marker_pending:
            out += b"\xee" * 6
            mock._end_marker_pending = False
        val = mock.tick()
        if val is not None:
            ticks = min(int(val) * TICKS_PER_US, 0xFFFFFFFF)
            out += bytes([0xAA]) + ticks.to_bytes(4, "little") + bytes([0x55])
        # Stop once the device is quiet and all markers have been written.
        if (
            not mock._counting
            and not mock._start_marker_pending
            and not mock._end_marker_pending
        ):
            break
    return bytes(out)


def _force_pulse(mock: MockGMCounter) -> None:
    """Move next_pulse_time into the past so the next tick() call fires immediately."""
    mock.next_pulse_time = 0.0


def _make(pulse_interval_us: int = 1000) -> MockGMCounter:
    return MockGMCounter(port="mock://test", pulse_interval_us=pulse_interval_us)


# ---------------------------------------------------------------------------
# SCPI command fidelity


class TestScpiCommands:
    def test_idn_response_format(self):
        resp = _make().handle_command("*IDN?")
        assert resp is not None
        parts = resp.split(",")
        # Manufacturer, model, serial, firmware version
        assert len(parts) == 4
        assert "TU Berlin" in parts[0]
        assert "GM-Counter" in parts[1]
        assert "MOCK-001" in parts[2]

    def test_rst_resets_all_settings(self):
        m = _make()
        m.handle_command("CONF:VOLT 620")
        m.handle_command("CONF:TIME 3")
        m.handle_command("CONF:REP 1")
        m.handle_command("CONF:STR 4")
        m.handle_command("INIT")
        m.handle_command("*RST")
        assert not m._counting
        assert m._voltage == 500
        assert m._counting_time_mode == 2
        assert not m._repeat
        assert m._stream_mode == 0

    def test_cls_returns_none(self):
        assert _make().handle_command("*CLS") is None

    def test_tst_returns_zero(self):
        assert _make().handle_command("*TST?") == "0"

    def test_opc_returns_one(self):
        assert _make().handle_command("*OPC?") == "1"

    def test_syst_err_no_error(self):
        resp = _make().handle_command("SYST:ERR?")
        assert resp is not None
        assert resp.startswith("0")

    def test_syst_clr_resets_count(self):
        m = _make()
        m.handle_command("INIT")
        _force_pulse(m)
        m.tick()  # first (suppressed)
        _force_pulse(m)
        m.tick()  # second — increments count
        assert m._count == 2
        m.handle_command("SYST:CLR")
        assert m._count == 0
        assert m._last_count == 0

    def test_init_starts_counting_and_queues_start_marker(self):
        m = _make()
        m.handle_command("INIT")
        assert m._counting
        assert not m._counting_only
        assert m._start_marker_pending

    def test_abor_stops_counting(self):
        m = _make()
        m.handle_command("INIT")
        m.handle_command("ABOR")
        assert not m._counting

    def test_meas_strt_sets_counting_only(self):
        m = _make()
        m.handle_command("MEAS:STRT")
        assert m._counting
        assert m._counting_only

    def test_meas_stp_stops_counting_only(self):
        m = _make()
        m.handle_command("MEAS:STRT")
        m.handle_command("MEAS:STP")
        assert not m._counting

    def test_conf_volt_set_and_query(self):
        m = _make()
        m.handle_command("CONF:VOLT 620")
        assert m.handle_command("CONF:VOLT?") == "620"
        assert m._voltage == 620

    def test_conf_volt_rejects_below_300(self):
        m = _make()
        m.handle_command("CONF:VOLT 200")
        assert m._voltage == 500  # unchanged

    def test_conf_volt_rejects_above_700(self):
        m = _make()
        m.handle_command("CONF:VOLT 750")
        assert m._voltage == 500  # unchanged

    def test_conf_volt_accepts_boundaries(self):
        m = _make()
        m.handle_command("CONF:VOLT 300")
        assert m._voltage == 300
        m.handle_command("CONF:VOLT 700")
        assert m._voltage == 700

    def test_conf_time_set_and_query(self):
        m = _make()
        m.handle_command("CONF:TIME 3")
        assert m.handle_command("CONF:TIME?") == "3"
        assert m._counting_time_mode == 3

    def test_conf_rep_on_off(self):
        m = _make()
        m.handle_command("CONF:REP 1")
        assert m._repeat
        assert m.handle_command("CONF:REP?") == "1"
        m.handle_command("CONF:REP 0")
        assert not m._repeat
        assert m.handle_command("CONF:REP?") == "0"

    def test_conf_str_set_and_query(self):
        m = _make()
        m.handle_command("CONF:STR 4")
        assert m._stream_mode == 4
        assert m.handle_command("CONF:STR?") == "4"

    def test_conf_spkr_set_and_query(self):
        m = _make()
        m.handle_command("CONF:SPKR 3")  # bit 0 = gm, bit 1 = ready
        assert m._speaker_gm
        assert m._speaker_ready
        assert m.handle_command("CONF:SPKR?") == "3"

    def test_conf_spkr_gm_only(self):
        m = _make()
        m.handle_command("CONF:SPKR 1")
        assert m._speaker_gm
        assert not m._speaker_ready
        assert m.handle_command("CONF:SPKR?") == "1"

    def test_fetc_stat_format_matches_adapter_parser(self):
        """FETC:STAT? must produce the CSV format GMCounterAdapter.get_data() parses.

        Expected: count,last_count,counting_time,repeat,progress,voltage,
                  (6 fields + trailing comma → 7 elements after split)
        """
        m = _make()
        m.handle_command("CONF:VOLT 600")
        resp = m.handle_command("FETC:STAT?")
        assert resp is not None
        parts = resp.split(",")
        assert len(parts) == 7, f"Expected 6 fields + trailing comma; got: {resp!r}"
        count, last_count, ct, repeat, progress, voltage, trailing = parts
        assert trailing == "", "Missing trailing comma"
        assert count.isdigit()
        assert last_count.isdigit()
        assert ct.isdigit()
        assert repeat in ("0", "1")
        assert progress.isdigit()
        assert voltage == "600"

    def test_fetc_stat_updates_after_counting(self):
        m = _make()
        m.handle_command("INIT")
        for _ in range(5):
            _force_pulse(m)
            m.tick()
        m.handle_command("ABOR")
        resp = m.handle_command("FETC:STAT?")
        parts = resp.split(",")
        count = int(parts[0])
        assert count >= 1  # at least some pulses counted

    def test_unknown_command_returns_none(self):
        assert _make().handle_command("UNKN:CMD?") is None


# ---------------------------------------------------------------------------
# Wire-protocol encoding fidelity


class TestWireProtocol:
    def test_start_marker_is_six_0xff(self):
        m = _make()
        m.handle_command("INIT")
        out = _collect_bytes(m, max_steps=1)
        assert out[:6] == b"\xff" * 6, f"Expected start marker, got: {out[:6]!r}"

    def test_no_start_marker_without_init(self):
        m = _make()
        out = _collect_bytes(m, max_steps=10)
        assert b"\xff" not in out

    def test_start_marker_cleared_after_emit(self):
        m = _make()
        m.handle_command("INIT")
        _collect_bytes(m, max_steps=1)
        assert not m._start_marker_pending

    def test_first_pulse_is_always_suppressed(self):
        """first_delta_is_from_start=false: host seeds event #1 at t=0."""
        m = _make()
        m.handle_command("INIT")
        # Drain start marker
        _collect_bytes(m, max_steps=1)
        _force_pulse(m)
        val = m.tick()
        assert val is None, f"First pulse should be suppressed; got {val}"
        assert m._first_pulse_done

    def test_second_pulse_returns_interval(self):
        m = _make(pulse_interval_us=1000)
        m.handle_command("INIT")
        _collect_bytes(m, max_steps=1)  # drain start marker
        _force_pulse(m)
        m.tick()  # first — suppressed
        _force_pulse(m)
        val = m.tick()
        assert val == 1000

    def test_packet_ticks_encoding_1000us(self):
        """1000 µs × 48 = 48000 ticks = 0xBB80 → little-endian [0x80, 0xBB, 0x00, 0x00]."""
        m = _make(pulse_interval_us=1000)
        m.handle_command("INIT")
        _collect_bytes(m, max_steps=1)  # start marker
        _force_pulse(m)
        m.tick()  # suppressed
        _force_pulse(m)
        val = m.tick()
        assert val == 1000
        ticks = val * TICKS_PER_US
        assert ticks == 48000
        encoded = ticks.to_bytes(4, "little")
        # 48000 = 0xBB80 in little-endian
        assert encoded == bytes([0x80, 0xBB, 0x00, 0x00])

    def test_full_packet_structure(self):
        """[0xAA][4 LE tick bytes][0x55] — 6 bytes total."""
        m = _make(pulse_interval_us=500)
        m.handle_command("INIT")
        _collect_bytes(m, max_steps=1)  # start marker
        _force_pulse(m)
        m.tick()  # suppressed
        m.next_pulse_time = 0.0
        out = _collect_bytes(m, max_steps=2)
        assert len(out) == 6, f"Expected 6-byte packet, got {len(out)} bytes"
        assert out[0] == 0xAA
        assert out[5] == 0x55
        ticks = int.from_bytes(out[1:5], "little")
        assert ticks == 500 * TICKS_PER_US  # 24000 = 0x5DC0 → [0xC0, 0x5D, 0x00, 0x00]

    def test_end_of_period_marker_is_six_0xee(self):
        m = _make()
        m.handle_command("CONF:TIME 1")  # mode 1 = 1-second period
        m.handle_command("INIT")
        m._measurement_start_time = time.time() - 2.0  # fake elapsed time
        out = _collect_bytes(m, max_steps=50)
        assert b"\xee" * 6 in out, "End-of-period marker not found"

    def test_counting_stops_after_period_ends(self):
        m = _make()
        m.handle_command("CONF:TIME 1")
        m.handle_command("INIT")
        m._measurement_start_time = time.time() - 2.0
        _collect_bytes(m, max_steps=50)
        assert not m._counting

    def test_no_end_marker_in_continuous_mode(self):
        """Mode 0 = continuous counting; 0xEE×6 must never appear."""
        m = _make(pulse_interval_us=1000)
        m.handle_command("CONF:TIME 0")
        m.handle_command("INIT")
        out = bytearray(_collect_bytes(m, max_steps=1))  # start marker only
        for _ in range(15):
            _force_pulse(m)
            out += _collect_bytes(m, max_steps=2)
        assert b"\xee" * 6 not in out
        assert m._counting  # still running

    def test_counting_only_emits_no_data_packets(self):
        """MEAS:STRT counter-only mode: pulses are counted but no packets emitted."""
        m = _make(pulse_interval_us=1000)
        m.handle_command("MEAS:STRT")
        for _ in range(20):
            _force_pulse(m)
            m.tick()
        assert m._count >= 1
        out = _collect_bytes(m, max_steps=5)
        assert 0xAA not in out

    def test_ticks_per_us_matches_config(self):
        """TICKS_PER_US in mock must equal config.json acquisition.ticks_per_us."""
        from gmcounter.infrastructure.config import import_config

        cfg = import_config()
        assert TICKS_PER_US == cfg["acquisition"]["ticks_per_us"]


# ---------------------------------------------------------------------------
# PacketParser round-trip


class TestPacketParserRoundtrip:
    def test_single_packet_decoded_correctly(self):
        m = _make(pulse_interval_us=1000)
        m.handle_command("INIT")
        _force_pulse(m)
        m.tick()  # suppressed first pulse
        _force_pulse(m)
        val = m.tick()
        ticks = min(int(val) * TICKS_PER_US, 0xFFFFFFFF)
        wire = b"\xff" * 6 + bytes([0xAA]) + ticks.to_bytes(4, "little") + bytes([0x55])

        parser = PacketParser()
        frames = parser.feed(wire)
        assert len(frames) == 1
        idx, us = frames[0]
        assert idx == 1
        assert abs(us - 1000.0) < 1.0

    def test_multiple_packets_all_decoded(self):
        m = _make(pulse_interval_us=2000)
        m.handle_command("INIT")
        _force_pulse(m)
        m.tick()  # suppressed first

        wire = bytearray(b"\xff" * 6)
        for _ in range(5):
            _force_pulse(m)
            val = m.tick()
            if val is not None:
                ticks = min(int(val) * TICKS_PER_US, 0xFFFFFFFF)
                wire += bytes([0xAA]) + ticks.to_bytes(4, "little") + bytes([0x55])

        parser = PacketParser()
        frames = parser.feed(bytes(wire))
        assert len(frames) == 5
        for _, us in frames:
            assert abs(us - 2000.0) < 1.0

    def test_end_marker_sets_end_of_period_flag(self):
        m = _make()
        m.handle_command("CONF:TIME 1")
        m.handle_command("INIT")
        m._measurement_start_time = time.time() - 2.0
        wire = _collect_bytes(m, max_steps=50)
        parser = PacketParser()
        parser.feed(wire)
        assert parser.end_of_period

    def test_index_sequence_is_contiguous(self):
        m = _make(pulse_interval_us=500)
        m.handle_command("INIT")
        _force_pulse(m)
        m.tick()  # suppressed

        wire = bytearray(b"\xff" * 6)
        for _ in range(8):
            _force_pulse(m)
            val = m.tick()
            if val is not None:
                ticks = min(int(val) * TICKS_PER_US, 0xFFFFFFFF)
                wire += bytes([0xAA]) + ticks.to_bytes(4, "little") + bytes([0x55])

        parser = PacketParser()
        frames = parser.feed(bytes(wire))
        assert len(frames) == 8
        for expected_idx, (actual_idx, _) in enumerate(frames, start=1):
            assert actual_idx == expected_idx
