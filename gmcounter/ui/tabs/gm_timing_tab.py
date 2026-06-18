# Layer: ui/tabs — GMTimingTab: GM inter-event timing experiment.
"""GM inter-event timing experiment tab; contributes 3 top-level view tabs."""
# The first registered experiment; contributes 3 top-level view tabs.

from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime
from time import time
from typing import Optional, List, Tuple

from PySide6.QtCore import QTimer, Signal  # pylint: disable=no-name-in-module
from PySide6.QtGui import (
    QStandardItem,
    QStandardItemModel,
)  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QTabWidget,
    QTableView,
    QWidget,
    QVBoxLayout,
    QLCDNumber,
)

from .base import PlotTabBase
from .registry import TabRegistry
from ...core.export import TabExport, build_gm_tab_export
from ...core.models import Frame, MeasurementSession, MeasurementPoint
from ...core.utils import calculate_statistics
from ...infrastructure.config import import_config

_log = logging.getLogger(__name__)
CONFIG = import_config()

_DATA_CFG = CONFIG.get("gm_timing", {})
_HS_CFG = _DATA_CFG.get("high_speed_mode", {})
HIGH_SPEED_BATCH_THRESHOLD: int = _HS_CFG.get("batch_threshold", 50)
HIGH_SPEED_BATCH_HISTORY: int = _HS_CFG.get("batch_history", 5)
MAX_HISTORY: int = _DATA_CFG.get("max_history_size", 2000)
GUI_UPDATE_INTERVAL: int = max(
    500, CONFIG.get("timers", {}).get("gui_update_interval", 500)
)


