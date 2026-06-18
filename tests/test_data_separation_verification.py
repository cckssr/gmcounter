#!/usr/bin/env python3
"""Verify that data_points is unbounded (for export) while gui_data_points is limited."""

import pytest
import sys

pytest.importorskip(
    "PySide6", reason="DataController is a QObject and requires PySide6"
)

from PySide6.QtWidgets import QApplication
from gmcounter.ui.controllers.data_controller import DataController

_app = QApplication.instance() or QApplication(sys.argv)


class MockPlotWidget:
    def update_plot_data(self, points, **kwargs):
        pass

    def clear_measurement_data(self):
        pass

    def clear(self):
        pass


def test_data_separation():
    """Full data_points are unlimited; gui_data_points respect max_history."""
    controller = DataController(plot_widget=MockPlotWidget(), max_history=3)

    for i in range(10):
        controller.add_data_point(i, float(i * 10))

    full_data = controller.get_all_data_for_export()
    data_info = controller.get_data_info()
    csv_data = controller.get_csv_data()

    assert len(full_data) == 10, (
        f"Full data should have 10 points, got {len(full_data)}"
    )
    assert data_info["gui_data_points"] == 3, (
        f"GUI data should be limited to 3, got {data_info['gui_data_points']}"
    )
    assert len(csv_data) == 11, (
        f"CSV should have 11 rows (header + 10 data), got {len(csv_data)}"
    )

    # Verify point structure (index, value, timestamp)
    for point in full_data:
        assert len(point) == 3, (
            f"Each point should be (index, value, timestamp), got {point}"
        )

    controller.stop_gui_updates()
