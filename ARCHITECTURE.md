# ARCHITECTURE.md — GMCounter

This document describes GMCounter's architecture: the design rules, their
rationale, and how to apply them when extending or maintaining the codebase.
It is organised by concern, not by file. CLAUDE.md's `§N` references point to
numbered sections here.

> **Portable principles:** The generic, project-agnostic rules these decisions
> are based on are captured in [PRINCIPLES.md](PRINCIPLES.md) — copy that file
> to any new PySide/firmware project as a starting point.

---

## 1. The three-layer rule (load-bearing decision)

Every module belongs to exactly one of three layers; dependencies flow in one
direction:

```ascii
  ui/  ─────────►  infrastructure/  ─────────►  core/
  │
  └──────────────────────────────────────────►  core/
```

| Layer             | Purpose                                                     | May import                   | Must NOT import                                |
| ----------------- | ----------------------------------------------------------- | ---------------------------- | ---------------------------------------------- |
| `core/`           | Pure domain: dataclasses, business rules, maths, protocols. | stdlib, peer `core/` modules | PySide6, `serial`, `infrastructure/`, `ui/`    |
| `infrastructure/` | Adapters: device I/O, file I/O, config, logging.            | stdlib, `serial`, `core/`    | `ui/`. **PySide6 only inside `qt_threads.py`** |
| `ui/`             | PySide6 windows, widgets, tabs, dialogs.                    | everything below             | nothing else; no domain rules of its own       |

**Forbidden edges (verify before merging):**

- `core/ → ui/` — would couple domain logic to widgets
- `core/ → infrastructure/` — would couple domain logic to serial/files
- `infrastructure/ → ui/` — would couple drivers to widgets

### Why

1. `core/` is testable without Qt. Tests for interval binning, duration
   trimming, export path composition, and reconnect logic run in milliseconds
   and never open a display.
2. Hardware can be mocked at the adapter boundary. `MockGMCounter` (PTY-based)
   speaks the same binary protocol as a real device; `DataAcquisitionThread`
   uses the same parser either way.
3. `infrastructure/` stays import-clean: only `qt_threads.py` has Qt, so every
   other infra module is unit-testable without a running QApplication.

### How to apply

When adding a feature, identify which layer it belongs to first. If it needs
Qt, it belongs in `ui/` (or, if it truly needs a QThread worker, in
`infrastructure/qt_threads.py`). If it could work in a CLI script, it belongs
in `core/` or `infrastructure/`.

Enforce with a one-liner pre-commit check:

```bash
# Should return zero files:
grep -rln "PySide6" gmcounter/core/ gmcounter/infrastructure/*.py \
  $(find gmcounter/infrastructure -name "*.py" ! -name "qt_threads.py")
```

---

## 2. Qt Designer is the source of truth for visual structure

Every visible widget, layout, label, button, group box, dock, table view, and
spinbox lives in a `.ui` file edited in Qt Designer. Python files contain only
**signal connections, slot logic, and state manipulation** — never widget
construction.

### The rule, precisely

- Allowed Qt object creation in window/dialog Python: base classes
  (`QMainWindow`, `QDialog`, `QWidget`), model classes attached to `.ui`
  views (`QStandardItemModel`), modal helpers (`QFileDialog`, `QMessageBox`),
  event types (`QCloseEvent`), and `@Slot` / `QTimer`.
- pyqtgraph widgets (`GeneralPlot`, `HistogramWidget`) are created in Python
  because Qt Designer cannot host third-party custom widgets. They are injected
  into empty `QWidget` containers declared in `.ui` with `native="true"`.
- `pyuic.sh` regenerates `pyqt/ui_*.py` from `pyqt/*.ui`. Generated files are
  committed but never edited by hand. After every `.ui` change:
  `bash gmcounter/pyqt/pyuic.sh`.

### Injection pattern

Tabs receive `.ui` widget references via an `inject_*()` call before `build()`.
They never import `Ui_MainWindow` or walk the widget tree:

```python
# In MainWindow.__init__:
self._gm_tab.inject_ui_containers(
    plot_container=self.ui.timePlot,   # QWidget native="true" declared in .ui
    hist_container=self.ui.histWidget,
    table_view=self.ui.tableView,
    ...
)
self._gm_tab.build()   # creates GeneralPlot inside timePlot — nothing else
```

