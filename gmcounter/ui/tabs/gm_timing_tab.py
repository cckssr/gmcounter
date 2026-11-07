# Layer: ui/tabs — GMTimingTab: GM inter-event timing experiment.
# The first experiment; its form carries three inner views (Zeitverlauf / Histogramm / Liste).

from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, List, Optional, Tuple

import numpy as np
from PySide6.QtCore import QTimer, Signal  # pylint: disable=no-name-in-module
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from gmcounter.pyqt.ui_timing_tab import Ui_TimingTab

from ...core.export import TabExport, build_gm_tab_export
from ...core.models import Frame, MeasurementPoint, MeasurementSession
from ...core.utils import calculate_statistics
from ..i18n import apply_strings
from .base import PlotTabBase
from .registry import TabRegistry

if TYPE_CHECKING:
    from ..context import AppContext

_log = logging.getLogger(__name__)

QUEUE_SIZE = 10_000
HISTOGRAM_WINDOW = 10_000  # newest points used for the histogram
HIGH_SPEED_REFRESH_MS = 2000
READOUT_COUNT_EVERY_N_TICKS = 5  # the count readout is refreshed every Nth GUI tick
TABLE_MAX_EVENTS = 5000  # the table stops growing beyond this many events


@TabRegistry.register
class GMTimingTab(PlotTabBase):
    """GM inter-event timing experiment.

    Inner views (``tabViews``): Zeitverlauf (line plot), Histogramm, Liste (data table).

    High-speed mode activates when the data rate exceeds the batch threshold: line plot and
    table stop updating, only the histogram and the count / rate readout refresh every 2 s,
    and the inner view switches to the histogram (suppressed during sweep / interval
    sessions, see :meth:`set_high_speed_autoswitch`).

    Every frame is stored in ``_data_points`` (the export); only the hand-over to the GUI
    queue is skipped when the queue is full or the high-speed mode is active. No per-frame
    widget work happens anywhere.
    """

    tab_id = "gm_timing"
    form_name = "timing_tab"
    order = 0
    session_kind = "single"
    provides_timing = True
    required_modules: set[str] = set()

    high_speed_changed = Signal(bool)
    readout_changed = Signal(int, float)  # (event count, rate in Hz)

    def __init__(self, context: "AppContext", parent: Optional[QWidget] = None) -> None:
        super().__init__(context, parent)
        self.ui = Ui_TimingTab()
        self.ui.setupUi(self)
        apply_strings(self, self.config.section("ui").get(self.form_name, {}))

        data_cfg = self.config.section("data_controller")
        hs_cfg = data_cfg.get("high_speed_mode", {})
        self._hs_threshold: int = hs_cfg.get("batch_threshold", 50)
        self._hs_history: int = hs_cfg.get("batch_history", 5)
        self._max_history: int = data_cfg.get("max_history_size", 2000)
        self._gui_interval_ms: int = max(
            500, self.config.get("timers.gui_update_interval", 500)
        )

        # Raw data storage (unbounded — for CSV export); GUI-limited copy for the plot
        self._data_points: List[Tuple[int, float, str]] = []
        self._gui_points: List[Tuple[int, float, str]] = []

        # Queue from the acquisition path to the GUI timer
        self._queue: queue.Queue = queue.Queue(maxsize=QUEUE_SIZE)
        self._queue_lock = threading.Lock()
        self._overflow_warned = False

        # High-speed mode
        self._high_speed = False
        self._batch_history: List[Tuple[float, int]] = []
        self._hist_timer: Optional[QTimer] = None
        self._hs_autoswitch: bool = True  # False during sweep / interval sessions
        self._gui_timer: Optional[QTimer] = None
        self._tick = 0  # GUI ticks since the count readout was refreshed
        self._shown_count = 0
        self._hist_tick = 0  # GUI ticks since the histogram was redrawn

        # Running device-time accumulator (sum of all received deltas in µs)
        self._cum_us: float = 0.0

        self._plot = self.ui.timePlot
        self._histogram = self.ui.histogramPlot
        self._table_model: Optional[QStandardItemModel] = None

        # Histogram controls
        self._hist_bin_size_us: int = 1_000
        self._hist_cutoff_us: int = 50_000
        self._user_adjusted_hist: bool = False
        self._updating_sliders: bool = False

        # Measurement session tracking for export
        self._session_start: Optional[datetime] = None
        self._session_end: Optional[datetime] = None
        self._rad_sample: str = ""
        self._group: str = ""
        self._subterm: str = ""

    # ------------------------------------------------------------------
    # Setup

    def build(self) -> None:
        """Label the promoted plots, set up table and controls, start the GUI timer."""
        ui = self.ui
        plot_cfg = self._plot.config
        plot_cfg.max_plot_points = self.config.get("plot.max_points", 1000)
        self._plot.reconfigure("xlabel", self.text("plot_x_label"))
        self._plot.reconfigure("ylabel", self.text("plot_y_label"))
        self._histogram.reconfigure("xlabel", self.text("histogram_x_label"))
        self._histogram.reconfigure("ylabel", self.text("histogram_y_label"))

        headers = self.config.get(f"ui.{self.form_name}.table_events_headers", [])
        self._table_model = QStandardItemModel(0, len(headers), ui.tableEvents)
        self._table_model.setHorizontalHeaderLabels(headers)
        ui.tableEvents.setModel(self._table_model)

        self._setup_hist_controls()
        ui.checkAutoScroll.toggled.connect(self._on_auto_scroll_toggled)
        ui.spinPlotPoints.valueChanged.connect(self._on_plot_points_changed)
        ui.buttonAutoRange.clicked.connect(self._on_auto_range)
        self._plot.user_interaction_detected.connect(self._on_plot_user_interaction)
        if ui.checkAutoScroll.isChecked():
            self._on_auto_scroll_toggled(True)

        ctrl = self.context.ctrl
        if ctrl is not None:
            ctrl.statistics_updated.connect(self.on_statistics)

        self._gui_timer = QTimer(self)
        self._gui_timer.timeout.connect(self._process_queue)
        self._gui_timer.start(self._gui_interval_ms)

    def _setup_hist_controls(self) -> None:
        """µs ranges for dead-time analysis; sliders drive the read-only spin boxes."""
        ui = self.ui
        # Bin size: 10 µs … 50 000 µs (50 ms), step 10 µs
        ui.sliderBinSize.setRange(10, 50_000)
        ui.sliderBinSize.setSingleStep(10)
        ui.sliderBinSize.setPageStep(100)
        ui.spinBinSize.setRange(10, 50_000)
        # Cut-off: 1 000 µs (1 ms) … 10 000 000 µs (10 s), step 1 000 µs
        ui.sliderCutoff.setRange(1_000, 10_000_000)
        ui.sliderCutoff.setSingleStep(1_000)
        ui.sliderCutoff.setPageStep(10_000)
        ui.spinCutoff.setRange(1_000, 10_000_000)

        ui.sliderBinSize.valueChanged.connect(ui.spinBinSize.setValue)
        ui.sliderCutoff.valueChanged.connect(ui.spinCutoff.setValue)
        ui.sliderBinSize.valueChanged.connect(self._on_bin_size_changed)
        ui.sliderCutoff.valueChanged.connect(self._on_cutoff_changed)
        self._set_sliders(self._hist_bin_size_us, self._hist_cutoff_us)

    # ------------------------------------------------------------------
    # Plot / histogram control handlers

    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        if checked:
            self._plot.set_auto_scroll(True, self.ui.spinPlotPoints.value())
        else:
            self._plot.set_auto_scroll(False)

    def _on_plot_points_changed(self, value: int) -> None:
        if self.ui.checkAutoScroll.isChecked():
            self._plot.set_auto_scroll(True, value)

    def _on_auto_range(self) -> None:
        self._plot.enable_auto_range(True)
        self.ui.checkAutoScroll.setChecked(True)

    def _on_plot_user_interaction(self) -> None:
        if self.ui.checkAutoScroll.isChecked():
            self.ui.checkAutoScroll.setChecked(False)

    def _on_bin_size_changed(self, value: int) -> None:
        if self._updating_sliders:
            return
        self._user_adjusted_hist = True
        self._hist_bin_size_us = value
        self._refresh_histogram()

    def _on_cutoff_changed(self, value: int) -> None:
        if self._updating_sliders:
            return
        self._user_adjusted_hist = True
        self._hist_cutoff_us = value
        self._refresh_histogram()

    def on_statistics(self, stats: dict) -> None:
        """Show count / min / max / mean / std of the acquired intervals."""
        if stats.get("count", 0) > 1:
            ui = self.ui
            ui.valueStatCount.setText(f"{stats.get('count', 0):.0f}")
            ui.valueStatMin.setText(f"{stats.get('min', 0):.0f}")
            ui.valueStatMax.setText(f"{stats.get('max', 0):.0f}")
            ui.valueStatMean.setText(f"{stats.get('avg', 0):.0f}")
            ui.valueStatStd.setText(f"{stats.get('stdev', 0):.0f}")

    def _refresh_histogram(self) -> None:
        values = [pt[1] for pt in self._data_points[-HISTOGRAM_WINDOW:]]
        if len(values) < 2:
            return
        self._histogram.update_histogram_us(
            values, self._hist_bin_size_us, self._hist_cutoff_us
        )

    def _auto_hist_params(self, values: list) -> tuple:
        """Derive bin_size_us and cutoff_us from the data distribution.

        Uses the 5th-percentile as a proxy for the dead-time floor (so the
        bins are narrow enough to resolve the region just beyond dead-time) and
        the 95th-percentile as the right cut-off (shows the bulk of the
        distribution while hiding extreme outliers).
        """
        arr = np.array(values, dtype=np.float64)
        if len(arr) < 2:
            return 1_000, 50_000

        floor_us = max(10.0, float(np.percentile(arr, 5)))
        p95_us = float(np.percentile(arr, 95))

        # ~5 bins across the dead-time region → good peak resolution
        bin_size = max(10, int(round(floor_us / 5.0 / 10) * 10))
        # Round cutoff to nearest millisecond
        cutoff = max(1_000, int(round(p95_us / 1_000) * 1_000))
        return min(bin_size, 50_000), min(cutoff, 10_000_000)

    def _set_sliders(self, bin_size_us: int, cutoff_us: int) -> None:
        """Update sliders programmatically without triggering the user-adjusted flag."""
        self._hist_bin_size_us = bin_size_us
        self._hist_cutoff_us = cutoff_us
        self._updating_sliders = True
        try:
            self.ui.sliderBinSize.setValue(bin_size_us)
            self.ui.sliderCutoff.setValue(cutoff_us)
        finally:
            self._updating_sliders = False

    def _update_histogram(self) -> None:
        """Redraw the histogram from the stored data (auto-parameters unless the user chose)."""
        if len(self._data_points) <= 1:
            return
        values = [pt[1] for pt in self._data_points[-HISTOGRAM_WINDOW:]]
        if not self._user_adjusted_hist:
            bin_size, cutoff = self._auto_hist_params(values)
            self._set_sliders(bin_size, cutoff)
        self._histogram.update_histogram_us(
            values, self._hist_bin_size_us, self._hist_cutoff_us
        )

    # ------------------------------------------------------------------
    # Session API used by the session controller

    def set_measurement_metadata(
        self, rad_sample: str, group: str, subterm: str
    ) -> None:
        self._rad_sample = rad_sample
        self._group = group
        self._subterm = subterm

    def set_high_speed_autoswitch(self, enabled: bool) -> None:
        """Enable or disable the automatic switch to the Histogramm view on high-speed.

        Disabled for the duration of a sweep / interval session so the experiment tab stays
        visible while data accumulates. Data acquisition and histogram updates are unaffected.
        """
        self._hs_autoswitch = enabled

    @property
    def high_speed_active(self) -> bool:
        return self._high_speed

    # ------------------------------------------------------------------
    # PlotTabBase lifecycle

    def on_frame(self, frame: Frame) -> None:
        self.on_frames([frame])

    def on_frames(self, frames: List[Frame]) -> None:
        """Store a whole batch; hand it to the GUI queue unless high-speed is active.

        Every frame is appended to the export data. Only the queue put may be skipped: the
        queue is not used at all in high-speed mode, and a full queue drops the surplus
        points for the plot (never for the export).
        """
        if not frames:
            return
        rows = [(f.index, f.value, f.timestamp) for f in frames]
        self._data_points.extend(rows)
        self._cum_us += sum(row[1] for row in rows)
        if self._high_speed:
            return
        with self._queue_lock:
            q = self._queue
            for row in rows:
                try:
                    q.put_nowait(row)
                except queue.Full:
                    if not self._overflow_warned:
                        _log.warning("Data queue overflow — GUI cannot keep up")
                        self._overflow_warned = True
                    break

    def on_reset(self) -> None:
        self._deactivate_high_speed()
        self._batch_history.clear()
        self._data_points.clear()
        self._gui_points.clear()
        self._cum_us = 0.0
        with self._queue_lock:
            self._queue = queue.Queue(maxsize=QUEUE_SIZE)
        self._overflow_warned = False
        self._session_start = datetime.now()
        self._session_end = None
        self._tick = 0
        self._shown_count = 0
        self._hist_tick = 0

        # Return histogram controls to auto mode for the new measurement
        self._user_adjusted_hist = False
        self._set_sliders(1_000, 50_000)

        self._plot.clear_measurement_data()
        self._histogram.clear_measurement_data()
        self.readout_changed.emit(0, 0.0)
        if self._table_model:
            self._table_model.removeRows(0, self._table_model.rowCount())

        if self._gui_timer and not self._gui_timer.isActive():
            self._gui_timer.start(self._gui_interval_ms)

    def on_measurement_started(self) -> None:
        self._session_start = datetime.now()

    def on_measurement_stopped(self) -> None:
        self._session_end = datetime.now()
        if self._high_speed:
            self._refresh_high_speed_view()
            if self._hist_timer is not None:
                self._hist_timer.stop()
        else:
            self._process_queue(final=True)
        if self._gui_timer:
            self._gui_timer.stop()

    # ------------------------------------------------------------------
    # Export (§7)

    def export(self) -> Optional[TabExport]:
        if not self._data_points:
            return None
        session = MeasurementSession(
            points=[
                MeasurementPoint(idx, val, ts) for idx, val, ts in self._data_points
            ],
            start_time=self._session_start,
            end_time=self._session_end or datetime.now(),
            radioactive_sample=self._rad_sample,
            subterm=self._subterm,
            group=self._group,
        )
        return build_gm_tab_export(
            session,
            tk_designation=self.config.get("save.tk_designation", "TK00"),
        )

    def get_statistics(self) -> dict:
        if not self._data_points:
            return {}
        values = [pt[1] for pt in self._data_points]
        s = calculate_statistics(values)
        return {
            "count": self._event_count(),
            "min": s["min"],
            "max": s["max"],
            "avg": s["mean"],
            "stdev": s["std"],
        }

    # ------------------------------------------------------------------
    # Internal — GUI update loop

    def _event_count(self) -> int:
        """Events seen so far (+1: the event at t=0 before the first delta)."""
        return len(self._data_points) + 1 if self._data_points else 0

    def _rate_hz(self) -> float:
        if self._cum_us <= 0 or not self._data_points:
            return 0.0
        return round(self._event_count() / (self._cum_us / 1e6), 1)

    def _publish_readout(self, count: Optional[int] = None) -> None:
        self.readout_changed.emit(
            self._event_count() if count is None else count, self._rate_hz()
        )

    def _process_queue(self, final: bool = False) -> None:
        """GUI tick: drain the queue, refresh plot / table / readout, detect high-speed.

        ``final`` flushes what is left after the measurement stopped (no high-speed
        detection, readout refreshed regardless of the throttle).
        """
        if self._high_speed:
            return
        with self._queue_lock:
            new_points: List[Tuple[int, float, str]] = []
            while True:
                try:
                    new_points.append(self._queue.get_nowait())
                except queue.Empty:
                    break

        if not new_points:
            if final:
                self._publish_readout()
            return

        self._gui_points.extend(new_points)
        if len(self._gui_points) > self._max_history:
            del self._gui_points[: len(self._gui_points) - self._max_history]

        self._update_plot_and_display(final)
        if len(self._data_points) < TABLE_MAX_EVENTS:
            self._update_table(new_points)

        if not final:
            self._check_high_speed(len(new_points), time())

    def _update_plot_and_display(self, final: bool) -> None:
        if self._gui_points:
            self._plot.update_plot_data(self._gui_points, deferred=True)

        self._tick += 1
        if final or self._tick >= READOUT_COUNT_EVERY_N_TICKS:
            self._tick = 0
            self._shown_count = self._event_count()
        self._publish_readout(self._shown_count)

        if len(self._data_points) > 1:
            self._hist_tick += 1
            if final or self._hist_tick >= 10:
                self._hist_tick = 0
                self._update_histogram()

    def _update_table(self, points: List[Tuple[int, float, str]]) -> None:
        model = self._table_model
        if model is None:
            return
        for idx, val, ts in points:
            model.appendRow(
                [QStandardItem(str(idx)), QStandardItem(str(val)), QStandardItem(ts)]
            )
        excess = model.rowCount() - self._max_history
        if excess > 0:
            model.removeRows(0, excess)

    def _check_high_speed(self, batch_size: int, now: float) -> None:
        if self._high_speed:
            return
        self._batch_history.append((now, batch_size))
        if len(self._batch_history) > self._hs_history:
            self._batch_history.pop(0)
        if len(self._batch_history) < self._hs_history:
            return
        avg = sum(b[1] for b in self._batch_history) / len(self._batch_history)
        if avg >= self._hs_threshold:
            self._activate_high_speed()

    def _activate_high_speed(self) -> None:
        if self._high_speed:
            return
        self._high_speed = True
        _log.info("HIGH_SPEED_MODE activated")
        self.status_message.emit("warning", self.text("text_high_speed"))
        self.high_speed_changed.emit(True)

        if self._gui_timer:
            self._gui_timer.stop()
        with self._queue_lock:  # the GUI queue is not used any more
            self._queue = queue.Queue(maxsize=QUEUE_SIZE)

        if self._hs_autoswitch:
            self.ui.tabViews.setCurrentWidget(self.ui.pageHistogram)

        if self._hist_timer is None:
            self._hist_timer = QTimer(self)
            self._hist_timer.timeout.connect(self._refresh_high_speed_view)
            self._hist_timer.start(HIGH_SPEED_REFRESH_MS)
        self._refresh_high_speed_view()

    def _deactivate_high_speed(self) -> None:
        if not self._high_speed:
            return
        self._high_speed = False
        if self._hist_timer:
            self._hist_timer.stop()
            self._hist_timer = None
        if self._gui_timer and not self._gui_timer.isActive():
            self._gui_timer.start(self._gui_interval_ms)
        self.high_speed_changed.emit(False)

    def _refresh_high_speed_view(self) -> None:
        """High-speed tick (every 2 s): histogram and count / rate readout only."""
        if not self._high_speed:
            return
        self._update_histogram()
        self._publish_readout()
