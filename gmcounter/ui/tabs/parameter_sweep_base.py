# Layer: ui/tabs — generic base for parameter-sweep experiments.
#
# Subclass to build "Abstandsgesetz", "Spannungskurve", etc.:
#   • set the class attributes (tab_id, order, instance, param_unit, …),
#   • decorate with @TabRegistry.register,
#   • add the per-instance texts ``text_*_<instance>`` to ui.sweep_tab in config.json.
#
# The form (sweep_tab.ui) is shared by all sweep tabs; the instance-specific labels, tooltips,
# headers and summary titles come from the ``text_*_<instance>`` keys. The session controller
# drives the shared Start / Stop / Save / Reset buttons through ``session_kind = "sweep"``.

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QHeaderView, QWidget  # pylint: disable=no-name-in-module

from gmcounter.pyqt.ui_sweep_tab import Ui_SweepTab

from ...core.export import TabExport
from ..common.prompt import MessageBoxPrompt, Prompt
from ..i18n import apply_strings
from .base import PlotTabBase

if TYPE_CHECKING:
    from ..context import AppContext
    from .gm_timing_tab import GMTimingTab

_log = logging.getLogger(__name__)


class ParameterSweepTabBase(PlotTabBase):
    """Base for parameter-sweep experiments (distance law, voltage curve, …).

    Subclass contract
    -----------------
    Set these class attributes:
        tab_id                  Stable registry key (``ui.tabs.<tab_id>`` is the title)
        order                   Tab position
        instance                Suffix of the ``text_*_<instance>`` keys in ``ui.sweep_tab``
        param_unit              Metadata unit string (e.g. "cm")
        param_metadata_key      Key injected into individual TabExport metadata
                                (e.g. "sample_distance_cm")
        summary_filename_hint   Stem for the summary CSV (e.g. "abstandsgesetz")

    Optional:
        param_format                    Table cell format of the parameter value
        uses_param_input                False: the parameter comes from
                                        ``context.voltage_readback`` and the input row is hidden
        applies_device_voltage_on_start True: the session controller sends the device settings
                                        before each Start
        clear_param_input_after_stop    Select the input after each point
        supports_log_axes               Offer the log-log switch of the plot (power laws)
    """

    form_name = "sweep_tab"
    session_kind = "sweep"
    required_modules: set[str] = set()

    instance: str = ""
    param_unit: str = ""
    param_metadata_key: str = "param_value"
    summary_filename_hint: str = "sweep"
    param_format: str = "{:.1f}"
    uses_param_input: bool = True
    applies_device_voltage_on_start: bool = False
    clear_param_input_after_stop: bool = False
    supports_log_axes: bool = False

    def __init__(self, context: "AppContext", parent: Optional[QWidget] = None) -> None:
        super().__init__(context, parent)
        self.ui = Ui_SweepTab()
        self.ui.setupUi(self)
        apply_strings(self, self.config.section("ui").get(self.form_name, {}))
        self._apply_instance_texts()

        self._plot = self.ui.sweepPlot
        self._table_model: Optional[QStandardItemModel] = None

        # Summary data
        self._measurements: List[dict] = []
        self._individual_exports: List[TabExport] = []
        self._session_start: Optional[datetime] = None
        self._has_unsaved = False
        self._updating_table = False
        # Set by tests; otherwise a prompt is created on use (a stored one would hold the
        # tab as its parent, a reference cycle that frees the Qt tree at a random moment).
        self._prompt: Optional[Prompt] = None

    # ------------------------------------------------------------------
    # Texts

    def _instance_text(self, name: str, default: str = "") -> str:
        value = self.config.get(f"ui.{self.form_name}.text_{name}_{self.instance}")
        return value if isinstance(value, str) else default

    @property
    def param_label(self) -> str:
        """Column header and axis label of the parameter (with unit)."""
        return self._instance_text("param_header")

    @property
    def summary_title(self) -> str:
        return self._instance_text("summary_title")

    def _apply_instance_texts(self) -> None:
        ui = self.ui
        ui.labelParam.setText(self._instance_text("param"))
        ui.spinParam.setSuffix(self._instance_text("param_suffix"))
        ui.spinParam.setToolTip(self._instance_text("param_tooltip"))
        hint = self._instance_text("hint")
        ui.labelHint.setText(hint)
        ui.labelHint.setVisible(bool(hint))
        ui.labelParam.setVisible(self.uses_param_input)
        ui.spinParam.setVisible(self.uses_param_input)
        ui.checkLogAxes.setVisible(self.supports_log_axes)

    # ------------------------------------------------------------------
    # PlotTabBase lifecycle

    @property
    def _gm_tab(self) -> Optional["GMTimingTab"]:
        return self.context.timing

    def build(self) -> None:
        """Label the promoted plot and set up the summary table."""
        self._plot.config.pen_width = self.config.get("plot.line_width", 1)
        self._plot.reconfigure("xlabel", self.param_label)
        self._plot.reconfigure("ylabel", self.text("plot_y_label"))

        cols = [
            self.param_label,
            *self.config.get(f"ui.{self.form_name}.table_summary_headers", []),
        ]
        self._table_model = QStandardItemModel(0, len(cols), self.ui.tableSummary)
        self._table_model.setHorizontalHeaderLabels(cols)
        self.ui.tableSummary.setModel(self._table_model)
        self.ui.tableSummary.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table_model.itemChanged.connect(self._on_table_item_changed)
        self.ui.checkLogAxes.toggled.connect(self._on_log_axes_toggled)
        self._add_delete_action()
        self._update_status()

    def on_measurement_started(self) -> None:
        self._session_start = datetime.now()

    def on_measurement_stopped(self) -> None:
        gm_tab = self._gm_tab
        if not gm_tab or not self._session_start:
            return

        end = datetime.now()
        duration_s = max((end - self._session_start).total_seconds(), 1e-6)

        # Snapshot the individual timing export before the timing tab is reset next run.
        indiv_export = gm_tab.export()
        run_settings: dict = {}
        run_timing: dict = {}
        if indiv_export:
            indiv_export.metadata[self.param_metadata_key] = self.current_param()
            indiv_export.metadata["sweep_parameter"] = self._sweep_parameter()
            indiv_export.metadata["measurement_index"] = len(self._measurements) + 1
            run_settings = dict(indiv_export.metadata.get("settings", {}))
            # The device time is what the run was cut by; the clock only as a fallback.
            device_time = indiv_export.metadata.get("timing", {}).get("device_time_s")
            if device_time:
                duration_s = device_time
            run_timing = dict(indiv_export.metadata.get("timing", {}))
            self._individual_exports.append(indiv_export)

        count = int(gm_tab.get_statistics().get("count", 0))
        entry = {
            "param": self.current_param(),
            "count": count,
            "duration_s": round(duration_s, 2),
            "rate_hz": round(count / duration_s, 3),
            "start": self._session_start.isoformat(),
            "end": end.isoformat(),
            "settings": run_settings,
            "timing": run_timing,
        }
        self._measurements.append(entry)
        self._session_start = None
        self._has_unsaved = True

        self._append_table_row(entry)
        self._refresh_plot()
        self._update_status()
        if self.clear_param_input_after_stop:
            self._focus_param_input()

    # ------------------------------------------------------------------
    # Data model

    def current_param(self) -> float:
        """The parameter of the running / last point."""
        if not self.uses_param_input:
            return float(self.context.voltage_readback())
        return self.ui.spinParam.value()

    def has_data(self) -> bool:
        return bool(self._measurements)

    def has_unsaved_data(self) -> bool:
        return self._has_unsaved and self.has_data()

    def mark_saved(self) -> None:
        self._has_unsaved = False

    @property
    def individual_exports(self) -> List[TabExport]:
        return list(self._individual_exports)

    def session_exports(self) -> List[TabExport]:
        return self.individual_exports

    def session_file_name(self, export: TabExport, index: int) -> str:
        value = export.metadata.get(self.param_metadata_key, "?")
        return f"p{value}{self.param_unit}_m{index + 1:02d}"

    def reset_session(self) -> None:
        self.reset_summary()

    def reset_summary(self) -> None:
        self._measurements.clear()
        self._individual_exports.clear()
        self._has_unsaved = False
        self._session_start = None
        if self._table_model:
            self._table_model.removeRows(0, self._table_model.rowCount())
        self._plot.clear_measurement_data()
        self._update_status()

    # ------------------------------------------------------------------
    # Export (PlotTabBase §7)

    def summary_export(self) -> Optional[TabExport]:
        if not self._measurements:
            return None
        cols = [
            self.param_label,
            *self.config.get(f"ui.{self.form_name}.table_summary_headers", []),
        ]
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
            "experiment": self.tab_id,
            "n_measurements": len(self._measurements),
            "sweep_parameter": self._sweep_parameter(),
            # One entry per point, in file order: the settings of every single run.
            "measurements": [
                {"index": i, **m} for i, m in enumerate(self._measurements, start=1)
            ],
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

    def _sweep_parameter(self) -> dict:
        """Which quantity is swept, for the metadata."""
        return {
            "name": self.param_metadata_key,
            "label": self.param_label,
            "unit": self.param_unit,
        }

    def _focus_param_input(self) -> None:
        """Select all text in the param input and give it keyboard focus."""
        if self.uses_param_input:
            self.ui.spinParam.selectAll()
            self.ui.spinParam.setFocus()

    @staticmethod
    def _format_time(iso: str) -> str:
        """Clock time of a start stamp for the table (the files keep the full stamp)."""
        try:
            return datetime.fromisoformat(iso).strftime("%H:%M:%S")
        except ValueError:
            return iso

    def _append_table_row(self, entry: dict) -> None:
        if self._table_model is None:
            return
        items = [
            QStandardItem(self.param_format.format(entry["param"])),
            QStandardItem(str(entry["count"])),
            QStandardItem(f"{entry['rate_hz']:.3f}"),
            QStandardItem(f"{entry['duration_s']:.2f}"),
            QStandardItem(self._format_time(entry["start"])),
        ]
        items[4].setToolTip(str(entry["start"]))
        for item in items:
            item.setEditable(False)
        if self.uses_param_input:
            # Only a value the user typed can be wrong; a read-back voltage cannot.
            items[0].setEditable(True)
            items[0].setToolTip(self.text("text_param_edit_hint"))
        self._table_model.appendRow(items)
        self.ui.tableSummary.scrollToBottom()

    def remove_point(self, index: int) -> bool:
        """Delete a recorded point (e.g. an aborted run) before the session is saved.

        The last remaining point stays: an empty series is ended with Reset. Returns False
        if nothing was removed.
        """
        if len(self._measurements) <= 1 or not 0 <= index < len(self._measurements):
            return False
        in_step = len(self._individual_exports) == len(self._measurements)
        del self._measurements[index]
        if in_step:
            del self._individual_exports[index]
            for i, export in enumerate(self._individual_exports, start=1):
                export.metadata["measurement_index"] = i  # file names follow the order
        if self._table_model is not None:
            self._table_model.removeRow(index)
        self._has_unsaved = True
        self._refresh_plot()
        self._update_status()
        return True

    def _add_delete_action(self) -> None:
        """Delete key and context menu entry of the summary table."""
        table = self.ui.tableSummary
        action = QAction(self.text("text_delete_point"), table)
        action.setShortcut(Qt.Key.Key_Delete)
        action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        action.triggered.connect(self._delete_selected_point)
        table.addAction(action)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

    def _on_log_axes_toggled(self, _checked: bool) -> None:
        self._refresh_plot()

    def _delete_selected_point(self) -> None:
        row = self.ui.tableSummary.currentIndex().row()
        if not 0 <= row < len(self._measurements):
            return
        title = self.text("text_delete_title")
        prompt = self._prompt or MessageBoxPrompt(self)
        if len(self._measurements) <= 1:
            prompt.info(self.text("text_delete_last_point"), title)
            return
        if prompt.ask(self.text("text_delete_point_confirm", n=row + 1), title):
            self.remove_point(row)

    def set_point_param(self, index: int, value: float) -> bool:
        """Correct the parameter of an already recorded point (before the session is saved).

        Updates the summary entry, the point's own export (metadata and therefore the file
        name), the table and the plot. Returns False if there is no such point or the value
        is not a valid parameter.
        """
        if not 0 <= index < len(self._measurements):
            return False
        spin = self.ui.spinParam
        if not math.isfinite(value) or not spin.minimum() <= value <= spin.maximum():
            return False
        value = round(value, spin.decimals())

        entry = self._measurements[index]
        entry["param"] = value
        # The point's own settings snapshot may hold the same quantity; keep them in step.
        for holder in (entry, entry.get("settings")):
            if isinstance(holder, dict) and self.param_metadata_key in holder:
                holder[self.param_metadata_key] = value
        if len(self._individual_exports) == len(self._measurements):
            metadata = self._individual_exports[index].metadata
            metadata[self.param_metadata_key] = value
            settings = metadata.get("settings")
            if isinstance(settings, dict) and self.param_metadata_key in settings:
                settings[self.param_metadata_key] = value

        if self._table_model is not None:
            item = self._table_model.item(index, 0)
            if item is not None:
                self._set_item_text(item, self.param_format.format(value))
        self._has_unsaved = True
        self._refresh_plot()
        self._update_status()
        return True

    def _set_item_text(self, item: QStandardItem, text: str) -> None:
        """Set a cell text without triggering the edit handler."""
        self._updating_table = True
        try:
            item.setText(text)
        finally:
            self._updating_table = False

    def _on_table_item_changed(self, item: QStandardItem) -> None:
        """A parameter cell was edited: apply it, or put the old value back."""
        if self._updating_table or item.column() != 0:
            return
        row = item.row()
        try:
            value = float(item.text().strip().replace(",", "."))
        except ValueError:
            value = float("nan")
        if not self.set_point_param(row, value):
            if 0 <= row < len(self._measurements):
                self._set_item_text(
                    item, self.param_format.format(self._measurements[row]["param"])
                )
            self.ui.valueStatus.setText(self.text("text_param_invalid"))

    def _refresh_plot(self) -> None:
        if not self._measurements:
            return
        # Rates, not counts: runs of different length (or aborted ones) stay comparable.
        points = [(m["param"], m["rate_hz"]) for m in self._measurements]
        errors = [
            math.sqrt(max(m["count"], 0)) / m["duration_s"] if m["duration_s"] else 0.0
            for m in self._measurements
        ]
        log = self.supports_log_axes and self.ui.checkLogAxes.isChecked()
        self._plot.set_summary_points(points, errors=errors, log=log)

    def _update_status(self) -> None:
        n = len(self._measurements)
        if n == 0:
            text = self.text("text_no_points")
        else:
            text = self.text("text_points_one" if n == 1 else "text_points_many", n=n)
        self.ui.valueStatus.setText(text)