### Justified exceptions

| Kind of object                               | Why Python creates it                          |
| -------------------------------------------- | ---------------------------------------------- |
| `GeneralPlot`, `HistogramWidget` (pyqtgraph) | Designer cannot host third-party widgets       |
| `QStandardItemModel` on a `.ui` `QTableView` | Non-visual data model; the view lives in `.ui` |
| `QStandardItem` rows appended at runtime     | Dynamic data                                   |

---

## 3. AppController: the single bridge between hardware and UI

`AppController` (`ui/controllers/app_controller.py`) is the sole `QObject`
that owns the device lifecycle, all `QTimer` instances, the
`DataAcquisitionThread`, the reconnect FSM, and the frame fan-out to the active
tab. Windows subscribe to its signals; they never poll the device directly.

### Signal contract

```python
class AppController(QObject):
    # --- connection lifecycle ---
    connection_status_changed = Signal(str, str)   # (state_str, detail)
    reconnect_attempt         = Signal(int, float)  # (attempt_n, delay_s)
    reconnect_succeeded       = Signal()
    connection_lost           = Signal()

    # --- measurement lifecycle ---
    measurement_started = Signal()
    measurement_stopped = Signal()

    # --- live data ---
    frames_ready = Signal(list)  # list[Frame], delivered to active PlotTabBase

    # --- device readbacks ---
    voltage_updated      = Signal(float)
    count_time_updated   = Signal(int)
```

### Rules

- **One controller.** `MainWindow` holds one `_ctrl` and passes it nothing else.
- **The controller emits, never blocks.** Long work goes to `DataAcquisitionThread`
  or `ReconnectWorker` (see §4).
- **Signal payload types are primitives or `@dataclass(frozen=True)`.** The
  `Frame` dataclass is the canonical cross-thread bundle.
- **The controller owns the recovery state machine.** Windows present state;
  they do not decide policy.
- **Cleanup is `_ctrl.cleanup()` from `closeEvent`.** Stops timers, stops the
  acquisition thread, waits for workers.

---

## 4. Threading: one place for Qt threads, queued signals everywhere else

PyQt threading bugs all trace back to "I touched a widget from a worker thread."
Two rules prevent them:

1. **All `QThread` subclasses live in `infrastructure/qt_threads.py`.** It is
   the _only_ infrastructure file allowed to import PySide6.
2. **Workers emit signals; they never touch widgets.** Qt's auto-connection
   upgrades the calls to queued delivery.

### `DataAcquisitionThread` shape

```python
class DataAcquisitionThread(QThread):
    data_batch = Signal(list)   # list[Frame] — fan-out to AppController

    def run(self):
        while not self._stop_flag.is_set():
            raw = self._dm.device.read_raw()   # blocks briefly
            frames = self._parser.feed(raw)
            if frames:
                self.data_batch.emit(frames)
```

The `PacketParser` is extracted into `infrastructure/packet_parser.py` so it
can be unit-tested without a QThread.

### `ReconnectWorker` shape

```python
class ReconnectWorker(QThread):
    succeeded = Signal()
    failed    = Signal()

    def run(self):
        ok = self._dm.attempt_automatic_reconnect(desired=self._desired_state)
        (self.succeeded if ok else self.failed).emit()
```

### Lifetime

The owning controller stores the worker as an attribute. A new worker
overwrites the attribute only after the previous one finished. Connect
`worker.finished` to `worker.deleteLater`.

---

## 5. Resilience: the connection state machine has one owner

Hardware drops. Treat reconnection as a first-class state machine inside
`AppController`, with these contracts:

