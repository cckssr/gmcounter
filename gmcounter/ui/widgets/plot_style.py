"""Look of the pyqtgraph plots: palette-following chrome and the configured colour set.

Background, axes, tick labels and legends follow the application palette (``QPalette.Window`` /
``QPalette.WindowText``), so light and dark themes both work; :func:`style_plot` applies them and
installs an event filter that restyles the plot when the application palette changes.

Curve colours come from the ``plot_colors`` section of config.json (:func:`plot_colors`):

* ``series``: list of colours for several curves in one plot (matplotlib's ``tab10`` by default),
* ``fit``: model / fit curves, ``reference``: reference lines and bands, ``marker``: highlighted
  points and markers,
* ``band_alpha`` / ``point_alpha``: opacity (0-255) of shaded bands and scatter points.

A colour is ``[r, g, b]`` (0-255), a hex string (``"#1f77b4"``) or a name of matplotlib's default
colour cycle (``"tab:blue"`` ... ``"tab:cyan"`` or ``"C0"`` ... ``"C9"``); matplotlib itself is not
needed. Missing or malformed entries become grey and are logged.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import pyqtgraph as pg
from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QWidget

from gmcounter.infrastructure.config import AppConfig, default_config

_log = logging.getLogger(__name__)

Rgb = tuple[int, int, int]

_FALLBACK: Rgb = (160, 160, 160)  # used (and logged) for a missing or malformed entry
_AXES = ("left", "bottom", "right", "top")

# matplotlib's default colour cycle ("tab10"), in cycle order: C0 ... C9
TAB10 = (
    ("tab:blue", "#1f77b4"),
    ("tab:orange", "#ff7f0e"),
    ("tab:green", "#2ca02c"),
    ("tab:red", "#d62728"),
    ("tab:purple", "#9467bd"),
    ("tab:brown", "#8c564b"),
    ("tab:pink", "#e377c2"),
    ("tab:gray", "#7f7f7f"),
    ("tab:olive", "#bcbd22"),
    ("tab:cyan", "#17becf"),
)
_NAMED = {name: hex_ for name, hex_ in TAB10} | {
    f"C{i}": hex_ for i, (_, hex_) in enumerate(TAB10)
}
_HEX = re.compile(r"#[0-9a-fA-F]{6}")


# ── Colour set (plot_colors in config.json) ──────────────────────────────────


def _rgb(value: Any, key: str) -> Rgb:
    if isinstance(value, str):
        text = _NAMED.get(value, value)
        if _HEX.fullmatch(text):
            return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))
    elif (
        isinstance(value, (list, tuple))
        and len(value) == 3
        and all(
            isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255
            for c in value
        )
    ):
        return (value[0], value[1], value[2])
    _log.warning(
        f"plot_colors.{key} must be [r, g, b], '#rrggbb', 'tab:<name>' or 'C0'-'C9', got {value!r}"
    )
    return _FALLBACK


def _rgb_list(value: Any, key: str) -> tuple[Rgb, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        _log.warning(f"plot_colors.{key} must be a list of colours, got {value!r}")
        return (_FALLBACK,)
    return tuple(_rgb(v, f"{key}[{i}]") for i, v in enumerate(value))


def _alpha(value: Any, key: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 255:
        return value
    _log.warning(f"plot_colors.{key} must be an integer 0-255, got {value!r}")
    return 255


@dataclass(frozen=True)
class PlotColors:
    """Resolved colour set of the plots."""

    series: tuple[Rgb, ...]
    fit: Rgb
    reference: Rgb
    marker: Rgb
    band_alpha: int
    point_alpha: int

    @classmethod
    def from_config(cls, config: AppConfig) -> PlotColors:
        """Colours of ``config``; a missing or malformed entry becomes grey (logged)."""
        section = config.section("plot_colors")
        return cls(
            series=_rgb_list(section.get("series"), "series"),
            fit=_rgb(section.get("fit"), "fit"),
            reference=_rgb(section.get("reference"), "reference"),
            marker=_rgb(section.get("marker"), "marker"),
            band_alpha=_alpha(section.get("band_alpha"), "band_alpha"),
            point_alpha=_alpha(section.get("point_alpha"), "point_alpha"),
        )

    def series_color(self, index: int) -> Rgb:
        """Colour of curve ``index`` (the list is cycled)."""
        return self.series[index % len(self.series)]


_current: PlotColors | None = None


def set_plot_colors(colors: PlotColors | None) -> None:
    """Colour set for plots created from now on (``None``: the packaged default again)."""
    global _current
    _current = colors


def plot_colors() -> PlotColors:
    """The active colour set; the colours of the packaged config.json if none was set."""
    global _current
    if _current is None:
        _current = PlotColors.from_config(default_config())
    return _current


# ── Palette following ────────────────────────────────────────────────────────


def palette_colors() -> tuple[QColor, QColor]:
    """Background and foreground colour of the application palette."""
    palette = QGuiApplication.palette()
    return palette.color(QPalette.ColorRole.Window), palette.color(
        QPalette.ColorRole.WindowText
    )


def _plot_items(widget: Any) -> list[Any]:
    """The ``PlotItem`` s shown by a ``PlotWidget`` or a ``GraphicsLayoutWidget``."""
    if hasattr(widget, "getPlotItem"):
        plot_item = widget.getPlotItem()  # None once the widget has been closed
        return [] if plot_item is None else [plot_item]
    layout = getattr(widget, "ci", None)
    items = getattr(layout, "items", {})
    return [item for item in items if isinstance(item, pg.PlotItem)]


def _apply(widget: Any) -> None:
    background, foreground = palette_colors()
    widget.setBackground(background)
    for plot_item in _plot_items(widget):
        for name in _AXES:
            axis = plot_item.getAxis(name)
            axis.setPen(foreground)
            axis.setTextPen(foreground)
        title = getattr(plot_item, "titleLabel", None)
        if title is not None and title.text:
            title.setText(title.text, color=foreground)
        legend = getattr(plot_item, "legend", None)
        if legend is not None:
            legend.setLabelTextColor(foreground)


class _PaletteWatcher(QObject):
    """Restyles its plot widget whenever the application palette changes."""

    _EVENTS = (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange)

    def __init__(self, widget: QWidget) -> None:
        super().__init__(widget)
        self._widget = widget

    def eventFilter(
        self, watched: QObject, event: QEvent
    ) -> bool:  # noqa: N802 (Qt API)
        if watched is self._widget and event.type() in self._EVENTS:
            try:
                _apply(self._widget)
            except (
                RuntimeError
            ):  # the plot is being torn down; its Qt items are already gone
                _log.debug("plot already deleted while restyling")
        return False


def style_plot(widget: Any) -> None:
    """Colour a ``PlotWidget`` / ``GraphicsLayoutWidget`` from the application palette.

    Call it once after the plot (and its legend) has been created; it keeps following palette
    changes afterwards. Calling it again only reapplies the colours.
    """
    _apply(widget)
    if not any(isinstance(child, _PaletteWatcher) for child in widget.children()):
        widget.installEventFilter(_PaletteWatcher(widget))
