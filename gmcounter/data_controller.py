#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data controller for managing measurements and plot updates."""

from typing import Optional, List, Tuple, Dict, Union
import queue
import threading
from time import time
from datetime import datetime

try:  # pragma: no cover - optional dependency for headless testing
    from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
        QLCDNumber,
        QTableView,
        QLineEdit,
    )  # type: ignore
    from PySide6.QtGui import (  # pylint: disable=no-name-in-module
        QStandardItemModel,
        QStandardItem,
    )
    from PySide6.QtCore import Qt, QTimer  # pylint: disable=no-name-in-module


except Exception:  # ImportError or missing Qt libraries

    class QLCDNumber:  # pragma: no cover - fallback stub
        def display(self, *args, **kwargs):
            pass

    class QListWidget:  # pragma: no cover - fallback stub
        def insertItem(self, *args, **kwargs):
            pass

        def item(self, *args, **kwargs):
            class _Item:
                def setTextAlignment(self, *a, **k):
                    pass

            return _Item()

        def count(self) -> int:
            return 0

        def takeItem(self, *args, **kwargs):
            pass

        def clear(self):
            pass

    class QTableView:  # pragma: no cover - fallback stub
        def setModel(self, *args, **kwargs):
            pass

    class QStandardItemModel:  # pragma: no cover - fallback stub
        def __init__(self, *args, **kwargs):
            pass

        def setHorizontalHeaderLabels(self, *args, **kwargs):
            pass

        def appendRow(self, *args, **kwargs):
            pass

        def rowCount(self):
            return 0

        def removeRow(self, *args, **kwargs):
            pass

    class _Alignment:
        AlignRight = 0

    class _Qt:
        AlignmentFlag = _Alignment

    class QTimer:  # pragma: no cover - fallback stub
        def __init__(self):
            self.timeout = self._MockSignal()

        def start(self, interval):
            pass

        def stop(self):
            pass

        class _MockSignal:
            def connect(self, callback):
                pass

    Qt = _Qt()

from .plot import PlotWidget, HistogramWidget
from .debug_utils import Debug
from .helper_classes import (
    import_config,
    SaveManager,
    create_dropbox_foldername,
    sanitize_subterm_for_folder,
    MessageHelper,
)

# Configuration constants
CONFIG = import_config()
MAX_HISTORY_SIZE = CONFIG["data_controller"]["max_history_size"]
UPDATE_INTERVAL = CONFIG["timers"]["gui_update_interval"]


