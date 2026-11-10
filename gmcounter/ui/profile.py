"""Profiles (``profiles`` in config.json): hide the tabs and widgets a profile does not need.

The renamed texts of a profile are plain config overrides merged by ``load_config``; this module
only hides things. Widgets are addressed by Designer object name below a *root*: the main
window, one of the dock panels (``connection_panel``, ``device_panel``, ``device_status_panel`` ...) or a tab id
(``gm_timing``). There is no second code path: a hidden control keeps its default value.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QBoxLayout, QWidget

if TYPE_CHECKING:
    from gmcounter.ui.windows.main_window import MainWindow

_log = logging.getLogger(__name__)


def profile_roots(window: MainWindow) -> dict[str, QObject]:
    """The objects ``hidden_widgets`` may refer to (the tabs are keyed by their tab id)."""
    ui = window.ui
    return {
        "main_window": window,
        "connection_panel": ui.connectionPanel,
        "device_panel": ui.devicePanel,
        "sample_panel": ui.samplePanel,
        "measurement_panel": ui.measurementPanel,
        "readout_panel": ui.readoutPanel,
        "device_status_panel": ui.deviceStatusPanel,
        "event_log_panel": ui.eventLogPanel,
        **window.tabs,
    }


def _keep_rows_left_aligned(root: QObject, hidden: QWidget) -> None:
    """A box layout row whose only stretching item is now hidden would spread the remaining
    items over the whole width: give the row a trailing stretch instead."""
    for layout in root.findChildren(QBoxLayout):
        index = layout.indexOf(hidden)
        if index < 0 or layout.stretch(index) <= 0:
            continue

        def stretches(i: int, layout: QBoxLayout = layout) -> bool:
            if layout.stretch(i) <= 0:
                return False
            widget = layout.itemAt(i).widget()
            return (
                widget is None or not widget.isHidden()
            )  # a spacer or a visible widget

        if not any(stretches(i) for i in range(layout.count()) if i != index):
            layout.addStretch(1)


def apply_profile(window: MainWindow) -> list[str]:
    """Hide the widgets of the active profile; returns the names that could not be found
    (``root.name``), which are also logged: a typo must not pass silently."""
    cfg = window.config
    roots = profile_roots(window)
    missing: list[str] = []
    for root_name, names in cfg.hidden_widgets().items():
        root = roots.get(root_name)
        if root is None:
            if root_name not in cfg.hidden_tabs():
                _log.warning("profile %r: unknown root %r", cfg.profile, root_name)
                missing.append(root_name)
            continue
        for name in names:
            target = root.findChild(QObject, name)
            if isinstance(target, (QWidget, QAction)):
                target.setVisible(False)
                if isinstance(target, QWidget):
                    _keep_rows_left_aligned(root, target)
            else:
                _log.warning(
                    "profile %r: no widget %r in %r", cfg.profile, name, root_name
                )
                missing.append(f"{root_name}.{name}")
    return missing


def next_profile(current: str, names: list[str]) -> str:
    """The profile the switch action leads to (cycles through ``names``)."""
    if current not in names or len(names) < 2:
        return current
    return names[(names.index(current) + 1) % len(names)]
