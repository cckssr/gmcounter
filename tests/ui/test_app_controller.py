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
