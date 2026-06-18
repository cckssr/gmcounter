# Layer: ui/tabs — TabRegistry (§6).
"""Runtime registry of frame-based experiment tab classes (§6).

Sweep tabs (:class:`~gmcounter.ui.tabs.parameter_sweep_base.ParameterSweepTabBase`
subclasses) are wired explicitly in ``MainWindow`` and are **not** registered
here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import PlotTabBase

_log = logging.getLogger(__name__)


class TabRegistry:
    """Class-level registry of experiment tab classes.

    Adding a new experiment is three steps:
      1. Subclass PlotTabBase, implement build() and on_frame().
      2. TabRegistry.register(MyTab) at import time.
      3. MainWindow iterates available() — the new tab appears.

    Tabs with required_modules = {"kdc101"} only appear when the matching
    module is registered in ModuleRegistry at runtime.
    """

    _tabs: list[type[PlotTabBase]] = []

    @classmethod
    def register(cls, tab_class: type[PlotTabBase]) -> None:
        """Register *tab_class* (no-op if already registered)."""
        if tab_class not in cls._tabs:
            cls._tabs.append(tab_class)
            _log.debug(
                "Registered tab: %s", getattr(tab_class, "tab_id", repr(tab_class))
            )

    @classmethod
    def available(cls, modules: dict[str, object]) -> list[type[PlotTabBase]]:
        """Return tab classes whose required_modules are all present in *modules*."""
        return [t for t in cls._tabs if t.required_modules.issubset(modules.keys())]

    @classmethod
    def all_registered(cls) -> list[type[PlotTabBase]]:
        """Return all registered tab classes regardless of module availability."""
        return list(cls._tabs)

    @classmethod
    def clear(cls) -> None:
        """Remove all registrations (useful in tests)."""
        cls._tabs.clear()
