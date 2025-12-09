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
    from PySide6.QtCore import (
        QTimer,
        QObject,
        Signal,
    )  # pylint: disable=no-name-in-module


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

from ..widgets.plot import PlotWidget, HistogramWidget
from ...infrastructure.logging import Debug
from ...infrastructure.config import import_config
from ...helper_classes_compat import (
    SaveManager,
)
from ..common import dialogs as MessageHelper

# Configuration constants
CONFIG = import_config()
MAX_HISTORY_SIZE = CONFIG["data_controller"]["max_history_size"]
# Increase GUI update interval to reduce load at high frequencies
# 500ms = 2 updates/sec is sufficient for visual feedback at high data rates
UPDATE_INTERVAL = max(500, CONFIG["timers"]["gui_update_interval"])

# HIGH_SPEED_MODE: Batch-based detection parameters from config
HIGH_SPEED_BATCH_THRESHOLD = CONFIG["data_controller"]["high_speed_mode"][
    "batch_threshold"
]
HIGH_SPEED_BATCH_HISTORY = CONFIG["data_controller"]["high_speed_mode"]["batch_history"]


class DataController(QObject):
    """Store measurement data and provide statistics for the UI."""

    # Signal emitted when HIGH_SPEED_MODE is activated/deactivated
    high_speed_mode_changed = Signal(bool)  # True = activated, False = deactivated

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
        super().__init__()
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
        # Max size: at 10kHz with 200ms updates = 2000 points max per batch
        # Use 10000 as safety buffer (= 1 second at 10kHz)
        self.data_queue: queue.Queue = queue.Queue(maxsize=10000)
        self._queue_lock = threading.Lock()
        self._last_update_time = time()
        self._last_table_update = time()  # Separate timer for table updates
        self._queue_overflow_warned = False  # Track if we warned about overflow

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

        # HIGH_SPEED_MODE: Batch-based detection
        self._high_speed_mode = False
        self._batch_history: List[Tuple[float, int]] = (
            []
        )  # List of (timestamp, batch_size)
        self._histogram_update_timer = (
            None  # Separate timer for histogram in high-speed mode
        )

        if self.table is not None:
            self.table_model = QStandardItemModel(0, 3, self.table)
            self.table_model.setHorizontalHeaderLabels(["Index", "Value (µs)", "Time"])
            self.table.setModel(self.table_model)

    def add_data_point_fast(
        self, index: Union[int, str], value: Union[float, str]
    ) -> None:
        """Quickly enqueue data points without immediate GUI update.

        This method is optimised for high-frequency acquisition (up to 10kHz).
        It performs minimal work in the caller's thread (acquisition thread):
        - Fast type conversion
        - Thread-safe enqueue to buffer
        - NO GUI operations

        The actual GUI updates happen in _process_queued_data() which runs
        in the main GUI thread every 200ms.

        Args:
            index: The data point index
            value: The measured value
        """
        try:
            # Fast validation and conversion - optimized for speed
            index_num = int(index)
            value_num = float(value)
            # Timestamp generation is relatively expensive but necessary
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Add to full dataset immediately (unbounded, for CSV export)
            # This MUST be fast and thread-safe
            self.data_points.append((index_num, value_num, timestamp))

            # Debug first few points to verify data flow
            if len(self.data_points) <= 3:
                Debug.info(
                    f"add_data_point_fast: point #{index_num} added, total={len(self.data_points)}"
                )

            # HIGH_SPEED_MODE detection is now done in _process_queued_data()
            # based on batch processing rate, not individual point timing

            # Thread-safe enqueue with overflow protection
            # Use put_nowait() to avoid blocking the acquisition thread
            try:
                with self._queue_lock:
                    self.data_queue.put_nowait((index_num, value_num, timestamp))
                    self._total_points_received += 1
                    self._queue_overflow_warned = False  # Reset warning flag
            except queue.Full:
                # Queue is full - GUI is not processing fast enough
                # This should rarely happen with proper GUI update intervals
                if not self._queue_overflow_warned:
                    Debug.warning(
                        "Data queue overflow! GUI cannot keep up with acquisition rate. "
                        "Some GUI updates may be skipped (data is still saved to file)."
                    )
                    self._queue_overflow_warned = True
                # Continue without blocking - data is already in data_points

        except (ValueError, TypeError) as e:
            Debug.error(f"Failed to convert values for fast queue: {e}")

    def _activate_high_speed_mode(self) -> None:
        """Activate HIGH_SPEED_MODE for optimal performance at high data rates.

        In this mode:
        - Plot updates are disabled
        - Table updates are disabled
        - Only histogram updates every 2 seconds (in separate timer)
        - GUI remains responsive with progress updates
        - Mode stays active until measurement ends (clear_data)
        """
        if self._high_speed_mode:
            return

        self._high_speed_mode = True

        # Log activation (detailed message is in _check_high_speed_mode)
        Debug.info(">>> HIGH_SPEED_MODE ACTIVATED <<<")

        # Emit signal to update UI (statusbar, etc.)
        self.high_speed_mode_changed.emit(True)

        # Stop regular GUI updates for plot/table
        if self.gui_update_timer is not None:
            self.gui_update_timer.stop()

        # Start separate histogram-only timer (2 seconds)
        if self.histogram and self._histogram_update_timer is None:
            self._histogram_update_timer = QTimer()
            self._histogram_update_timer.timeout.connect(self._update_histogram_only)
            self._histogram_update_timer.start(2000)  # Every 2 seconds

    def _deactivate_high_speed_mode(self) -> None:
        """Deactivate HIGH_SPEED_MODE and return to normal operation."""
        if not self._high_speed_mode:
            return

        self._high_speed_mode = False
        Debug.info(">>> HIGH_SPEED_MODE DEACTIVATED (slower data rate detected) <<<")

        # Emit signal to update UI
        self.high_speed_mode_changed.emit(False)

        # Stop histogram-only timer
        if self._histogram_update_timer is not None:
            self._histogram_update_timer.stop()
            self._histogram_update_timer = None

        # Restart regular GUI updates (will be started in clear_data or automatically)
        # Don't restart here to avoid conflicts with clear_data()
        Debug.debug("HIGH_SPEED_MODE cleanup complete")

    def _check_high_speed_mode(self, batch_size: int, current_time: float) -> None:
        """Check if HIGH_SPEED_MODE should be activated based on batch processing rate.

        This method tracks the number of points processed in each batch and activates
        HIGH_SPEED_MODE when the average batch size exceeds the threshold.
        Once activated, the mode is NOT deactivated until measurement ends (clear_data).

        Args:
            batch_size: Number of points processed in this batch
            current_time: Current timestamp in seconds
        """
        # If already in HIGH_SPEED_MODE, stay there (only deactivate on clear_data)
        if self._high_speed_mode:
            return

        # Add current batch to history
        self._batch_history.append((current_time, batch_size))

        # Keep only last N batches
        if len(self._batch_history) > HIGH_SPEED_BATCH_HISTORY:
            self._batch_history.pop(0)

        # Need minimum number of batches for reliable detection
        if len(self._batch_history) < HIGH_SPEED_BATCH_HISTORY:
            return

        # Calculate average batch size over recent history
        total_points = sum(batch[1] for batch in self._batch_history)
        avg_batch_size = total_points / len(self._batch_history)

        # Activate HIGH_SPEED_MODE if average batch size exceeds threshold
        if avg_batch_size >= HIGH_SPEED_BATCH_THRESHOLD:
            Debug.info(
                f">>> HIGH_SPEED_MODE ACTIVATED <<<\n"
                f"Average batch size: {avg_batch_size:.1f} points (threshold: {HIGH_SPEED_BATCH_THRESHOLD})\n"
                f"Last {HIGH_SPEED_BATCH_HISTORY} batches: {[b[1] for b in self._batch_history]}"
            )
            self._activate_high_speed_mode()

    def _update_histogram_only(self) -> None:
        """Update only histogram in HIGH_SPEED_MODE (called every 2 seconds)."""
        if not self._high_speed_mode or not self.histogram:
            return

        try:
            # Use all data points for histogram (not limited to gui_data_points)
            if len(self.data_points) > 1:
                values = [
                    point[1] for point in self.data_points[-10000:]
                ]  # Last 10k points
                self.histogram.update_histogram(values)
                Debug.debug(f"HIGH_SPEED: Histogram updated with {len(values)} points")
        except Exception as e:
            Debug.error(f"Failed to update histogram in HIGH_SPEED_MODE: {e}")

    def _process_queued_data(self) -> None:
        """Process all queued data points and update the GUI.

        In HIGH_SPEED_MODE, this method is NOT called (timer stopped).
        """
        # Continue processing even in HIGH_SPEED_MODE, but with reduced frequency
        # Plot updates are heavily downsampled (500 points max) so it's safe
        if self.data_queue.empty():
            Debug.debug("_process_queued_data: Queue is empty, returning")
            return

        Debug.debug(
            f"_process_queued_data called, queue size: ~{self.data_queue.qsize()}"
        )

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

            # Add all new points to GUI data (with limit)
            # NOTE: data_points are already populated in add_data_fast()
            for index_num, value_num, timestamp in new_points:
                self.gui_data_points.append((index_num, value_num, timestamp))

            # Only limit GUI data; full data remain unlimited
            while len(self.gui_data_points) > self.max_history:
                self.gui_data_points.pop(0)

            # Update GUI widgets with all new points
            if new_points:
                # Update plot and histogram only once with last value
                last_index, last_value, last_timestamp = new_points[-1]

                # In HIGH_SPEED_MODE: Skip plot/table updates (only histogram every 2s)
                # This prevents GUI freezing at extreme data rates (>1 kHz)
                if not self._high_speed_mode:
                    self._update_plot_and_display(
                        last_index, last_value, last_timestamp
                    )

                    # CRITICAL PERFORMANCE: Disable table updates when data rate is too high
                    # Table rendering is EXTREMELY expensive and causes GUI freeze
                    # Only update table if we have <5000 total points (= first 5 seconds at 1kHz)
                    if (
                        len(self.data_points) < 5000
                        and (current_time - self._last_table_update) >= 0.5
                    ):
                        self._update_table_with_batch(new_points)
                        self._last_table_update = current_time
                else:
                    # In HIGH_SPEED_MODE: Only update LCD display (fast operation)
                    if self.display is not None:
                        self.display.display(last_value)

                # Performance logging
            time_since_last = current_time - self._last_update_time
            if time_since_last > 0:
                rate = len(new_points) / time_since_last
                Debug.debug(
                    f"Processed {len(new_points)} points in {time_since_last:.3f}s "
                    f"(rate: {rate:.1f} Hz, total: {self._total_points_received})"
                )

            self._last_update_time = current_time

            # NEW: Batch-based HIGH_SPEED_MODE detection
            self._check_high_speed_mode(len(new_points), current_time)

        except Exception as e:
            Debug.error(f"Error processing queued data: {e}", exc_info=True)

    def _update_plot_and_display(
        self, index: int, value: float, timestamp: Optional[str] = None
    ) -> None:
        """Update plot, LCD and histogram with the latest data point.

        PERFORMANCE: Updates are throttled and optimized for high frequencies.
        """
        try:
            # Update plot widget with all current data points
            # Only update plot if we have data to show
            if self.plot and len(self.gui_data_points) > 0:
                # Always use batch update for better performance
                # Pass only the last N points to reduce rendering overhead
                Debug.debug(
                    f"Updating plot with {len(self.gui_data_points)} gui_data_points"
                )
                if hasattr(self.plot, "update_plot_batch"):
                    self.plot.update_plot_batch(self.gui_data_points)
                else:
                    # Fallback - use standard method but with full dataset
                    self.plot.update_plot(self.gui_data_points)
            else:
                if self.plot:
                    Debug.debug(
                        f"Plot exists but gui_data_points empty: {len(self.gui_data_points)}"
                    )
                else:
                    Debug.debug("No plot widget available")

            # Update LCD display with total count (every 5th call for smoothness)
            # At 500ms GUI updates, this means LCD updates every 2.5 seconds
            if self.display:
                if not hasattr(self, "_display_update_counter"):
                    self._display_update_counter = 0
                self._display_update_counter += 1
                if self._display_update_counter >= 5:
                    self._display_update_counter = 0
                    self.display.display(len(self.data_points))  # Show total count

            # Update histogram with current data distribution (every 10th call)
            # At 500ms GUI updates, this means histogram updates every 5 seconds
            if self.histogram and len(self.gui_data_points) > 1:
                if not hasattr(self, "_histogram_update_counter"):
                    self._histogram_update_counter = 0
                self._histogram_update_counter += 1
                if self._histogram_update_counter >= 10:
                    self._histogram_update_counter = 0
                    # Extract values for histogram (only the measurement values)
                    values = [point[1] for point in self.gui_data_points]
                    self.histogram.update_histogram(values)

        except (AttributeError, RuntimeError) as e:
            Debug.error(f"Failed to update plot/display widgets: {e}", exc_info=True)

    def _update_table_with_batch(
        self, new_points: List[Tuple[int, float, str]]
    ) -> None:
        """Update table model with a batch of new data points.

        Args:
            new_points: List of (index, value, timestamp) tuples to add to table.
        """
        if self.table_model is None:
            return

        try:
            # Add each point to the table
            for index, value, timestamp in new_points:
                row = [
                    QStandardItem(str(index)),
                    QStandardItem(str(value)),
                    QStandardItem(timestamp),
                ]
                self.table_model.appendRow(row)

            # Remove old rows to maintain max_history limit
            while self.table_model.rowCount() > self.max_history:
                self.table_model.removeRow(0)

        except Exception as table_error:
            Debug.error(f"Failed to update table model: {table_error}", exc_info=True)

    def _update_gui_widgets(
        self, index: int, value: float, timestamp: Optional[str] = None
    ) -> None:
        """Update plot, LCD, histogram and table with a single data point.

        This method is kept for backwards compatibility and legacy code paths.
        """
        # Update plot and display
        self._update_plot_and_display(index, value, timestamp)

        # Update table with single point
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._update_table_with_batch([(index, value, timestamp)])

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
        """Clear all data points and reset optional widgets.

        Thread-safe: Can be called from GUI thread while acquisition is running.
        """
        try:
            Debug.info(f"DataController: Clearing {len(self.data_points)} data points")

            # Deactivate HIGH_SPEED_MODE if active
            if self._high_speed_mode:
                self._deactivate_high_speed_mode()

            # Reset HIGH_SPEED_MODE tracking
            self._batch_history.clear()

            # Stop GUI updates temporarily to prevent race conditions
            was_running = False
            if hasattr(self, "gui_update_timer") and self.gui_update_timer is not None:
                was_running = self.gui_update_timer.isActive()
                if was_running:
                    self.gui_update_timer.stop()

            # Remove stored points (both full and GUI data)
            self.data_points = []
            self.gui_data_points = []

            # Clear the queue with lock
            with self._queue_lock:
                # Create new queue to ensure clean state
                self.data_queue = queue.Queue(maxsize=10000)

            # Reset counters
            self._total_points_received = 0
            self._points_processed_in_last_update = 0
            self._last_update_time = time()
            self._last_table_update = time()
            self._queue_overflow_warned = False

            # Reset display update counters
            if hasattr(self, "_display_update_counter"):
                self._display_update_counter = 0
            if hasattr(self, "_histogram_update_counter"):
                self._histogram_update_counter = 0

            # Always restart GUI updates with correct interval (important!)
            # The timer might have been stopped by HIGH_SPEED_MODE or clear operation
            if self.gui_update_timer is not None:
                self.gui_update_timer.start(UPDATE_INTERVAL)
                Debug.info(
                    f"GUI update timer RESTARTED with {UPDATE_INTERVAL}ms interval (isActive={self.gui_update_timer.isActive()})"
                )
            else:
                Debug.error("GUI update timer is None, cannot restart!")

            # Clear the plot
            if self.plot:
                Debug.info("DataController: Clearing plot")
                # Use clear_measurement_data() instead of clear() to avoid MRO issues with PyQtGraph
                if hasattr(self.plot, "clear_measurement_data"):
                    self.plot.clear_measurement_data()
                else:
                    self.plot.clear()
            else:
                Debug.info("DataController: No plot to clear")

            # Reset displayed value
            if self.display:
                self.display.display(0)

            # Clear the histogram
            if self.histogram:
                Debug.info("DataController: Clearing histogram")
                # Use clear_measurement_data() instead of clear() to avoid MRO issues with PyQtGraph
                if hasattr(self.histogram, "clear_measurement_data"):
                    self.histogram.clear_measurement_data()
                else:
                    self.histogram.clear()

            if self.stat_display:
                for display in self.stat_display:
                    display.clear()

            # Clear the table model
            if self.table_model is not None:
                Debug.info(
                    f"DataController: Clearing table with {self.table_model.rowCount()} rows"
                )
                try:
                    while self.table_model.rowCount() > 0:
                        self.table_model.removeRow(0)
                    Debug.info("DataController: Table cleared successfully")
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
            MessageHelper.info(
                parent,
                CONFIG.get("messages", {}).get(
                    "no_data_to_save", "Keine Messdaten zum Speichern vorhanden."
                ),
                "Warnung",
            )
            return None

        if not rad_sample or not group_letter:
            MessageHelper.info(
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
