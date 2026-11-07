"""The Designer forms carry the German strings from config.json and open on their own.

Regenerate out-of-date forms with ``gmcounter/pyqt/pyuic.sh``."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from gmcounter.infrastructure.config import load_config
from gmcounter.pyqt.preview import build_form
from gmcounter.pyqt.sync_texts import PYQT_DIR, synced_text

FORMS = sorted(path.stem for path in PYQT_DIR.glob("*.ui"))

# Forms whose strings still live in the .ui file; remove the stem once its texts moved to
# config.json (``ui.<form>``). One form per line.
NOT_YET_MIGRATED = {
    "alert",
    "connection",
    "control",
    "mainwindow",
}

# Designer property -> config key suffix understood by ``apply_strings``.
_TEXT_PROPERTIES = {
    "text": "",
    "title": "",
    "windowTitle": "",
    "toolTip": "@tooltip",
    "suffix": "@suffix",
    "prefix": "@prefix",
    "placeholderText": "@placeholder",
}
_LETTER = re.compile(r"[^\W\d_]")


def _hard_coded_texts(path) -> list[str]:
    """Descriptions of text properties in the form that no config string provides."""
    root = ET.parse(path).getroot()
    strings = load_config().section("ui").get(path.stem, {})
    top = root.find("widget")
    problems = []
    for element in root.iter():
        if element.tag not in ("widget", "action") or not element.get("name"):
            continue
        name = "self" if element is top else element.get("name")
        for prop in element.findall("property"):
            suffix = _TEXT_PROPERTIES.get(prop.get("name"))
            node = prop.find("string")
            if suffix is None or node is None or not _LETTER.search(node.text or ""):
                continue
            if prop.get("name") == "windowTitle" and element is top:
                suffix = "@title"
            if strings.get(f"{name}{suffix}") != node.text:
                problems.append(f"{name}.{prop.get('name')}={node.text!r}")
        for attr in element.findall("attribute"):
            node = attr.find("string")
            if attr.get("name") == "title" and node is not None and node.text:
                if strings.get(f"{name}@tab") != node.text:
                    problems.append(f"{name}.tab={node.text!r}")
    return problems


@pytest.mark.parametrize("form", FORMS)
def test_form_texts_match_config(form: str) -> None:
    path = PYQT_DIR / f"{form}.ui"
    assert synced_text(path, load_config()) == path.read_text(encoding="utf-8")


@pytest.mark.parametrize("form", FORMS)
def test_form_opens_without_logic(qtbot, form: str) -> None:
    widget = build_form(form)
    qtbot.addWidget(widget)
    widget.show()


@pytest.mark.parametrize("form", [f for f in FORMS if f not in NOT_YET_MIGRATED])
def test_every_ui_text_comes_from_config(form: str) -> None:
    assert _hard_coded_texts(PYQT_DIR / f"{form}.ui") == []
