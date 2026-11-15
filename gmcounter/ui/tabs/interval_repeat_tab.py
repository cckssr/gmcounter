# Layer: ui/tabs — IntervalRepeatTab: MCS-style interval/repeat measurement.
#
# One continuous acquisition sliced into R equal-width intervals.
# Own form: interval_tab.ui.

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtGui import (  # pylint: disable=no-name-in-module
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import QHeaderView, QWidget  # pylint: disable=no-name-in-module

from gmcounter.pyqt.ui_interval_tab import Ui_IntervalTab

from ...core.export import TabExport
from ...core.interval_binning import IntervalBinner
from ..i18n import apply_strings
from .base import PlotTabBase
from .registry import TabRegistry

if TYPE_CHECKING:
    from ..context import AppContext

_log = logging.getLogger(__name__)


@TabRegistry.register
class IntervalRepeatTab(PlotTabBase):
    """MCS-style interval/repeat measurement tab.

    Receives frames from the active acquisition (``receives_frames``) and bins them live
    into R equal-width intervals of width W seconds.  On save writes a summary CSV plus one
    CSV per interval (per-interval raw deltas).
    """

    tab_id = "interval_repeat"
    form_name = "interval_tab"
    order = 30
    session_kind = "interval"
    receives_frames = True
    required_modules: set[str] = set()

    def __init__(self, context: "AppContext", parent: Optional[QWidget] = None) -> None:
        super().__init__(context, parent)
        self.ui = Ui_IntervalTab()
        self.ui.setupUi(self)
        apply_strings(self, self.config.section("ui").get(self.form_name, {}))

        self._binner: Optional[IntervalBinner] = None
        self._has_unsaved: bool = False
        self._session_start: Optional[datetime] = None
        self._plot = self.ui.intervalPlot
        self._table_model: Optional[QStandardItemModel] = None

    # ------------------------------------------------------------------
    # PlotTabBase lifecycle

    def build(self) -> None:
        """Label the promoted plot and set up the interval table."""
        self._plot.config.pen_width = self.config.get("plot.line_width", 1)
        self._plot.reconfigure("xlabel", self.text("plot_x_label"))
        self._plot.reconfigure("ylabel", self.text("plot_y_label"))

        cols = self.config.get(f"ui.{self.form_name}.table_intervals_headers", [])
        self._table_model = QStandardItemModel(0, len(cols), self.ui.tableIntervals)
        self._table_model.setHorizontalHeaderLabels(cols)
        self.ui.tableIntervals.setModel(self._table_model)
        self.ui.tableIntervals.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._update_status()

    def on_reset(self) -> None:
        self._binner = IntervalBinner(self.width_s * 1e6, self.repeat_count)
        self._has_unsaved = False
        if self._table_model:
            self._table_model.removeRows(0, self._table_model.rowCount())
        self._plot.clear_measurement_data()
        self._update_status()

    def on_measurement_started(self) -> None:
        self._session_start = datetime.now()

    def on_measurement_stopped(self) -> None:
        if self._binner and self._binner.total_count() > 0:
            self._has_unsaved = True
        self._update_status()

    def on_frames(self, frames) -> None:
        if not frames or self._binner is None:
            return
        points = [(f.index, f.value) for f in frames]
        touched = self._binner.feed(points)
        if touched:
            self._refresh_plot()
            self._refresh_table_incremental(touched)

    # ------------------------------------------------------------------
    # Data model

    @property
    def width_s(self) -> float:
        return self.ui.spinWidth.value()

    @property
    def repeat_count(self) -> int:
        return self.ui.spinRepeats.value()

    def has_data(self) -> bool:
        return bool(self._binner and self._binner.total_count() > 0)

    def has_unsaved_data(self) -> bool:
        return self._has_unsaved and self.has_data()

    def mark_saved(self) -> None:
        self._has_unsaved = False

    def reset(self) -> None:
        self.on_reset()

    def reset_session(self) -> None:
        self.reset()

    def session_exports(self) -> List[TabExport]:
        return self.interval_exports

    def session_file_name(self, export: TabExport, index: int) -> str:
        return export.filename_hint

    # ------------------------------------------------------------------
    # Export

    def summary_export(self) -> Optional[TabExport]:
        if not self._binner or not self.has_data():
            return None
        bins = self._binner.bins
        cols = self.config.get(f"ui.{self.form_name}.export_intervals_columns", [])
        rows = []
        for i in range(bins.repeats):
            t_start = i * bins.width_us / 1e6
            t_end = (i + 1) * bins.width_us / 1e6
            count = bins.counts[i]
            cps = round(count / (bins.width_us / 1e6), 4) if bins.width_us > 0 else 0.0
            rows.append(
                [str(i), str(count), str(cps), f"{t_start:.6f}", f"{t_end:.6f}"]
            )
        metadata = {
            "dc:date": datetime.now().strftime("%Y-%m-%d"),
            "dc:title": self.text("text_summary_title"),
            "interval_width_s": bins.width_us / 1e6,
            "repeats": bins.repeats,
            "true_total_count": self._binner.total_count(),
            "total_device_time_s": round(bins.cum_us / 1e6, 6),
        }
        return TabExport(
            filename_hint="intervalle",
            columns=cols,
            rows=rows,
            metadata=metadata,
        )

    def export(self) -> Optional[TabExport]:
        return self.summary_export()

    @property
    def interval_exports(self) -> List[TabExport]:
        if not self._binner or not self.has_data():
            return []
        bins = self._binner.bins
        result = []
        for i in range(bins.repeats):
            deltas = bins.deltas[i]
            cols = self.config.get(f"ui.{self.form_name}.export_interval_columns", [])
            rows = [[str(j), str(d)] for j, d in enumerate(deltas)]
            t_start = i * bins.width_us / 1e6
            t_end = (i + 1) * bins.width_us / 1e6
            metadata = {
                "interval_index": i,
                "interval_count": bins.counts[i],
                "interval_width_s": bins.width_us / 1e6,
                "t_start_s": t_start,
                "t_end_s": t_end,
            }
            result.append(
                TabExport(
                    filename_hint=f"interval_{i:03d}",
                    columns=cols,
                    rows=rows,
                    metadata=metadata,
                )
            )
        return result

    # ------------------------------------------------------------------
    # Private helpers

    def _refresh_plot(self) -> None:
        if not self._binner:
            return
        bins = self._binner.bins
        pts = [(i, bins.counts[i]) for i in range(bins.repeats)]
        self._plot.set_summary_points(pts)

    def _refresh_table_incremental(self, touched: List[int]) -> None:
        if self._table_model is None or self._binner is None:
            return
        bins = self._binner.bins
        for i in touched:
            count = bins.counts[i]
            t_start = i * bins.width_us / 1e6
            t_end = (i + 1) * bins.width_us / 1e6
            cps = round(count / (bins.width_us / 1e6), 2) if bins.width_us > 0 else 0.0
            row_items = [
                QStandardItem(str(i)),
                QStandardItem(str(count)),
                QStandardItem(str(cps)),
                QStandardItem(f"{t_start:.3f}"),
                QStandardItem(f"{t_end:.3f}"),
            ]
            if i < self._table_model.rowCount():
                for col, item in enumerate(row_items):
                    self._table_model.setItem(i, col, item)
            else:
                # Fill any missing rows up to and including i
                while self._table_model.rowCount() <= i:
                    placeholder = [QStandardItem("0")] * 5
                    self._table_model.appendRow(placeholder)
                for col, item in enumerate(row_items):
                    self._table_model.setItem(i, col, item)

    def _update_status(self) -> None:
        if not self.has_data():
            self.ui.valueStatus.setText(self.text("text_no_data"))
            return
        bins = self._binner.bins  # type: ignore[union-attr]
        self.ui.valueStatus.setText(
            self.text(
                "text_status",
                n=self._binner.total_count(),  # type: ignore[union-attr]
                repeats=bins.repeats,
                t=round(bins.cum_us / 1e6, 1),
            )
        )
