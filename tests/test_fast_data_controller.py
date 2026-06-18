#!/usr/bin/env python3
"""Test for DataController fast-queue functionality.

NOTE: This test exercises real threading and Qt timer behavior which requires
a running Qt event loop. It is kept for manual / integration runs only.
"""

import pytest

pytest.importorskip("PySide6", reason="DataController requires PySide6")

pytestmark = pytest.mark.skip(
    reason=(
        "DataController fast-queue tests rely on real threading + Qt event loop. "
        "Run manually with QT_QPA_PLATFORM=offscreen if needed."
    )
)

import sys
import time
import threading
from pathlib import Path

from gmcounter.ui.controllers.data_controller import DataController
from gmcounter.infrastructure.logging import Debug


def test_fast_data_processing():
    """DataController handles high-frequency data via add_data_point_fast."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)

    class MockPlotWidget:
        def __init__(self):
            self.points = []

        def update_plot_data(self, points, **kwargs):
            self.points = list(points)

        def clear_measurement_data(self):
            self.points = []

        def clear(self):
            self.points = []

    plot_widget = MockPlotWidget()
    controller = DataController(plot_widget=plot_widget, gui_update_interval=100)

    def generate_fast_data():
        for i in range(100):
            controller.add_data_point_fast(i, 1000 + i * 10)
            time.sleep(0.01)

    data_thread = threading.Thread(target=generate_fast_data)
    data_thread.start()
    data_thread.join()
    time.sleep(0.2)

    perf_stats = controller.get_performance_stats()
    stats = controller.get_statistics()

    assert perf_stats["total_points_received"] > 0
    assert stats["count"] > 0

    controller.stop_gui_updates()
