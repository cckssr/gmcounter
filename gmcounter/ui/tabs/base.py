# Layer: ui/tabs — PlotTabBase contract (§6).
# Experiment specifics live in subclasses — MainWindow must NOT branch per experiment.

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Signal  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from ...core.export import TabExport
from ...core.models import Frame
from .tab_title import TabTitle

if TYPE_CHECKING:
    from ..context import AppContext


class PlotTabBase(QWidget):
    """Contract for experiment tabs (§6).

    A tab is a QWidget with its own Designer form, built as ``Tab(context, parent=None)``.

    Class attributes
    ────────────────
    tab_id            Stable key (config ``ui.tabs.<tab_id>``, profiles, tests).
    title             User-visible label, resolved from the configuration (TabTitle).
    order             Position among the tabs (ascending).
    session_kind      "single" | "sweep" | "interval": how the session controller runs the
                      shared Start / Stop / Save / Reset buttons while this tab is selected.
    receives_frames   True if the tab consumes the acquired frames itself while selected
                      (otherwise the timing tab receives them).
    provides_timing   True for the tab that acquires the timing data (context.timing).
    form_name         Section of the tab's form below ``ui`` in config.json.
    hides_global_distance  True if the tab has its own distance input, so the sample panel's
                      distance row is hidden and reset while the tab is selected.
    required_modules  ModuleRegistry IDs required for this tab to be visible.

    Outbound signals (uniform across all tabs)
    ──────────────────────────────────────────
    status_message(str, str)       ("info"|"warning"|"error", text)
    filename_hint_changed()
    request_module_action(str, dict)

    Lifecycle hooks (override only what you need)
    ─────────────────────────────────────────────
    build()                         Called once after the tab is created.
    on_frame(frame) / on_frames(frames)
    on_reset()                      Before a new measurement starts.
    on_measurement_started() / on_measurement_stopped()
    export() -> TabExport           Returns current data for the save service.
    get_statistics() -> dict        Returns {count, min, max, avg, stdev} for AppController.

    Session hooks (tabs with ``session_kind`` "sweep" or "interval")
    ────────────────────────────────────────────────────────────────
    has_data(), has_unsaved_data(), mark_saved(), summary_export(), session_exports(),
    session_file_name(export, index), reset_session().
    """

    tab_id: str = ""
    title = TabTitle()
    order: int = 100
    session_kind: str = "single"
    receives_frames: bool = False
    hides_global_distance: bool = False
    provides_timing: bool = False
    form_name: str = ""  # section of the tab's form below ``ui`` in config.json
    required_sources: set[str] = set()
    required_modules: set[str] = set()

    # Outbound signals
    status_message = Signal(str, str)
    filename_hint_changed = Signal()
    request_module_action = Signal(str, dict)

    def __init__(self, context: "AppContext", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.context = context
        self.config = context.config

    def text(self, key: str, **fmt) -> str:
        """Configured string ``ui.<form_name>.<key>`` (underscore keys of the tab's form)."""
        return self.config.text(f"{self.form_name}.{key}", **fmt)

    # ------------------------------------------------------------------
    # Lifecycle hooks — override as needed

    def build(self) -> None:
        """One-time setup after construction (plot labels, headers, timers)."""

    def on_frame(self, frame: Frame) -> None:
        """Process one acquired data point."""

    def on_frames(self, frames: "list[Frame]") -> None:
        """Process a batch of acquired data points.

        Default implementation forwards each frame to :meth:`on_frame`.  Tabs on
        a high-rate stream should override this to handle the whole batch at once.
        """
        for frame in frames:
            self.on_frame(frame)

    def on_reset(self) -> None:
        """Clear data before a new measurement."""

    def on_connection_state(self, state: str) -> None:
        """React to connection state changes ('connected'/'disconnected'/'reconnecting')."""

    def on_activated(self) -> None:
        """Called when this tab becomes the active (visible) tab."""

    def on_deactivated(self) -> None:
        """Called when the user navigates away from this tab."""

    def on_measurement_started(self) -> None:
        """Called when a new measurement begins."""

    def on_measurement_stopped(self) -> None:
        """Called when a measurement ends."""

    def inject_modules(self, modules: dict[str, object]) -> None:
        """Receive updated ModuleRegistry snapshot."""

    # ------------------------------------------------------------------
    # Data export (§7)

    def export(self) -> Optional[TabExport]:
        """Return a TabExport for the generic save service, or None without data."""
        return None

    def get_statistics(self) -> dict:
        """Return {count, min, max, avg, stdev} for the AppController stats timer."""
        return {}

    # ------------------------------------------------------------------
    # Session hooks (sweep / interval tabs)

    def has_data(self) -> bool:
        return False

    def has_unsaved_data(self) -> bool:
        return False

    def mark_saved(self) -> None:
        """The session data has been written to disk."""

    def summary_export(self) -> Optional[TabExport]:
        """Summary table of the session (one row per measurement point / interval)."""
        return None

    def session_exports(self) -> list[TabExport]:
        """Detail exports written next to the summary (one file each)."""
        return []

    def session_file_name(self, export: TabExport, index: int) -> str:
        """Suffix (without extension) appended to the summary file stem for ``export``."""
        return f"{export.filename_hint}"

    def reset_session(self) -> None:
        """Discard the session data."""
