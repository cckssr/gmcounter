# Design Principles

This document captures the portable design principles used across PySide6 GUI
projects and Arduino/PlatformIO firmware that communicate over serial. Each rule
is stated generically — no project-specific class names — so it can be copied or
referenced in other codebases.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how these principles are applied
concretely in GMCounter.

---

## PySide6 / Qt

### P1 — Three-layer separation

**Rule:** Organise the code into exactly three layers with a strict one-way
dependency graph:

```ascii
UI  →  Infrastructure  →  Core
│                           ↑
└───────────────────────────┘
```

- `core/` — pure domain: dataclasses, algorithms, maths, protocol logic.
  Zero imports of Qt, serial drivers, or file I/O.
- `infrastructure/` — adapters: device drivers, file writers, configuration,
  logging. No Qt except in one dedicated threading file (see P4).
- `ui/` — PySide6 windows, widgets, tabs, dialogs. No domain logic.

**Why:** `core/` is testable without Qt or hardware — tests run in milliseconds
and never open a display. Hardware can be mocked at the adapter boundary.
Infrastructure stays import-clean so every module except the threading file
is unit-testable without a running `QApplication`.

**How to apply:** Before adding code, decide which layer it belongs to. If it
needs Qt, put it in `ui/` (or the Qt-threading file). If it could run in a
CLI script, put it in `core/` or `infrastructure/`. Enforce with a pre-commit
grep check.

---

### P2 — Qt Designer is the source of visual truth

**Rule:** Every static widget (button, label, spinbox, group box, table view,
plot container) lives in a `.ui` file. Python files only: connect signals to
slots, attach data models to views, inject third-party widgets into empty
`QWidget` containers.

**Why:** The visual structure is auditable in Qt Designer without reading Python.
Layout bugs are caught without running the app. The Python layer stays small
and focused on behaviour.

**How to apply:** When adding a new control, add it to the `.ui` file first.
Only create widgets in Python for:

- Third-party plot libraries (pyqtgraph, matplotlib) that Designer cannot host.
- `QStandardItemModel` attached to a `.ui` `QTableView` — non-visual logic.
- Runtime-dynamic rows/items appended to existing models.

After any `.ui` edit, regenerate the Python binding with `pyside6-uic`.
Commit the generated file alongside the `.ui` source.

---

### P3 — Single controller, signal-based fan-out

**Rule:** One `QObject` subclass ("the controller") owns the device lifecycle,
all `QTimer` instances, the acquisition thread, and the reconnect FSM. Windows
subscribe to its signals; they never talk to the device directly.

**Why:** Prevents multiple owners for the same resource. Connection state,
measurement state, and reconnect policy live in one place, making them easier
to test and reason about.

**How to apply:** The controller exposes signals (`measurement_started`,
`frames_ready`, `connection_lost`, …). Windows and tabs subscribe; they never
hold a reference to the device. The controller exposes a `cleanup()` method
called from `closeEvent` to stop timers and join threads.

---

### P4 — Threading discipline: workers emit, never touch widgets

**Rule:**

1. All `QThread` subclasses live in a single file (`infrastructure/qt_threads.py`
   or equivalent) — the **only** place in the infrastructure layer that may import Qt.
2. Workers read from hardware or do blocking I/O. When done, they `emit()` a
   signal. They never call methods on a widget or a controller directly.
3. All cross-thread signal connections use `Qt.ConnectionType.QueuedConnection`
   (auto-connection between objects on different threads achieves this by default).

**Why:** Every "widget accessed from wrong thread" crash traces back to a thread
that called a widget method directly. Queued signals make cross-thread calls safe
and auditable — the signal payload crosses the thread boundary, not a reference
to a mutable object.

**How to apply:** Extract blocking I/O into a `QThread.run()` method. Emit a
signal with a primitive payload (int, float, string, frozen dataclass). The
controller slot on the main thread does the UI update.

---

### P5 — Mocks as implementations, not test fixtures

**Rule:** A mock device is a full implementation of the same adapter interface,
not a `unittest.mock.MagicMock`. Place it next to the real driver in
`infrastructure/`, not in `tests/`. Exclude it from the distribution wheel.

**Why:** Mocking at the adapter boundary means the acquisition thread, packet
parser, and reconnect logic run **unchanged** against the mock. The mock is a
PTY-based (or equivalent) stub that speaks the real wire protocol — tests get
faithful coverage of the infrastructure layer without physical hardware.

**How to apply:**

- Real driver: `infrastructure/devices/my_device.py`
- Mock driver: `infrastructure/mocks/mock_my_device.py`
- Both satisfy the same interface (Python structural subtyping / Protocol).
- Exclude the mocks package from `pyproject.toml` wheel discovery:

  ```toml
  [tool.setuptools.packages.find]
  exclude = ["mypackage.infrastructure.mocks", "mypackage.infrastructure.mocks.*"]
  ```

---

### P6 — Config-driven, no magic numbersÍ

