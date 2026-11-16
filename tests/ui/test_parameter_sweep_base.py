"""Tests for ui.tabs.parameter_sweep_base.ParameterSweepTabBase data-model methods."""

import sys
import pytest

pytest.importorskip("PySide6", reason="ParameterSweepTabBase requires PySide6")

from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

from gmcounter.infrastructure.config import default_config
from gmcounter.ui.context import AppContext
from gmcounter.ui.tabs.parameter_sweep_base import ParameterSweepTabBase
from gmcounter.core.export import TabExport

_app = QApplication.instance() or QApplication(sys.argv)


class ConcreteTab(ParameterSweepTabBase):
    tab_id = "test_sweep"
    instance = "distance"  # texts come from ui.sweep_tab.*_distance
    param_unit = "cm"
    param_metadata_key = "distance_cm"
    summary_filename_hint = "test_sweep"


def _make_tab(**context_kwargs):
    context = AppContext(config=default_config(), **context_kwargs)
    return ConcreteTab(context)


def test_initial_state_no_data():
    tab = _make_tab()
    assert not tab.has_data()
    assert not tab.has_unsaved_data()


def test_mark_saved_clears_flag():
    tab = _make_tab()
    tab._has_unsaved = True
    tab._measurements = [{"param": 10.0}]
    assert tab.has_unsaved_data()
    tab.mark_saved()
    assert not tab.has_unsaved_data()


def test_reset_summary_clears_data():
    tab = _make_tab()
    tab._measurements = [{"param": 5.0, "count": 100}]
    tab._has_unsaved = True
    tab.reset_summary()
    assert not tab.has_data()
    assert not tab.has_unsaved_data()


def test_individual_exports_returns_copy():
    tab = _make_tab()
    export = MagicMock(spec=TabExport)
    tab._individual_exports.append(export)
    result = tab.individual_exports
    assert len(result) == 1
    result.append(MagicMock())  # modify returned list
    assert len(tab._individual_exports) == 1  # original unchanged


def test_summary_export_returns_none_when_no_data():
    tab = _make_tab()
    assert tab.summary_export() is None


def test_summary_export_returns_tab_export_with_data():
    tab = _make_tab()
    from datetime import datetime

    tab._measurements = [
        {
            "param": 20.0,
            "count": 150,
            "rate_hz": 2.5,
            "duration_s": 60.0,
            "start": datetime.now().isoformat(),
        }
    ]
    export = tab.summary_export()
    assert export is not None
    assert export.filename_hint == "test_sweep"
    assert len(export.rows) == 1
    assert export.rows[0][0] == "20.0"


def test_current_param_from_voltage_readback():
    """A tab without its own input takes the parameter from the device read-back."""

    class ReadbackTab(ConcreteTab):
        uses_param_input = False

    tab = ReadbackTab(
        AppContext(config=default_config(), voltage_readback=lambda: 42.0)
    )
    assert tab.current_param() == pytest.approx(42.0)


def test_current_param_from_input():
    tab = _make_tab()
    tab.ui.spinParam.setValue(12.5)
    assert tab.current_param() == pytest.approx(12.5)


# ---------------------------------------------------------------- correcting a recorded point


def _tab_with_points(*params: float, tab_cls=None):
    """A built tab holding one recorded point (and its own export) per parameter value."""
    from datetime import datetime

    tab = (tab_cls or ConcreteTab)(AppContext(config=default_config()))
    tab.build()
    for i, param in enumerate(params, start=1):
        entry = {
            "param": param,
            "count": 10 * i,
            "rate_hz": 0.5,
            "duration_s": 60.0,
            "start": datetime.now().isoformat(),
            "settings": {},
        }
        tab._measurements.append(entry)
        tab._individual_exports.append(
            TabExport("d", ["a"], [["1"]], {"distance_cm": param, "settings": {}})
        )
        tab._append_table_row(entry)
    return tab


def test_set_point_param_corrects_entry_export_table_and_file_name():
    tab = _tab_with_points(5.0, 15.0)
    assert tab.set_point_param(1, 20.0)

    assert tab._measurements[1]["param"] == 20.0
    export = tab.session_exports()[1]
    assert export.metadata["distance_cm"] == 20.0
    assert tab.session_file_name(export, 1) == "p20.0cm_m02"
    assert tab._table_model.item(1, 0).text() == "20.0"
    assert tab.summary_export().rows[1][0] == "20.0"
    assert tab.has_unsaved_data()


def test_set_point_param_rejects_unknown_points_and_invalid_values():
    tab = _tab_with_points(5.0)
    assert not tab.set_point_param(3, 10.0)
    assert not tab.set_point_param(0, float("nan"))
    assert not tab.set_point_param(0, -1.0)
    assert tab._measurements[0]["param"] == 5.0


def test_editing_the_table_cell_applies_the_value():
    tab = _tab_with_points(5.0, 15.0)
    tab._table_model.item(1, 0).setText("20,0")  # decimal comma is accepted
    assert tab._measurements[1]["param"] == 20.0
    assert tab._table_model.item(1, 0).text() == "20.0"


