"""GeneralPlot: thin cheap curve, and only real mouse interaction disables the auto modes."""

from __future__ import annotations

import pytest
from gmcounter.ui.widgets.plot import GeneralPlot

from .test_gm_timing_tab import _frames


def _points(count: int) -> list[tuple[float, float]]:
    return [(float(i), float(i % 7)) for i in range(count)]


@pytest.fixture
def plot(qtbot):
    widget = GeneralPlot()
    qtbot.addWidget(widget)
    widget.resize(400, 300)
    widget.show()
    return widget


def test_the_curve_uses_a_thin_pen_without_symbols(plot):
    plot.update_plot_data(_points(600))
    pen = plot._plot_curve.opts["pen"]
    assert pen.width() == 1
    assert plot._plot_curve.opts.get("symbol") is None


def test_the_line_width_comes_from_the_config(window):
    timing = window.tabs["gm_timing"]
    assert timing.ui.timePlot.config.pen_width == window.config.get("plot.line_width")


def test_programmatic_range_changes_keep_auto_scroll(qtbot, plot):
    interactions = []
    plot.user_interaction_detected.connect(lambda: interactions.append(1))
    plot.set_auto_scroll(True, 100)
    for start in range(0, 600, 100):
        plot.update_plot_data(_points(start + 100))
        qtbot.wait(30)  # pyqtgraph applies its range updates on the next paint
    assert plot._auto_scroll_enabled
    assert interactions == []


def test_the_first_data_update_keeps_the_auto_scroll_checkbox(qtbot, window):
    timing = window.tabs["gm_timing"]
    window.ui.tabWidget.setCurrentWidget(timing)
    assert timing.ui.checkAutoScroll.isChecked()
    timing.on_frames(_frames(50))
    timing._process_queue()
    qtbot.wait(50)
    timing.on_frames(_frames(50, start=50))
    timing._process_queue()
    qtbot.wait(50)
    assert timing.ui.checkAutoScroll.isChecked()


def test_a_manual_pan_or_zoom_disables_auto_scroll(plot):
    interactions = []
    plot.user_interaction_detected.connect(lambda: interactions.append(1))
    plot.set_auto_scroll(True, 100)
    plot.update_plot_data(_points(300))
    # the signal the viewbox emits from its mouse drag / wheel / zoom-box handlers
    plot.getViewBox().sigRangeChangedManually.emit([True, True])
    assert not plot._auto_scroll_enabled and not plot._auto_range_enabled
    assert interactions == [1]


# ---------------------------------------------------------------- SI axes


def test_an_si_axis_picks_the_prefix_from_the_visible_range(qtbot, plot):
    """Data stays in µs; the axis reads µs, ms or s, and keeps its unit after a relabel."""
    plot.reconfigure("ylabel", "Zeit")
    plot.set_axis_si("left", "s", 1e-6)
    plot.reconfigure("ylabel", "Zeit")  # relabelling must not drop the unit
    axis = plot.getAxis("left")
    for rng, prefixed in (((0, 800), "µs"), ((0, 250_000), "ms"), ((0, 20e6), "s")):
        plot.getViewBox().setRange(yRange=rng, padding=0)
        assert f"Zeit ({prefixed})" in axis.labelString()


# ---------------------------------------------------------------- summary plot


def test_the_summary_shows_symbols_and_error_bars(plot):
    plot.set_summary_points([(3.0, 10.0), (2.0, 30.0)], errors=[1.0, 2.0])
    curve = plot._summary_curve
    assert curve.opts["symbol"] == "o"
    xs, ys = curve.getData()
    assert list(xs) == [2.0, 3.0]  # sorted by x, errors follow their points
    assert list(ys) == [30.0, 10.0]
    assert list(plot._summary_errors.opts["top"]) == [2.0, 1.0]


def test_the_log_summary_drops_non_positive_points_and_switches_the_axes(plot):
    plot.set_summary_points([(2.0, 100.0), (4.0, 25.0), (5.0, 0.0)], log=True)
    xs, ys = plot._summary_curve.getData()
    assert list(xs) == pytest.approx([0.30103, 0.60206], abs=1e-4)  # log10(2), log10(4)
    assert plot.getAxis("left").logMode and plot.getAxis("bottom").logMode

    plot.set_summary_points([(2.0, 100.0)], log=False)
    assert not plot.getAxis("left").logMode


def test_clearing_removes_the_summary(plot):
    plot.set_summary_points([(1.0, 1.0)], errors=[0.1])
    plot.clear_measurement_data()
    assert plot._summary_curve is None and plot._summary_errors is None
