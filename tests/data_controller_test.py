import sys
import unittest
import pytest

pytest.importorskip(
    "PySide6", reason="DataController is a QObject and requires PySide6"
)

from PySide6.QtWidgets import QApplication
from gmcounter.ui.controllers.data_controller import DataController

_app = QApplication.instance() or QApplication(sys.argv)


class DummyLCD:
    def __init__(self):
        self.value = None

    def display(self, value):
        self.value = value


class DummyPlot:
    def __init__(self):
        self.data = []

    def update_plot_data(self, points, **kwargs):
        self.data = list(points)

    def clear_measurement_data(self):
        self.data.clear()

    def clear(self):
        self.data.clear()


class DataControllerTests(unittest.TestCase):
    def setUp(self):
        self.lcd = DummyLCD()
        self.plot = DummyPlot()
        self.ctrl = DataController(
            plot_widget=self.plot,
            display_widget=self.lcd,
            histogram_widget=None,
            table_widget=None,
            max_history=3,
        )

    def tearDown(self):
        self.ctrl.stop_gui_updates()

    def test_get_statistics(self):
        self.ctrl.add_data_point(1, 1)
        self.ctrl.add_data_point(2, 3)
        stats = self.ctrl.get_statistics()
        self.assertEqual(stats["count"], 2.0)
        self.assertEqual(stats["min"], 1.0)
        self.assertEqual(stats["max"], 3.0)
        self.assertAlmostEqual(stats["avg"], 2.0)

    def test_get_csv_data(self):
        self.ctrl.add_data_point(1, 2)
        csv_data = self.ctrl.get_csv_data()
        self.assertEqual(csv_data[0], ["Index", "Value (µs)", "Time"])
        self.assertEqual(csv_data[1][0], "1")
        self.assertEqual(csv_data[1][1], "2.0")

    def test_clear_data_resets_points(self):
        self.ctrl.add_data_point(1, 1.0)
        self.ctrl.clear_data()
        self.assertEqual(len(self.ctrl.data_points), 0)
        self.assertEqual(len(self.ctrl.gui_data_points), 0)

    def test_history_limit(self):
        for i in range(5):
            self.ctrl.add_data_point(i, i * 0.1)
        # data_points is unbounded; gui_data_points is limited to max_history
        self.assertEqual(len(self.ctrl.data_points), 5)
        self.assertEqual(len(self.ctrl.gui_data_points), 3)

    def test_add_data_point_fast_queues_and_stores(self):
        """add_data_point_fast immediately appends to data_points and enqueues for GUI."""
        for i in range(3):
            self.ctrl.add_data_point_fast(i, float(i * 0.1))

        # data_points is populated immediately by add_data_point_fast
        self.assertEqual(len(self.ctrl.data_points), 3)
        # Queue holds the same points for deferred GUI update
        self.assertEqual(self.ctrl.data_queue.qsize(), 3)
        # Verify stored values (index, value, timestamp)
        self.assertEqual(self.ctrl.data_points[0][0], 0)
        self.assertAlmostEqual(self.ctrl.data_points[0][1], 0.0)
        self.assertEqual(self.ctrl.data_points[2][0], 2)
        self.assertAlmostEqual(self.ctrl.data_points[2][1], 0.2)


if __name__ == "__main__":
    unittest.main()
