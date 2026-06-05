"""Tests for core/interval_binning.py — no Qt required."""

from gmcounter.core.interval_binning import IntervalBinner, IntervalBins


def _feed(binner, values):
    """Helper: feed a list of µs values (index assigned automatically)."""
    points = list(enumerate(values))
    return binner.feed(points)


def test_plus_one_seeding():
    # First feed seeds event #1 into bin 0 even before any delta
    b = IntervalBinner(width_us=1_000_000.0, repeats=5)
    _feed(b, [])
    assert b.bins.counts[0] == 0  # no points → no seeding yet

    b2 = IntervalBinner(width_us=1_000_000.0, repeats=5)
    _feed(b2, [100_000.0])
    assert b2.bins.counts[0] >= 1  # seeded +1 on first non-empty feed


def test_total_count_equals_n_deltas_plus_1():
    b = IntervalBinner(width_us=1_000_000.0, repeats=3)
    _feed(b, [100_000.0, 200_000.0, 300_000.0])
    # 3 deltas + 1 seed = 4
    assert b.total_count() == 4


def test_worked_example_w1s_r3():
    """Worked example from the plan: W=1 s, 11 deltas → bin 0 count 12, 1070 ms → bin 1."""
    W = 1_000_000.0  # 1 s in µs
    b = IntervalBinner(width_us=W, repeats=3)

    # 10 deltas of 980_000 µs each → all terminate at < 1s so bin 0 (after seed)
    # cum_us after each: 980_000, 1_960_000 (crosses into bin 1), …
    # Actually for the plan's example: W=1s, 11 deltas where
    # first 10 are 90_000 µs (~90ms each) → cum=900_000 (all in bin 0)
    # then delta 1_070_000 µs → cum=1_970_000 → bin 1
    # Let's use W=1s, 10 deltas of 90ms + 1 delta of 1070ms
    _feed(b, [90_000.0] * 10)
    # cum_us = 900_000 µs — all 10 deltas in bin 0
    # bin 0 = 1 (seed) + 10 (deltas in bin 0) = 11
    assert b.bins.counts[0] == 11

    _feed(b, [1_070_000.0])
    # cum_us = 1_970_000 µs → bin 1
    assert b.bins.counts[1] == 1
    assert b.total_count() == 12  # 11 delta + 1 seed


def test_straddling_boundary():
    # Delta that lands exactly on a boundary goes to the upper bin
    W = 1_000_000.0
    b = IntervalBinner(width_us=W, repeats=3)
    _feed(b, [1_000_000.0])  # cum=1_000_000 → floor(1_000_000/1_000_000) = 1 → bin 1
    assert b.bins.counts[0] == 1  # only seed
    assert b.bins.counts[1] == 1


def test_last_bin_fill():
    W = 500_000.0  # 0.5 s
    b = IntervalBinner(width_us=W, repeats=2)
    _feed(b, [400_000.0])  # cum=400_000 → bin 0 (seed also bin 0)
    _feed(b, [200_000.0])  # cum=600_000 → bin 1
    assert b.bins.counts[0] == 2  # seed + first delta
    assert b.bins.counts[1] == 1


def test_events_past_window_discarded():
    W = 500_000.0
    b = IntervalBinner(width_us=W, repeats=2)
    _feed(b, [1_500_000.0])  # cum=1_500_000 → bin 3 which is >= repeats=2 → discarded
    assert sum(b.bins.counts) == 1  # only seed


def test_per_bin_delta_partition():
    W = 1_000_000.0
    b = IntervalBinner(width_us=W, repeats=2)
    _feed(b, [300_000.0, 400_000.0])  # both in bin 0 (cum=300k, 700k)
    _feed(b, [400_000.0])  # cum=1_100_000 → bin 1
    bins = b.bins
    assert len(bins.deltas[0]) == 2
    assert len(bins.deltas[1]) == 1
    assert bins.deltas[0] == [300_000.0, 400_000.0]
    assert bins.deltas[1] == [400_000.0]


def test_bins_snapshot_is_copy():
    b = IntervalBinner(width_us=1_000_000.0, repeats=2)
    _feed(b, [100_000.0])
    snap1 = b.bins
    _feed(b, [100_000.0])
    snap2 = b.bins
    assert snap1.counts[0] != snap2.counts[0] or snap1.cum_us != snap2.cum_us