**Rule:** Every tuneable constant (timer intervals, retry caps, voltage limits,
plot bounds) lives in a config file, not hardcoded. Code reads it at module level
with a sensible default fallback.

**Why:** Changing a timing parameter should not require code edits and a release.
The config file documents the tuneable knobs in one place.

**How to apply:**

```python
CONFIG = import_config()  # cache at module level
TIMER_INTERVAL_MS = CONFIG.get("timers", {}).get("gui_update_ms", 200)
```

All user-visible strings also belong in config (under a language key) to
simplify future i18n.

---

### P7 — Status bar for transients, modal for terminal failures

**Rule:** Recoverable status (connection attempt, measurement running, settings
applied) goes to the status bar and/or a scrollback event-log panel.
`QMessageBox` is reserved for terminal failures ("save failed", "connection lost
after N retries") and user decisions ("discard unsaved data?").

**Why:** Modals block the UI and force the user to dismiss them before anything
else can happen. For recoverable transients this is user-hostile. The event log
provides a persistent in-session audit trail without any interruption.

---

## Firmware (PlatformIO / Arduino)

### F1 — PlatformIO multi-environment builds

**Rule:** One `platformio.ini` with a base environment (`env:device_name`) plus
per-device-serial environments that `extend` it and set `DEVICE_SERIAL` as a
compile-time define.

```ini
[env:device_base]
platform = renesas-ra
board    = uno_r4_minima
framework = arduino
build_flags = '-DFW_VERSION="1.0.0"'

[env:device_E20134]
extends  = env:device_base
build_flags =
    ${env:device_base.build_flags}
    '-DDEVICE_SERIAL="E20134"'
```

**Why:** Baking the serial number at build time avoids reading it from EEPROM
at runtime (slower, more error-prone). Different devices get their own named
firmware binary. CI can build all envs in a matrix.

**How to apply:** Add a `native` env for host-side unit tests that does not
require hardware:

```ini
[env:native]
platform = native
build_flags = -std=c++17 -I test -I src '-DDEVICE_SERIAL="TEST"'
test_build_src = no
```

---

### F2 — SCPI as the host ↔ firmware command contract

**Rule:** Use SCPI (IEEE 488.2) syntax for all host-to-firmware and
firmware-to-host text commands.

Short forms (`CONF:VOLT 500`) and long forms (`CONFIGURE:VOLTAGE 500`) both
parse to the same handler. Query form adds `?` (`CONF:VOLT?`).

**Why:** SCPI is a well-understood instrument control standard. The command
namespace is structured and extensible. Third-party tools (e.g. a serial
terminal, Python VISA, or a test script) can talk to the device without knowing
the application protocol.

**How to apply:**

- Parse the raw line into `(header, param, isQuery)` before dispatching.
- Handle `*IDN?`, `*RST`, `*CLS` at minimum (IEEE 488.2 mandatory commands).
- Maintain an error queue (`SYST:ERR?`) so the host can retrieve error strings
  without adding protocol overhead to the hot data path.
- Implement `HELP?` to self-document the command set.

**Protocol layering:** The SCPI layer runs on `Serial` (USB CDC, host-facing).
A secondary bus (`Serial1`, UART) drives the downstream detector hardware using
a simpler single-character command set. Keep the two layers separate — the
firmware translates between them.

---

### F3 — Native unit tests with Unity

**Rule:** Test SCPI parsing, dispatch, error-queue, and core state logic using
the [Unity](https://www.throwtheswitch.org/unity) framework in a `native` PlatformIO
environment. Tests compile and run on the host without any microcontroller.

**Why:** Running tests on the host is fast (no flash/reset cycle), deterministic,
and CI-friendly. Logic errors in the command parser or state machine are caught
before the firmware ever touches hardware.

**How to apply:**

- `firmware/test/` one directory per test suite; each includes exactly the
  `.cpp` files it needs.
- Provide an `Arduino.h` shim (`firmware/test/Arduino.h` → `arduino_mock.h`)
  that stubs `Serial`, `String`, `millis()`, `delay()`, etc.
- Run: `pio test -e native`

---

### F4 — No blocking in the main loop

**Rule:** The Arduino `loop()` function must return quickly. Never use `delay()`
or a busy-wait loop in the main loop body. Use non-blocking patterns (timer
comparisons with `millis()` / `micros()`, interrupt service routines, event
flags) instead.

**Why:** A blocked main loop drops incoming serial bytes, misses interrupt
events, and causes timing jitter that corrupts inter-event measurements. At
1 Mbaud a 1 ms block can lose ~125 bytes.

**How to apply:**

- For pulse timing: use a hardware timer interrupt or a cycle-counter ISR
  (`DWT->CYCCNT` on Cortex-M). Store the delta and return immediately.
- For SCPI: read one character at a time into a line buffer; dispatch only when
  `\n` is received.
- For state machines: use an enum + `switch`; advance one transition per loop
  iteration.
