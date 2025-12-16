"""
Reusable plot widgets using pyqtgraph.

This module provides general-purpose plotting widgets that can be used
across different applications. The widgets support real-time data updates,
auto-scrolling, auto-ranging, and histogram visualization.

Classes:
    GeneralPlot: Real-time line plot with configurable axes and update modes
    HistogramWidget: Histogram plot for frequency distribution visualization
    FastPlotCurveItem: Optimized curve item for high-performance plotting

Performance Features:
    - Batch data updates to minimize rendering overhead
    - Lazy item creation to avoid unnecessary overhead
    - skipFiniteCheck option for pre-validated data
    - Efficient range calculations with caching
    - GPU acceleration via OpenGL when available
"""

from __future__ import annotations

from typing import Iterable, Optional, Tuple, List, Dict, Any
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Signal, Slot, QTimer  # pylint: disable=no-name-in-module
from PySide6.QtGui import QSurfaceFormat  # pylint: disable=no-name-in-module
from ...infrastructure.logging import Debug

# CRITICAL: Disable vsync for maximum plot update speed
sfmt = QSurfaceFormat()
sfmt.setSwapInterval(0)
QSurfaceFormat.setDefaultFormat(sfmt)

try:  # pragma: no cover - optional dependency during headless tests
    # Enable OpenGL acceleration if available
    pg.setConfigOption("useOpenGL", True)
    pg.setConfigOption("enableExperimental", True)
    Debug.info("PyQtGraph OpenGL acceleration ENABLED")
except ImportError as e:
    Debug.warning(f"PyQtGraph OpenGL not available: {e}")
    Debug.info("Using standard rendering (slower but stable)")

# Performance-optimized configuration based on pyqtgraph examples
# Disable antialiasing for speed (can be enabled per-plot if needed)
pg.setConfigOption("antialias", False)
# Optimize downsampling
pg.setConfigOption("imageAxisOrder", "row-major")
# Prefer PlotCurveItem over PlotDataItem (simpler, faster)
pg.setConfigOption("useNumba", True)  # Use numba if available for acceleration