def test_editing_the_table_cell_with_text_restores_the_old_value():
    tab = _tab_with_points(5.0, 15.0)
    tab._table_model.item(1, 0).setText("abc")
    assert tab._measurements[1]["param"] == 15.0
    assert tab._table_model.item(1, 0).text() == "15.0"
    assert tab.ui.valueStatus.text() == tab.text("text_param_invalid")


def test_only_the_parameter_cell_of_a_typed_parameter_is_editable():
    tab = _tab_with_points(5.0)
    assert tab._table_model.item(0, 0).isEditable()
    assert not any(tab._table_model.item(0, c).isEditable() for c in range(1, 5))


def test_a_read_back_parameter_cannot_be_edited():
    class ReadbackTab(ConcreteTab):
        uses_param_input = False

    tab = _tab_with_points(5.0, tab_cls=ReadbackTab)
    assert not tab._table_model.item(0, 0).isEditable()


# ---------------------------------------------------------------- deleting points, plot, table text


def test_remove_point_renumbers_exports_and_file_names():
    tab = _tab_with_points(5.0, 15.0, 20.0)
    assert tab.remove_point(1)

    assert [m["param"] for m in tab._measurements] == [5.0, 20.0]
    assert tab._table_model.rowCount() == 2
    exports = tab.session_exports()
    assert [e.metadata["distance_cm"] for e in exports] == [5.0, 20.0]
    assert [tab.session_file_name(e, i) for i, e in enumerate(exports)] == [
        "p5.0cm_m01",
        "p20.0cm_m02",
    ]
    assert [e.metadata["measurement_index"] for e in exports] == [1, 2]
    assert tab.has_unsaved_data()


def test_the_last_point_cannot_be_removed():
    tab = _tab_with_points(5.0)
    assert not tab.remove_point(0)
    assert not tab.remove_point(7)
    assert len(tab._measurements) == 1


def test_delete_asks_first_and_explains_the_last_point():
    class FakePrompt:
        def __init__(self):
            self.answer, self.asked, self.infos = False, 0, 0

        def ask(self, text, title):
            self.asked += 1
            return self.answer

        def info(self, text, title):
            self.infos += 1

    tab = _tab_with_points(5.0, 15.0)
    tab._prompt = prompt = FakePrompt()
    tab.ui.tableSummary.setCurrentIndex(tab._table_model.index(1, 0))

    tab._delete_selected_point()
    assert prompt.asked == 1 and len(tab._measurements) == 2  # declined

    prompt.answer = True
    tab._delete_selected_point()
    assert len(tab._measurements) == 1

    tab._delete_selected_point()  # only one left: explained, not asked
    assert prompt.infos == 1 and prompt.asked == 2


def test_the_plot_shows_rates_with_poisson_errors(monkeypatch):
    tab = _tab_with_points(5.0, 15.0)
    tab._measurements[0].update(count=400, rate_hz=8.0, duration_s=50.0)
    seen = {}
    monkeypatch.setattr(
        tab._plot,
        "set_summary_points",
        lambda points, errors=None, log=False: seen.update(
            points=points, errors=errors, log=log
        ),
    )
    tab._refresh_plot()

    assert seen["points"][0] == (5.0, 8.0)  # rate, not the count
    assert seen["errors"][0] == pytest.approx(0.4)  # sqrt(400) / 50 s
    assert seen["log"] is False


def test_the_log_switch_exists_only_where_a_power_law_is_expected():
    from gmcounter.ui.tabs.distance_law_tab import DistanceLawTab

    plain = _make_tab()
    plain.show()
    assert not plain.ui.checkLogAxes.isVisible()

    distance = DistanceLawTab(AppContext(config=default_config()))
    distance.show()
    assert distance.ui.checkLogAxes.isVisible()
    distance.build()
    distance.ui.checkLogAxes.setChecked(True)  # re-plots; must not fail without data


def test_the_table_shows_clock_time_and_fixed_decimals():
    tab = _tab_with_points(5.0)
    entry = tab._measurements[0]
    entry.update(rate_hz=46.21, duration_s=10.5, start="2026-11-15T17:46:20.841896")
    tab._table_model.removeRows(0, 1)
    tab._append_table_row(entry)

    cells = [tab._table_model.item(0, c).text() for c in range(5)]
    assert cells[2:] == ["46.210", "10.50", "17:46:20"]
    assert tab._table_model.item(0, 4).toolTip() == "2026-11-15T17:46:20.841896"


def test_the_distance_input_and_table_have_two_decimals():
    from gmcounter.ui.tabs.distance_law_tab import DistanceLawTab

    tab = _tab_with_points(6.75, tab_cls=DistanceLawTab)
    assert tab.ui.spinParam.decimals() == 2
    assert tab._table_model.item(0, 0).text() == "6.75"
    assert tab.set_point_param(0, 7.126)  # rounded to the input's two decimals
    assert tab._measurements[0]["param"] == 7.13
