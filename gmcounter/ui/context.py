"""Shared state handed to the tabs: configuration, controllers and small accessors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from gmcounter.infrastructure.config import AppConfig

if TYPE_CHECKING:
    from gmcounter.core.services import SaveService
    from gmcounter.infrastructure.device_manager import DeviceManager
    from gmcounter.ui.common.file_dialogs import FileDialogManager
    from gmcounter.ui.controllers.app_controller import AppController
    from gmcounter.ui.tabs.gm_timing_tab import GMTimingTab


def _no_voltage() -> float:
    return 0.0


def _no_settings() -> dict:
    return {}


@dataclass
class AppContext:
    """What a tab may use of the application; the main window fills it in.

    ``timing`` is set as soon as the timing tab is built (the sweep tabs read the acquired
    data from it). The three callables hide the panels from the tabs: the live voltage
    read-back (V), the entered device settings and the entered sample metadata.
    """

    config: AppConfig
    device_manager: DeviceManager | None = None
    ctrl: AppController | Any | None = None
    save_service: SaveService | None = None
    file_dialogs: FileDialogManager | None = None
    timing: GMTimingTab | Any | None = None
    voltage_readback: Callable[[], float] = field(default=_no_voltage)
    device_settings: Callable[[], dict] = field(default=_no_settings)
    sample_metadata: Callable[[], dict] = field(default=_no_settings)