class GMTimingTab(PlotTabBase):
    """GM inter-event timing experiment.

    Contributes 3 top-level view tabs to the shared QTabWidget:
      0 — Zeitverlauf (line plot)
      1 — Histogramm
      2 — Liste (data table)

    High-speed mode activates when the data rate exceeds the batch
    threshold: plot/table updates stop, only histogram updates every 2 s.
    Auto-switch to Histogramm tab happens inside this tab (not MainWindow).
    """

    tab_id = "gm_timing"
    tab_title = "Zeitverlauf"
    required_modules: set[str] = set()

    # Signal — MainWindow switches to Histogramm tab on high-speed activation
    _switch_to_histogram = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Raw data storage (unbounded — for CSV export)
        self._data_points: List[Tuple[int, float, str]] = []
        # GUI-limited copy
        self._gui_points: List[Tuple[int, float, str]] = []

        # Queue from acquisition thread
        self._queue: queue.Queue = queue.Queue(maxsize=10000)
        self._queue_lock = threading.Lock()
        self._overflow_warned = False

        # High-speed mode
        self._high_speed = False
        self._batch_history: List[Tuple[float, int]] = []
        self._hist_timer: Optional[QTimer] = None
        self._hs_autoswitch: bool = True  # set False during sweep sessions

        # GUI update timer
        self._gui_timer: Optional[QTimer] = None

        # Injection slots (set by MainWindow after build())
        self._plot_container: Optional[QWidget] = None
        self._hist_container: Optional[QWidget] = None
        self._table_view: Optional[QTableView] = None
        self._count_lcd: Optional[QLCDNumber] = None
        self._last_count_lcd: Optional[QLCDNumber] = None
        self._rate_lcd: Optional[QLCDNumber] = None
        self._tab_widget_ref: Optional[QTabWidget] = None

        # Running device-time accumulator (sum of all received deltas in µs)
        self._cum_us: float = 0.0

        # Lazily created widgets
        self._plot = None
        self._histogram = None
        self._table_model: Optional[QStandardItemModel] = None

        # Measurement session tracking for export
        self._session_start: Optional[datetime] = None
        self._session_end: Optional[datetime] = None
        self._rad_sample: str = ""
        self._group: str = ""
        self._subterm: str = ""

    # ------------------------------------------------------------------
    # Dependency injection from MainWindow

    def inject_ui_containers(
        self,
        plot_container: QWidget,
        hist_container: QWidget,
        table_view: QTableView,
        count_lcd: Optional[QLCDNumber] = None,
        last_count_lcd: Optional[QLCDNumber] = None,
        rate_lcd: Optional[QLCDNumber] = None,
        tab_widget: Optional[QTabWidget] = None,
    ) -> None:
        """Receive the .ui container widgets before build() is called."""
        self._plot_container = plot_container
        self._hist_container = hist_container
        self._table_view = table_view
        self._count_lcd = count_lcd
        self._last_count_lcd = last_count_lcd
        self._rate_lcd = rate_lcd
        self._tab_widget_ref = tab_widget

    def set_measurement_metadata(
        self, rad_sample: str, group: str, subterm: str
    ) -> None:
        """Store metadata fields embedded in the TabExport on save.

        Args:
            rad_sample: Radioactive sample identifier string.
            group: Measurement group (experiment series).
            subterm: Sub-term / sub-experiment label.
        """
        self._rad_sample = rad_sample
        self._group = group
        self._subterm = subterm

    def set_high_speed_autoswitch(self, enabled: bool) -> None:
        """Enable or disable the automatic tab switch to Histogramm on high-speed.

        MainWindow disables this for the duration of a sweep session so the
        Abstandsgesetz (or voltage) tab stays visible while data accumulates.
        Data acquisition and histogram updates are unaffected.
        """
        self._hs_autoswitch = enabled

    # ------------------------------------------------------------------
    # PlotTabBase lifecycle

    def build(self) -> None:
        """Create plot/histogram/table inside the .ui containers."""
        from ..widgets.plot import GeneralPlot, HistogramWidget, PlotConfig

        if self._plot_container and self._plot is None:
            bg = (
                self._plot_container.palette()
                .color(self._plot_container.backgroundRole())
                .name()
            )
            cfg = PlotConfig(
                xlabel=CONFIG.get("plot", {}).get("x_label", "Index"),
                ylabel=CONFIG.get("plot", {}).get("y_label", "Zeit (µs)"),
                max_plot_points=CONFIG.get("plot", {}).get("max_points", 1000),
                background_color=bg,
            )
            self._plot = GeneralPlot(config=cfg)
            QVBoxLayout(self._plot_container).addWidget(self._plot)

        if self._hist_container and self._histogram is None:
            hist_bg = (
                self._hist_container.palette()
                .color(self._hist_container.backgroundRole())
                .name()
            )
            self._histogram = HistogramWidget(
                xlabel=CONFIG.get("histogram", {}).get("x_label", "Zeit (µs)"),
                ylabel=CONFIG.get("histogram", {}).get("y_label", "Häufigkeit"),
                background=hist_bg,
            )
            QVBoxLayout(self._hist_container).addWidget(self._histogram)

        if self._table_view is not None and self._table_model is None:
            self._table_model = QStandardItemModel(0, 3, self._table_view)
            self._table_model.setHorizontalHeaderLabels(["Index", "Wert (µs)", "Zeit"])
            self._table_view.setModel(self._table_model)

        # GUI update timer
        self._gui_timer = QTimer(self)
        self._gui_timer.timeout.connect(self._process_queue)
        self._gui_timer.start(GUI_UPDATE_INTERVAL)

    def on_frame(self, frame: Frame) -> None:
        """Enqueue incoming data point (called from main thread via Qt signal)."""
        try:
            ts = frame.timestamp
            self._data_points.append((frame.index, frame.value, ts))
            with self._queue_lock:
                self._queue.put_nowait((frame.index, frame.value, ts))
        except queue.Full:
            if not self._overflow_warned:
                _log.warning("Data queue overflow — GUI cannot keep up")
                self._overflow_warned = True

    def on_frames(self, frames: List[Frame]) -> None:
        """Batch entrypoint — append a whole batch under one lock acquisition.

        Overrides PlotTabBase.on_frames so a 10 kHz stream costs one lock cycle
        per GUI-thread delivery instead of one per point.
        """
        if not frames:
            return
        dp = self._data_points
        q = self._queue
        with self._queue_lock:
            for frame in frames:
                row = (frame.index, frame.value, frame.timestamp)
                dp.append(row)
                self._cum_us += (
                    frame.value
                )  # always accumulate for device-time tracking
                try:
                    q.put_nowait(row)
                except queue.Full:
                    if not self._overflow_warned:
                        _log.warning("Data queue overflow — GUI cannot keep up")
                        self._overflow_warned = True
                    break

    def on_reset(self) -> None:
        """Clear all data, reset plots, counters, and high-speed mode."""
        self._deactivate_high_speed()
        self._batch_history.clear()
        self._data_points.clear()
        self._gui_points.clear()
        self._cum_us = 0.0
        with self._queue_lock:
            self._queue = queue.Queue(maxsize=10000)
        self._overflow_warned = False
        self._session_start = datetime.now()
        self._session_end = None

        if self._plot and hasattr(self._plot, "clear_measurement_data"):
            self._plot.clear_measurement_data()
        if self._histogram and hasattr(self._histogram, "clear_measurement_data"):
            self._histogram.clear_measurement_data()
        if self._count_lcd:
            self._count_lcd.display(0)
        if self._rate_lcd:
            self._rate_lcd.display(0)
        if self._table_model:
            while self._table_model.rowCount() > 0:
                self._table_model.removeRow(0)

        if self._gui_timer and not self._gui_timer.isActive():
            self._gui_timer.start(GUI_UPDATE_INTERVAL)

    def on_measurement_started(self) -> None:
        """Record the session start time."""
        self._session_start = datetime.now()

    def on_measurement_stopped(self) -> None:
        """Record the session end time and stop the GUI update timer."""
        self._session_end = datetime.now()
        if self._gui_timer:
            self._gui_timer.stop()

    def contribute_tabs(self, tab_widget: QTabWidget) -> None:
        """Add Zeitverlauf / Histogramm / Liste as top-level tabs.

        The tab pages are already in the .ui (setupUi created them); this
        method ensures they are properly labelled and registered.
        """
        # The existing 3 pages are already added by setupUi.
        # Store the reference for high-speed auto-switch.
        self._tab_widget_ref = tab_widget

    # ------------------------------------------------------------------
    # Export (§7)

    def export(self) -> Optional[TabExport]:
        """Return a TabExport of all recorded inter-event deltas, or None if empty."""
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
            tk_designation=CONFIG.get("save", {}).get("tk_designation", "TK00"),
        )

    def get_statistics(self) -> dict:
        """Return {count, min, max, avg, stdev} computed from all acquired deltas."""
        if not self._data_points:
            return {}
        values = [pt[1] for pt in self._data_points]
        s = calculate_statistics(values)
        true_count = (
            len(self._data_points) + 1
        )  # +1: the event at t=0 before first delta
        return {
            "count": true_count,
            "min": s["min"],
            "max": s["max"],
            "avg": s["mean"],
            "stdev": s["std"],
        }

    def get_csv_data(self) -> List[List[str]]:
        """Legacy helper used by save dialogs."""
        rows = [["Index", "Value (µs)", "Time"]]
        for idx, val, ts in self._data_points:
            rows.append([str(idx), str(val), ts])
        return rows

    # ------------------------------------------------------------------
    # Internal — GUI update loop

    def _process_queue(self) -> None:
        """Drain the inter-thread queue and update plot, table, and LCDs."""
        if self._queue.empty():
            return

        new_points: List[Tuple[int, float, str]] = []
        now = time()

        with self._queue_lock:
            while not self._queue.empty():
                try:
                    new_points.append(self._queue.get_nowait())
                except queue.Empty:
                    break

        if not new_points:
            return

        for pt in new_points:
            self._gui_points.append(pt)
        while len(self._gui_points) > MAX_HISTORY:
            self._gui_points.pop(0)

        last_idx, last_val, last_ts = new_points[-1]

        if not self._high_speed:
            self._update_plot_and_display(last_val)
            if len(self._data_points) < 5000:
                self._update_table(new_points)
            self._update_rate_display(now)
        else:
            if self._count_lcd:
                self._count_lcd.display(last_val)

        # High-speed detection
        self._check_high_speed(len(new_points), now)

    def _update_plot_and_display(self, last_val: float) -> None:
        """Refresh the line plot, event count LCD, and histogram (throttled)."""
        if self._plot and self._gui_points:
            self._plot.update_plot_data(self._gui_points, deferred=True)

        if self._count_lcd:
            if not hasattr(self, "_lcd_counter"):
                self._lcd_counter = 0
            self._lcd_counter += 1
            if self._lcd_counter >= 5:
                self._lcd_counter = 0
                true_count = len(self._data_points) + 1 if self._data_points else 0
                self._count_lcd.display(true_count)

        if self._histogram and len(self._gui_points) > 1:
            if not hasattr(self, "_hist_counter"):
                self._hist_counter = 0
            self._hist_counter += 1
            if self._hist_counter >= 10:
                self._hist_counter = 0
                values = [pt[1] for pt in self._gui_points]
                self._histogram.update_histogram(values)

    def _update_table(self, points: List[Tuple[int, float, str]]) -> None:
        """Append *points* to the data table, capped at MAX_HISTORY rows."""
        if self._table_model is None:
            return
        for idx, val, ts in points:
            self._table_model.appendRow(
                [
                    QStandardItem(str(idx)),
                    QStandardItem(str(val)),
                    QStandardItem(ts),
                ]
            )
        while self._table_model.rowCount() > MAX_HISTORY:
            self._table_model.removeRow(0)

    def _check_high_speed(self, batch_size: int, now: float) -> None:
        """Activate high-speed mode if the rolling batch average exceeds the threshold."""
        if self._high_speed:
            return
        self._batch_history.append((now, batch_size))
        if len(self._batch_history) > HIGH_SPEED_BATCH_HISTORY:
            self._batch_history.pop(0)
        if len(self._batch_history) < HIGH_SPEED_BATCH_HISTORY:
            return
        avg = sum(b[1] for b in self._batch_history) / len(self._batch_history)
        if avg >= HIGH_SPEED_BATCH_THRESHOLD:
            self._activate_high_speed()

    def _activate_high_speed(self) -> None:
        """Switch to high-speed mode: disable plot/table updates, start 2 s histogram timer."""
        if self._high_speed:
            return
        self._high_speed = True
        _log.info("HIGH_SPEED_MODE activated")
        self.status_message.emit("warning", "⚡ HIGH-SPEED MODE — Plot deaktiviert")

        if self._gui_timer:
            self._gui_timer.stop()

        # Switch to Histogramm tab (index 1) — skipped during sweep sessions
        if self._tab_widget_ref and self._hs_autoswitch:
            self._tab_widget_ref.setCurrentIndex(1)

        # Start histogram-only timer (every 2 s)
        if self._histogram and self._hist_timer is None:
            self._hist_timer = QTimer(self)
            self._hist_timer.timeout.connect(self._update_histogram_only)
            self._hist_timer.start(2000)

    def _deactivate_high_speed(self) -> None:
        """Exit high-speed mode and resume normal GUI update timer."""
        if not self._high_speed:
            return
        self._high_speed = False

        if self._hist_timer:
            self._hist_timer.stop()
            self._hist_timer = None

        if self._gui_timer and not self._gui_timer.isActive():
            self._gui_timer.start(GUI_UPDATE_INTERVAL)

    def _update_rate_display(self, now: float) -> None:
        """Recompute and display events-per-second from the device-time accumulator."""
        if not self._rate_lcd:
            return
        if self._cum_us > 0 and self._data_points:
            true_count = len(self._data_points) + 1
            cps = true_count / (self._cum_us / 1e6)
            self._rate_lcd.display(round(cps, 1))

    def _update_histogram_only(self) -> None:
        """Update only the histogram during high-speed mode (called every 2 s)."""
        if not self._high_speed or not self._histogram:
            return
        now = time()
        if len(self._data_points) > 1:
            values = [pt[1] for pt in self._data_points[-10000:]]
            self._histogram.update_histogram(values)
        self._update_rate_display(now)


# Register this experiment at import time
TabRegistry.register(GMTimingTab)
