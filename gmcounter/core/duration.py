# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
#
# Delta-based duration trimming for device-time-gated measurements.
# The running sum of inter-event deltas is the authoritative elapsed time.

from __future__ import annotations


def accumulate_and_trim(
    points: list,
    accum_us: float,
    target_us: float,
) -> tuple:
    """Trim a batch of (index, value_us) points to stay within target_us.

    Returns (kept_points, new_accum_us, reached).

    kept_points   — points whose cumulative arrival time <= target_us.
    new_accum_us  — updated accumulator (may exceed target_us on crossing).
    reached       — True if the target was crossed; caller should stop.

    target_us == 0 means infinite mode: all points kept, reached always False.
    """
    if target_us == 0:
        total = accum_us + sum(v for _, v in points)
        return list(points), total, False

    kept = []
    for point in points:
        _, value = point
        accum_us += value
        if accum_us <= target_us:
            kept.append(point)
        else:
            return kept, accum_us, True

    return kept, accum_us, False
