"""Message texts for UI modules that have no ``AppConfig`` at hand.

The texts live in the ``messages`` section of config.json; a missing key yields the key itself
(visible, not fatal), like ``AppConfig.message``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ...infrastructure.config import import_config


@lru_cache(maxsize=1)
def _messages() -> dict[str, Any]:
    section = import_config().get("messages", {})
    return section if isinstance(section, dict) else {}


def message(key: str, **fmt: Any) -> str:
    """Message ``key`` from config.json, formatted with ``fmt``."""
    value = _messages().get(key, key)
    text = value if isinstance(value, str) else key
    return text.format(**fmt) if fmt else text