class DataController:
    """Store measurement data and provide statistics for the UI."""

    def __init__(
        self,
        plot_widget: PlotWidget,
        display_widget: Optional[QLCDNumber] = None,
        histogram_widget: Optional[HistogramWidget] = None,
        stat_display: Optional[List[QLineEdit]] = None,
        table_widget: Optional[QTableView] = None,
        max_history: int = MAX_HISTORY_SIZE,
        gui_update_interval: int = UPDATE_INTERVAL,
    ):
        """Initialise the data controller.

        Args:
            plot_widget: Plotting widget used for visualisation.
            display_widget: Optional LCD display for the current value.
            histogram_widget: Optional histogram widget for data distribution.
            stat_display: Optional list of QLineEdit widgets for statistics display.
                [count, min, max, avg, standardDeviation]
            table_widget: Optional table widget for data display.
            max_history: Maximum number of data points for GUI display (not file storage).
        """
        self.plot = plot_widget
        self.display = display_widget
        self.histogram = histogram_widget
        self.stat_display = stat_display
        self.table = table_widget
        self.table_model: Optional[QStandardItemModel] = None
        self.max_history = max_history

        # Full data storage (for CSV export, etc.)
        self.data_points: List[Tuple[int, float, str]] = []

        # GUI-limited data (for plot and histogram widget)
        self.gui_data_points: List[Tuple[int, float, str]] = []
        self.max_history = max_history

        # Queue for high-frequency data acquisition
        self.data_queue: queue.Queue = queue.Queue()
        self._queue_lock = threading.Lock()
        self._last_update_time = time()

        # Timer for GUI updates
        try:
            self.gui_update_timer = QTimer()
            if hasattr(self.gui_update_timer.timeout, "connect"):
                self.gui_update_timer.timeout.connect(self._process_queued_data)
                self.gui_update_timer.start(gui_update_interval)
            else:
                self.gui_update_timer = None
        except Exception as e:
            # Fallback for headless testing
            self.gui_update_timer = None
            Debug.error("GUI update timer not available", e)

        # Performance counters
        self._total_points_received = 0
        self._points_processed_in_last_update = 0

        if self.table is not None:
            self.table_model = QStandardItemModel(0, 3, self.table)
            self.table_model.setHorizontalHeaderLabels(["Index", "Value (µs)", "Time"])
            self.table.setModel(self.table_model)

    def add_data_point_fast(
        self, index: Union[int, str], value: Union[float, str]
    ) -> None:
        """Quickly enqueue data points without immediate GUI update.

        This method is optimised for high-frequency acquisition and updates
        does not update the GUI immediately. Instead the data are enqueued
        and processed every 100ms.

        Args:
            index: The data point index
            value: The measured value
        """
        try:
            # Fast validation and conversion
            index_num = int(index)
            value_num = float(value)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Vollständige Daten sofort hinzufügen (für CSV-Export, unbegrenzt)
            self.data_points.append((index_num, value_num, timestamp))

            # Thread-safe enqueue
            with self._queue_lock:
                self.data_queue.put((index_num, value_num, timestamp))
                self._total_points_received += 1

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values for fast queue: {e}")

    def _process_queued_data(self) -> None:
        """Process all queued data points and update the GUI."""
        if self.data_queue.empty():
            return

        new_points = []
        current_time = time()

        try:
            # Retrieve all available data points from the queue
            with self._queue_lock:
                while not self.data_queue.empty():
                    try:
                        index_num, value_num, timestamp = self.data_queue.get_nowait()
                        new_points.append((index_num, value_num, timestamp))
                    except queue.Empty:
                        break

            if not new_points:
                return

            self._points_processed_in_last_update = len(new_points)

            # Add all new points to the full data set (for CSV export)
            for index_num, value_num, timestamp in new_points:
                self.data_points.append((index_num, value_num, timestamp))

            # Add all new points to GUI data as well (with limit)
            for index_num, value_num, timestamp in new_points:
                self.gui_data_points.append((index_num, value_num, timestamp))

            # Only limit GUI data; full data remain unlimited
            while len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # Update GUI only once with the last value
            if new_points:
                last_index, last_value, last_timestamp = new_points[-1]
                self._update_gui_widgets(last_index, last_value, last_timestamp)

            # Performance logging
            time_since_last = current_time - self._last_update_time
            if time_since_last > 0:
                rate = len(new_points) / time_since_last
                Debug.debug(
                    f"Processed {len(new_points)} points in {time_since_last:.3f}s "
                    f"(rate: {rate:.1f} Hz, total: {self._total_points_received})"
                )

            self._last_update_time = current_time

        except Exception as e:
            Debug.error(f"Error processing queued data: {e}", exc_info=True)

    def _update_gui_widgets(
        self, index: int, value: float, timestamp: Optional[str] = None
    ) -> None:
        """Update plot, LCD and history list with a single data point."""
        try:
            # Update plot widget with all current data points
            if self.plot and len(self.gui_data_points) > 0:
                # Use the efficient batch update method when available
                if hasattr(self.plot, "update_plot_batch"):
                    self.plot.update_plot_batch(self.gui_data_points)
                else:
                    # Fallback - use the standard update_plot method with all data
                    self.plot.update_plot(self.gui_data_points)

            # Update current value display with the last value
            if self.display:
                self.display.display(value)

            # Update histogram with current data distribution
            if self.histogram and len(self.gui_data_points) > 1:
                # Extract values for histogram (only the measurement values)
                values = [point[1] for point in self.gui_data_points]
                self.histogram.update_histogram(values)

            # Update table model with new data
            if self.table_model is not None:
                try:
                    # Use timestamp if provided, otherwise create current timestamp
                    if timestamp is None:
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    row = [
                        QStandardItem(str(index)),
                        QStandardItem(str(value)),
                        QStandardItem(timestamp),
                    ]
                    self.table_model.appendRow(row)
                    while self.table_model.rowCount() > self.max_history:
                        self.table_model.removeRow(0)
                except Exception as table_error:
                    Debug.error(
                        f"Failed to update table model: {table_error}", exc_info=True
                    )

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update GUI widgets: {e}", exc_info=True)

    def add_data_point(self, index: Union[int, str], value: Union[float, str]) -> None:
        """Add a point and update optional widgets.

        Note: ``add_data_point_fast`` should be used for high frequency data
        acquisition, this method is kept for compatibility.
        """

        # Ensure numeric values
        try:
            # Ensure values are numeric
            index_num = int(index)
            value_num = float(value)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Add data to full storage (unbounded for file saving)
            self.data_points.append((index_num, value_num, timestamp))

            # Add data to GUI storage (bounded for display)
            self.gui_data_points.append((index_num, value_num, timestamp))
            if len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # Update GUI widgets directly
            self._update_gui_widgets(index_num, value_num, timestamp)

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update UI elements: {e}", exc_info=True)

    def stop_gui_updates(self) -> None:
        """Stop the GUI update timer."""
        if hasattr(self, "gui_update_timer") and self.gui_update_timer is not None:
            try:
                self.gui_update_timer.stop()
                Debug.debug("GUI update timer stopped")
            except Exception as e:
                Debug.debug(f"Error stopping GUI timer: {e}")

    def start_gui_updates(self, interval: int = 100) -> None:
        """Start the GUI update timer."""
        if hasattr(self, "gui_update_timer") and self.gui_update_timer is not None:
            try:
                self.gui_update_timer.start(interval)
                Debug.debug(f"GUI update timer started with {interval}ms interval")
            except Exception as e:
                Debug.debug(f"Error starting GUI timer: {e}")

    def clear_data(self) -> None:
        """Clear all data points and reset optional widgets."""
        try:
            # Remove stored points (both full and GUI data)
            self.data_points = []
            self.gui_data_points = []

            # Clear the queue
            with self._queue_lock:
                while not self.data_queue.empty():
                    try:
                        self.data_queue.get_nowait()
                    except queue.Empty:
                        break

            # Reset counters
            self._total_points_received = 0
            self._points_processed_in_last_update = 0
            self._last_update_time = time()

            # Clear the plot
            if self.plot:
                self.plot.clear()

            # Reset displayed value
            if self.display:
                self.display.display(0)

            # Clear the histogram
            if self.histogram:
                self.histogram.clear()

            if self.stat_display:
                for display in self.stat_display:
                    display.clear()

            # Clear the table model
            if self.table_model is not None:
                try:
                    while self.table_model.rowCount() > 0:
                        self.table_model.removeRow(0)
                except Exception as table_error:
                    Debug.error(
                        f"Failed to clear table model: {table_error}", exc_info=True
                    )

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to reset UI elements: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, float]:
        """Return basic statistics for the stored data."""
        # Initialise statistics with defaults
        stats: Dict[str, float] = {
            "count": float(len(self.data_points)),
            "min": 0.0,
            "max": 0.0,
            "avg": 0.0,
            "stdev": 0.0,
        }

        if self.data_points:
            try:
                # Werte extrahieren (zweites Element jedes Tupels)
                values = [float(point[1]) for point in self.data_points]

                # Calculate basic statistics
                stats["min"] = min(values)
                stats["max"] = max(values)
                stats["avg"] = sum(values) / len(values)

                # Calculate standard deviation (if more than one value available)
                if len(values) > 1:
                    mean = stats["avg"]
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    stats["stdev"] = variance**0.5

            except (ValueError, TypeError) as e:
                Debug.error(f"Value conversion error: {e}", exc_info=True)
            except (ZeroDivisionError, OverflowError) as e:
                Debug.error(
                    f"Statistical calculation error: {e}",
                    exc_info=True,
                )
        if self.stat_display:
            for i, number in enumerate(stats.values()):
                self.stat_display[i].setText(f"{number:,.0f}")

        return stats

    def get_data_as_list(self) -> List[Tuple[int, float, str]]:
        """Return all stored data points as a list."""
        return self.data_points.copy()

    def get_csv_data(self) -> List[List[str]]:
        """Prepare the stored data for CSV export."""
        result: List[List[str]] = [["Index", "Value (µs)", "Time"]]
        for idx, value, timestamp in self.data_points:
            result.append([str(idx), str(value), timestamp])
        return result

    def get_performance_stats(self) -> Dict[str, Union[int, float]]:
        """Return performance statistics for data acquisition."""
        queue_size = 0
        with self._queue_lock:
            queue_size = self.data_queue.qsize()

        return {
            "total_points_received": self._total_points_received,
            "points_in_last_update": self._points_processed_in_last_update,
            "queue_size": queue_size,
            "stored_points": len(self.data_points),
            "last_update_time": self._last_update_time,
        }

    def get_data_info(self) -> dict:
        """Return information about the stored data."""
        return {
            "total_data_points": len(self.data_points),
            "gui_data_points": len(self.gui_data_points),
            "max_history_limit": self.max_history,
            "data_points_for_export": self.data_points,  # Full data for CSV export
            "gui_points_for_display": self.gui_data_points,  # Limited data for GUI
        }

    def get_all_data_for_export(self) -> List[Tuple[int, float, str]]:
        """Return all collected data points without cropping.

        Return:
          List[Tuple[int, float]]: All datapoints with timestamp
        """
        return self.data_points.copy()

    # ============= Integrated SaveManager Methods =============

    def init_save_manager(self, base_dir: Optional[str] = None) -> None:
        """Initialize the integrated SaveManager.

        Args:
            base_dir: Base directory for saving files. If None, uses default from CONFIG.
        """
        if base_dir is None:
            base_dir = CONFIG.get("data_controller", {}).get(
                "default_save_dir", "GMCounter"
            )
        self.save_manager = SaveManager(base_dir=base_dir)
        self.measurement_start: Optional[datetime] = None
        self.measurement_end: Optional[datetime] = None
        Debug.info(f"SaveManager initialized with base_dir: {base_dir}")

    def save_measurement_auto(
        self,
        rad_sample: str,
        group_letter: str,
        subterm: str = "",
        suffix: str = "",
    ) -> Optional[str]:
        """Auto-save measurement with current data.

        Args:
            rad_sample: Radioactive sample name
            group_letter: Group identifier
            subterm: Subgroup term for folder structure
            suffix: Optional suffix for filename

        Returns:
            Path to saved file or None if failed
        """
        if not hasattr(self, "save_manager"):
            self.init_save_manager()

        if not self.save_manager.auto_save or self.save_manager.last_saved:
            return None

        data = self.get_csv_data()

        saved_path = self.save_manager.auto_save_measurement(
            rad_sample,
            group_letter,
            data,
            self.measurement_start or datetime.now(),
            self.measurement_end or datetime.now(),
            subterm,
            suffix,
        )

        return str(saved_path) if saved_path else None

    def save_measurement_manual(
        self,
        parent,
        rad_sample: str,
        group_letter: str,
        subterm: str = "",
    ) -> Optional[str]:
        """Manually save measurement via file dialog.

        Args:
            parent: Parent widget for dialog
            rad_sample: Radioactive sample name
            group_letter: Group identifier
            subterm: Subgroup term for folder structure

        Returns:
            Path to saved file or None if cancelled/failed
        """
        if not hasattr(self, "save_manager"):
            self.init_save_manager()

        data = self.get_csv_data()

        if not data or len(data) <= 1:  # Only header row
            MessageHelper.warning(
                parent,
                CONFIG.get("messages", {}).get(
                    "no_data_to_save", "Keine Messdaten zum Speichern vorhanden."
                ),
                "Warnung",
            )
            return None

        if not rad_sample or not group_letter:
            MessageHelper.warning(
                parent,
                CONFIG.get("messages", {}).get(
                    "select_sample_and_group",
                    "Bitte wählen Sie eine radioaktive Probe und eine Gruppenzuordnung aus.",
                ),
                "Warnung",
            )
            return None

        saved_path = self.save_manager.manual_save_measurement(
            parent,
            rad_sample,
            group_letter,
            data,
            self.measurement_start or datetime.now(),
            self.measurement_end or datetime.now(),
            subterm,
        )

        return str(saved_path) if saved_path else None

    def has_unsaved_data(self) -> bool:
        """Check if there is unsaved measurement data."""
        if not hasattr(self, "save_manager"):
            return len(self.data_points) > 0
        return self.save_manager.has_unsaved()

    def mark_data_unsaved(self) -> None:
        """Mark current data as unsaved."""
        if not hasattr(self, "save_manager"):
            self.init_save_manager()
        self.save_manager.mark_unsaved()

    def mark_data_saved(self) -> None:
        """Mark current data as saved."""
        if hasattr(self, "save_manager"):
            self.save_manager.last_saved = True

    def set_auto_save(self, enabled: bool) -> None:
        """Enable or disable auto-save."""
        if not hasattr(self, "save_manager"):
            self.init_save_manager()
        self.save_manager.auto_save = enabled

    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        if not hasattr(self, "save_manager"):
            return False
        return self.save_manager.auto_save

    def set_measurement_times(self, start: datetime, end: datetime) -> None:
        """Set measurement start and end times."""
        self.measurement_start = start
        self.measurement_end = end
