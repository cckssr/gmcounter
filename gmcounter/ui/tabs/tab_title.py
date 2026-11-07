"""Config-driven tab titles: ``ui.tabs.<tab_id>`` in config.json."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from gmcounter.infrastructure.config import default_config

if TYPE_CHECKING:
    from gmcounter.ui.tabs.base import PlotTabBase


class TabTitle:
    """Class attribute that resolves a tab's German title from the configuration.

    On an instance the tab's own ``config`` is used; on the class (``GMTimingTab.title``) the
    cached ``default_config()``.
    """

    @overload
    def __get__(self, obj: None, owner: type[PlotTabBase]) -> str: ...

    @overload
    def __get__(self, obj: PlotTabBase, owner: type[PlotTabBase]) -> str: ...

    def __get__(self, obj: PlotTabBase | None, owner: type[PlotTabBase]) -> str:
        """Return the configured title of ``owner.tab_id`` (falls back to the key path)."""
        config = obj.config if obj is not None else default_config()
        return config.text(f"tabs.{owner.tab_id}")
