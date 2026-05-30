# ARCHITECTURE.md

A reusable architectural blueprint for a desktop PySide6/PyQt application that
talks to hardware, displays live data, and lets a user run multi-mode
measurement experiments. Distilled from the `polarisation-ui` project so it can
be applied as-is to refactor another PyQt project.

The document is organised by concern, not by file. Each section starts with the
**rule** (what to do), then the **rationale** (why this rule pays off in a
PyQt+hardware codebase), then a **how-to-apply** sketch with concrete code/file
shapes from this repo.

---

## 1. The three-layer rule (this is the load-bearing decision)

Every module belongs to exactly one of three layers, and dependencies flow in
exactly one direction:

```ascii
  ui/  ─────────►  infrastructure/  ─────────►  core/
  │
  └──────────────────────────────────────────►  core/
```

| Layer             | Purpose                                         | What it MAY import                     | What it MUST NOT import                                        |
| ----------------- | ----------------------------------------------- | -------------------------------------- | -------------------------------------------------------------- |
| `core/`           | Pure domain: dataclasses, business rules, math. | stdlib, `numpy`, peer `core/` modules  | PySide6, Qt, `serial`, hardware SDKs, `ui/`, `infrastructure/` |
| `infrastructure/` | Adapters: device I/O, files, config, logging.   | stdlib, `serial`, vendor SDKs, `core/` | `ui/`. **PySide6 only inside ONE designated file** (see §6)    |
| `ui/`             | PySide6 widgets and presentation logic.         | everything below                       | nothing else; no business rules of its own                     |

**Forbidden edges (verify before merging):**

- `core/ → ui/` — would couple physics to widgets
- `core/ → infrastructure/` — would couple physics to serial/files
- `infrastructure/ → ui/` — would couple drivers to widgets

### Why this layout

1. **You can unit-test core without Qt installed.** Tests for goniometer math,
   filename composition, calibration curves, and circular-mean angle averaging
   run in milliseconds and never touch a screen.
2. **You can mock hardware at the adapter boundary.** The UI does not know
   whether it's talking to a real Arduino or a PTY-backed simulator.
3. **You can replace the UI framework.** The CLI launcher (`main.py`) and the
   `--debug-only` / `--power-cal` standalone modes prove this — they reuse the
   exact same `core/` and `infrastructure/` and only swap the top-level
   widget.

### How to apply

When starting a refactor, the very first commit should be physical relocation:
move every dataclass and every pure function into `core/`, every adapter and
file-I/O into `infrastructure/`, and leave only widgets, signals, and slots in
`ui/`. Resist the urge to "clean up while moving" — do the move, get green
tests, then refactor inside each layer.

Mark each layer's `__init__.py` with the import rule as a comment so future
readers can't accidentally introduce a back-edge.

---

## 2. Qt Designer is the source of truth for visual structure

Every visible widget, layout, label, button, group box, menu, and dock lives
in a `.ui` file edited in Qt Designer. Python files contain only **signal
connections, slot logic, and state manipulation** — never widget construction.

### The rule, precisely

- Allowed Qt imports in window/dialog Python files: base classes
  (`QMainWindow`, `QDialog`, `QWidget`), modal helpers (`QFileDialog`,
  `QMessageBox`), event types (`QCloseEvent`), and `@Slot` / `QTimer`.
- `QButtonGroup` may be instantiated in Python because it is a non-visual
  logical helper. Its member buttons must still live in the `.ui`.
- `pyuic.sh` regenerates `ui_*.py` from `*.ui`. Generated files are committed
  but never edited by hand.

### Exceptions (allowed, but each one is justified in writing)

| Kind of file                                 | Why Python builds widgets here                      |
| -------------------------------------------- | --------------------------------------------------- |
| `*_plot.py` (pyqtgraph widgets)              | Designer can't host third-party custom widgets      |
| `PlotTabBase` subclasses                     | Tab-extensibility pattern uses `build()` for layout |
| One-off windows with no Designer counterpart | User-approved; document the exception in CLAUDE.md  |

