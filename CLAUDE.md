# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GMCounter is a PySide6 desktop GUI for a Geiger-Müller counter device connected via USB serial (Arduino). It measures inter-event timing in microseconds and is used for random number generation research.

## Commands

```bash
# Run the app
python -m gmcounter
# or after pip install -e .
gmcounter
python -m gmcounter --profile student   # UI profile: expert (default) or student (Praktikum)

# Tests
pytest                                # all tests
pytest tests/core/                    # core layer (no Qt needed)
pytest tests/infrastructure/          # infrastructure layer (no Qt needed)
QT_QPA_PLATFORM=offscreen pytest tests/ui/  # UI layer (offscreen)
pytest --cov=gmcounter

# Format / lint
black gmcounter tests
flake8 gmcounter tests

# Designer forms (gmcounter/pyqt/*.ui)
bash gmcounter/pyqt/pyuic.sh                  # sync texts from config.json, regenerate every ui_<form>.py
bash gmcounter/pyqt/pyuic.sh sample_panel     # only the named forms (stems without .ui)
python -m gmcounter.pyqt.sync_texts --check   # exit 1 if a .ui file is out of date
python -m gmcounter.pyqt.preview               # list the forms
python -m gmcounter.pyqt.preview sweep_tab    # show one form on its own (--watch reloads on save)
```

Install for development: `pip install -e ".[dev]"`

## Architecture

Three strict layers — dependency direction is **UI → Infrastructure → Core**.
Lower layers must never import from higher ones.

### Layer rules (enforced, verified with grep)

| Layer                          | May import                         | Must NOT import                       |
| ------------------------------ | ---------------------------------- | ------------------------------------- |
| `core/`                        | stdlib only                        | PySide6, serial, infrastructure/, ui/ |
| `infrastructure/`              | core/, stdlib, serial, vendor SDKs | ui/                                   |
| `infrastructure/qt_threads.py` | PySide6 (only this file!)          | —                                     |
| `ui/`                          | infrastructure/, core/, PySide6    | —                                     |

### `gmcounter/core/` — Pure Python, zero Qt

- `models.py`: `MeasurementPoint`, `MeasurementSession`, `DeviceSettings`, `DeviceInfo`, `Frame` (frozen cross-thread bundle), `DesiredState` (reconnect replay snapshot)
- `export.py`: `TabExport` dataclass (§7) + `build_gm_tab_export()` + `compose_save_path()` — pure composition, no I/O
- `services.py`: `MeasurementService`, `SaveService` (CSV/JSON), `DeviceControlService`, `MeasurementStateService`
- `reconnect_service.py`: `ReconnectStrategy` + `ConnectionRetryService` (exponential backoff)
- `duration.py`: `accumulate_and_trim()` — trims a batch of `(index, value_us)` points to stay within a `target_us` device-time budget; returns `(kept_points, new_accum_us, reached)`
- `interval_binning.py`: `IntervalBinner` + `IntervalBins` — MCS-style binning of a continuous acquisition into R equal-width intervals; `feed()` returns touched bin indices for incremental plot refresh
- `utils.py`: filename sanitization, statistics helpers
- `formatting.py`: display format helpers
- `exceptions.py`: `GMCounterError` hierarchy
- `ports.py`: `Logger` Protocol (so core never imports infrastructure.logging)

### `gmcounter/infrastructure/` — Adapters, Qt only in qt_threads.py

