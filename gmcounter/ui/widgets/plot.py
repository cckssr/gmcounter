"""Plot widgets using :mod:`pyqtgraph`."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple, List
import numpy as np

from ...infrastructure.logging import Debug

try:  # pragma: no cover - optional dependency during headless tests
    import pyqtgraph as pg
    from PySide6.QtCore import Signal, QObject  # pylint: disable=no-name-in-module

    # CRITICAL PERFORMANCE: Enable OpenGL acceleration if available
    # This can provide 10-100x speedup for large datasets
    try:
        import pyqtgraph.opengl as gl  # noqa: F401

        pg.setConfigOption("useOpenGL", True)
        pg.setConfigOption("enableExperimental", True)
        Debug.info("PyQtGraph OpenGL acceleration ENABLED")
    except Exception as e:
        Debug.warning(f"PyQtGraph OpenGL not available: {e}")
        Debug.info("Using standard rendering (slower but stable)")

    # Additional performance optimizations for pyqtgraph
    pg.setConfigOption("antialias", False)  # Disable antialiasing for speed
    pg.setConfigOption("foreground", "k")  # Black foreground
    pg.setConfigOption("background", "w")  # White background

except Exception:  # pragma: no cover - fallback stubs
    from PySide6.QtWidgets import QWidget

    class Signal:  # pragma: no cover - fallback stub
        def __init__(self, *args):
            pass

        def emit(self, *args):
            pass

        def connect(self, *args):
            pass

    class QObject:  # pragma: no cover - fallback stub
        pass

    class _DummyPlotWidget(QWidget, object):
        def __init__(self, *_, **__):
            super().__init__()

        def plot(self, *_, **__):
            return self

        def clear(self):
            pass

        def setLabel(self, *_, **__):
            pass

        def setTitle(self, *_):
            pass

        def autoRange(self, *_, **__):
            pass

    pg = type("MockPyQtGraph", (), {"PlotWidget": _DummyPlotWidget})()


class PlotWidget(pg.PlotWidget):
    """A real-time plot widget using pyqtgraph."""

    # Signal emitted when user manually interacts with the plot
    user_interaction_detected = Signal()

    def __init__(
        self,
        title: Optional[str] = None,
        xlabel: str = "Index",
        ylabel: str = "Time (µs)",
        max_plot_points: int = 500,
        fontsize: int = 12,
    ):
        """
        Initialize the plot widget.

        Args:
            max_plot_points (int): Maximum number of points to display in the plot
            width (int): Width of the plot in inches
            height (int): Height of the plot in inches
            dpi (int): DPI (dots per inch) of the plot
            fontsize (int): Font size to use in the plot
            xlabel (str): Label for the x-axis
            ylabel (str): Label for the y-axis
            title (str): Title of the plot
        """
        super().__init__()

        self.max_plot_points = max_plot_points
        self.fontsize = fontsize
        self._user_interacted = False
        self._auto_scroll_enabled = False
        self._auto_range_enabled = False
        self._programmatic_update = (
            False  # Flag to prevent triggering on programmatic changes
        )

        # Set up the plot appearance
        self.setBackground(None)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel("bottom", xlabel)
        self.setLabel("left", ylabel)
        self.setTitle(title)

        # Store config for potential future use
        self._plot_config = {"xlabel": xlabel, "ylabel": ylabel, "title": title}

        # Connect to view range changed signal to detect user interaction
        viewbox = self.plotItem.getViewBox()
        viewbox.sigRangeChanged.connect(self._on_view_changed)

        # Redraw the canvas
        self.update()  # Triggers an explicit QWidget repaint

    def _on_view_changed(self):
        """Called when user pans or zooms the plot.

        Disables auto-range and auto-scroll when user manually adjusts the view.
        Emits signal to notify MainWindow to update UI checkboxes.
        """
        # Ignore programmatic updates
        if self._programmatic_update:
            return

        # Check if this is a user-initiated change
        viewbox = self.plotItem.getViewBox()
        if viewbox.state["mouseEnabled"][0] or viewbox.state["mouseEnabled"][1]:
            # Only react if auto-range or auto-scroll is currently enabled
            if self._auto_range_enabled or self._auto_scroll_enabled:
                self._auto_range_enabled = False
                self._auto_scroll_enabled = False
                self._user_interacted = True
                Debug.info(
                    "Auto-Range und Auto-Scroll durch Benutzerinteraktion deaktiviert"
                )
                # Emit signal to notify MainWindow
                self.user_interaction_detected.emit()

    def set_auto_scroll(self, enabled: bool, max_points: int = None):
        """Enable or disable auto-scroll mode.

        Args:
            enabled: Whether to enable auto-scroll
            max_points: Maximum number of points to display (optional)
        """
        self._auto_scroll_enabled = enabled
        if max_points is not None:
            self.max_plot_points = max_points
        Debug.debug(f"Auto-Scroll: {enabled}, Max Points: {self.max_plot_points}")

    def enable_auto_range(self, enabled: bool = True):
        """Enable or disable automatic range adjustment.

        Args:
            enabled: Whether to enable auto-range
        """
        self._auto_range_enabled = enabled
        self._user_interacted = not enabled

        viewbox = self.plotItem.getViewBox()
        if enabled:
            viewbox.enableAutoRange(enable=True)
            Debug.debug("Auto-Range aktiviert")
        else:
            viewbox.enableAutoRange(enable=False)
            Debug.debug("Auto-Range deaktiviert")

    def clear_measurement_data(self):
        """Clear plot measurement data for new measurement.

        This method is called when starting a new measurement to ensure
        the plot is in a clean state.
        """
        Debug.info(
            f"PlotWidget.clear_measurement_data() called, _plot_item exists: {hasattr(self, '_plot_item')}, is None: {getattr(self, '_plot_item', None) is None}"
        )
        if hasattr(self, "_plot_item") and self._plot_item is not None:
            # Remove the plot item completely for clean re-initialization
            try:
                self.removeItem(self._plot_item)
                Debug.info("PlotWidget: Successfully removed _plot_item from view")
            except Exception as e:
                Debug.error(f"PlotWidget: Error removing _plot_item: {e}")
            self._plot_item = None
            Debug.info("PlotWidget: _plot_item set to None")
        else:
            Debug.info(
                f"PlotWidget.clear_measurement_data(): _plot_item is already None or doesn't exist"
            )

        # Reset scroll counter
        if hasattr(self, "_scroll_update_counter"):
            self._scroll_update_counter = 0

        # Also call base class clear() to ensure complete cleanup
        try:
            super().clear()
            Debug.info("PlotWidget: Base class clear() called")
        except Exception as e:
            Debug.error(f"PlotWidget: Error calling base clear(): {e}")

    def clear(self):
        """Clear plot data efficiently.

        PERFORMANCE: Remove the plot item to ensure clean state for next measurement.
        """
        Debug.info(
            f"PlotWidget.clear() called, _plot_item exists: {hasattr(self, '_plot_item')}, is None: {getattr(self, '_plot_item', None) is None}"
        )
        if hasattr(self, "_plot_item") and self._plot_item is not None:
            # Remove the plot item completely for clean re-initialization
            try:
                self.removeItem(self._plot_item)
                Debug.info("PlotWidget: Successfully removed _plot_item from view")
            except Exception as e:
                Debug.error(f"PlotWidget: Error removing _plot_item: {e}")
            self._plot_item = None
            Debug.info("PlotWidget: _plot_item set to None")
        else:
            Debug.info(
                f"PlotWidget.clear(): _plot_item is already None or doesn't exist"
            )

        # Reset scroll counter
        if hasattr(self, "_scroll_update_counter"):
            self._scroll_update_counter = 0

        # Also call base class clear() to ensure complete cleanup
        try:
            super().clear()
            Debug.info("PlotWidget: Base class clear() called")
        except Exception as e:
            Debug.error(f"PlotWidget: Error calling base clear(): {e}")

    def update_plot(self, data_points: List[Tuple[int, float, str]]):
        """
        Updates the plot using external data source.

        PERFORMANCE: Uses setData() instead of clear()+plot() for efficiency.
        Downsamples data if more than 2000 points to prevent rendering lag.

        Args:
            data_points: List of (index_num, value_num, timestamp) tuples
        """
        if not data_points:
            Debug.debug("update_plot called with empty data_points")
            return

        # AGGRESSIVE Downsampling for smooth performance
        # Render maximum 500 points for smooth 60 FPS rendering
        MAX_RENDER_POINTS = 500
        if len(data_points) > MAX_RENDER_POINTS:
            # Calculate step size to downsample
            step = len(data_points) // MAX_RENDER_POINTS
            display_points = data_points[::step]
        else:
            display_points = data_points

        # Extract data arrays with efficient dtype
        all_indices = np.array([point[0] for point in display_points], dtype=np.float32)
        all_values_us = np.array(
            [point[1] for point in display_points], dtype=np.float32
        )

        # Disable symbols for better performance when many points
        use_symbols = len(display_points) < 200  # Only show symbols for <200 points

        # CRITICAL PERFORMANCE FIX: Use setData() instead of clear()+plot()
        # This reuses the existing plot item instead of destroying and recreating it
        if not hasattr(self, "_plot_item") or self._plot_item is None:
            # First time: create plot item
            Debug.info(
                f"Creating new plot item with {len(display_points)} points, symbols={use_symbols}"
            )
            # CRITICAL: Disconnect sigRangeChanged to prevent false user interaction detection
            # The signal will trigger multiple times during plot creation and cause auto-scroll to be disabled
            viewbox = self.plotItem.getViewBox()
            try:
                viewbox.sigRangeChanged.disconnect(self._on_view_changed)
                signal_disconnected = True
            except:
                signal_disconnected = False

            if use_symbols:
                self._plot_item = self.plot(
                    all_indices,
                    all_values_us,
                    pen="gray",
                    symbol="o",
                    symbolSize=4,
                    symbolBrush="r",
                    symbolPen="r",
                )
            else:
                # No symbols for better performance
                self._plot_item = self.plot(
                    all_indices,
                    all_values_us,
                    pen="gray",
                )

            # Reconnect signal after plot creation
            if signal_disconnected:
                viewbox.sigRangeChanged.connect(self._on_view_changed)
                Debug.debug(
                    "PlotWidget: sigRangeChanged reconnected after plot creation"
                )
        else:
            # Subsequent updates: just update data (MUCH faster!)
            self._plot_item.setData(all_indices, all_values_us)

        # Debug only occasionally to reduce overhead
        if len(data_points) % 100 == 0:  # Log every 100th update
            Debug.debug(
                f"Plot updated with {len(display_points)}/{len(data_points)} points"
            )

        # Handle range adjustment based on mode
        # PERFORMANCE: Skip range calculations if not needed
        viewbox = self.plotItem.getViewBox()

        if self._auto_range_enabled:
            # Auto-range mode: let pyqtgraph handle it immediately for responsive UI
            self._programmatic_update = True
            viewbox.enableAutoRange(enable=True)
            self._programmatic_update = False
        elif self._auto_scroll_enabled:
            # Auto-scroll mode: update range only every 100 updates to reduce overhead
            if not hasattr(self, "_scroll_update_counter"):
                self._scroll_update_counter = 0

            self._scroll_update_counter += 1

            # Update range every 10 calls for smooth scrolling
            if self._scroll_update_counter >= 10:
                self._scroll_update_counter = 0

                # Show only the last max_plot_points
                display_data_for_range = (
                    data_points[-self.max_plot_points :]
                    if len(data_points) > self.max_plot_points
                    else data_points
                )

                if len(display_data_for_range) > 0:
                    # Extract indices and values for range calculation only
                    range_indices = np.array(
                        [point[0] for point in display_data_for_range], dtype=np.float32
                    )
                    range_values_us = np.array(
                        [point[1] for point in display_data_for_range], dtype=np.float32
                    )

                    # Calculate proper ranges with minimal padding
                    x_min, x_max = range_indices.min(), range_indices.max()
                    y_min, y_max = range_values_us.min(), range_values_us.max()

                    # Ensure minimum range for single-point plots
                    if x_max == x_min:
                        x_padding = max(1, x_min * 0.1)  # 10% of index or at least 1
                        final_x_range = [x_min - x_padding, x_max + x_padding]
                    else:
                        x_range = x_max - x_min
                        x_padding = x_range * 0.05
                        final_x_range = [x_min - x_padding, x_max + x_padding]

                    if y_max == y_min:
                        y_padding = max(
                            1000, y_min * 0.1
                        )  # 10% of value or at least 1000µs
                        final_y_range = [y_min - y_padding, y_max + y_padding]
                    else:
                        y_range = y_max - y_min
                        y_padding = y_range * 0.05
                        final_y_range = [y_min - y_padding, y_max + y_padding]

                    # Set manual range for auto-scroll
                    self._programmatic_update = True
                    viewbox.enableAutoRange(enable=False)
                    viewbox.setRange(
                        xRange=final_x_range, yRange=final_y_range, padding=0
                    )
                    self._programmatic_update = False
        else:
            # Manual mode: don't change the view if user has interacted
            if not self._user_interacted:
                # First time or no user interaction yet - set initial range
                display_data_for_range = (
                    data_points[-self.max_plot_points :]
                    if len(data_points) > self.max_plot_points
                    else data_points
                )

                if len(display_data_for_range) > 0:
                    # Extract indices and values for range calculation only
                    range_indices = np.array(
                        [point[0] for point in display_data_for_range]
                    )
                    range_values_us = np.array(
                        [point[1] for point in display_data_for_range]
                    )

                    # Calculate proper ranges with minimal padding
                    x_min, x_max = range_indices.min(), range_indices.max()
                    y_min, y_max = range_values_us.min(), range_values_us.max()

                    # Ensure minimum range for single-point plots
                    if x_max == x_min:
                        x_padding = max(1, x_min * 0.1)
                        final_x_range = [x_min - x_padding, x_max + x_padding]
                    else:
                        x_range = x_max - x_min
                        x_padding = x_range * 0.05
                        final_x_range = [x_min - x_padding, x_max + x_padding]

                    if y_max == y_min:
                        y_padding = max(1000, y_min * 0.1)
                        final_y_range = [y_min - y_padding, y_max + y_padding]
                    else:
                        y_range = y_max - y_min
                        y_padding = y_range * 0.05
                        final_y_range = [y_min - y_padding, y_max + y_padding]

                    # Set initial range
                    self._programmatic_update = True
                    viewbox.enableAutoRange(enable=False)
                    viewbox.setRange(
                        xRange=final_x_range, yRange=final_y_range, padding=0
                    )
                    self._programmatic_update = False
                    Debug.debug(f"Initial range: {final_x_range}, {final_y_range}")

    def update_plot_batch(self, data_points: List[Tuple[int, float, str]]):
        """
        Batch update method for efficient plot updates with multiple data points.
        This is the same as update_plot but with a clearer name for batch operations.

        Args:
            data_points: List of (index_num, value_num, timestamp) tuples
        """
        self.update_plot(data_points)

    def get_data_in_range(self, max_points: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Legacy method - no longer needed with centralized data management
        """
        return np.array([]), np.array([])