| Contract                              | Behaviour in GMCounter                                                                                                                                                                                                           |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **B1 — silent first failure**         | The first read error does not show a popup. It increments a counter and schedules a retry. Only the second consecutive failure (or a new error type) updates the status bar.                                                     |
| **B2 — exponential backoff with cap** | Delays grow `500 ms → 1 s → 2 s → 4 s → … → 16 s`, capped. Parameters in `config.json → connection.*`.                                                                                                                           |
| **B3 — non-blocking UI**              | The status bar and `EventLogPanel` show reconnect state. Inputs are **not** disabled during `RECONNECTING` — the user can continue entering parameters for the next measurement.                                                 |
| **B4 — data survives reconnect**      | Measurement buffers, plots, and the session journal are preserved across a drop. A `gap` can be written to the journal for downstream analysis.                                                                                  |
| **B5 — desired-state replay**         | Voltage, counting time, repeat mode, and stream mode are snapshotted in a `DesiredState` dataclass (`core/models.py`) and re-applied on every successful reconnect via `DeviceManager.attempt_automatic_reconnect(desired=...)`. |
| **B6 — filter resets on recovery**    | Internal parser state (`PacketParser.reset()`) is flushed on reconnect so a partial packet from before the drop does not corrupt the first frame after.                                                                          |
| **B7 — terminal state is explicit**   | When backoff is exhausted, `AppController` emits `connection_lost` and the EventLogPanel notes the session journal path so the user can recover data.                                                                            |

### Crash-safe journaling

`SessionJournal` (`infrastructure/session_journal.py`) appends every data
point to `~/.gmcounter/sessions/<ts>/journal.csv` with `fsync` every ~1 s. On
startup, `find_orphan_journals()` reports sessions without a `finalized` marker
so the user can recover partial data.

---

## 6. Extensibility: experiment tabs as a plugin point

There are two tab patterns; choose based on whether the experiment needs
real-time frames.

### Pattern A — Frame-based tab (`PlotTabBase`)

For experiments that process every acquired data point live (time-series,
histogram). `AppController.set_active_tab()` wires `frames_ready` to it.

```python
class PlotTabBase(QWidget):
    tab_id:          str        = ""     # stable key, used in tests
    tab_title:        str        = ""     # user-visible label
    required_modules: set[str]   = set()  # gates visibility on a HostModule

    # lifecycle hooks
    def build(self) -> None: ...
    def on_frames(self, frames: list[Frame]) -> None: ...   # prefer over on_frame
    def on_reset(self) -> None: ...
    def on_measurement_started(self) -> None: ...
    def on_measurement_stopped(self) -> None: ...
    def export(self) -> Optional[TabExport]: ...
```

**Adding a frame-based tab:**

1. Add a `QWidget` page in `mainwindow.ui`.
2. Subclass `PlotTabBase`, implement `build()` and `on_frames()`.
3. Call `TabRegistry.register(MyTab)` at module level (import-time).
4. In `MainWindow.__init__`, call `inject_*()` + `build()`.

`required_modules` gating: tab is hidden until a `HostModule` with the
declared `id` is registered in `ModuleRegistry` at runtime.

### Pattern B — Parameter-sweep tab (`ParameterSweepTabBase`)

For experiments that sweep one external parameter (distance, voltage) across
multiple complete measurements and accumulate a summary. These tabs are
**overlay listeners**: they do not receive frames directly; they snapshot
`GMTimingTab`'s completed export when `measurement_stopped` fires.

```python
class ParameterSweepTabBase(PlotTabBase):
    # subclasses set class attributes only — no method bodies needed:
    param_label:           str   # axis label, e.g. "Probenabstand (cm)"
    param_unit:            str   # e.g. "cm"
    param_metadata_key:    str   # key on individual exports
    summary_filename_hint: str   # CSV stem, e.g. "abstandsgesetz"
    summary_title:         str   # metadata title

    def set_gm_tab(self, gm_tab): ...
    def inject_ui(self, plot_container, table_view, param_input, status_label): ...
    def on_measurement_stopped(self) -> None: ...
    def has_unsaved_data(self) -> bool: ...
    def mark_saved(self) -> None: ...
    def reset_summary(self) -> None: ...
    @property
    def individual_exports(self) -> list[TabExport]: ...
    def summary_export(self) -> Optional[TabExport]: ...
```

The `.ui` page needs exactly four named widgets:
`<prefix>Input` (QDoubleSpinBox), `<prefix>Plot` (QWidget native),
`<prefix>Table` (QTableView), `<prefix>Status` (QLabel).

**IMPORTANT: Sweep tabs do NOT call `TabRegistry.register()`.** They are
explicitly wired in `MainWindow.__init__` and do not go through the
auto-discovery path (unlike frame-based tabs which do register).

**Sweep session lifecycle** (managed by `MainWindow`):

- Start on a sweep tab → disables GM view tabs (0–2), suppresses
  `GMTimingTab` high-speed auto-switch, sets `_sweep_session = True`
