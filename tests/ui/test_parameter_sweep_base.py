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
