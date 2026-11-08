"""No hard-coded German in the UI code: user-visible texts live in config.json."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import gmcounter

ROOT = Path(gmcounter.__file__).parent
GERMAN = re.compile(r"[äöüÄÖÜß]")
# Unavoidable German literals, as "relative/path.py": {"literal", ...}. Keep empty if possible.
ALLOWED: dict[str, set[str]] = {}


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def _german_literals(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = _docstring_nodes(tree)
    found = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and GERMAN.search(node.value)
        ):
            found.append((node.lineno, node.value))
    return found


def _files() -> list[Path]:
    # generated Designer modules (gmcounter/pyqt) are not scanned: strings come from the forms
    return sorted((ROOT / "ui").rglob("*.py")) + [ROOT / "main.py"]


def test_no_german_string_literals_in_the_ui_code():
    offenders = []
    for path in _files():
        rel = path.relative_to(ROOT).as_posix()
        for line, text in _german_literals(path):
            if text not in ALLOWED.get(rel, set()):
                offenders.append(f"{rel}:{line}: {text[:60]!r}")
    assert offenders == [], "German literals (move them to config.json):\n" + "\n".join(
        offenders
    )


def test_the_scan_sees_a_german_literal(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text('"""Doc mit Umlaut ä."""\nx = "Größe"\n# Kommentar ü\n')
    assert _german_literals(sample) == [(2, "Größe")]