### Why this rule

PyQt projects rot fastest when widget construction sprawls across Python. You
end up with three different ways to add a "save" button (`.ui`, Python, copy-
pasted from another window), and you can't diff visual changes. Forcing
Designer also gives you free internationalisation hooks and the WYSIWYG
preview as a sanity check.

### How to apply

1. For each existing window/dialog, create a `.ui` file in `pyqt/`.
2. Move every widget into it. The Python file shrinks to: `setupUi(self)`,
   `_connect_signals()`, and slot methods.
3. Run `pyuic.sh` (or `pyside6-uic`) to regenerate `ui_*.py` on every `.ui`
   change. Put this in a pre-commit hook if you can.
4. Add a CI check that imports each window class — broken `setupUi()` is
   loud and immediate.

---

## 3. The Controller pattern bridges device → UI

A single `*Controller` (`QObject`) owns the polling timer, the read loop, the
reconnect state machine, the rolling-average buffers, and emits Qt signals
that windows subscribe to. The window never polls; the device never knows
about Qt.

### Anatomy of a controller

```python
class DataController(QObject):
    # ---- outbound signals (the entire contract with the UI) ----
    angles_updated   = Signal(float, float)
    intensity_updated = Signal(float)
    frame_ready      = Signal(Frame)            # consolidated per-sample bundle
    diagnostics_updated = Signal(bool, str, bool, str)
    poll_rate_updated = Signal(float)

    error_occurred   = Signal(str)
    retry_connecting = Signal(int, float)       # attempt#, delay_s
    reconnect_succeeded = Signal()
    connection_lost  = Signal()

    measurement_started = Signal()
    measurement_stopped = Signal()

    def __init__(self, device_manager, parent=None):
        super().__init__(parent)
        self.poll_timer = QTimer(self); self.poll_timer.timeout.connect(self._poll)
        self._retry_timer = QTimer(self); self._retry_timer.setSingleShot(True)
        ...
```

### Rules

- **One controller per stream.** Don't fan poll loops out across windows.
- **The controller emits, never blocks.** Long work goes to a `QThread`
  worker (§4).
- **Signal types carry primitives or `@dataclass(frozen=True)`** — never raw
  device handles or mutable buffers. Cross-thread queued signals must be safe
  to copy.
- **The controller owns the recovery state machine** (errors, backoff,
  buffer flushes). Windows present state; they don't choose policy.
- **Cleanup is a single method** (`controller.cleanup()`) called from
  `closeEvent`. Stops timers, joins workers, closes journals.

### Why

PyQt code goes wrong when widgets directly call `device.read()`. The poll
becomes coupled to whichever window is open, error handling is duplicated per
window, and threading becomes whack-a-mole. Concentrating the state machine
makes every UI surface a passive observer.

### How to apply

Define the signal list **first** — that is the controller's public API. Make
windows only consume signals; never let a window keep a reference to the
device manager except for one-shot user actions (zero, set-gain, connect).

---

## 4. Threading: one place for Qt threads, queued signals everywhere else

PyQt's threading mistakes are all variations of "I touched a widget from a
worker thread." Avoid them with three rules.

1. **All `QThread` subclasses live in one module** (`infrastructure/qt_threads.py`).
   It is the _only_ infrastructure file allowed to import PySide6. Every other
   infrastructure file stays Qt-free so it can be unit-tested with plain
   `pytest`.
2. **Workers emit signals; they never touch widgets.** Receivers live on the
   main thread and Qt's auto-connection upgrades the calls to queued
   delivery.
3. **Workers expose a clean `abort()` flag**, not `terminate()`. The `run()`
   method polls the flag at every loop boundary.

### Standard worker shape

```python
class ReconnectWorker(QThread):
    succeeded = Signal()
    failed    = Signal()

    def __init__(self, device_manager, parent=None):
        super().__init__(parent)
        self._dm = device_manager

    def run(self):
        try:
            ok = self._dm.reconnect_encoders()      # blocks with sleep()
        except Exception as exc:
            Debug.error(f"reconnect: {exc}")
            self.failed.emit(); return
        (self.succeeded if ok else self.failed).emit()
```

