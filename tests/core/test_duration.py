"""Tests for core/duration.py — no Qt required."""

from gmcounter.core.duration import accumulate_and_trim


def test_empty_batch():
    kept, accum, reached = accumulate_and_trim([], 0.0, 1_000_000.0)
    assert kept == []
    assert accum == 0.0
    assert reached is False


def test_target_zero_keeps_all():
    points = [(0, 500.0), (1, 300.0), (2, 200.0)]
    kept, accum, reached = accumulate_and_trim(points, 0.0, 0.0)
    assert kept == points
    assert reached is False
    assert accum == 1000.0


def test_target_zero_accumulates():
    _, accum1, _ = accumulate_and_trim([(0, 400.0)], 100.0, 0.0)
    assert accum1 == 500.0
    _, accum2, _ = accumulate_and_trim([(1, 200.0)], accum1, 0.0)
    assert accum2 == 700.0


def test_all_points_under_target():
    points = [(0, 100.0), (1, 200.0), (2, 300.0)]
    kept, accum, reached = accumulate_and_trim(points, 0.0, 1_000_000.0)
    assert kept == points
    assert accum == 600.0
    assert reached is False


def test_exact_boundary_included():
    # Last point lands exactly on the target
    points = [(0, 500.0), (1, 500.0)]
    kept, accum, reached = accumulate_and_trim(points, 0.0, 1000.0)
    assert len(kept) == 2
    assert accum == 1000.0
    assert reached is False


def test_single_crossing_trim():
    points = [(0, 500.0), (1, 600.0), (2, 300.0)]
    kept, accum, reached = accumulate_and_trim(points, 0.0, 1000.0)
    assert len(kept) == 1
    assert kept[0] == (0, 500.0)
    assert accum == 1100.0
    assert reached is True


def test_first_point_crosses():
    points = [(0, 2000.0), (1, 100.0)]
    kept, accum, reached = accumulate_and_trim(points, 0.0, 1000.0)
    assert kept == []
    assert reached is True


def test_high_rate_overshoot_in_one_batch():
    points = [(i, 100.0) for i in range(100)]
    kept, accum, reached = accumulate_and_trim(points, 0.0, 550.0)
    assert len(kept) == 5
    assert accum == 600.0
    assert reached is True


def test_multi_batch_accumulation_continuity():
    # Accumulator carries over between calls
    points1 = [(0, 400.0), (1, 400.0)]
    kept1, accum1, reached1 = accumulate_and_trim(points1, 0.0, 1000.0)
    assert len(kept1) == 2
    assert accum1 == 800.0
    assert reached1 is False

    points2 = [(2, 100.0), (3, 200.0)]
    kept2, accum2, reached2 = accumulate_and_trim(points2, accum1, 1000.0)
    assert len(kept2) == 1
    assert kept2[0] == (2, 100.0)
    assert reached2 is True
