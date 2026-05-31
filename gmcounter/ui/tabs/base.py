# Layer: ui/tabs — PlotTabBase contract (§6).
# Experiment specifics live in subclasses — MainWindow must NOT branch per experiment.

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from ...core.export import TabExport
from ...core.models import Frame


class PlotTabBase(QWidget):
    """Contract for experiment tabs (§6).

    Class attributes
    ────────────────
    tab_id            Stable key used in tests and persistence.
    tab_title         User-visible label for the first contributed tab.
    required_sources  Data streams required (reserved for future use).
    required_modules  ModuleRegistry IDs required for this tab to be visible.

    Outbound signals (uniform across all tabs)
    ──────────────────────────────────────────
    status_message(str, str)       ("info"|"warning"|"error", text)
    filename_hint_changed()
    request_module_action(str, dict)

    Lifecycle hooks (override only what you need)
    ─────────────────────────────────────────────
    build()                         Called once after the tab is added.
    on_frame(frame)                 Called for each acquired data point.
    on_reset()                      Before a new measurement starts.
    on_connection_state(state)
    on_activated() / on_deactivated()
    on_measurement_started() / on_measurement_stopped()
    inject_modules(modules)         Called when ModuleRegistry changes.
    export() -> TabExport           Returns current data for the save service.
    get_statistics() -> dict        Returns {count, min, max, avg, stdev} for AppController.

    contribute_tabs(tab_widget)
    ───────────────────────────
    Called by MainWindow to let the experiment add its view tab(s) to the
    shared QTabWidget.  The default implementation adds one tab (self) with
    tab_title.  Override when contributing multiple views (e.g. GMTimingTab).
    """

    tab_id: str = ""
    tab_title: str = "Experiment"
    required_sources: set[str] = set()
    required_modules: set[str] = set()

    # Outbound signals
    status_message = Signal(str, str)
    filename_hint_changed = Signal()
    request_module_action = Signal(str, dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

    # ------------------------------------------------------------------
    # Lifecycle hooks — override as needed

    def build(self) -> None:
        """One-time setup after the tab is inserted into the window."""

    def on_frame(self, frame: Frame) -> None:
        """Process one acquired data point."""

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
        """Return a TabExport for the generic save service.

        Return None if there is no data to export.
        """
        return None

    def get_statistics(self) -> dict:
        """Return {count, min, max, avg, stdev} for the AppController stats timer."""
        return {}

    # ------------------------------------------------------------------
    # Tab contribution

    def contribute_tabs(self, tab_widget) -> None:
        """Add this experiment's view tab(s) to *tab_widget* (QTabWidget).

        Default: add *self* as a single tab labelled tab_title.
        Override in GMTimingTab to add 3 top-level views.
        """
        from PySide6.QtWidgets import QTabWidget  # local import avoids circular

        if isinstance(tab_widget, QTabWidget):
            tab_widget.addTab(self, self.tab_title)
