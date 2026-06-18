# Contributing to GMCounter

Thank you for your interest in contributing. This document covers dev setup,
the coding conventions, and the GitHub PR → auto-release workflow.

---

## Dev Setup

```bash
git clone https://github.com/cckssr/gmcounter.git
cd gmcounter
pip install -e ".[dev]"
```

| Tool        | Purpose          | Command                                                      |
| ----------- | ---------------- | ------------------------------------------------------------ |
| ruff        | Format + lint    | `ruff format gmcounter tests` / `ruff check gmcounter tests` |
| pytest      | Tests            | `pytest`                                                     |
| pyside6-uic | Regenerate Qt UI | `bash gmcounter/pyqt/pyuic.sh`                               |

### Test layers

```bash
pytest tests/core tests/infrastructure        # pure Python, no Qt needed
QT_QPA_PLATFORM=offscreen pytest tests/ui/   # headless Qt (set env var)
pytest --cov=gmcounter                        # full suite with coverage
```

Integration tests that drive the `MockGMCounter` PTY are marked `integration`:

```bash
pytest -m integration
```

---

## Architecture Rules

Three strict layers — dependency direction is **UI → Infrastructure → Core**.
Lower layers must never import from higher ones.

| Layer             | May import                      | Must NOT import                          |
| ----------------- | ------------------------------- | ---------------------------------------- |
| `core/`           | stdlib only                     | PySide6, serial, infrastructure/, ui/    |
| `infrastructure/` | core/, stdlib, serial           | ui/; PySide6 only inside `qt_threads.py` |
| `ui/`             | infrastructure/, core/, PySide6 | —                                        |

Every new feature belongs to one layer. If it needs Qt it belongs in `ui/`
(or, if it truly needs a QThread worker, in `infrastructure/qt_threads.py`).
If it could run in a CLI script it belongs in `core/` or `infrastructure/`.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full contract and rationale and
[PRINCIPLES.md](PRINCIPLES.md) for the portable design principles these rules
are based on.

### Verify the layer rules before committing

```bash
# Should return zero files:
grep -rln "PySide6" gmcounter/core/ gmcounter/infrastructure/*.py \
  $(find gmcounter/infrastructure -name "*.py" ! -name "qt_threads.py")
```

---

## UI-First Workflow

Every static widget lives in a `.ui` file edited in Qt Designer
(`gmcounter/pyqt/*.ui`). Python only connects signals and injects pyqtgraph
widgets into empty containers declared in `.ui`.

After any `.ui` change:

```bash
bash gmcounter/pyqt/pyuic.sh
```

The generated `pyqt/ui_*.py` files are committed but **never hand-edited**.
See [ARCHITECTURE.md §2](ARCHITECTURE.md) for the full rule.

---

## Docstrings

All public functions and classes use **Google-style** docstrings:

```python
def my_function(x: int, y: float) -> str:
    """One-line summary.

    Args:
        x: Description of x.
        y: Description of y.

    Returns:
        Description of the return value.

    Raises:
        ValueError: If x is negative.
    """
```

Type hints are required on new code. No bare `Any`.

---

## PR Flow and Auto-Versioning

### One release label per PR

When a pull request is merged into `main`, the `auto-release.yml` workflow
checks for a **release label**. The first matching label (highest precedence
first) determines the version bump:

| Label                                                     | Effect                      |
| --------------------------------------------------------- | --------------------------- |
| `major` / `semver:major` / `release:major` / `bump:major` | Bump major: `2.x.y → 3.0.0` |
| `minor` / `semver:minor` / `release:minor` / `bump:minor` | Bump minor: `2.1.x → 2.2.0` |
| `patch` / `semver:patch` / `release:patch` / `bump:patch` | Bump patch: `2.1.1 → 2.1.2` |

**No matching label → no release.** The workflow exits silently. This is
intentional — not every PR needs a release.

### What happens automatically

1. The version is bumped in three files:
   - `pyproject.toml` (`version = "X.Y.Z"`)
   - `gmcounter/__init__.py` (`__version__ = "X.Y.Z"`)
   - `gmcounter/config.json` (key `de.application.version`)
2. A commit `chore: bump version to vX.Y.Z` is pushed to `main`.
3. A tag `vX.Y.Z` is created and pushed.
4. A GitHub release is published with auto-generated notes and the wheel/sdist
   attached.

**Do not hand-edit version strings** in those three files. The workflow manages
them.

### Manual release (workflow_dispatch)

Go to _Actions → Auto Release → Run workflow_ and choose the bump type and
optional pre-release suffix (`a`, `b`, `rc`).

### Optional: PAT_TOKEN secret

By default, the workflow uses `GITHUB_TOKEN`. A push from `GITHUB_TOKEN` does
**not** re-trigger other workflows (GitHub restriction). If you need the version
bump commit to trigger CI or Pages, add a Personal Access Token as a repository
secret named `PAT_TOKEN`.

---

## Firmware Contributions

The firmware lives in `firmware/` and is a [PlatformIO](https://platformio.org/)
project targeting the Arduino UNO R4 Minima (Renesas RA4M1).

### Building

```bash
# Flash to the default env (unknown serial number)
pio run -e uno_r4_minima --target upload

# Flash with a specific device serial number baked in
pio run -e uno_E20134 --target upload
```

### Native unit tests (no hardware needed)

```bash
pio test -e native
```

The native tests compile and run on the host (macOS/Linux) using the Unity
framework. They cover the SCPI parser, dispatcher, error queue, and GM core logic.
The `firmware/test/Arduino.h` shim provides the Arduino API stubs.

### Conventions

- All host-facing commands use SCPI (IEEE 488.2) syntax — see the
  [firmware docs](https://cckssr.github.io/gmcounter/hardware/firmware.html).
- State lives in `gmState` (`firmware/src/state.h`); side-effects in handler
  functions (`firmware/src/scpi.cpp`).
- Never add `delay()` or blocking loops in the main loop body.

---

## Docs Workflow

```bash
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html -W
open docs/_build/html/index.html
```

Docs are published automatically to GitHub Pages on every push to `main` via
`sphinx-docs.yml`. See [.github/WORKFLOWS.md](.github/WORKFLOWS.md) for the
full workflow description and the knobs available if you want to reuse the
workflows in another project.