class HistogramWidget(pg.PlotWidget):
    """A histogram widget using pyqtgraph."""

    def __init__(
        self, title: Optional[str] = None, xlabel: str = "CPM", ylabel: str = "Count"
    ):
        """
        Initialize the histogram widget.

        Args:
            title: Plot title
            xlabel: X-axis label (CPM values)
            ylabel: Y-axis label (frequency count)
        """
        super().__init__()

        self.setBackground(None)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel("bottom", xlabel)
        self.setLabel("left", ylabel)
        self.setTitle(title)

        self._hist_item = None

    def clear_measurement_data(self):
        """
        Clear measurement data from histogram.
        
        Removes the histogram bar item completely to ensure clean state
        for next measurement.
        """
        Debug.debug(
            f"HistogramWidget.clear_measurement_data() called, _hist_item exists: {hasattr(self, '_hist_item')}, is None: {getattr(self, '_hist_item', None) is None}"
        )
        
        if hasattr(self, "_hist_item") and self._hist_item is not None:
            self.removeItem(self._hist_item)
            self._hist_item = None
            Debug.debug("HistogramWidget.clear_measurement_data(): _hist_item removed and set to None")
        else:
            Debug.debug(
                "HistogramWidget.clear_measurement_data(): _hist_item is already None or doesn't exist"
            )
        
        Debug.debug("HistogramWidget.clear_measurement_data(): Completed")

    def update_histogram(self, data: Iterable[float], bins: int = 50):
        """
        Update the histogram with new data.

        PERFORMANCE: Reuses BarGraphItem instead of recreating it.

        Args:
            data: CPM values to create histogram from
            bins: Number of histogram bins
        """
        if not data:
            return

        # Calculate histogram
        hist, bin_edges = np.histogram(data, bins=bins)

        # Calculate bin centers and width
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        width = bin_edges[1] - bin_edges[0]

        # Reuse or create histogram item
        if self._hist_item is None:
            # First time: create new item
            self._hist_item = pg.BarGraphItem(
                x=bin_centers,
                height=hist,
                width=width * 0.8,
                brush="w",
            )
            self.addItem(self._hist_item)
        else:
            # Update existing item (faster than removing and recreating)
            self._hist_item.setOpts(
                x=bin_centers,
                height=hist,
                width=width * 0.8,
            )

        # Always auto-range to fit data (histogram should always show full distribution)
        # User interaction (zoom/pan) is intentionally ignored for histogram
        self.autoRange()