- Stop → Start re-enabled immediately for the next parameter point
- Speichern → write summary CSV + auto-named individual timing CSVs; call
  `reset_summary()`, re-enable view tabs, clear `_sweep_session`
- Reset → discard summary, re-enable view tabs

### The registry

`TabRegistry` (`ui/tabs/registry.py`) only holds **frame-based** tabs that are
auto-discovered by `AppController`:

```python
class TabRegistry:
    @classmethod
    def register(cls, tab_class: type[PlotTabBase]) -> None: ...
    @classmethod
    def available(cls, modules: dict) -> list[type[PlotTabBase]]:
        return [t for t in cls._tabs if t.required_modules.issubset(modules)]
```

---

## 7. Save / Export: tabs declare a schema, the writer is generic

Tabs return a `TabExport` dataclass; the infrastructure writer handles CSV +
sidecar `_MD.json` without knowing what experiment produced it.

```python
@dataclass
class TabExport:
    filename_hint:   str               # e.g. "gm_timing", "abstandsgesetz"
    columns:         list[str]
    rows:            list[list[str]]   # already-stringified values
    metadata:        dict              # Dublin-Core-style sidecar
    filename_tokens: list[str] = field(default_factory=list)
```

**Two write paths:**

- `infrastructure.save_service.write_export(export, csv_path)` — standalone
  function, used by `MainWindow` for manual saves via file dialog.
- `infrastructure.save_service.SaveService.save(export)` — auto-index helper,
  used by the app when saving to a predetermined directory tree.

`core.export.compose_save_path()` composes the target path from a `TabExport`
and a base directory — pure logic, no I/O.

`core.export.build_gm_tab_export()` builds a `TabExport` from a
`MeasurementSession` — also pure, no I/O.

Unsaved-state tracking (dirty flag + `base_dir` for dialog suggestions) lives
in `core.services.SaveState`, which holds no file I/O.

---

## 8. Modules: host-side peripherals are a Protocol

Some hardware lives on the host (USB-attached stages, power supplies), not
behind the firmware. Model them with a Protocol and a tiny registry:

```python
@runtime_checkable
class HostModule(Protocol):
    @property
    def id(self) -> str: ...
    def connect(self) -> bool: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    def describe(self) -> str: ...

class ModuleRegistry:
    @classmethod
    def register(cls, m: HostModule) -> None: ...
    @classmethod
    def get(cls, mid: str) -> Optional[HostModule]: ...
    @classmethod
    def all(cls) -> dict[str, HostModule]: ...
```

Tabs gate themselves with `required_modules`. If a tab declares
`required_modules = {"kdc101"}`, it is hidden until the `kdc101` module is
registered at runtime.

---

## 9. Status, errors, and logging

### User feedback surfaces

| Surface                | What it shows                                  | Lifetime                                              |
| ---------------------- | ---------------------------------------------- | ----------------------------------------------------- |
| `StatusBar`            | One-line transient status                      | 3–8 s, via `StatusBarManager.show_info/warning/error` |
| `EventLogPanel` (dock) | Timestamped scrollback of every status message | Persistent in-session                                 |

Modals (`QMessageBox`) are reserved for **terminal** failures (connection lost,
save failed) and user questions ("discard unsaved data?"). Never use modals for
recoverable transients.

### Logging

Use `logging.getLogger(__name__)` in every module. `infrastructure.logging.Debug`
configures the `gmcounter` root logger (levels `DEBUG_OFF / INFO / VERBOSE / ERROR`)
with console + rotating file handler and a global `sys.excepthook`. All
`getLogger` output propagates through it automatically.

The `core.ports.Logger` Protocol allows `core/` modules to log without
importing `infrastructure.logging`.

---

## 10. Configuration

One `config.json` at `gmcounter/config.json`, loaded via `import_config()` from
`gmcounter.infrastructure.config`. All values live under the `"de"` language key.

Key sections:

| Section               | Contents                                                        |
| --------------------- | --------------------------------------------------------------- |
| `acquisition.*`       | `ticks_per_us` (48 for RA4M1 @ 48 MHz), read chunk/timeout      |
| `connection.*`        | Backoff parameters (retry attempts, delays, factor)             |
| `timers.*`            | GUI update interval, statistics interval, acquisition poll rate |
| `gm_counter.*`        | `demo_mode`, default voltage, `count_time_map`, `label_map`     |
| `save.*`              | `base_folder`, `tk_designation` for directory naming            |
| `gm_timing.*`         | `max_history_size`, high-speed batch parameters                 |
| `ui.*`                | `theme` (`"dark"` or `"light"`)                                 |
| `messages.*`          | All user-visible German strings (for i18n)                      |
| `radioactive_samples` | List of valid sample codes                                      |