### Lifetime

The owning controller stores the worker as an attribute (so it is not garbage-
collected while running) and connects `worker.finished` to `worker.deleteLater`.
A new worker overwrites the attribute only after the old one finished.

### Why

Crashes from "QObject: Cannot create children for a parent that is in a
different thread" or zombie threads on shutdown are the #1 source of PyQt
support tickets. The "one Qt module in infrastructure" rule keeps Qt out of
your mock layer and forces every infra dependency to be testable without a
display.

### How to apply

When porting a project: grep for `QThread`, `QtCore` in your infrastructure;
move every offender into one file. Anything else that needs background work
becomes a callable that the Qt-thread module wraps.

---

## 5. Resilience: the connection state machine has one owner

Hardware drops. Treat reconnection as a first-class state machine inside the
controller, with these contracts:

| Contract                              | Behaviour                                                                                                                                                                                     |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **B1 — silent first failure**         | The first read error does not show a popup or error banner. It increments a counter and schedules a retry. Only the second consecutive failure (or a new error type) raises `error_occurred`. |
| **B2 — exponential backoff with cap** | Delays `[1 s, 2 s, 4 s, 8 s, 15 s]`, capped. Controlled by the controller's `_retry_timer`.                                                                                                   |
| **B3 — non-blocking UI**              | A `ConnectionBanner` (a `QFrame` overlay) shows state. Inputs are **not** disabled during `RECONNECTING` — the user can keep entering points.                                                 |
| **B4 — data survives reconnect**      | Measurement buffers, plots, and the session journal are preserved. A `gap` marker is written so plots can show a discontinuity.                                                               |
| **B5 — desired-state replay**         | All `CONF:*` settings (gain, mux, stream sources, rate) are snapshotted in a `DesiredState` dataclass and reapplied on every successful reconnect.                                            |
| **B6 — filter resets on recovery**    | Spike-filter reference values and averaging buffers are flushed on reconnect so a stale "before" sample doesn't reject the first "after" sample.                                              |
| **B7 — terminal state is explicit**   | When the backoff cap is exhausted, emit `connection_lost`. The UI offers "Export partial data" pointing at the on-disk journal.                                                               |

### Crash-safe journaling

Every emitted frame is appended to `~/.<app>/sessions/<ts>/journal.csv` with
`fsync` every ~1 s. On startup, scan for sessions without a `finalized`
marker — these are orphans. Offer recovery export, then delete (or keep on
user request).

### Why

The most painful bug a hardware UI can ship is "user took a long measurement,
USB dropped at minute 47, all data lost." The journal + desired-state snapshot
makes this a recoverable inconvenience instead of an incident.

### How to apply

Implement the journal _before_ implementing the disk export feature. Once
journaling is in, the explicit "Save" button just exports the journal to a
user-chosen path and renames it `finalized`.

---

## 6. Extensibility: experiment tabs as a plugin point

A measurement application accumulates experiment modes. Bake the extension
seam in from day one — even if you only have one tab today.

### The tab contract

```python
class PlotTabBase(QWidget):
    tab_id:           str        = ""        # stable key, used in tests & persistence
    tab_title:        str        = ""        # user-visible label
    required_sources: set[str]   = set()     # data streams the tab needs (e.g. {"ADC"})
    required_modules: set[str]   = set()     # host modules required (e.g. {"kdc101"})

    # outbound signals (uniform across all tabs)
    status_message        = Signal(str, str)   # ("info"|"warning"|"error", text)
    filename_hint_changed = Signal()
    request_module_action = Signal(str, dict)

    # lifecycle hooks (override only what you need)
    def build(self) -> None: ...
    def on_frame(self, frame: Frame) -> None: ...
    def on_reset(self) -> None: ...
    def on_connection_state(self, state: ConnState) -> None: ...
    def on_activated(self)   -> None: ...
    def on_deactivated(self) -> None: ...
    def on_measurement_started(self) -> None: ...
    def on_measurement_stopped(self) -> None: ...
    def inject_modules(self, modules: dict[str, object]) -> None: ...
```

