# docs-sync — Documentation maintenance skill

Invoked with `/docs-sync`. Keeps the documentation set in sync after code changes.

---

## Doc-map: what owns what

| Source of truth                          | What it documents                                                     |
| ---------------------------------------- | --------------------------------------------------------------------- |
| `CLAUDE.md`                              | Dev commands, architecture rules, layer table, extension points       |
| `ARCHITECTURE.md`                        | Design decisions, module contracts, signal flows, §-references        |
| `PRINCIPLES.md`                          | Project-agnostic PySide/Qt + firmware rules with rationale            |
| `README.md`                              | Project overview, install, demo mode, badges                          |
| `CONTRIBUTING.md`                        | PR flow, auto-versioning labels, UI-first workflow, firmware          |
| `docs/index.rst`                         | Sphinx toctree root                                                   |
| `docs/api.rst`                           | `automodule` entries for all 38 `gmcounter/**/*.py` modules           |
| `docs/hardware/firmware.rst`             | SCPI command table, PlatformIO envs, native Unity tests               |
| `docs/hardware/gm-counter-protocol.rst`  | Binary protocol (start/data/end markers)                              |
| Other `docs/*.rst`                       | User-facing guides — delegate to the markdown sources via `{include}` |
| Google docstrings in `gmcounter/**/*.py` | Rendered by Sphinx `automodule` into `docs/api.rst`                   |

---

## After a code change — what to update

### Added / renamed a public symbol (function, class, property)

- Add/update a Google-style docstring in the source file.
- If it's a **new module**, add an `automodule` entry to `docs/api.rst`.

### Changed architecture or layer contract

- Update `ARCHITECTURE.md` (§-references stay stable).
- If the change affects the portable rule, also update `PRINCIPLES.md`.
- `CLAUDE.md` should be updated for anything affecting dev workflow.

### Changed the binary protocol or SCPI commands

- Update `docs/hardware/gm-counter-protocol.rst` (protocol) and/or
  `docs/hardware/firmware.rst` (SCPI table comes from `firmware/src/scpi.cpp`).

### Added a new experiment tab

- Add the `automodule` entry to `docs/api.rst` under the appropriate section.
- Update `ARCHITECTURE.md` if the tab pattern introduces a new contract.
- The `CLAUDE.md` "Adding a … tab" section may need updating.

### Changed UI layout (`.ui` file)

- Run `bash gmcounter/pyqt/pyuic.sh` to regenerate `pyqt/ui_*.py`.
- Never hand-edit generated files.

### Bumped version

- `pyproject.toml`, `gmcounter/__init__.py`, and `gmcounter/config.json` (key `de.application.version`) must all agree.
- The auto-release workflow handles this on merge; only fix manually if you edited them by hand.

---

## Rebuild docs locally

```bash
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html -W
open docs/_build/html/index.html
```

Warnings-as-errors (`-W`) catches dead `toctree` entries, missing `automodule` targets, and broken `{include}` paths.

---

## Docstring style

Google convention (enforced by `ruff` with `pydocstyle.convention = "google"`):

```python
def my_func(arg: int) -> str:
    """One-line summary.

    Args:
        arg: Description of the argument.

    Returns:
        Description of the return value.

    Raises:
        ValueError: When arg is negative.
    """
```

Private helpers (`_name`) and trivial one-liners only need the summary line.
Module docstrings: one sentence describing what the module provides.

---

## Publish (GitHub Pages)

Push to any branch — `sphinx-docs.yml` builds on every push.
Pages are served from the `gh-pages` branch automatically once enabled in:
**Settings → Pages → Source: GitHub Actions** (one-time manual step).