### Rules

- **No magic numbers in code.** Timer intervals, retry caps, and thresholds all
  come from config with a `.get(key, default)` fallback.
- `import_config()` re-reads the JSON on every call. Cache the result at
  module level: `CONFIG = import_config()`.

---

## 11. Mocks live next to drivers, not in tests

A mock is an _implementation_ of the same adapter contract, not a test
fixture. `infrastructure/mocks/mock_gm_counter.py` (`MockGMCounter`) is a
PTY-backed simulator that speaks the same binary protocol as a real GM counter
device. The device adapter under test (`GMCounterAdapter`, `DataAcquisitionThread`,
`PacketParser`) is literally unchanged when switching to the mock.

Mocks are excluded from the wheel:

```toml
[tool.setuptools.packages.find]
exclude = ["gmcounter.infrastructure.mocks", "gmcounter.infrastructure.mocks.*"]
```

---

## 12. Window lifecycle and teardown

`closeEvent` is the only place that does shutdown:

```python
def closeEvent(self, event):
    if self._save_state.has_unsaved():
        # ask user to confirm discard
        ...
    self._ctrl.cleanup()          # stops timers, joins threads, closes journal
    self._device_manager.disconnect()
    event.accept()
```

### Rules

- `AppController` exposes `cleanup()`; `MainWindow` never stops its timers directly.
- Workers are joined with a bounded `wait(3000)` after `quit()`; never `terminate()`.
- Every modal dialog sets `WA_DeleteOnClose`.

---

## 13. Naming conventions

| Item             | Convention                                                                   |
| ---------------- | ---------------------------------------------------------------------------- |
| Device adapters  | `{Name}Adapter` (e.g. `GMCounterAdapter`)                                    |
| Mocks            | `Mock{Name}` (e.g. `MockGMCounter`)                                          |
| Tab classes      | `{Experiment}Tab` with `tab_id = "{experiment}"`                             |
| Signals          | `verb_past_tense` (`measurement_stopped`, `frames_ready`, `connection_lost`) |
| Slots / handlers | `_handle_*` or `_on_*` for receivers; `_action_verb` for user-initiated      |
| Type hints       | Required on new code. No bare `Any`. Use `Optional[X]` for nullable.         |
| Config keys      | `snake_case` matching the subsystem name (e.g. `gm_timing`, `acquisition`)   |

---

## 14. Anti-patterns to remove aggressively

1. **Widgets constructed in Python where a `.ui` could host them.** Every such
   instance creates a divergence between the visual design and the Python.
2. **`QTimer` started inside a window `__init__` to poll a device.** Move it
   into `AppController`.
3. **`device.read()` called from a slot on the main thread.** Push it into
   `DataAcquisitionThread`.
4. **`time.sleep()` in any UI code path.** Use `QTimer.singleShot(ms, slot)`.
5. **`QMessageBox` for transient errors.** Use the status bar / `EventLogPanel`.
6. **`try/except ImportError` around `from PySide6 import ...`** — either Qt
   is a hard dependency or it isn't.
7. **`print()` for debugging.** Use `logging.getLogger(__name__).debug(...)`.
8. **Direct `import` of the deprecated `controllers/__init__` package for
   `DataController` or `ControlWidget`** — both are removed.

---

## 15. Reference layout (actual on-disk tree)

