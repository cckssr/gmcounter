"""IntervalRepeatTab exports: every file has the shared raw format and its own duration."""

from __future__ import annotations

from gmcounter.core.export import RAW_COLUMNS
from gmcounter.core.models import Frame


def _feed(tab, values_us):
    tab.on_reset()
    tab.on_frames(
        [Frame(index=i, value=v, timestamp=f"t{i}") for i, v in enumerate(values_us)]
    )


def test_interval_files_use_the_raw_format_with_timestamps(window):
    tab = window.tabs["interval_repeat"]
    tab.ui.spinWidth.setValue(1.0)
    tab.ui.spinRepeats.setValue(2)
    _feed(tab, [300_000.0, 400_000.0, 600_000.0])  # events at 0.3, 0.7 s and 1.3 s

    first, second = tab.interval_exports
    assert first.columns == list(RAW_COLUMNS)
    assert [row[:3] for row in first.rows] == [
        ["0", "300000.0", "t0"],
        ["1", "400000.0", "t1"],
    ]
    assert [row[:3] for row in second.rows] == [["2", "600000.0", "t2"]]


def test_each_interval_file_states_the_device_time_it_covers(window):
    tab = window.tabs["interval_repeat"]
    tab.ui.spinWidth.setValue(1.0)
    tab.ui.spinRepeats.setValue(2)
    _feed(tab, [300_000.0, 400_000.0, 600_000.0])  # the run ends at 1.3 s

    first, second = tab.interval_exports
    assert {row[3] for row in first.rows} == {"1.000"}  # a whole interval
    assert {row[3] for row in second.rows} == {"0.300"}  # only what was measured of it


def test_the_summary_has_a_duration_per_interval(window):
    tab = window.tabs["interval_repeat"]
    tab.ui.spinWidth.setValue(1.0)
    tab.ui.spinRepeats.setValue(2)
    _feed(tab, [300_000.0, 400_000.0, 600_000.0])

    summary = tab.summary_export()
    assert summary.columns[-1] == "Duration (s)"
    assert [row[-1] for row in summary.rows] == ["1.000", "0.300"]
