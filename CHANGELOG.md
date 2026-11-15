# Changelog

All notable changes to GMCounter are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

Add every user-visible change under `## [Unreleased]` in the pull request that makes it. The release workflow (`.github/workflows/auto-release.yml`) turns that section into the entry of the new version and into the text of the GitHub release. Releases up to 2.1.2 are listed on the [releases page](https://github.com/cckssr/gmcounter/releases).

## [Unreleased]

This is a major release: the user interface was rebuilt from the ground up. The measurement protocol, the exported file formats and the firmware command set are unchanged.

### Added

- Qt Designer forms as the only source of visual structure: the main window, every dock panel and every experiment tab has a `.ui` file in `gmcounter/pyqt/`. `pyuic.sh` regenerates the `ui_<form>.py` modules, `sync_texts` copies the configured texts into the forms, and `python -m gmcounter.pyqt.preview` shows a single form without devices.
- Dock layout with three dockable side panels (controls, connection with live readout and device status, event log) around a central tab area. The toolbar shows or hides each panel and toggles full-screen mode.
- Connection panel that replaces the connection dialog. It lists the serial ports, preselects the last used port and baud rate, shows the states disconnected, connecting, connected, reconnecting, failed and lost, and connects in a worker thread so the window never blocks.
- `gmcounter --simulate` runs the application on a simulated GM counter (mock device on a pseudo-terminal), so every experiment can be tried without hardware. It needs a source checkout and a Unix-like OS.
- UI profiles `student` (Praktikum) and `expert`, selected with `gmcounter --profile <id>` or `application.profile` in `config.json`. The student profile is the default, and `gmcounter --help` says so. A profile hides tabs and widgets purely through configuration, and the toolbar switches it at run time on the same device connection.
- Experiment tabs from a registry: Einzelmessung (timing), Abstandsgesetz (distance law), Spannungskurve (voltage response) and Intervalle (interval repeat). A new tab is a registered class plus a form, with no change to the main window.
- Interval tab that bins one continuous acquisition into equal-width intervals, with incremental plot refresh and one detail file per interval.
- Histogram bin-size and cut-off controls.
- High-speed mode in the timing tab: line plot and table pause at high count rates while the histogram and readouts keep updating.
- Palette-following plot styling and configurable curve colours (`plot_colors`).
- `SessionController`, which gives the shared Start, Stop, Save and Reset buttons their meaning for the selected tab, guards unsaved data, and writes the summary and detail files of sweep and interval sessions.
- Test suites for the Designer forms, string keys, profiles, small screens, connection panel, session controller and panels, and a scan that keeps project artifacts English.
- This changelog, and an automated release flow that stamps it (see Changed).

### Changed

- **Breaking:** `gmcounter` without options starts the reduced `student` (Praktikum) profile, which hides the baud rate, the query mode and some readback rows. Use `gmcounter --profile expert` (or set `application.profile` to `expert`) for every control. Each profile keeps its own saved window layout.
- **Breaking:** the application opens unconnected. Connect in the connection panel; Start and Apply stay disabled until the link is up. The connection dialog and `ConnectionWindow` no longer exist.
- **Breaking:** the Python structure of the UI layer changed. `MainWindow` takes `(config, device_manager=None, persist=True, *, simulate=False, simulation=None)`, tabs are built as `Tab(context)` with an `AppContext`, and `Launcher` owns the `DeviceManager`. Code that imported the old `ui_mainwindow`, `ConnectionWindow` or `DataController` must be updated.
- **Breaking:** `core.services.SaveService` was renamed to `SaveState` (it only tracks the unsaved flag and the base directory). Writing is done by `infrastructure.save_service`.
- `DeviceManager.apply_device_settings` and `DeviceManager.fetch_device_info` are public methods.
- All user-visible German texts live in `gmcounter/config.json` under `de`, applied to the forms by object name. Code comments, docstrings, documentation, log messages and test names are English.
- PySide6 is capped below 6.12, which aborts with a reference-count error on Python 3.10 and 3.11.
- CI runs `ruff format --check` and `ruff check`, then the whole test suite once per Python version (3.10, 3.11, 3.12). It runs once per pull request update and no longer again on the branch push, the merge or the release.
- The release workflow reads the `major`, `minor` or `patch` label of the merged pull request, bumps the version in `pyproject.toml`, `gmcounter/__init__.py` and `gmcounter/config.json`, stamps this changelog, builds and checks the wheel, tags the commit and publishes the release with the changelog section as its text. Manual releases run the tests first.
- The documentation workflow no longer installs a `requirements.txt` that does not exist.
- The README describes the application, the simulation mode and the profiles, with screenshots. The workflow notes moved from `.github/README.md` to `.github/WORKFLOWS.md`, because GitHub showed the former instead of the project README.

### Removed

- The counter-only `MEAS:STRT` / `MEAS:STOP` mode, which no experiment used.
- The legacy `DataController`, the old `mainwindow.ui` and the obsolete root-level test scripts that exercised them.
- `docs/QUICK_REFERENCE.md` and `requirements.txt` (dependencies are declared in `pyproject.toml`).

### Fixed

- Stopping a measurement no longer triggers a reconnect. The acquisition thread treated "no packet for 3 s" as a lost link, so stopping after a quiet stretch (a weak source, or a stop shortly after the start) reported "Connection lost" and reopened the port. A silent line is no longer a loss signal; a real loss still shows as a serial error.
- The group letter is no longer logged as an error while no group is selected.
- Voltage and counting-time ranges in the firmware `HELP` output.
- Corrupted `FETC:STAT?` answers caused by the continuous stream mode on `Serial1`; the device readout ignores incomplete reads instead of showing zeros.
- The line plot uses a thin pen, and Auto-Scroll survives programmatic range changes.