class PlotConfig:
    """
    Configuration for GeneralPlot.

    Attributes:
        title (Optional[str]): Plot title
        xlabel (str): X-axis label
        ylabel (str): Y-axis label
        fontsize (int): Font size for labels and title
        max_plot_points (int): Maximum number of points to display in auto-scroll mode
        background_color (Optional[str]): Background color (CSS format)
        grid_alpha (float): Alpha transparency for grid lines (0.0-1.0)
        use_opengl (bool): Enable OpenGL rendering (best performance)
        antialias (bool): Enable antialiasing (slower but prettier)
        skip_finite_check (bool): Skip checking for NaN/inf values (faster if data is pre-validated)
        pen_width (int): Width of plot line
        symbol_size (int): Size of plot symbols
    """

    title: Optional[str] = None
    xlabel: str = "X"
    ylabel: str = "Y"
    fontsize: int = 11
    max_plot_points: int = 1000
    background_color: Optional[str] = None
    grid_alpha: float = 0.3
    use_opengl: bool = True
    antialias: bool = False
    skip_finite_check: bool = False
    pen_width: int = 5
    symbol_size: int = 10

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class FastPlotCurveItem(pg.PlotCurveItem):
    """
    Optimized PlotCurveItem for high-performance plotting.

    This class extends PlotCurveItem with performance optimizations:
    - Direct data management for minimal overhead
    - Efficient clipping detection
    - Support for skipFiniteCheck for pre-validated data
    """

    def __init__(self, **kwds):
        """Initialize with performance defaults."""
        # Set performance-optimized defaults
        kwds.setdefault("antialias", False)
        kwds.setdefault(
            "pen", pg.mkPen(width=1, color="#0099FF")
        )  # Cyan - visible on Windows
        super().__init__(**kwds)
        self._cached_range: Optional[
            Tuple[Tuple[float, float], Tuple[float, float]]
        ] = None
        self._data_changed = True

    def setData(self, *args, **kwds):
        """
        Set data with optimized performance.

        Args:
            x, y: Data arrays or lists
            pen: Pen for drawing
            antialias: Enable antialiasing (default: False for speed)
            skipFiniteCheck: Skip NaN/inf checking (faster for pre-validated data)
            connect: Connection array or string ('all', 'pairs', 'finite', 'array')
        """
        # Mark cache as invalid
        self._data_changed = True
        # Use parent's setData with performance options
        kwds.setdefault("skipFiniteCheck", False)
        super().setData(*args, **kwds)

    def get_range(self) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Get cached data range (x_range, y_range).

        Returns None if data is empty or invalid.
        """
        if not self._data_changed and self._cached_range is not None:
            return self._cached_range

        if self.xData is None or self.yData is None or len(self.xData) == 0:
            return None

        try:
            x_min = float(np.amin(self.xData))
            x_max = float(np.amax(self.xData))
            y_min = float(np.amin(self.yData))
            y_max = float(np.amax(self.yData))
            self._cached_range = ((x_min, x_max), (y_min, y_max))
            self._data_changed = False
            return self._cached_range
        except (ValueError, TypeError):
            return None

    def generateSvg(self, **kwds):
        """Generate SVG representation (optional implementation)."""
        # Required by abstract GraphicsItem interface
        return None


class GeneralPlot(pg.PlotWidget):
    """
    A high-performance real-time plot widget using pyqtgraph.

    This widget provides efficient plotting for live data streams with support for:
    - Auto-scrolling mode (shows last N points)
    - Auto-ranging mode (fits all data automatically)
    - Manual zoom/pan mode
    - Batch data updates for maximum efficiency
    - GPU acceleration via OpenGL
    - Automatic downsampling for large datasets
    - Pre-validated data support (skipFiniteCheck)

    Design based on pyqtgraph performance examples and best practices.

    Signals:
        user_interaction_detected: Emitted when user manually pans or zooms
        plot_updated: Emitted after plot data update (int: number of points)
        plot_cleared: Emitted when plot is cleared
        auto_scroll_changed: Emitted when auto-scroll state changes (bool: enabled)
        auto_range_changed: Emitted when auto-range state changes (bool: enabled)

    Example:
        >>> config = PlotConfig(title="Temperature", xlabel="Time (s)", ylabel="°C")
        >>> plot = GeneralPlot(config)
        >>> plot.update_plot_data([(1, 25.5), (2, 26.3), (3, 25.8)])
        >>> plot.set_auto_scroll(True, max_points=500)
    """

    # Signals for reactive UI integration
    user_interaction_detected = Signal()
    plot_updated = Signal(int)  # Emits number of displayed points
    plot_cleared = Signal()
    auto_scroll_changed = Signal(bool)  # Emits enabled state
    auto_range_changed = Signal(bool)  # Emits enabled state

    # Performance tuning
    MAX_RENDER_POINTS = 5000  # Max points before downsampling triggers
    SCROLL_UPDATE_INTERVAL = 5  # Update scroll range every N updates

    def __init__(
        self,
        config: Optional[PlotConfig] = None,
    ):
        """
        Initialize the plot widget with performance optimizations.

        Args:
            config: PlotConfig object with initial settings
        """
        super().__init__()

        if config is None:
            config = PlotConfig()

        self.config = config

        # Performance flags
        self._user_interacted = False
        self._auto_scroll_enabled = False
        self._auto_range_enabled = True  # Start with auto-range enabled
        self._programmatic_update = False
        self._pending_update = False

        # Data management
        self._plot_curve: Optional[FastPlotCurveItem] = None
        self._scroll_counter = 0
        self._last_data_points: List[Tuple[float, float]] = []
        self._is_clearing = False

        # Deferred update mechanism for batch operations
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._process_deferred_update)
        self._deferred_data: List[Tuple[float, float]] = []

        # Configure plot appearance
        self._configure_appearance()

        # Set up interaction detection
        self._connect_signals()

        Debug.debug("GeneralPlot initialized with auto-range enabled")

    def _configure_appearance(self) -> None:
        """Configure plot appearance based on config."""
        # Determine background color
        background = self.config.background_color

        # Only set background if explicitly configured
        # For None, we'll set it dynamically in showEvent()
        if background:
            self.setBackground(background)

        self.showGrid(x=True, y=True, alpha=self.config.grid_alpha)

        if self.config.title:
            self.setTitle(self.config.title)

        self.setLabel("bottom", self.config.xlabel)
        self.setLabel("left", self.config.ylabel)

        # Configure ViewBox for performance
        viewbox = self.getViewBox()
        if viewbox:
            # Disable some interactive features for performance if needed
            viewbox.setMouseEnabled(x=True, y=True)
            viewbox.enableAutoRange(enable=True)

    def _connect_signals(self) -> None:
        """Connect signals for user interaction detection."""
        viewbox = self.getViewBox()
        if viewbox:
            viewbox.sigRangeChanged.connect(self._on_view_range_changed)

    def _on_view_range_changed(self) -> None:
        """
        Detect when user manually pans or zooms the plot.

        Automatically disables auto-range/auto-scroll when user interacts,
        allowing manual control.
        """
        # Ignore programmatic updates
        if self._programmatic_update or self._is_clearing:
            return

        viewbox = self.getViewBox()
        if not viewbox:
            return

        # Only process if auto modes are active
        if self._auto_range_enabled or self._auto_scroll_enabled:
            self._auto_range_enabled = False
            self._auto_scroll_enabled = False
            self._user_interacted = True
            Debug.debug("Auto modes disabled by user interaction")
            self.user_interaction_detected.emit()

    @Slot(bool)
    def set_auto_scroll(self, enabled: bool, max_points: Optional[int] = None) -> None:
        """
        Enable or disable auto-scroll mode.

        In auto-scroll mode, the plot shows only the last N points and
        automatically scrolls as new data arrives.

        Args:
            enabled: Whether to enable auto-scroll mode
            max_points: Maximum number of points to display
        """
        self._auto_scroll_enabled = enabled

        if max_points is not None:
            self.config.max_plot_points = max(10, max_points)

        self.auto_scroll_changed.emit(enabled)
        Debug.debug(
            f"Auto-scroll: {enabled}, max_points: {self.config.max_plot_points}"
        )

    @Slot(bool)
    def enable_auto_range(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic range adjustment.

        In auto-range mode, axes automatically adjust to fit all data.

        Args:
            enabled: Whether to enable auto-range
        """
        self._auto_range_enabled = enabled
        self._user_interacted = not enabled

        viewbox = self.getViewBox()
        if viewbox:
            self._programmatic_update = True
            viewbox.enableAutoRange(enable=enabled)
            self._programmatic_update = False

        self.auto_range_changed.emit(enabled)
        state = "enabled" if enabled else "disabled"
        Debug.debug(f"Auto-range {state}")

    @Slot()
    def clear_measurement_data(self) -> None:
        """
        Clear all plot data and reset state.

        Call this before starting a new measurement series.
        """
        self._is_clearing = True
        Debug.debug("Clearing plot data")

        try:
            if self._plot_curve is not None:
                self.removeItem(self._plot_curve)
                self._plot_curve = None

            self._last_data_points.clear()
            self._deferred_data.clear()
            self._scroll_counter = 0
            self._user_interacted = False

            # Reset to auto-range
            self.enable_auto_range(True)

        finally:
            self._is_clearing = False

        self.plot_cleared.emit()

    @Slot(list)
    def update_plot_data(
        self,
        data_points: List[Tuple[float, float]],
        use_symbols: bool = False,
        deferred: bool = False,
    ) -> None:
        """
        Update plot with new data points (high-performance method).

        PERFORMANCE TIPS:
        - Pass lists of tuples for fastest updates
        - Use deferred=True for burst updates (batches them together)
        - Use use_symbols=True only for <200 points
        - Use skipFiniteCheck=True only if data is pre-validated

        Args:
            data_points: List of (x, y) tuples
            use_symbols: Display symbols at points (slower)
            deferred: If True, batch updates together (for streaming data)
        """
        if not data_points:
            return

        if deferred:
            # Batch updates together to reduce rendering overhead
            self._deferred_data.extend(data_points)
            if not self._update_timer.isActive():
                self._update_timer.start(16)  # ~60 FPS
            return

        # Immediate update
        self._perform_plot_update(data_points, use_symbols)

    def _process_deferred_update(self) -> None:
        """Process batched deferred updates."""
        if self._deferred_data:
            data = self._deferred_data[:]
            self._deferred_data.clear()
            self._perform_plot_update(data, use_symbols=False)

    def _perform_plot_update(
        self, data_points: List[Tuple[float, float]], use_symbols: bool = False
    ) -> None:
        """
        Perform the actual plot update (internal method).

        Args:
            data_points: List of (x, y) tuples
            use_symbols: Display symbols at points
        """
        if not data_points:
            return

        # Store current data
        self._last_data_points = data_points.copy()

        # Extract arrays for plotting
        x_arr = np.array([p[0] for p in data_points], dtype=np.float32)
        y_arr = np.array([p[1] for p in data_points], dtype=np.float32)

        # Determine rendering mode
        # Increased threshold to 1000 points for better visibility on Windows
        show_symbols = use_symbols and len(data_points) < 1000

        # Create or update plot curve item
        if self._plot_curve is None:
            self._create_plot_curve(x_arr, y_arr, show_symbols)
        else:
            self._update_plot_curve(x_arr, y_arr, show_symbols)

        # Update range based on current mode
        self._update_view_range(data_points)

        # Emit signal
        self.plot_updated.emit(len(data_points))

    def _create_plot_curve(
        self, x_arr: np.ndarray, y_arr: np.ndarray, show_symbols: bool
    ) -> None:
        """
        Create initial plot curve item (lazy creation).

        Args:
            x_arr: X data array
            y_arr: Y data array
            show_symbols: Whether to show symbols at points
        """
        Debug.debug(
            f"Creating plot curve ({len(x_arr)} points, symbols={show_symbols})"
        )

        # Create optimized curve item
        self._plot_curve = FastPlotCurveItem()

        if show_symbols:
            self._plot_curve.setData(
                x_arr,
                y_arr,
                pen=pg.mkPen(width=self.config.pen_width, color="#0099FF"),  # Cyan line
                symbol="o",
                symbolSize=self.config.symbol_size,
                symbolBrush=pg.mkBrush("#FF3333"),  # Bright red symbols
                symbolPen=pg.mkPen("#FF3333", width=2),  # Bright red border
                antialias=self.config.antialias,
                skipFiniteCheck=self.config.skip_finite_check,
            )
        else:
            self._plot_curve.setData(
                x_arr,
                y_arr,
                pen=pg.mkPen(width=self.config.pen_width, color="#0099FF"),  # Cyan line
                antialias=self.config.antialias,
                skipFiniteCheck=self.config.skip_finite_check,
            )

        self.addItem(self._plot_curve)

    def _update_plot_curve(
        self, x_arr: np.ndarray, y_arr: np.ndarray, show_symbols: bool
    ) -> None:
        """
        Update existing plot curve (fast update).

        Args:
            x_arr: X data array
            y_arr: Y data array
            show_symbols: Whether to show symbols at points
        """
        # Update data using fast setData method
        if self._plot_curve is None:
            return

        if show_symbols:
            self._plot_curve.setData(
                x_arr,
                y_arr,
                symbol="o",
                symbolSize=self.config.symbol_size,
                skipFiniteCheck=self.config.skip_finite_check,
            )
        else:
            self._plot_curve.setData(
                x_arr, y_arr, skipFiniteCheck=self.config.skip_finite_check
            )

    def _update_view_range(self, data_points: List[Tuple[float, float]]) -> None:
        """
        Update plot range based on current mode.

        Args:
            data_points: All data points for range calculation
        """
        viewbox = self.getViewBox()
        if not viewbox or not self._plot_curve:
            return

        if self._auto_range_enabled:
            # Auto-range mode: let pyqtgraph handle it
            self._programmatic_update = True
            viewbox.enableAutoRange(enable=True)
            self._programmatic_update = False

        elif self._auto_scroll_enabled:
            # Auto-scroll mode: update periodically
            self._scroll_counter += 1
            if self._scroll_counter >= self.SCROLL_UPDATE_INTERVAL:
                self._scroll_counter = 0
                self._apply_scroll_view(data_points, viewbox)

        elif not self._user_interacted:
            # Initial range (manual mode, no user interaction yet)
            self._apply_initial_view(data_points, viewbox)

    def _apply_scroll_view(
        self, data_points: List[Tuple[float, float]], viewbox: Any
    ) -> None:
        """
        Apply scrolling view showing last N points.

        Args:
            data_points: All data points
            viewbox: PyQtGraph ViewBox instance
        """
        # Select data for display
        max_pts = self.config.max_plot_points
        display_data = (
            data_points[-max_pts:] if len(data_points) > max_pts else data_points
        )

        if not display_data:
            return

        x_range, y_range = self._calculate_range(display_data)

        self._programmatic_update = True
        viewbox.enableAutoRange(enable=False)
        viewbox.setRange(xRange=x_range, yRange=y_range, padding=0)
        self._programmatic_update = False

    def _apply_initial_view(
        self, data_points: List[Tuple[float, float]], viewbox: Any
    ) -> None:
        """
        Apply initial range for manual mode.

        Args:
            data_points: All data points
            viewbox: PyQtGraph ViewBox instance
        """
        max_pts = self.config.max_plot_points
        display_data = (
            data_points[-max_pts:] if len(data_points) > max_pts else data_points
        )

        if not display_data:
            return

        x_range, y_range = self._calculate_range(display_data)

        self._programmatic_update = True
        viewbox.enableAutoRange(enable=False)
        viewbox.setRange(xRange=x_range, yRange=y_range, padding=0.05)
        self._programmatic_update = False

    @staticmethod
    def _calculate_range(
        data_points: List[Tuple[float, float]],
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate axis ranges for data with smart padding.

        Args:
            data_points: Data points

        Returns:
            Tuple of (x_range, y_range) as [[min, max], [min, max]]
        """
        if not data_points:
            return [0, 1], [0, 1]

        x_vals = np.array([p[0] for p in data_points], dtype=np.float32)
        y_vals = np.array([p[1] for p in data_points], dtype=np.float32)

        x_min, x_max = float(x_vals.min()), float(x_vals.max())
        y_min, y_max = float(y_vals.min()), float(y_vals.max())

        # Smart padding
        def pad_range(vmin: float, vmax: float) -> Tuple[float, float]:
            if vmax == vmin:
                padding = max(1, abs(vmin) * 0.1)
                return (vmin - padding, vmax + padding)
            else:
                padding = (vmax - vmin) * 0.05
                return (vmin - padding, vmax + padding)

        x_min_p, x_max_p = pad_range(x_min, x_max)
        y_min_p, y_max_p = pad_range(y_min, y_max)

        return [x_min_p, x_max_p], [y_min_p, y_max_p]

    def append_data(self, x: float, y: float) -> None:
        """
        Append a single data point (streaming mode).

        More efficient than update_plot_data for single-point updates.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        if self._last_data_points:
            # Append to existing data
            self._last_data_points.append((x, y))
        else:
            # First point
            self._last_data_points = [(x, y)]

        # Use deferred update for efficiency in streaming
        self.update_plot_data([(x, y)], deferred=True)

    @Slot(str, str)
    def reconfigure(
        self,
        key: str = "",
        value: str = "",
    ) -> None:
        """
        Reconfigure plot appearance.

        Args:
            key: Config key (e.g., 'title', 'xlabel', 'ylabel', 'background_color')
            value: New value
        """
        if not key or value == "":
            Debug.warning("Plot reconfigure: Empty key or value")
            return

        if not hasattr(self.config, key):
            Debug.warning(f"Plot reconfigure: Unknown key '{key}'")
            return

        setattr(self.config, key, value)
        Debug.debug(f"Plot reconfigured: {key}={value}")

        # Apply changes
        if key == "title":
            self.setTitle(value)
        elif key == "xlabel":
            self.setLabel("bottom", value)
        elif key == "ylabel":
            self.setLabel("left", value)
        elif key == "background_color":
            self.setBackground(value)
        elif key == "grid_alpha":
            self.showGrid(x=True, y=True, alpha=float(value))


class HistogramWidget(pg.PlotWidget):
    """
    High-performance histogram widget using pyqtgraph.

    Provides efficient histogram visualization with automatic binning and
    range adjustment for frequency distribution analysis.

    Design based on pyqtgraph performance best practices.
    Uses PlotConfig for consistent configuration with GeneralPlot.

    Signals:
        histogram_updated: Emitted after update (int: number of bins)
        histogram_cleared: Emitted when histogram is cleared

    Slots:
        update_histogram: Update histogram with data
        clear_measurement_data: Clear histogram data
        reconfigure: Change labels and title

    Example:
        >>> config = PlotConfig(title="Distribution", xlabel="Value", ylabel="Frequency")
        >>> histogram = HistogramWidget(config=config)
        >>> histogram.update_histogram([1.2, 2.3, 1.8, 2.1, 1.9], bins=10)
    """

    # Signals for reactive UI integration
    histogram_updated = Signal(int)  # Emits number of bins
    histogram_cleared = Signal()

    # Performance tuning
    DEFAULT_BINS = 50

    def __init__(
        self,
        config: Optional[PlotConfig] = None,
        title: Optional[str] = None,
        xlabel: str = "Value",
        ylabel: str = "Count",
        background: Optional[str] = None,
        grid_alpha: float = 0.3,
    ):
        """
        Initialize the histogram widget.

        Supports both new (PlotConfig) and legacy parameter styles for backward compatibility.

        Args:
            config: PlotConfig object with histogram settings (preferred)
            title: Histogram title (optional, legacy parameter)
            xlabel: X-axis label (bin values, legacy parameter)
            ylabel: Y-axis label (frequency count, legacy parameter)
            background: Background color (None = system theme, legacy parameter)
            grid_alpha: Grid line transparency (0.0-1.0, legacy parameter)
        """
        super().__init__()

        # Handle both new PlotConfig style and legacy parameters
        if config is None:
            # Legacy parameter style: create PlotConfig from individual parameters
            self.config = PlotConfig(
                title=title,
                xlabel=xlabel,
                ylabel=ylabel,
                background_color=background,
                grid_alpha=grid_alpha,
            )
        else:
            # New PlotConfig style: use provided config
            self.config = config
            # Override with explicit parameters if provided
            if title is not None:
                self.config.title = title
            if xlabel != "Value":
                self.config.xlabel = xlabel
            if ylabel != "Count":
                self.config.ylabel = ylabel
            if background is not None:
                self.config.background_color = background
            if grid_alpha != 0.3:
                self.config.grid_alpha = grid_alpha

        # Internal state
        self._hist_item: Optional[pg.BarGraphItem] = None
        self._is_clearing = False
        self._pending_update = False
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._process_deferred_histogram_update)
        self._deferred_histogram_data: Optional[Tuple[np.ndarray, int, str]] = None

        # Performance: Track last bin count for optimization
        self._last_bin_count = 0

        # Configure appearance (matches GeneralPlot pattern)
        self._configure_appearance()

        Debug.debug("HistogramWidget initialized (dark mode aware, PlotConfig unified)")

    def _configure_appearance(self) -> None:
        """Configure histogram appearance based on config (matches GeneralPlot pattern)."""
        # Configure background (None = respect system theme/dark mode)
        if self.config.background_color:
            self.setBackground(self.config.background_color)

        # Configure grid
        self.showGrid(x=True, y=True, alpha=self.config.grid_alpha)

        # Configure labels
        self.setLabel("bottom", self.config.xlabel)
        self.setLabel("left", self.config.ylabel)

        # Configure title
        if self.config.title:
            self.setTitle(self.config.title)

        Debug.debug(
            f"Histogram appearance configured: title={self.config.title}, "
            f"alpha={self.config.grid_alpha}"
        )

    @Slot()
    def clear_measurement_data(self) -> None:
        """
        Clear histogram data and reset state.

        Call this before processing a new data series.
        """
        self._is_clearing = True
        Debug.debug("Clearing histogram data")

        try:
            if self._hist_item is not None:
                self.removeItem(self._hist_item)
                self._hist_item = None

        finally:
            self._is_clearing = False

        self.histogram_cleared.emit()

    def _process_deferred_histogram_update(self) -> None:
        """Process deferred histogram update from batch queue."""
        if self._deferred_histogram_data is None:
            return

        data_arr, bins, color = self._deferred_histogram_data
        self._deferred_histogram_data = None
        self._perform_histogram_update(data_arr, bins, color)

    def _perform_histogram_update(
        self, data_arr: np.ndarray, bins: int, color: str
    ) -> None:
        """Perform actual histogram update (internal method)."""
        if data_arr.size == 0:
            return

        try:
            # Calculate histogram using numpy (vectorized, very fast)
            hist, bin_edges = np.histogram(data_arr, bins=bins)

            # Reuse or create bar graph item (lazy initialization)
            if self._hist_item is None:
                # First time: create new item
                # Use x0 and x1 (bin edges) for precise bar placement
                self._hist_item = pg.BarGraphItem(
                    x0=bin_edges[:-1],
                    x1=bin_edges[1:],
                    height=hist,
                    brush=color,
                    pen="w",
                )
                self.addItem(self._hist_item)
                Debug.debug(f"Histogram created with {bins} bins")
            else:
                # Update existing item (no allocation, just data update)
                self._hist_item.setOpts(
                    x0=bin_edges[:-1],
                    x1=bin_edges[1:],
                    height=hist,
                    brush=color,
                    pen="w",
                )

            # Auto-range only if bin count changed (optimization)
            if bins != self._last_bin_count:
                self.autoRange()
                self._last_bin_count = bins

            # Emit signal
            self.histogram_updated.emit(bins)

        except Exception as e:  # pylint: disable=broad-except
            Debug.error(f"Error updating histogram: {e}")
        finally:
            self._pending_update = False

    @Slot(list, int, str)
    def update_histogram(
        self,
        data: Iterable[float],
        bins: int = DEFAULT_BINS,
        color: str = "w",
        deferred: bool = True,
    ) -> None:
        """
        Update histogram with new data (high-performance method).

        PERFORMANCE TIPS:
        - Convert lists to numpy arrays before calling for best speed
        - Use appropriate bin count (default 50 usually good)
        - Pre-filter data to remove NaN/inf for faster updates
        - Use deferred=True for burst updates (batches them together)

        Args:
            data: Values to create histogram from
            bins: Number of histogram bins (default: 50)
            color: Bar color (default: white)
            deferred: If True, batch updates together (16ms intervals)
        """
        if not data:
            Debug.debug("update_histogram called with empty data")
            return

        try:
            # Convert to numpy array for fast computation
            data_arr = np.asarray(data, dtype=np.float32)

            # Skip NaN and inf values for efficiency
            data_arr = data_arr[np.isfinite(data_arr)]

            if deferred:
                # Batch updates together to reduce overhead
                self._deferred_histogram_data = (data_arr, bins, color)
                if not self._update_timer.isActive():
                    self._update_timer.start(16)  # ~60 FPS
                return

            # Immediate update
            self._perform_histogram_update(data_arr, bins, color)

        except Exception as e:  # pylint: disable=broad-except
            Debug.error(f"Error in update_histogram: {e}")

    @Slot(str, str)
    def reconfigure(
        self,
        key: str = "",
        value: str = "",
    ) -> None:
        """
        Reconfigure histogram appearance (unified with GeneralPlot pattern).

        Args:
            key: Config key (e.g., 'title', 'xlabel', 'ylabel', 'background_color', 'grid_alpha')
            value: New value

        Legacy signature still supported:
            reconfigure(title=..., xlabel=..., ylabel=...)
        """
        # Handle legacy signature: reconfigure(title, xlabel, ylabel)
        # In this case, key will be title and value might be unused
        if key and not value and isinstance(key, str) and key != "":
            # Legacy call: reconfigure(title_value)
            self.config.title = key
            self.setTitle(key)
            Debug.debug(f"Histogram reconfigured (legacy): title={key}")
            return

        # New unified signature
        if not key or value == "":
            Debug.warning("Histogram reconfigure: Empty key or value")
            return

        if not hasattr(self.config, key):
            Debug.warning(f"Histogram reconfigure: Unknown key '{key}'")
            return

        setattr(self.config, key, value)
        Debug.debug(f"Histogram reconfigured: {key}={value}")

        # Apply changes
        if key == "title":
            self.setTitle(value)
        elif key == "xlabel":
            self.setLabel("bottom", value)
        elif key == "ylabel":
            self.setLabel("left", value)
        elif key == "background_color":
            self.setBackground(value)
        elif key == "grid_alpha":
            self.showGrid(x=True, y=True, alpha=float(value))


# ============================================================
# BACKWARD COMPATIBILITY ALIAS
# ============================================================
# For existing code that imports PlotWidget, provide an alias
# to the new GeneralPlot class. This ensures a smooth transition.
PlotWidget = GeneralPlot
