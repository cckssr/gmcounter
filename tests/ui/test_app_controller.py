"""Tests for ui.controllers.app_controller.AppController — signal contract + lifecycle."""

import sys
import pytest

pytest.importorskip("PySide6", reason="AppController requires PySide6")

from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal

from gmcounter.ui.controllers.app_controller import AppController
from gmcounter.infrastructure.device_manager import DeviceManager
from gmcounter.core.services import MeasurementStateService

_app = QApplication.instance() or QApplication(sys.argv)


def _make_controller():
    """Build an AppController with a minimal mock DeviceManager."""
    dm = MagicMock(spec=DeviceManager)
    dm.connected = False
    dm.device = None
    dm.measurement_state = MeasurementStateService()
    status_bar = MagicMock()
    status_bar.show_info = MagicMock()
    status_bar.show_warning = MagicMock()
    status_bar.show_error = MagicMock()
    with (
        patch("gmcounter.ui.controllers.app_controller.DataAcquisitionThread"),
        patch("gmcounter.ui.controllers.app_controller.StatePollerThread"),
        patch(
            "gmcounter.ui.controllers.app_controller.find_orphan_journals",
            return_value=[],
        ),
    ):
        ctrl = AppController(dm, status_bar=status_bar)
    return ctrl


def test_app_controller_has_required_signals():
    ctrl = _make_controller()
    expected_signals = [
        "frames_ready",
        "statistics_updated",
        "device_state_updated",
        "measurement_started",
        "measurement_stopped",
        "status_message",
        "retry_connecting",
        "reconnect_succeeded",
        "connection_lost",
        "high_speed_mode_changed",
        "progress_updated",
    ]
    for name in expected_signals:
        assert hasattr(ctrl, name), f"AppController is missing signal: {name}"
    ctrl.cleanup()


def test_app_controller_cleanup_does_not_raise():
    ctrl = _make_controller()
    ctrl.cleanup()  # must not raise


def test_app_controller_set_active_tab():
    ctrl = _make_controller()
    mock_tab = MagicMock()
    ctrl.set_active_tab(mock_tab)
    assert ctrl._active_tab is mock_tab
    ctrl.cleanup()


def _measuring_controller(target_s: int, confirmed: bool = True):
    ctrl = _make_controller()
    ctrl.device_manager.connected = True
    ctrl.device_manager.stop_measurement.return_value = confirmed
    ctrl.device_manager.start_measurement.return_value = True
    ctrl.device_manager.device = MagicMock()
    assert ctrl.start_measurement(total_seconds=target_s)
    return ctrl


def test_reaching_the_target_stops_with_the_device_time_as_result():
    ctrl = _measuring_controller(target_s=1)
    results: list[dict] = []
    ctrl.run_finished.connect(results.append)

    ctrl._on_data_batch([(0, 600_000.0), (1, 600_000.0)])  # crosses 1 s

    (result,) = results
    assert result["stop_reason"] == "target_reached"
    assert result["target_s"] == 1.0
    assert result["device_time_s"] == 1.0  # the crossing event is cut off
    assert result["wall_time_s"] >= 0.0
    assert result["stop_confirmed"] is True
    ctrl.cleanup()


def test_a_manual_stop_reports_the_accumulated_device_time():
    ctrl = _measuring_controller(target_s=0)
    results: list[dict] = []
    ctrl.run_finished.connect(results.append)

    ctrl._on_data_batch([(0, 250_000.0), (1, 250_000.0)])
    ctrl.stop_measurement()

    assert results[0]["stop_reason"] == "manual"
    assert results[0]["device_time_s"] == 0.5
    ctrl.cleanup()


def test_an_unconfirmed_stop_is_reported_to_the_user():
    ctrl = _measuring_controller(target_s=0, confirmed=False)
    results: list[dict] = []
    ctrl.run_finished.connect(results.append)
    shown: list[str] = []
    ctrl._notify = lambda text, color="": shown.append(text)

    ctrl.stop_measurement()

    assert results[0]["stop_confirmed"] is False
    assert any("nicht bestätigt" in text for text in shown)
    ctrl.cleanup()


def test_timing_is_published_every_tick():
    ctrl = _measuring_controller(target_s=10)
    ticks: list[tuple] = []
    ctrl.timing_updated.connect(lambda *args: ticks.append(args))

    ctrl._on_data_batch([(0, 2_500_000.0)])
    ctrl._tick_progress()

    device_s, wall_s, target_s = ticks[-1]
    assert (device_s, target_s) == (2.5, 10.0)
    assert wall_s >= 0.0
    ctrl.cleanup()
