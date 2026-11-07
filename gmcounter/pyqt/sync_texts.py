"""Write the German UI strings from config.json into the Designer ``.ui`` files.

At run time the texts are applied by ``gmcounter.ui.i18n.apply_strings``; the forms themselves
carry no text, so Qt Creator / Designer shows empty buttons and labels. This tool copies the
strings that ``apply_strings`` would set into the matching ``.ui`` properties, so the forms are
readable while editing. ``config.json`` stays the source of truth: texts typed in Designer are
overwritten by the next run.

    .venv/bin/python -m gmcounter.pyqt.sync_texts           # update the .ui files
    .venv/bin/python -m gmcounter.pyqt.sync_texts --check   # exit 1 if a .ui is stale

``gmcounter/pyqt/pyuic.sh`` runs this before regenerating the ``ui_*.py`` modules.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from gmcounter.infrastructure.config import AppConfig, load_config

PYQT_DIR = Path(__file__).resolve().parent

# .ui file stem -> sections of the ``ui`` config that the code applies to it; the default is
# the stem itself (e.g. ``"a_scan_tab": ("a_scan_actions",)``).
SECTIONS: dict[str, tuple[str, ...]] = {}

# ``name@kind`` suffix -> Designer property.
_KIND_PROPERTIES = {
    "tooltip": "toolTip",
    "suffix": "suffix",
    "prefix": "prefix",
    "placeholder": "placeholderText",
    "title": "windowTitle",
}
# Widgets whose caption is not ``text``: group boxes have ``title``, docks use ``windowTitle``.
_TITLE_PROPERTIES = {"QGroupBox": "title", "QDockWidget": "windowTitle"}


def _property_for(kind: str, class_name: str) -> str:
    if kind:
        return _KIND_PROPERTIES.get(kind, "")
    return _TITLE_PROPERTIES.get(class_name, "text")


def _set_string_property(element: ET.Element, name: str, text: str) -> None:
    for prop in element.findall("property"):
        if prop.get("name") == name:
            string = prop.find("string")
            if string is None:
                string = ET.SubElement(prop, "string")
            string.text = text
            string.attrib.pop("notr", None)
            return
    prop = ET.Element("property", name=name)
    ET.SubElement(prop, "string").text = text
    last = max(
        (i for i, child in enumerate(element) if child.tag == "property"), default=-1
    )
    element.insert(last + 1, prop)


def _set_string_attribute(element: ET.Element, name: str, text: str) -> None:
    for attr in element.findall("attribute"):
        if attr.get("name") == name:
            string = attr.find("string")
            if string is None:
                string = ET.SubElement(attr, "string")
            string.text = text
            string.attrib.pop("notr", None)
            return
    attr = ET.Element("attribute", name=name)
    ET.SubElement(attr, "string").text = text
    element.insert(0, attr)


def sync_text(source: str, strings: dict[str, object]) -> str:
    """Return the ``.ui`` XML ``source`` with the plain-string entries of ``strings`` applied."""
    root = ET.fromstring(source)
    top = root.find("widget")
    elements = {
        element.get("name"): element
        for element in root.iter()
        if element.tag in ("widget", "action") and element.get("name")
    }
    for key, text in strings.items():
        name, _, kind = key.partition("@")
        if "_" in name or not isinstance(text, str):
            continue
        element = top if name == "self" else elements.get(name)
        if element is None:
            continue
        if kind == "tab":  # a tab page's title is an <attribute>, not a <property>
            _set_string_attribute(element, "title", text)
            continue
        prop = _property_for(kind, element.get("class", "QAction"))
        if prop:
            _set_string_property(element, prop, text)
    ET.indent(root, space=" ")
    body = re.sub(
        r"<(\w+)([^<>]*?) />", r"<\1\2/>", ET.tostring(root, encoding="unicode")
    )
    # Qt writes a double quote in element text as ``&quot;`` (ElementTree leaves it bare).
    body = re.sub(
        r">([^<]*)<", lambda m: ">" + m.group(1).replace('"', "&quot;") + "<", body
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}\n'


def synced_text(path: Path, config: AppConfig) -> str:
    """Content of the form ``path`` with the configured strings of its ``ui`` sections applied.

    A form whose config sections are empty or missing is returned unchanged.
    """
    strings: dict[str, object] = {}
    for section in SECTIONS.get(path.stem, (path.stem,)):
        strings.update(config.section("ui").get(section, {}))
    source = path.read_text(encoding="utf-8")
    if not strings:  # form not migrated yet: leave the file byte-for-byte untouched
        return source
    return sync_text(source, strings)


def main(argv: list[str] | None = None) -> int:
    """Update (or with ``--check`` verify) all forms; returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check", action="store_true", help="only report out-of-date files"
    )
    parser.add_argument("forms", nargs="*", help="form stems to handle (default: all)")
    args = parser.parse_args(argv)
    config = load_config()
    stale = 0
    paths = [PYQT_DIR / f"{stem}.ui" for stem in args.forms] or sorted(
        PYQT_DIR.glob("*.ui")
    )
    for path in paths:
        new = synced_text(path, config)
        if new == path.read_text(encoding="utf-8"):
            continue
        stale += 1
        if args.check:
            print(f"out of date: {path.name}")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"updated {path.name}")
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
