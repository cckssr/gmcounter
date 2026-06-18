#!/usr/bin/env python3
"""Integration test: DataController clears and restarts correctly between measurements."""

import pytest
import sys

pytest.importorskip(
    "PySide6", reason="DataController is a QObject and requires PySide6"
)

from PySide6.QtWidgets import QApplication
from gmcounter.ui.controllers.data_controller import DataController

_app = QApplication.instance() or QApplication(sys.argv)


class MockPlotWidget:
    def __init__(self):
        self.cleared = False
        self.points = []

    def update_plot_data(self, points, **kwargs):
        self.points = list(points)

    def clear_measurement_data(self):
        self.cleared = True
        self.points = []

    def clear(self):
        self.cleared = True
        self.points = []


def test_complete_plot_reset():
    """DataController correctly resets all data between measurements."""
    plot_widget = MockPlotWidget()
    controller = DataController(plot_widget=plot_widget, max_history=5)

    # First measurement: 8 points
    for i in range(8):
        controller.add_data_point(i, float(i * 10))

    full_data_1 = controller.get_all_data_for_export()
    data_info_1 = controller.get_data_info()

    assert len(full_data_1) == 8, (
        f"Full data should have 8 points, got {len(full_data_1)}"
    )
    assert data_info_1["gui_data_points"] == 5, (
        f"GUI data should be limited to 5, got {data_info_1['gui_data_points']}"
    )

    # Start new measurement
    controller.clear_data()
    plot_widget.cleared = False  # reset flag set by clear_data

    full_data_2 = controller.get_all_data_for_export()
    data_info_2 = controller.get_data_info()

    assert len(full_data_2) == 0, "Full data should be empty after clear"
    assert data_info_2["gui_data_points"] == 0, "GUI data should be 0 after clear"

    # Second measurement: 3 points starting at index 0
    for i in range(3):
        controller.add_data_point(i, float(i * 20))

    full_data_3 = controller.get_all_data_for_export()
    data_info_3 = controller.get_data_info()

    assert len(full_data_3) == 3, (
        f"New measurement should have 3 points, got {len(full_data_3)}"
    )
    assert data_info_3["gui_data_points"] == 3
    assert full_data_3[0][0] == 0, f"First index should be 0, got {full_data_3[0][0]}"
    assert full_data_3[1][0] == 1
    assert full_data_3[2][0] == 2

    controller.stop_gui_updates()
