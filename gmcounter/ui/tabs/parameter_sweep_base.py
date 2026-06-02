# Layer: ui/tabs — generic base for parameter-sweep experiments.
#
# Subclass to build "Abstandsgesetz", "Spannungskurve", etc.:
#   • declare class attributes (param_label, summary_filename_hint, …)
#   • register in TabRegistry
#   • MainWindow calls inject_ui() with the .ui widgets, then build()
#   • MainWindow connects AppController.measurement_stopped here
#   • MainWindow routes the shared Start/Stop/Speichern buttons via
#     isinstance(..., ParameterSweepTabBase)
#
# No widgets are created here — all static layout lives in .ui.

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Optional, List, TYPE_CHECKING

from PySide6.QtGui import QStandardItemModel, QStandardItem  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QWidget,
    QTableView,
    QLabel,
    QDoubleSpinBox,
    QVBoxLayout,
    QHeaderView,
)

from .base import PlotTabBase
from ...core.export import TabExport

if TYPE_CHECKING:
    from .gm_timing_tab import GMTimingTab

_log = logging.getLogger(__name__)


class ParameterSweepTabBase(PlotTabBase):
    """Base for parameter-sweep experiments (distance law, voltage curve, …).

    Subclass contract
    -----------------
    Set these class attributes:
        tab_id                  Stable registry key
        tab_title               Shown as tab label
        param_label             Axis / column header (e.g. "Probenabstand (cm)")
        param_unit              Metadata unit string (e.g. "cm")
        param_metadata_key      Key injected into individual TabExport metadata
                                (e.g. "sample_distance_cm")
        summary_filename_hint   Stem for the summary CSV (e.g. "abstandsgesetz")
        summary_title           Human title for the summary (used in metadata)

    Then call TabRegistry.register(MyTab) at module level.

    MainWindow injection order (before build):
        set_gm_tab(gm_tab)
        inject_ui(plot_container, table_view, param_input, status_label)
        build()
    MainWindow also connects:
        ctrl.measurement_stopped → self.on_measurement_stopped
    """

    # -- Subclass-defined -----------------------------------------------
    param_label: str = "Parameter"
    param_unit: str = ""
    param_metadata_key: str = "param_value"
    summary_filename_hint: str = "sweep"
    summary_title: str = "Parameter-Sweep"
    # Table cell format string applied to the parameter value
    param_format: str = "{:.1f}"
    # Set True if the tab requires the device voltage to be applied on each Start
    applies_device_voltage_on_start: bool = False

    # -- Internal -------------------------------------------------------
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._gm_tab: Optional["GMTimingTab"] = None

        # .ui widget references (set by inject_ui)
        self._plot_container: Optional[QWidget] = None
        self._table_view: Optional[QTableView] = None
        self._param_input: Optional[QDoubleSpinBox] = None
        self._status_label: Optional[QLabel] = None
        # Optional callable that provides the parameter value (takes priority
        # over _param_input when set; used e.g. for voltage from device control).
        self._param_provider: Optional[Callable[[], float]] = None

        # Created in build()
        self._plot = None  # GeneralPlot instance
        self._table_model: Optional[QStandardItemModel] = None

        # Summary data
        self._measurements: List[dict] = []
        self._individual_exports: List[TabExport] = []
        self._session_start: Optional[datetime] = None
        self._has_unsaved = False

    # ------------------------------------------------------------------
    # Dependency injection (called by MainWindow before build)

    def set_gm_tab(self, gm_tab: "GMTimingTab") -> None:
        self._gm_tab = gm_tab

    def inject_ui(
        self,
        plot_container: QWidget,
        table_view: QTableView,
        status_label: QLabel,
        param_input: Optional[QDoubleSpinBox] = None,
        param_provider: Optional[Callable[[], float]] = None,
    ) -> None:
        """Receive the .ui container widgets. Call before build().

        Either *param_input* (a QDoubleSpinBox in the tab page) or
        *param_provider* (a zero-argument callable, e.g. ``lambda: ctrl.voltage``)
        must be supplied so the tab can read the current parameter value.
        """
        self._plot_container = plot_container
        self._table_view = table_view
        self._param_input = param_input
        self._param_provider = param_provider
        self._status_label = status_label

    # ------------------------------------------------------------------
    # PlotTabBase lifecycle

    def build(self) -> None:
        """Create GeneralPlot inside the .ui container and wire the table model."""
        from ..widgets.plot import GeneralPlot, PlotConfig

        if self._plot_container and self._plot is None:
            bg = (
                self._plot_container.palette()
                .color(self._plot_container.backgroundRole())
                .name()
            )
            cfg = PlotConfig(
                xlabel=self.param_label,
                ylabel="Anzahl Ereignisse",
                background_color=bg,
            )
            self._plot = GeneralPlot(config=cfg)
            layout = QVBoxLayout(self._plot_container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._plot)

        if self._table_view is not None and self._table_model is None:
            cols = [
                self.param_label,
                "Anzahl",
                "Rate (1/s)",
                "Dauer (s)",
                "Zeitstempel",
            ]
            self._table_model = QStandardItemModel(0, len(cols), self._table_view)
            self._table_model.setHorizontalHeaderLabels(cols)
            self._table_view.setModel(self._table_model)
            hdr = self._table_view.horizontalHeader()
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # ------------------------------------------------------------------
    # Measurement lifecycle

    def on_measurement_started(self) -> None:
        self._session_start = datetime.now()

    def on_measurement_stopped(self) -> None:
        if not self._gm_tab or not self._session_start:
            return

        end = datetime.now()
        duration_s = max((end - self._session_start).total_seconds(), 1e-6)

        # Snapshot individual timing export before GMTimingTab is reset next run.
        # GMTimingTab.on_measurement_stopped() fires first (set_active_tab connected
        # earlier), so _session_end is already set on the export.
        indiv_export = self._gm_tab.export()
        if indiv_export:
            param_val = self._current_param()
            indiv_export.metadata[self.param_metadata_key] = param_val
            self._individual_exports.append(indiv_export)

        stats = self._gm_tab.get_statistics() if self._gm_tab else {}
        count = int(stats.get("count", 0))
        rate = round(count / duration_s, 3)

        entry = {
            "param": self._current_param(),
            "count": count,
            "duration_s": round(duration_s, 2),
            "rate_hz": rate,
            "start": self._session_start.isoformat(),
        }
        self._measurements.append(entry)
        self._session_start = None
        self._has_unsaved = True

        self._append_table_row(entry)
        self._refresh_plot()
        self._update_status()

    # ------------------------------------------------------------------
    # Data model

    def current_param(self) -> float:
        return self._current_param()

    def _current_param(self) -> float:
        if self._param_provider is not None:
            return float(self._param_provider())
        return self._param_input.value() if self._param_input else 0.0

    def has_data(self) -> bool:
        return bool(self._measurements)

    def has_unsaved_data(self) -> bool:
        return self._has_unsaved and self.has_data()

    def mark_saved(self) -> None:
        self._has_unsaved = False

    @property
    def individual_exports(self) -> List[TabExport]:
        return list(self._individual_exports)

    def reset_summary(self) -> None:
        self._measurements.clear()
        self._individual_exports.clear()
        self._has_unsaved = False
        self._session_start = None
        if self._table_model:
            self._table_model.removeRows(0, self._table_model.rowCount())
        if self._plot:
            self._plot.clear_measurement_data()
        self._update_status()

    # ------------------------------------------------------------------
    # Export (PlotTabBase §7)

    def summary_export(self) -> Optional[TabExport]:
        if not self._measurements:
            return None
        cols = [self.param_label, "Anzahl", "Rate (1/s)", "Dauer (s)", "Zeitstempel"]
        rows = [
            [
                str(m["param"]),
                str(m["count"]),
                str(m["rate_hz"]),
                str(m["duration_s"]),
                m["start"],
            ]
            for m in self._measurements
        ]
        metadata = {
            "dc:date": datetime.now().strftime("%Y-%m-%d"),
            "dc:title": self.summary_title,
            "n_measurements": len(self._measurements),
        }
        return TabExport(
            filename_hint=self.summary_filename_hint,
            columns=cols,
            rows=rows,
            metadata=metadata,
        )

    def export(self) -> Optional[TabExport]:
        return self.summary_export()

    # ------------------------------------------------------------------
    # Private helpers

    def _append_table_row(self, entry: dict) -> None:
        if self._table_model is None:
            return
        self._table_model.appendRow(
            [
                QStandardItem(self.param_format.format(entry["param"])),
                QStandardItem(str(entry["count"])),
                QStandardItem(str(entry["rate_hz"])),
                QStandardItem(str(entry["duration_s"])),
                QStandardItem(entry["start"]),
            ]
        )
        if self._table_view:
            self._table_view.scrollToBottom()

    def _refresh_plot(self) -> None:
        if not self._plot or not self._measurements:
            return
        # Sort by parameter value for connecting line
        pts = sorted((m["param"], m["count"]) for m in self._measurements)
        self._plot.set_summary_points(pts)

    def _update_status(self) -> None:
        if not self._status_label:
            return
        n = len(self._measurements)
        if n == 0:
            self._status_label.setText("Keine Messpunkte aufgezeichnet.")
        else:
            self._status_label.setText(
                f"{n} Messpunkt{'e' if n != 1 else ''} aufgezeichnet."
            )
