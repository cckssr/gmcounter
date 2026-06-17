# Layer: infrastructure — Qt-free binary packet parser for the GM stream.
#
# Pure logic so it is unit-testable without PySide6 or hardware. The acquisition
# thread (qt_threads.py) owns one of these and feeds it raw serial chunks.

from typing import List, Tuple


class PacketParser:
    """Incremental decoder for the GM counter binary protocol.

    Wire format (little-endian):
        start marker      : 0xFF × 6   (everything before it is discarded)
        data packet       : 0xAA [b0 b1 b2 b3] 0x55   — b0..b3 = inter-event
                            delta in firmware timer ticks
        end-of-period     : 0xEE × 6   (finite-time measurement complete;
                            firmware sends this just before stopping the stream)

    ``feed()`` appends a chunk and returns every newly completed point as
    ``(index, value_us)`` where ``value_us = ticks / ticks_per_us``.  Partial
    packets and a start marker split across two chunks are carried over.
    The whole thing is a single O(n) pass — no per-packet reslicing.

    After ``feed()`` check ``end_of_period`` to see whether the firmware has
    signalled that the counting period is over.  Call ``clear_end_of_period()``
    after acting on it.
    """

    START_BYTE = 0xAA
    END_BYTE = 0x55
    PACKET_SIZE = 6
    START_MARKER = b"\xff\xff\xff\xff\xff\xff"
    END_OF_PERIOD_MARKER = b"\xee\xee\xee\xee\xee\xee"

    def __init__(self, ticks_per_us: float = 48.0) -> None:
        self._scale = float(ticks_per_us) or 1.0
        self._buf = bytearray()
        self._index = 0
        self._synced = False  # True once the 0xFF×6 marker has been seen
        self._end_of_period = False  # True when 0xEE×6 sentinel is detected

    @property
    def index(self) -> int:
        return self._index

    @property
    def synced(self) -> bool:
        return self._synced

    @property
    def end_of_period(self) -> bool:
        """True when the firmware end-of-period sentinel (0xEE×6) was detected."""
        return self._end_of_period

    def clear_end_of_period(self) -> None:
        """Reset end-of-period flag after the caller has acted on it."""
        self._end_of_period = False

    def reset(self) -> None:
        """Clear buffer, index, sync and end-of-period state (between measurements)."""
        self._buf.clear()
        self._index = 0
        self._synced = False
        self._end_of_period = False

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
        eop = self.END_OF_PERIOD_MARKER
        eop_len = len(eop)
        i = 0
        n = len(buf)
        while n - i >= self.PACKET_SIZE:
            # Check for end-of-period sentinel before attempting data framing.
            if buf[i : i + eop_len] == eop:
                self._end_of_period = True
                i += eop_len
                n = len(buf)  # update length after consuming marker
                break  # stop processing; let the caller handle completion
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