### The registry

```python
class TabRegistry:
    _tabs: list[type[PlotTabBase]] = []
    @classmethod
    def register(cls, tab_class): ...
    @classmethod
    def available(cls, modules):
        return [t for t in cls._tabs if t.required_modules.issubset(modules.keys())]
```

Adding a new experiment is three steps:

1. Subclass `PlotTabBase`, implement `build()` and `on_frame()`.
2. `TabRegistry.register(MyTab)` at import time.
3. The main window iterates the registry; the new tab appears.

Tabs declaring `required_modules = {"kdc101"}` only become visible when the
matching module is registered in the `ModuleRegistry` at runtime. When the
device is unplugged, `_refresh_tab_visibility()` hides them again without
destroying state.

### Why

Without this seam, every new experiment becomes a fork of the main window.
With it, the main window is _closed for modification, open for extension_.

### How to apply

When refactoring, identify the chunks of `MainWindow` that change per
experiment (controls, plots, save logic) and pull them behind `PlotTabBase`.
Anything that stays in the main window is shared chrome: connection panel,
status bar, menus, file naming.

---

## 7. Save / Export: tabs declare a schema, the writer is generic

Tabs return a `TabExport` dataclass; the save service writes any CSV+metadata
without knowing what kind of experiment it was.

```python
@dataclass
class TabExport:
    filename_hint:   str            # e.g. "brewster", "malus"
    columns:         list[str]
    rows:            list[list[str]]  # already-stringified
    metadata:        dict
    filename_tokens: list[str] = field(default_factory=list)
```

`save_tab_export(path, exp, group_letter, suffix, ...)` handles directory
creation, header writing, sidecar `metadata.json`, and timestamping.

### Why

Centralising the writer means every experiment gets the same Dublin-Core-style
metadata, the same CSV dialect, and the same atomic write semantics. A new
experiment adds zero lines of file-I/O code.

---

## 8. Modules: host-side peripherals are a Protocol

Some hardware lives on the host (USB-attached stages, power meters), not
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
    _registry: dict[str, HostModule] = {}
    @classmethod
    def register(cls, m: HostModule): cls._registry[m.id] = m
    @classmethod
    def get(cls, mid: str): return cls._registry.get(mid)
    @classmethod
    def all(cls): return dict(cls._registry)
