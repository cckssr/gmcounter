"""Tests for core.services.SaveState (unsaved-flag + base_dir tracking)."""

import pytest
from pathlib import Path

from gmcounter.core.services import SaveState


def test_initial_state_is_saved(tmp_path):
    state = SaveState(base_dir=tmp_path)
    assert not state.has_unsaved()


def test_mark_unsaved_sets_flag(tmp_path):
    state = SaveState(base_dir=tmp_path)
    state.mark_unsaved()
    assert state.has_unsaved()


def test_mark_saved_clears_flag(tmp_path):
    state = SaveState(base_dir=tmp_path)
    state.mark_unsaved()
    state.mark_saved()
    assert not state.has_unsaved()


def test_base_dir_resolved_from_string(tmp_path):
    # When base_dir is a relative string, it should be resolved under ~/Documents.
    state = SaveState(base_dir="GMCounterTest")
    expected = Path.home() / "Documents" / "GMCounterTest"
    assert state.base_dir == expected


def test_base_dir_absolute_path(tmp_path):
    state = SaveState(base_dir=tmp_path)
    assert state.base_dir == tmp_path


def test_base_dir_created_if_missing(tmp_path):
    new_dir = tmp_path / "subdir" / "data"
    state = SaveState(base_dir=new_dir)
    assert state.base_dir.exists()


def test_measurement_state_service():
    from gmcounter.core.services import MeasurementStateService

    svc = MeasurementStateService()
    assert not svc.measurement_active
    svc.start_measurement()
    assert svc.measurement_active
    svc.stop_measurement()
    assert not svc.measurement_active
    svc.start_measurement()
    svc.reset()
    assert not svc.measurement_active
