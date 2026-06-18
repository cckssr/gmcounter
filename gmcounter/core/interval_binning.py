# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
#
# MCS-style interval binning: one continuous acquisition sliced into
# R contiguous fixed-width intervals.
"""MCS-style interval binning for continuous acquisitions.

:class:`IntervalBinner` slices one continuous acquisition into *R*
equal-width device-time intervals.  It is a reusable, dependency-free
building block; the UI layer uses it in :class:`~gmcounter.ui.tabs.interval_repeat_tab.IntervalRepeatTab`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List


@dataclass
class IntervalBins:
    """Snapshot of interval-binner state."""

    width_us: float
    repeats: int
    counts: List[int]  # len == repeats; true events per bin (bin 0 seeded +1)
    deltas: List[List[float]]  # per-bin deltas (terminating-event assignment)
    cum_us: float  # device-time of last processed event


class IntervalBinner:
    """Slice a continuous acquisition into *repeats* equal-width bins.

    Convention ("+1"): the first detected pulse defines t=0 and is counted
    as event #1 (bin 0 seeded with +1 on the first :meth:`feed` call).
    Each subsequent delta advances ``cum_us``; the terminating event is
    assigned to ``floor(cum_us / width_us)``.  Events landing in bin
    ``>= repeats`` are silently discarded (past window).
    ``total_count() == N_deltas + 1``.
    """

    def __init__(self, width_us: float, repeats: int) -> None:
        self.width_us = float(width_us)
        self.repeats = int(repeats)
        self._counts: List[int] = [0] * self.repeats
        self._deltas: List[List[float]] = [[] for _ in range(self.repeats)]
        self._cum_us: float = 0.0
        self._first_feed_done: bool = False

    def feed(self, points: list) -> List[int]:
        """Process a batch of (index, value_us) points.

        Seeds event #1 into bin 0 on the very first call, then advances
        the device-time accumulator for each delta and assigns the
        terminating event to the appropriate bin.

        Returns the list of bin indices touched this batch (for incremental
        plot refresh — caller only needs to redraw those bars).
        """
        touched: List[int] = []

        if not self._first_feed_done and points:
            self._first_feed_done = True
            self._counts[0] += 1  # seed event #1 at t=0 into bin 0
            if 0 not in touched:
                touched.append(0)

        for _, value in points:
            self._cum_us += value
            bin_idx = int(math.floor(self._cum_us / self.width_us))
            if bin_idx < self.repeats:
                self._counts[bin_idx] += 1
                self._deltas[bin_idx].append(float(value))
                if bin_idx not in touched:
                    touched.append(bin_idx)

        return touched

    def total_count(self) -> int:
        """True event count == N_deltas + 1 (the +1 seed in bin 0)."""
        return sum(self._counts)

    @property
    def bins(self) -> IntervalBins:
        """Return a snapshot of the current binner state."""
        return IntervalBins(
            width_us=self.width_us,
            repeats=self.repeats,
            counts=list(self._counts),
            deltas=[list(d) for d in self._deltas],
            cum_us=self._cum_us,
        )