```

Tabs gate themselves with `required_modules`. The main window calls
`tab.inject_modules(ModuleRegistry.all())` whenever the registry changes.

### Why

Without this, every tab grows direct imports of every optional driver. With
it, the tab declares "I need `kdc101`" and is invisible when it isn't there.
Mocks satisfy the same Protocol, so tests never touch real hardware.

---

## 9. Status, errors, and logging

### Three concentric layers of user feedback

| Layer                         | What it says                                       | Lifetime                                         |
| ----------------------------- | -------------------------------------------------- | ------------------------------------------------ |
| `StatusBar`                   | One-line transient status (`✓ Connected`, `⚠ ...`) | 3–8 s, set via `show_info/success/warning/error` |
| `EventLogPanel` (dock)        | Timestamped scrollback of every status line        | persistent in-session                            |
| `ConnectionBanner` (`QFrame`) | Reconnect countdown / "data lost" callout          | only while not OK                                |

Forbidden: modal `QMessageBox.warning` for routine errors. Modals belong to
**terminal** failures (connection lost, save failed) and to _questions_
("export orphan journal?"), never to recoverable transients.

### Status LEDs

A tiny helper (`set_connection_status(led, label, text, style)`) keeps every
status indicator consistent. The styles come from `config.json`, so changing
"red" project-wide is a one-line edit.

### The Debug singleton

A single `Debug` class wraps `logging` with four levels (`OFF`, `ERROR`,
`INFO`, `VERBOSE`), a console + rotating file handler, and a global
`sys.excepthook` hook so unhandled exceptions land in the log instead of the
console.

### Why

A consistent status surface is the single biggest UX win in a lab tool: the
operator always knows _where_ to look for the answer to "is something wrong?"
The dock log gives a paper trail when things did go wrong.

---

## 10. Configuration

One `config.json` at the package root, loaded once via `import_config()`.
Sections:

- `messages.*` — every user-visible string (so i18n is a config swap)
- `ui.status_led.*` — LED colours
- `timers.*` — poll interval, diagnostic interval
- `connection.*` — `max_retry_attempts`, `backoff_delays_ms`
- `acquisition.*` — defaults for averaging, spike filter
- `save.*` — base folder name

### Rules

- **No magic numbers in code.** Timer intervals, retry caps, spike thresholds
  all come from config and have a `.get(key, default)` fallback.
- **Settings dialog changes live in memory only**, never written back to
  `config.json`. The config is the _default_, not the _state_.

---

## 11. Mocks live next to drivers, not in tests

A mock is an _implementation_ of the same adapter contract, not a test
fixture. Put them in `infrastructure/mocks/`. Exclude them from the wheel via
`pyproject.toml`:

```toml
[tool.setuptools.packages.find]
exclude = ["polarisation_ui.infrastructure.mocks", "polarisation_ui.infrastructure.mocks.*"]
```

Where possible, mocks should speak the same wire protocol as the real device
(here: a PTY-backed SCPI simulator), so the device adapter under test is
literally unchanged.

### Why

This rule kills "the mock passes but production fails" bugs because tests
exercise the same parser and the same serial code path. A test that
side-steps the adapter doesn't validate it.

---

## 12. Window lifecycle and teardown

`closeEvent` is the only place that does shutdown. The order is:

```python
def closeEvent(self, event):
    if self._is_measuring:
        self.data_controller.stop_measurement()
    self.data_controller.cleanup()       # stops timers, joins workers, closes journal
    self.device_manager.disconnect_all()
    event.accept()
