"""Dock panels: group boxes with their own Designer form, driven by the main window.

Panels only build their form, apply the configured strings, expose intent signals and small
setters; they never talk to devices.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter


def fill_combo(combo: QComboBox, items: Iterable[str], *, keep_empty: bool) -> None:
    """Replace the items of ``combo``; ``keep_empty`` leaves it without a selection."""
    combo.clear()
    combo.addItems([str(item) for item in items])
    if keep_empty:
        combo.setCurrentIndex(-1)


def set_contains_completer(combo: QComboBox, items: Iterable[str]) -> None:
    """Attach a case-insensitive "contains" completer for ``items`` to an editable combo."""
    completer = QCompleter([str(item) for item in items], combo)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    combo.setCompleter(completer)
