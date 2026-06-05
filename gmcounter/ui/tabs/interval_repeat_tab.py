# Layer: ui/tabs — IntervalRepeatTab: MCS-style interval/repeat measurement.
#
# One continuous acquisition sliced into R equal-width intervals.
# Lives on its own .ui page (mainwindow.ui → "interval").

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from PySide6.QtGui import (  # pylint: disable=no-name-in-module
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QDoubleSpinBox,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .base import PlotTabBase
from ...core.export import TabExport
from ...core.interval_binning import IntervalBinner

_log = logging.getLogger(__name__)


class IntervalRepeatTab(PlotTabBase):
    """MCS-style interval/repeat measurement tab.

    Receives frames from the active acquisition and bins them live into R
    equal-width intervals of width W seconds.  On save writes a summary CSV
    plus one CSV per interval (per-interval raw deltas).
    """

    tab_id = "interval_repeat"
    tab_title = "Intervalle"
    required_modules: set[str] = set()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._binner: Optional[IntervalBinner] = None
        self._has_unsaved: bool = False
        self._session_start: Optional[datetime] = None

        # .ui widget references (injected by MainWindow)
        self._plot_container: Optional[QWidget] = None
        self._table_view: Optional[QTableView] = None
        self._width_input: Optional[QDoubleSpinBox] = None
        self._repeat_input: Optional[QSpinBox] = None
        self._status_label: Optional[QLabel] = None

        # Created in build()
        self._plot = None
        self._table_model: Optional[QStandardItemModel] = None

    # ------------------------------------------------------------------
    # Dependency injection (called by MainWindow before build)

    def inject_ui(
        self,
        plot_container: QWidget,
        table_view: QTableView,
        width_input: QDoubleSpinBox,
        repeat_input: QSpinBox,
        status_label: QLabel,
    ) -> None:
        self._plot_container = plot_container
        self._table_view = table_view
        self._width_input = width_input
        self._repeat_input = repeat_input
        self._status_label = status_label

    # ------------------------------------------------------------------
    # PlotTabBase lifecycle

    def build(self) -> None:
        from ..widgets.plot import GeneralPlot, PlotConfig

        if self._plot_container and self._plot is None:
            bg = (
                self._plot_container.palette()
                .color(self._plot_container.backgroundRole())
                .name()
            )
            cfg = PlotConfig(
                xlabel="Intervall",
                ylabel="Anzahl Ereignisse",
                background_color=bg,
            )
            self._plot = GeneralPlot(config=cfg)
            layout = QVBoxLayout(self._plot_container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._plot)

        if self._table_view is not None and self._table_model is None:
            cols = ["Index", "Anzahl", "cps", "t_start (s)", "t_end (s)"]
            self._table_model = QStandardItemModel(0, len(cols), self._table_view)
            self._table_model.setHorizontalHeaderLabels(cols)
            self._table_view.setModel(self._table_model)
            hdr = self._table_view.horizontalHeader()
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def on_reset(self) -> None:
        w = self._width_input.value() if self._width_input else 1.0
        r = self._repeat_input.value() if self._repeat_input else 10
        self._binner = IntervalBinner(w * 1e6, r)
        self._has_unsaved = False
        if self._table_model:
            self._table_model.removeRows(0, self._table_model.rowCount())
        if self._plot and hasattr(self._plot, "clear_measurement_data"):
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
        return self._width_input.value() if self._width_input else 1.0

    @property
    def repeat_count(self) -> int:
        return self._repeat_input.value() if self._repeat_input else 10

    def has_data(self) -> bool:
        return bool(self._binner and self._binner.total_count() > 0)

    def has_unsaved_data(self) -> bool:
        return self._has_unsaved and self.has_data()

    def mark_saved(self) -> None:
        self._has_unsaved = False

    def reset(self) -> None:
        self.on_reset()

    # ------------------------------------------------------------------
    # Export

    def summary_export(self) -> Optional[TabExport]:
        if not self._binner or not self.has_data():
            return None
        bins = self._binner.bins
        cols = ["Index", "Anzahl", "cps", "t_start_s", "t_end_s"]
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
            "dc:title": "Intervallmessung — Zusammenfassung",
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
            cols = ["Index", "Delta (µs)"]
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
        if not self._plot or not self._binner:
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
        if not self._status_label:
            return
        if not self.has_data():
            self._status_label.setText("Keine Daten.")
        else:
            bins = self._binner.bins  # type: ignore[union-attr]
            n = self._binner.total_count()
            t = round(bins.cum_us / 1e6, 1)
            self._status_label.setText(
                f"{n} Ereignisse in {bins.repeats} Intervallen · {t} s"
            )
