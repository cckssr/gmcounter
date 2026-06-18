# GMCounter

[![CI](https://github.com/cckssr/gmcounter/actions/workflows/ci.yml/badge.svg)](https://github.com/cckssr/gmcounter/actions/workflows/ci.yml)
[![Docs](https://github.com/cckssr/gmcounter/actions/workflows/sphinx-docs.yml/badge.svg)](https://cckssr.github.io/gmcounter/)
[![Version](https://img.shields.io/github/v/release/cckssr/gmcounter)](https://github.com/cckssr/gmcounter/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)

GMCounter is a PySide6 desktop application for a Geiger-Müller counter connected
over USB serial. It records inter-event timings in microseconds, presents the data
live, and supports analysis workflows for random-number research and detector
characterisation.

**No hardware required to try it** — demo mode is on by default and uses a
software-emulated serial port.

📖 **Full documentation:** [cckssr.github.io/gmcounter](https://cckssr.github.io/gmcounter/)

---

## What It Does

- Live time-series, histogram, and tabular views of incoming events
- Parameter-sweep experiments: distance law (1/r²) and voltage-response curve
- MCS-style interval-repeat experiment (`IntervalRepeatTab`)
- Export to CSV with a sidecar `_MD.json` metadata file
- Crash-safe session journal (`~/.gmcounter/sessions/`) for data recovery
- Exponential-backoff auto-reconnect that replays device state on recovery

---

## Installation

### From the repository (no clone needed)

```bash
pip install "git+https://github.com/cckssr/gmcounter.git"
```

Pin a specific release:

```bash
pip install "git+https://github.com/cckssr/gmcounter.git@v2.1.2"
```

### From a local clone

```bash
pip install .
```

Development (editable, with linting and test tools):

```bash
pip install -e ".[dev]"
```

---

## Running the Application

```bash
gmcounter
# or
python -m gmcounter
```

The connection dialog opens first. Select a serial port or accept the default
demo-mode mock port — no physical hardware is needed in demo mode
(`demo_mode: true` in `gmcounter/config.json`).

---

## Requirements

- Python 3.10 or newer
- PySide6 ≥ 6.5
- pyserial, numpy, scipy, pyqtgraph, pillow
- A Geiger-Müller counter with the [matching firmware](firmware/) connected over
  USB serial for hardware-backed operation

---

## Project Structure

```ascii
gmcounter/
  core/           Pure domain logic — no Qt, no serial (unit-testable standalone)
  infrastructure/ Serial adapters, file I/O, config, logging; Qt only in qt_threads.py
  ui/             PySide6 windows, tabs, widgets, dialogs
  pyqt/           Generated Qt Designer outputs — do NOT hand-edit
firmware/         PlatformIO / Arduino UNO R4 firmware (SCPI command set)
tests/            Unit, integration, and UI tests
docs/             Sphinx documentation source
```

Dependency direction: **UI → Infrastructure → Core** (enforced; lower layers
must never import upward).

---

## Development

```bash
# Format and lint
ruff format gmcounter tests
ruff check gmcounter tests

# Tests
pytest tests/core tests/infrastructure        # no Qt needed
QT_QPA_PLATFORM=offscreen pytest tests/ui/   # headless Qt

# After editing .ui files in gmcounter/pyqt/
bash gmcounter/pyqt/pyuic.sh

# Build docs locally
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow, PR flow, and
auto-versioning rules.

---

## Architecture and Design

- [ARCHITECTURE.md](ARCHITECTURE.md) — project-specific design contracts (§1–§17)
- [PRINCIPLES.md](PRINCIPLES.md) — portable PySide/firmware design principles with rationale
- [docs/](https://cckssr.github.io/gmcounter/) — full Sphinx documentation

---

## License

MIT License — see [LICENSE](LICENSE).
