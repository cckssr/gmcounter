# Layer: ui/tabs — TabRegistry (§6).

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import PlotTabBase

_log = logging.getLogger(__name__)

_T = TypeVar("_T")
DEFAULT_ORDER = 100


class TabRegistry:
    """Class-level registry of experiment tab classes.

    Adding a new experiment is two steps:
      1. Subclass PlotTabBase (``tab_id``, ``order``, ``session_kind``, its own form).
      2. Decorate the class with ``@TabRegistry.register`` and import its module in
         ``gmcounter/ui/tabs/__init__.py``.

    The main window iterates ``available()`` (sorted by ``order``), so it never names a
    concrete tab. Tabs with ``required_modules = {"kdc101"}`` only appear when the matching
    module is registered in ModuleRegistry at runtime.
    """

    _tabs: list[type[PlotTabBase]] = []

    @classmethod
    def register(cls, tab_class: _T) -> _T:
        """Register ``tab_class``; usable as a class decorator (returns the class)."""
        if tab_class not in cls._tabs:
            cls._tabs.append(tab_class)  # type: ignore[arg-type]
            _log.debug("Registered tab: %s", tab_class.tab_id)  # type: ignore[attr-defined]
        return tab_class

    @classmethod
    def available(cls, modules: dict[str, object]) -> list[type[PlotTabBase]]:
        """Tab classes whose required_modules are all in *modules*, sorted by ``order``."""
        usable = [t for t in cls._tabs if t.required_modules.issubset(modules.keys())]
        return sorted(usable, key=lambda t: getattr(t, "order", DEFAULT_ORDER))

    @classmethod
    def all_registered(cls) -> list[type[PlotTabBase]]:
        return list(cls._tabs)

    @classmethod
    def clear(cls) -> None:
        """Remove all registrations (useful in tests)."""
        cls._tabs.clear()
