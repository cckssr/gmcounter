# Tests for the Qt-free binary packet parser (infrastructure.packet_parser).

from gmcounter.infrastructure.packet_parser import PacketParser

MARKER = b"\xff\xff\xff\xff\xff\xff"


def _packet(ticks: int) -> bytes:
    return bytes([0xAA]) + int(ticks).to_bytes(4, "little") + bytes([0x55])


def test_discards_until_marker():
    p = PacketParser(ticks_per_us=48)
    # Garbage + a packet *before* the marker must be dropped.
    out = p.feed(b"\x01\x02\x03" + _packet(4800) + MARKER + _packet(9600))
    assert p.synced
    assert out == [(1, 200.0)]  # only the post-marker packet, 9600/48 = 200 µs


def test_tick_to_us_conversion():
    p = PacketParser(ticks_per_us=48)
    p.feed(MARKER)
    out = p.feed(_packet(4800) + _packet(96))  # 100 µs, 2 µs
    assert out == [(1, 100.0), (2, 2.0)]


def test_indices_are_monotonic_across_feeds():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    a = p.feed(_packet(10) + _packet(20))
    b = p.feed(_packet(30))
    assert a == [(1, 10.0), (2, 20.0)]
    assert b == [(3, 30.0)]
    assert p.index == 3


def test_packet_split_across_two_feeds():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    pkt = _packet(1234)
    assert p.feed(pkt[:3]) == []  # partial — nothing yet
    assert p.feed(pkt[3:]) == [(1, 1234.0)]


def test_marker_split_across_two_feeds():
    p = PacketParser(ticks_per_us=1)
    assert p.feed(MARKER[:4]) == []
    assert not p.synced
    out = p.feed(MARKER[4:] + _packet(7))
    assert p.synced
    assert out == [(1, 7.0)]


def test_resync_after_corruption():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    # One valid packet, then a corrupt byte run, then another valid packet.
    stream = _packet(100) + b"\x00\xbb\xcc" + _packet(200)
    out = p.feed(stream)
    assert (1, 100.0) in out
    assert (2, 200.0) in out
    assert len(out) == 2


def test_reset_clears_state():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER + _packet(5))
    p.reset()
    assert not p.synced
    assert p.index == 0
    # After reset a fresh stream must start from index 1 again.
    assert p.feed(MARKER + _packet(9)) == [(1, 9.0)]


def test_max_uint32_value():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    assert p.feed(_packet(0xFFFFFFFF)) == [(1, float(0xFFFFFFFF))]


# ── End-of-period sentinel (0xEE×6) ──────────────────────────────────────────

EOP = b"\xee\xee\xee\xee\xee\xee"


def test_eop_marker_sets_end_of_period():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    out = p.feed(EOP)
    assert out == []
    assert p.end_of_period


def test_eop_marker_after_data_packets():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    out = p.feed(_packet(10) + _packet(20) + EOP)
    assert out == [(1, 10.0), (2, 20.0)]
    assert p.end_of_period


def test_eop_marker_split_across_feeds():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    p.feed(_packet(5))  # a normal packet first
    # Split the EOP sentinel across two reads
    assert not p.end_of_period
    p.feed(EOP[:3])
    assert not p.end_of_period  # incomplete marker — not triggered yet
    p.feed(EOP[3:])
    assert p.end_of_period


def test_eop_clear_end_of_period():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    p.feed(EOP)
    assert p.end_of_period
    p.clear_end_of_period()
    assert not p.end_of_period


def test_reset_clears_end_of_period():
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    p.feed(EOP)
    assert p.end_of_period
    p.reset()
    assert not p.end_of_period
    assert not p.synced


def test_eop_does_not_consume_following_data():
    """Any bytes after the EOP marker stay in the buffer for the next feed."""
    p = PacketParser(ticks_per_us=1)
    p.feed(MARKER)
    # Packet after the sentinel must not be decoded in the same pass.
    out = p.feed(EOP + _packet(99))
    assert p.end_of_period
    # No data packets should be decoded from the same pass (parsing stops at EOP).
    # The residual bytes stay in the buffer for a potential subsequent feed.
    assert out == []
