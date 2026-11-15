"""Owns the main window and rebuilds it when the user switches the profile."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from ..infrastructure.config import load_config
from ..infrastructure.device_manager import DeviceManager
from ..infrastructure.simulation import SimulatedCounter
from .windows.main_window import MainWindow

_log = logging.getLogger(__name__)


class Launcher(QObject):
    """Creates the main window for a profile and swaps it for another one on request.

    The launcher owns the ``DeviceManager`` (and, with ``simulate``, the simulated counter)
    for the whole run; the user connects in the window's connection panel. A switch closes the
    old window without disconnecting the device, builds the new window from
    ``load_config(profile=...)`` on the SAME ``DeviceManager`` (still connected) and keeps the
    window mode (full screen, maximised, normal). It is refused while a measurement runs or
    unsaved data exists, so the close never asks the unsaved-data question.
    """

    def __init__(
        self,
        device_manager: DeviceManager | None = None,
        profile: str | None = None,
        window_mode: str | None = None,
        persist: bool = True,
        overrides: dict[str, Any] | None = None,
        parent: QObject | None = None,
        *,
        simulate: bool = False,
    ) -> None:
        super().__init__(parent)
        self._device_manager = device_manager or DeviceManager()
        self.simulation: SimulatedCounter | None = None
        if simulate:
            self.simulation = SimulatedCounter()
            self.simulation.start()
        self._profile = profile
        self._window_mode = window_mode
        self._persist = persist
        self._overrides = overrides
        self.window: MainWindow | None = None

    def start(self) -> MainWindow:
        """Build and show the first window."""
        return self._open(self._profile, self._window_mode)

    def _open(self, profile: str | None, window_mode: str | None) -> MainWindow:
        config = load_config(profile=profile, overrides=self._overrides)
        window = MainWindow(
            config,
            self._device_manager,
            persist=self._persist,
            simulation=self.simulation,
        )
        window.profile_switch_requested.connect(self._on_switch_requested)
        window.show_initial(window_mode)
        self.window = window
        _log.info("profile %s", config.profile)
        return window

    def _on_switch_requested(self, profile: str) -> None:
        # not inside the slot of the window that is about to be destroyed
        QTimer.singleShot(0, lambda: self.switch_to(profile))

    def switch_to(self, profile: str) -> MainWindow | None:
        """Rebuild the window with ``profile``; returns the window that is current afterwards."""
        old = self.window
        if old is None or old.config.profile == profile:
            return old
        blocker = old.switch_blocker()
        if blocker:
            old.notify(blocker, "orange")
            return old
        mode = (
            "fullscreen"
            if old.isFullScreen()
            else "maximized"
            if old.isMaximized()
            else "normal"
        )
        app = QApplication.instance()
        if app is not None:
            app.setQuitOnLastWindowClosed(False)  # closing the old window must not quit
        try:
            if not old.close_for_switch():
                return old
            old.deleteLater()
            return self._open(profile, mode)
        finally:
            if app is not None:
                app.setQuitOnLastWindowClosed(True)

    def shutdown(self) -> None:
        """Stop the simulated counter (application exit; the window closed the port)."""
        if self.simulation is not None:
            self.simulation.stop()
            self.simulation = None
