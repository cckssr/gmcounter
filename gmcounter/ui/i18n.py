"""Apply the German UI strings from config.json to widgets built from Designer forms.

Keys are Designer object names (camelCase, no underscore; ``self`` is the root widget);
``name@kind`` selects another property: ``@tooltip``, ``@suffix``, ``@prefix``,
``@placeholder``, ``@title`` (window title), ``@tab`` (the title of a tab page in its
``QTabWidget``).
Keys with an underscore (e.g. ``plot_y_label``) are plain texts looked up by the code and are
skipped here.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDockWidget, QTabWidget, QWidget

_log = logging.getLogger(__name__)


def apply_strings(root: QObject, strings: Mapping[str, object]) -> None:
    """Set the texts of ``strings`` on the children of ``root`` (see the module docstring)."""
    for key, text in strings.items():
        name, _, kind = key.partition("@")
        if "_" in name or not isinstance(text, str):
            continue
        obj: QObject | None = root if name == "self" else root.findChild(QObject, name)
        if obj is None:
            _log.warning(f"ui string for unknown object {name!r}")
            continue
        if kind == "tooltip":
            obj.setToolTip(text)  # type: ignore[attr-defined]
        elif kind == "suffix":
            obj.setSuffix(text)  # type: ignore[attr-defined]
        elif kind == "prefix":
            obj.setPrefix(text)  # type: ignore[attr-defined]
        elif kind == "placeholder":
            obj.setPlaceholderText(text)  # type: ignore[attr-defined]
        elif kind == "title":
            obj.setWindowTitle(text)  # type: ignore[attr-defined]
        elif kind == "tab":
            if not _set_tab_title(obj, text):
                _log.warning(f"ui string {key!r}: {name!r} is not a tab page")
        elif isinstance(obj, QDockWidget):
            obj.setWindowTitle(text)
        elif hasattr(obj, "setTitle"):
            obj.setTitle(text)
        elif hasattr(obj, "setText"):
            obj.setText(text)
        else:
            _log.warning(f"cannot set text on {name!r}")


def _set_tab_title(page: QObject, text: str) -> bool:
    """Set the tab text of ``page`` in the nearest enclosing ``QTabWidget``."""
    if not isinstance(page, QWidget):
        return False
    parent = page.parentWidget()
    while parent is not None and not isinstance(parent, QTabWidget):
        parent = parent.parentWidget()
    if parent is None or (index := parent.indexOf(page)) < 0:
        return False
    parent.setTabText(index, text)
    return True
