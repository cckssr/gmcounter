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

# Tests
pytest                                # all tests
pytest tests/core/                    # core layer (no Qt needed)
pytest tests/infrastructure/          # infrastructure layer (no Qt needed)
QT_QPA_PLATFORM=offscreen pytest tests/ui/  # UI layer (offscreen)
pytest --cov=gmcounter

# Format / lint
black gmcounter tests
flake8 gmcounter tests

# Recompile Qt UI files after editing .ui files in gmcounter/pyqt/
bash gmcounter/pyqt/pyuic.sh
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
- `qt_threads.py`: `DataAcquisitionThread(QThread)` + `ReconnectWorker(QThread)` — **only Qt file in infrastructure/**
- `session_journal.py`: `SessionJournal` — append-only crash-safe journal, `find_orphan_journals()`
- `save_service.py`: `SaveService` — generic `TabExport` writer (no per-experiment code)
- `config.py`: `import_config()` — loads `gmcounter/config.json` (language key `"de"`)
- `logging.py`: `Debug` singleton with `DEBUG_OFF / INFO / VERBOSE / ERROR` levels

### `gmcounter/ui/` — PySide6 presentation, no business logic

- `controllers/app_controller.py`: **`AppController(QObject)`** — owns all QTimers, DataAcquisitionThread, reconnect FSM (§5), frame fan-out to active tab
- `tabs/base.py`: `PlotTabBase(QWidget)` — experiment tab contract (§6)
- `tabs/registry.py`: `TabRegistry` — register/available(modules) filtering
- `tabs/gm_timing_tab.py`: `GMTimingTab` — GM experiment, contributes 3 top-level views (Zeitverlauf/Histogramm/Liste); `set_high_speed_autoswitch(bool)` suppresses auto-tab-switch during sweep sessions
- `tabs/parameter_sweep_base.py`: `ParameterSweepTabBase` — generic base for parameter-sweep experiments (distance law, voltage curve, …); all layout in `.ui`, injected via `inject_ui()`
- `tabs/distance_law_tab.py`: `DistanceLawTab` — 1/r² distance-law sweep; pure class-attribute subclass of `ParameterSweepTabBase`
- `windows/main_window.py`: `MainWindow` — **thin**, setupUi + AppController signal subscriptions; routes shared Start/Stop/Speichern buttons via `_current_sweep_tab()` check; manages `_sweep_session` flag
- `dialogs/connection.py`: `ConnectionWindow` — port enumeration, baud select, demo-mode mock port
- `widgets/plot.py`: `GeneralPlot` (real-time line plot, `set_summary_points()` for scatter/line sweep summary), `HistogramWidget` — all pyqtgraph
- `widgets/event_log_panel.py`: `EventLogPanel` — dockable timestamped status scrollback (§9)
- `common/`: `dialogs.py`, `statusbar.py` (`StatusBarManager`), `file_dialogs.py`

### `gmcounter/pyqt/` — Generated Qt UI code

`ui_mainwindow.py`, `ui_connection.py`, `ui_alert.py` are auto-generated by `pyside6-uic` from `.ui` files. **Never hand-edit these files.**

## UI-first rule

**Every static widget lives in a `.ui` file.** Buttons, labels, spinboxes, group boxes, table views, and empty plot containers all belong in Qt Designer, not in Python. Python code only:

- calls `setupUi()` / `inject_ui()` / `inject_ui_containers()`
- connects signals to slots
- injects pyqtgraph widgets into native `QWidget` containers declared in `.ui`

The **only** justified exceptions (where Python creates widgets):

- pyqtgraph `PlotWidget` subclasses (`GeneralPlot`, `HistogramWidget`) — Designer cannot host third-party custom widgets
- `QStandardItemModel` attached to a `.ui` `QTableView` — a non-visual logical helper

After any `.ui` edit run `bash gmcounter/pyqt/pyuic.sh` to regenerate before testing.

## Adding a frame-based experiment tab

A frame-based tab receives every acquired data point in real time.

1. Declare a `QWidget` page in `mainwindow.ui`, add any static widgets (plot containers, table, labels, controls).
2. Subclass `PlotTabBase`, implement `build()` (inject pyqtgraph into the `.ui` containers) and `on_frames()`:

   ```python
   class MyTab(PlotTabBase):
       tab_id = "my_exp"
       tab_title = "My Experiment"
       required_modules = set()   # or {"kdc101"} to gate on a host module

       def build(self): ...          # inject GeneralPlot into .ui container
       def on_frames(self, frames): ...
       def export(self) -> TabExport: ...
   ```

3. Call `TabRegistry.register(MyTab)` at module level.
4. In `MainWindow.__init__`: inject `.ui` widgets, call `build()`. The page already exists in `.ui`; do NOT call `addTab()` programmatically.

`required_modules` gating: if `{"kdc101"}` is declared, the tab is hidden until a `HostModule` with `id="kdc101"` is registered in `ModuleRegistry`.

## Adding a parameter-sweep experiment tab

A sweep tab accumulates (parameter, count, rate) points across multiple measurements without requiring an intermediate save. Use this pattern for distance law, voltage response curve, etc.

1. Declare a `QWidget` page in `mainwindow.ui` with exactly this widget set (names matter — MainWindow injects by name):
   - `QDoubleSpinBox name="<prefix>Input"` — parameter input
   - `QWidget name="<prefix>Plot" native="true"` — empty container for GeneralPlot
   - `QTableView name="<prefix>Table"` — summary table
   - `QLabel name="<prefix>Status"` — status text

2. Subclass `ParameterSweepTabBase` and set class attributes only — no method bodies needed. **Do NOT call `TabRegistry.register()`** — sweep tabs are explicitly wired in `MainWindow` and do not go through the auto-discovery path:

   ```python
   class VoltageResponseTab(ParameterSweepTabBase):
       tab_id = "voltage_response"
       tab_title = "Spannungskurve"
       required_modules: set[str] = set()

       param_label          = "Spannung (V)"
       param_unit           = "V"
       param_metadata_key   = "gm_voltage_v"
       summary_filename_hint = "spannungskurve"
       summary_title        = "Spannungskurve — Zusammenfassung"
   ```

3. In `MainWindow.__init__`, inject and build (after `_ctrl.set_active_tab(self._gm_tab)`):

   ```python
   self._voltage_tab = VoltageResponseTab(parent=self)
   self._voltage_tab.set_gm_tab(self._gm_tab)
   self._voltage_tab.inject_ui(
       plot_container=self.ui.voltagePlot,
       table_view=self.ui.voltageTable,
       param_input=self.ui.voltageInput,
       status_label=self.ui.voltageStatus,
   )
   self._voltage_tab.build()
   self._ctrl.measurement_stopped.connect(self._voltage_tab.on_measurement_stopped)
   ```

The shared **Start / Stop / Speichern / Reset** buttons route automatically: `MainWindow._current_sweep_tab()` returns the active sweep tab (if any), and `_handle_start/save/reset` branch on that. No per-tab button wiring is needed.

**Sweep session lifecycle** (handled by MainWindow):

- Start on a sweep tab → disables the three GM view tabs (Zeitverlauf/Histogramm/Liste), suppresses GMTimingTab's high-speed auto-switch, sets `_sweep_session = True`
- Stop → Start re-enabled immediately for the next distance/voltage point
- Speichern → saves summary CSV + auto-named individual timing CSVs → resets GMTimingTab, re-enables view tabs, clears `_sweep_session`
- Reset → discards summary, re-enables view tabs

## Key Conventions

**Config**: All tuneable constants live in `gmcounter/config.json` under the `"de"` key. Access with `import_config()` from `gmcounter.infrastructure.config`. `demo_mode: true` by default (no real hardware needed).

**Binary protocol**: Packets are 6 bytes — `[0xAA, b1, b2, b3, b4, 0x55]`. Bytes 1–4 encode the inter-event time in microseconds (little-endian 32-bit). Measurement start is signalled by `0xFF × 6` — the acquisition thread discards all data before this marker.

**Qt signals across threads**: Data flows from `DataAcquisitionThread.data_batch` → `AppController._on_data_batch` → `frames_ready` signal → active `PlotTabBase.on_frames()`. All cross-thread connections use `Qt.ConnectionType.QueuedConnection`.

**Reconnect replay (§5 B5)**: When the connection drops, `AppController` saves a `DesiredState` snapshot. After a successful reconnect via `ReconnectWorker`, `DeviceManager.attempt_automatic_reconnect(desired=...)` re-applies voltage, counting time, repeat mode, and stream mode — so the Arduino is back in the user's configured state.

**Crash-safe journaling**: `SessionJournal` appends every data point to `~/.gmcounter/sessions/<ts>/journal.csv` with fsync every ~1 s. On startup `find_orphan_journals()` reports sessions without a `finalized` marker.

**Deprecated files**: `gmcounter/helper_classes.py` is marked _DEPRECATED NEVER USE_. `gmcounter/helper_classes_compat.py` re-exports from it for backwards compatibility — do not add new code to either. These will be removed in a future cleanup.

**Mocks excluded from wheel**: `infrastructure/mocks/` is in `pyproject.toml`'s exclude list.