```
gmcounter/
├── __init__.py                   # version
├── __main__.py                   # python -m gmcounter entry point
├── main.py                       # QApplication + MainWindow bootstrap
├── config.json                   # all tunables and user-visible strings
├── core/                         # pure Python — NO Qt, NO serial
│   ├── models.py                 # MeasurementPoint, Frame, DesiredState, …
│   ├── export.py                 # TabExport, build_gm_tab_export, compose_save_path
│   ├── services.py               # SaveState, MeasurementStateService
│   ├── reconnect_service.py      # ReconnectStrategy, ConnectionRetryService
│   ├── duration.py               # accumulate_and_trim()
│   ├── interval_binning.py       # IntervalBinner, IntervalBins
│   ├── utils.py                  # filename sanitization, calculate_statistics
│   ├── exceptions.py             # GMCounterError hierarchy
│   └── ports.py                  # Logger Protocol
├── infrastructure/               # adapters — Qt ONLY in qt_threads.py
│   ├── config.py                 # import_config()
│   ├── logging.py                # Debug singleton
│   ├── device_manager.py         # connect/disconnect, desired-state replay
│   ├── packet_parser.py          # incremental binary decoder
│   ├── qt_threads.py             # DataAcquisitionThread, ReconnectWorker
│   ├── serial_device.py          # low-level serial helpers
│   ├── session_journal.py        # crash-safe append-only journal
│   ├── save_service.py           # write_export(), SaveService (auto-index)
│   ├── devices/gm_counter.py     # GMCounterAdapter
│   ├── mocks/mock_gm_counter.py  # MockGMCounter (PTY, excluded from wheel)
│   └── modules/registry.py       # HostModule Protocol + ModuleRegistry
├── pyqt/                         # Qt Designer sources + generated ui_*.py
│   ├── mainwindow.ui             # ← edit in Qt Designer
│   ├── connection.ui
│   ├── alert.ui
│   ├── ui_mainwindow.py          # ← generated by pyuic.sh — DO NOT EDIT
│   ├── ui_connection.py
│   ├── ui_alert.py
│   └── pyuic.sh                  # regeneration script
└── ui/
    ├── controllers/
    │   └── app_controller.py     # AppController(QObject) — sole controller
    ├── windows/
    │   └── main_window.py        # MainWindow — chrome only
    ├── dialogs/
    │   └── connection.py         # ConnectionWindow
    ├── tabs/
    │   ├── base.py               # PlotTabBase
    │   ├── registry.py           # TabRegistry (frame-based tabs only)
    │   ├── gm_timing_tab.py      # GMTimingTab (frame-based, 3 views)
    │   ├── parameter_sweep_base.py   # ParameterSweepTabBase
    │   ├── distance_law_tab.py   # DistanceLawTab (sweep)
    │   ├── voltage_response_tab.py  # VoltageResponseTab (sweep)
    │   └── interval_repeat_tab.py   # IntervalRepeatTab (frame-based, MCS)
    ├── widgets/
    │   ├── plot.py               # GeneralPlot, HistogramWidget (pyqtgraph)
    │   └── event_log_panel.py    # EventLogPanel (dock)
    ├── resources/
    │   └── stylesheet.py         # get_stylesheet(), apply_stylesheet()
    └── common/
        ├── dialogs.py            # show_info/warning/error helpers
        ├── statusbar.py          # StatusBarManager
        └── file_dialogs.py       # FileDialogManager (save dialog UI)
```

---

## 16. Quick checklist when reviewing a PR

- [ ] No `core/` import of Qt, PySide6, `serial`, or `infrastructure/`.
- [ ] No `infrastructure/` Qt import outside `qt_threads.py`.
- [ ] No `ui/` widget constructed in Python where a `.ui` could host it.
- [ ] Every new signal carries primitives or a frozen dataclass (`Frame`, `TabExport`).
- [ ] Every new worker has a stop flag and a `failed` signal.
- [ ] Every new frame-based tab subclasses `PlotTabBase` and calls
      `TabRegistry.register()` at import time.
- [ ] Every new sweep tab subclasses `ParameterSweepTabBase`, sets six class
      attributes, and does **NOT** call `TabRegistry.register()`.
- [ ] Every new sweep tab's `.ui` page declares the four named widgets
      (`<prefix>Input`, `<prefix>Plot`, `<prefix>Table`, `<prefix>Status`).
- [ ] Every new tunable lives in `config.json` under a sensible section, not
      hardcoded.
- [ ] Tests exist at the right layer: `tests/core/` → unit, `tests/infrastructure/`
      → with mock device, `tests/ui/` → with `QTest`/offscreen.

---

## 17. One-line summary

> GMCounter is maintainable because the **physics is pure** (`core/`),
> the **drivers are mockable** (`infrastructure/`),
> the **widgets come from Designer** (`pyqt/*.ui`),
> and the **controller is the only thing that talks to hardware** (`AppController`).