- `serial_device.py`: `SerialDevice` — Qt-free pyserial base class
- `devices/gm_counter.py`: `GMCounterAdapter` — GM counter command set (s/b/j/o/f/w/U)
- `mocks/mock_gm_counter.py`: `MockGMCounter` — wire-compatible PTY-based mock (**excluded from wheel**)
- `modules/registry.py`: `HostModule` Protocol + `ModuleRegistry` (§8)
- `device_manager.py`: `DeviceManager` — **Qt-free**, plain callbacks, manages connection lifecycle
- `packet_parser.py`: `PacketParser` — incremental binary decoder; extracted from `qt_threads.py` for testability; owned by `DataAcquisitionThread`
- `qt_threads.py`: `DataAcquisitionThread`, `StatePollerThread`, `ReconnectWorker` (all `QThread`) — **only Qt file in infrastructure/**
- `session_journal.py`: `SessionJournal` — append-only crash-safe journal, `find_orphan_journals()`
- `save_service.py`: `SaveService` — generic `TabExport` writer (no per-experiment code)
- `config.py`: `AppConfig` (`get`, `section`, `text`, `message`, profile helpers) + `load_config(path, overrides, profile)` — loads `gmcounter/config.json` (language key `"de"`), merges the profile overrides; `default_config()` and `import_config()` for module-level use
- `logging.py`: `Debug` singleton with `DEBUG_OFF / INFO / VERBOSE / ERROR` levels

### `gmcounter/ui/` — PySide6 presentation, no device logic

Startup: `gmcounter/main.py` (`--profile`) shows `dialogs/connection.py`, then `launcher.py` builds the `MainWindow` for the profile.

- `launcher.py`: `Launcher(QObject)` — builds the main window from `load_config(profile=...)` on the connected `DeviceManager`; a runtime profile switch closes the window and builds the other one on the same connection, keeping the window mode; refused while measuring or with unsaved data
- `profile.py`: `apply_profile(window)` hides the widgets of `hidden_widgets` (by Designer object name, below `main_window`, a panel or a tab id); `next_profile()` for the switch action
- `i18n.py`: `apply_strings(root, strings)` — sets the configured German texts on the children of a Designer form (see "Strings & profiles")
- `context.py`: `AppContext` dataclass — what the tabs may use: `config`, `device_manager`, `ctrl`, `save_service`, `file_dialogs`, `timing` (the timing tab, set when built), and the callables `voltage_readback`, `device_settings`, `sample_metadata` that hide the panels from the tabs
- `controllers/app_controller.py`: **`AppController(QObject)`** — owns all QTimers, DataAcquisitionThread, reconnect FSM (§5), frame fan-out to the active tab (`frames_ready` → `on_frames`)
- `controllers/session_controller.py`: **`SessionController(QObject)`** — what the shared Start / Stop / Save / Reset buttons mean for the selected tab; branches on `session_kind` ("single", "sweep", "interval"), guards unsaved data, writes summary and detail files; talks to the user through `common/prompt.py`
- `controllers/data_controller.py`: `DataController` — legacy, no longer wired into the window; do not extend
- `tabs/base.py`: `PlotTabBase(QWidget)` — experiment tab contract (§6)
- `tabs/registry.py`: `TabRegistry` — `@TabRegistry.register`, `available(modules)` sorted by `order`
- `tabs/tab_title.py`: `TabTitle` — tab title from `ui.tabs.<tab_id>`
- `tabs/gm_timing_tab.py`: `GMTimingTab` (`tab_id="gm_timing"`, `order=0`, `provides_timing`) — GM timing experiment, form `timing_tab.ui`, inner views Zeitverlauf / Histogramm / Liste; high-speed mode (line plot and table paused, histogram and readouts every 2 s, automatic switch to the histogram unless `set_high_speed_autoswitch(False)`, which the session controller sets during sweep and interval sessions); export never drops frames
- `tabs/parameter_sweep_base.py`: `ParameterSweepTabBase` — base of the sweep experiments; form `sweep_tab.ui` shared by all of them
- `tabs/distance_law_tab.py`: `DistanceLawTab` (`order=10`) and `tabs/voltage_response_tab.py`: `VoltageResponseTab` (`order=20`) — class-attribute subclasses of `ParameterSweepTabBase`
- `tabs/interval_repeat_tab.py`: `IntervalRepeatTab(PlotTabBase)` (`order=30`, form `interval_tab.ui`, `session_kind="interval"`, `receives_frames=True`) — bins one continuous acquisition into R equal-width intervals with `IntervalBinner`
- `panels/`: dock panels `DevicePanel`, `SamplePanel`, `MeasurementPanel`, `ReadoutPanel`, `DeviceStatusPanel`, `EventLogPanel` — each a `QGroupBox` (`EventLogPanel`: `QWidget`) with its own `.ui`; they expose intent signals and setters, never talk to devices; `panels/__init__.py` has the shared combo helpers
- `windows/main_window.py`: `MainWindow` — composes the three docks (`dockControls`: device, sample, measurement panel; `dockLive`: readout and device status panel; `dockLog`: event log) and the tab widget; builds the tabs from `TabRegistry` and never names a concrete tab; keeps no experiment logic
- `dialogs/connection.py`: `ConnectionWindow` — port enumeration, baud select, demo-mode mock port
- `widgets/plot.py`: `GeneralPlot` (real-time line plot, `reconfigure(...)`, `set_summary_points()`) and `HistogramWidget` — pyqtgraph, promoted in the `.ui` files
- `widgets/plot_style.py`: palette-following plot chrome and the curve colours of `plot_colors` in config.json
- `widgets/status_led.py` (`StatusLed`), `widgets/elided_label.py` (`ElidedLabel`, middle elision for paths), `widgets/vscroll.py` (`lock_vertical_scroll`) — small reusable widgets
- `common/`: `dialogs.py`, `file_dialogs.py`, `statusbar.py` (`StatusBarManager`), `prompt.py` (`Prompt` protocol, `MessageBoxPrompt`), `messages.py` (`message(key)` for code without an `AppConfig`)
- `resources/stylesheet.py`: `get_stylesheet(mode)` / `apply_stylesheet(app, mode)` — dark/light stylesheets; currently not applied (the import in `main.py` is commented out)

### `gmcounter/pyqt/` — Designer forms and generated code

- `*.ui` forms are the only source of visual structure: `main_window.ui` (MainWindow), `device_panel.ui`, `sample_panel.ui`, `measurement_panel.ui`, `readout_panel.ui`, `device_status_panel.ui`, `event_log_panel.ui` (panels), `timing_tab.ui`, `sweep_tab.ui`, `interval_tab.ui` (experiment tabs), `connection.ui` (connection dialog)
- `ui_<form>.py`: generated by `pyside6-uic` from `<form>.ui` (`pyuic.sh`). **Never hand-edit these files.**
- `sync_texts.py`: copies the configured German texts into the `.ui` properties, so Qt Designer shows them; run by `pyuic.sh`
- `preview.py`: shows one form with its texts, without controllers or devices

## UI-first rule

**Every static widget lives in a `.ui` file** — main window, dock panels, experiment tabs and dialogs alike. Python code only:

- calls `setupUi()` and `apply_strings()`
- connects signals to slots and sets values or states
- holds behaviour (controllers, tabs, panels) on the widgets the form declares, found by object name

Python creates widgets only where Designer cannot express them, and only for non-visual helpers:

- `QStandardItemModel` attached to a `.ui` `QTableView`
- `QCompleter` attached to a `.ui` combo box

Custom widgets are promoted in the `.ui` files, not created in Python: the dock panels in `main_window.ui` (header `gmcounter.ui.panels.*`), `GeneralPlot` and `HistogramWidget` (header `gmcounter.ui.widgets.plot`), `StatusLed` (header `gmcounter.ui.widgets.status_led`).

After any `.ui` edit run `bash gmcounter/pyqt/pyuic.sh [form]` to regenerate before testing.

## Strings & profiles

**Strings**: every user-visible German text lives in `gmcounter/config.json` under `"de"`, never in code or in a `.ui` file (the `.ui` texts are copies made by `sync_texts`).

- `ui.<form>.<objectName>`: text of a Designer object; `name@kind` selects another property: `@tooltip`, `@suffix`, `@prefix`, `@placeholder`, `@title` (window title), `@tab` (page title of a `QTabWidget`). Object names come from the form.
- `ui.<form>.<key_with_underscore>`: plain texts that the code reads by key (e.g. `plot_y_label`, `table_summary_headers`, `text_param_distance`)
- `ui.tabs.<tab_id>`: tab titles; `messages.<key>`: message texts (`AppConfig.message` or `common.messages.message`)
- Missing keys show the key itself (visible, not fatal). Run `pyuic.sh` after changing texts.

**Profiles**: `profiles.<id>` in config.json with `name`, `hidden_tabs` (tab ids), `hidden_widgets` (root → object names) and `overrides` (merged over the defaults for this profile).

- `expert` (Experte) hides nothing; `student` (Praktikum) hides the query mode and some readback rows
- select with `--profile <id>` or `application.profile`; the toolbar action (`actionSwitchProfile`) switches at run time through `Launcher`
- a profile is config only: no code change; hidden controls keep their default values
- tests: `tests/ui/test_profile.py`; `tests/ui/test_designer_forms.py` and `test_main_window_strings.py` check forms and texts

## Adding a frame-based experiment tab

A frame-based tab consumes the acquired data points itself while it is selected (`receives_frames = True`). `IntervalRepeatTab` is the reference.

1. Create `gmcounter/pyqt/my_tab.ui`: a `QWidget` named `MyTab` with the static widgets (plots as promoted `GeneralPlot`, tables, spin boxes). Keep it free of texts.
2. Add the texts to `config.json` under `ui.my_tab` (keys = object names, see "Strings & profiles") and `ui.tabs.my_exp`, then run `bash gmcounter/pyqt/pyuic.sh my_tab`.
3. Create the tab module and import it in `gmcounter/ui/tabs/__init__.py`:

   ```python
   @TabRegistry.register
   class MyTab(PlotTabBase):
       tab_id = "my_exp"                   # title: ui.tabs.my_exp
       form_name = "my_tab"                # texts: ui.my_tab
       order = 40
       session_kind = "interval"           # "single" | "sweep" | "interval"
       receives_frames = True
       required_modules: set[str] = set()  # e.g. {"kdc101"}: shown only if that module is registered

       def __init__(self, context: "AppContext", parent: Optional[QWidget] = None) -> None:
           super().__init__(context, parent)
           self.ui = Ui_MyTab()
           self.ui.setupUi(self)
           apply_strings(self, self.config.section("ui").get(self.form_name, {}))

       def build(self) -> None: ...                 # once, after construction
       def on_frames(self, frames) -> None: ...     # batch of Frame objects
       def on_reset(self) -> None: ...              # before a new measurement
       def export(self) -> Optional[TabExport]: ... # data for the save service
   ```

   Imports: `Ui_MyTab` from `gmcounter.pyqt.ui_my_tab`, `apply_strings` from `..i18n`, `PlotTabBase` from `.base`, `TabRegistry` from `.registry`, `TabExport` from `...core.export`.

4. `MainWindow` needs no change: it creates every registered tab as `Tab(context)`, calls `build()` and adds the page with its title. Profiles can hide it via `hidden_tabs`.

Hooks for sessions (`session_kind` "interval" or "sweep"): `has_data()`, `has_unsaved_data()`, `mark_saved()`, `summary_export()`, `session_exports()`, `session_file_name(export, index)`, `reset_session()`.

## Adding a parameter-sweep experiment tab

A sweep tab accumulates (parameter, count, rate) points across several measurements; the session is saved once at the end. All sweep tabs share `sweep_tab.ui` (`SweepTab`: `labelParam`, `spinParam`, `labelHint`, `valueStatus`, `sweepPlot`, `tableSummary`), so no new form is needed.

1. Add the instance texts to `config.json` under `ui.sweep_tab`, with `<instance>` as the suffix: `text_param_<instance>`, `text_param_suffix_<instance>`, `text_param_tooltip_<instance>`, `text_param_header_<instance>`, `text_summary_title_<instance>`, optional `text_hint_<instance>`; and the title `ui.tabs.<tab_id>`.
2. Subclass `ParameterSweepTabBase` with class attributes only and register it. This is `DistanceLawTab` in `gmcounter/ui/tabs/distance_law_tab.py`:

   ```python
   @TabRegistry.register
   class DistanceLawTab(ParameterSweepTabBase):
       tab_id = "distance_law"
       order = 10
       instance = "distance"
       hides_global_distance = True  # the tab has its own distance input

       param_unit = "cm"
       param_metadata_key = "sample_distance_cm"
       summary_filename_hint = "abstandsgesetz"
       clear_param_input_after_stop = True
   ```

3. Optional class attributes: `param_format` (table format), `uses_param_input = False` (the parameter comes from the device read-back, the input row is hidden), `applies_device_voltage_on_start = True` (device settings are sent before each Start). `VoltageResponseTab` uses the last two.
4. Import the module in `gmcounter/ui/tabs/__init__.py`. The shared Start / Stop / Save / Reset buttons drive the tab through `session_kind = "sweep"` (set by the base); no per-tab button wiring.

**Sweep session lifecycle** (`SessionController`):

- Start on a sweep tab: the first point of a session warns on infinite time, then `tabs_locked` locks the other tabs and `set_high_speed_autoswitch(False)` keeps the timing view; each point starts a measurement without a save in between
- Stop → Start is enabled again immediately for the next point
- Save (button "Speichern") → summary CSV plus one automatically named detail CSV per point, then the session is reset, the other tabs are unlocked and the auto-switch is restored
- Reset → discards the session after a confirmation if it holds data

## Key Conventions

**Config**: All tuneable constants live in `gmcounter/config.json` under the `"de"` key. Access with `load_config()` / `default_config()` from `gmcounter.infrastructure.config`. `demo_mode: true` by default (no real hardware needed).

**Binary protocol**: Three marker types, all decoded by `PacketParser`:
- Start marker: `0xFF × 6` — everything before it is discarded; parser must see this before accepting data packets
- Data packet: `[0xAA, b0, b1, b2, b3, 0x55]` — bytes 1–4 encode inter-event delta in firmware timer ticks (little-endian 32-bit); divide by `ticks_per_us` (config, default 48 for RA4M1 at 48 MHz) to get µs
- End-of-period marker: `0xEE × 6` — firmware sends this when a finite-time counting period completes; `PacketParser.end_of_period` flag is set; caller must call `clear_end_of_period()` after handling

**Qt signals across threads**: Data flows from `DataAcquisitionThread.data_batch` → `AppController._on_data_batch` → `frames_ready` signal → active `PlotTabBase.on_frames()`. All cross-thread connections use `Qt.ConnectionType.QueuedConnection`.

**Reconnect replay (§5 B5)**: When the connection drops, `AppController` saves a `DesiredState` snapshot. After a successful reconnect via `ReconnectWorker`, `DeviceManager.attempt_automatic_reconnect(desired=...)` re-applies voltage, counting time, repeat mode, and stream mode — so the Arduino is back in the user's configured state.

**Crash-safe journaling**: `SessionJournal` appends every data point to `~/.gmcounter/sessions/<ts>/journal.csv` with fsync every ~1 s. On startup `find_orphan_journals()` reports sessions without a `finalized` marker.

**Deprecated files**: `ui/controllers/data_controller.py` (`DataController`) is legacy — new code should not use it.

**Mocks excluded from wheel**: `infrastructure/mocks/` is in `pyproject.toml`'s exclude list.

**Logging**: Use `infrastructure.logging.Debug` for all logging. It has four levels: `DEBUG_OFF`, `INFO`, `VERBOSE`, and `ERROR`. Logs are printed to the console with timestamps and exception handler.