```

### Rules

- Controllers expose `cleanup()`; windows never stop their timers directly.
- Workers are joined with a bounded `wait(3000)` after `quit()`; never
  `terminate()`.
- `WA_DeleteOnClose` is set on every modal dialog and standalone window so
  Python and Qt both free their refs.

---

## 13. Naming and small conventions

| Item                 | Convention                                                             |
| -------------------- | ---------------------------------------------------------------------- |
| Abstract interfaces  | `{Name}Adapter` or `{Name}Base`                                        |
| Mocks                | `Mock{Name}` (`MockArduino`, `MockPM400`)                              |
| Real implementations | `{Name}{Transport}` (e.g. `DualEncoderArduino`)                        |
| Tab classes          | `{Experiment}Tab` with `tab_id = "{experiment}"`                       |
| Signals              | `verb_past_tense` (`angles_updated`, `frame_ready`, `connection_lost`) |
| Slots                | `_handle_*` / `_on_*` for receivers; `_action_verb` for user-initiated |
| Type hints           | Required on new code. No bare `Any`. Use `Optional[X]` for nullable.   |

---

## 14. Anti-patterns to refactor out aggressively

When you find these in an existing PyQt project, prioritise removing them:

1. **Widgets created in Python in classes that have a `.ui` counterpart.**
   They drift out of sync with Designer; every change requires editing two
   files; reviewers can't see visual diffs.
2. **`QTimer` started inside a window's `__init__` to poll a device.**
   The window now owns hardware state and can't be reopened cleanly. Move it
   into a controller.
3. **`device.read()` called from a slot.** Slot runs on the main thread; a
   slow read freezes the UI. Push it into a worker or behind a controller's
   poll loop.
4. **`time.sleep()` in any UI code path.** Use `QTimer.singleShot(ms, slot)`.
5. **`QMessageBox` for transient errors.** Use the status bar / event log.
6. **`try/except` around `from PySide6 import ...`** to "support running
   without Qt." Either you depend on Qt or you don't; this hides import
   failures.
7. **Per-window logging setup.** One `Debug.init(...)` at app start, period.
8. **Mutable globals for device state.** Stuff them on the controller; tests
   then re-instantiate to reset.
9. **Direct `print()` debugging.** It survives commits. Use `Debug.debug()`.
10. **A single huge `mainwindow.py`.** Split per concern (connection panel,
    measurement panel, plot tabs, dialog launchers). If `mainwindow.py` is
    over ~1000 lines, you are missing an abstraction — usually the tab/plugin
    seam (§6).

---

## 15. Reference layout (what the on-disk tree should look like)

```asciss
<project>/
├── main.py                          # tiny launcher; chooses entry point
├── pyproject.toml                   # excludes mocks from wheel
├── <pkg>/
│   ├── main.py                      # builds QApplication, opens MainWindow
│   ├── config.json                  # all user-visible strings + tunables
│   ├── core/                        # pure Python — NO Qt, NO hardware
│   │   ├── models.py                # dataclasses (state, readings, settings, Frame, exports)
│   │   ├── services.py              # business logic / state transitions
│   │   ├── exceptions.py            # custom error hierarchy
│   │   ├── utils.py                 # math (circular mean, statistics)
│   │   └── formatting.py            # display helpers
│   ├── infrastructure/              # adapters — Qt only in qt_threads.py
│   │   ├── config.py                # JSON loader
│   │   ├── logging.py               # Debug singleton
│   │   ├── device_manager.py        # connect/disconnect, reconnect, desired-state
│   │   ├── qt_threads.py            # all QThread workers (ONLY Qt file in this layer)
│   │   ├── serial_device.py         # low-level serial helpers
│   │   ├── session_journal.py       # crash-safe append-only CSV
│   │   ├── save_service.py          # CSV + metadata writer
│   │   ├── devices/                 # real device adapters
│   │   ├── mocks/                   # protocol-level mocks (excluded from wheel)
│   │   └── modules/                 # HostModule adapters + ModuleRegistry
│   ├── pyqt/                        # Qt Designer .ui sources + generated ui_*.py
│   └── ui/
│       ├── controllers/             # DataController etc. — signals to widgets
│       ├── windows/                 # MainWindow, dialogs, debug window
│       ├── widgets/                 # ConnectionBanner, EventLogPanel, pyqtgraph plots
│       │   ├── plot_tab_base.py     # PlotTabBase + ConnState enum
│       │   ├── tab_registry.py      # TabRegistry singleton
│       │   └── tabs/                # one file per experiment tab
│       ├── dialogs/                 # settings dialogs (UI-only logic)
│       └── common/                  # statusbar, status_led, dialogs helpers
└── tests/
    ├── core/                        # pure unit tests
    ├── infrastructure/              # against mocks
    └── ui/                          # with pytest-qt + QTest
```

---

## 16. Quick checklist when reviewing a PR in this style

- [ ] No `core/` import of Qt, PySide6, `serial`, or vendor SDKs.
- [ ] No `infrastructure/` Qt import outside `qt_threads.py`.
- [ ] No `ui/` widget constructed in Python where a `.ui` could host it.
- [ ] Every new signal carries primitives or a frozen dataclass.
- [ ] Every new worker has an `abort()` flag and a `failed` signal.
- [ ] Every new poll loop pauses during synchronous device commands.
- [ ] Every new error path either silently retries (first failure), updates
      the status bar (recoverable), or shows a modal (terminal/question).
- [ ] Every new tab subclasses `PlotTabBase`, declares `tab_id` and
      `tab_title`, and registers in `tabs/__init__.py`.
- [ ] Every new tunable lives in `config.json`, not hardcoded.
- [ ] Tests exist next to the change: `core/` → unit, `infrastructure/` →
      against mock, `ui/` → `QTest`.

---

## 17. One-line summary

> A PyQt hardware UI is maintainable when the **physics is pure**, the
> **drivers are mockable**, the **widgets come from Designer**, the
> **threading is concentrated**, the **state machine has one owner**, and
> **every experiment is a tab the main window doesn't know about**.
