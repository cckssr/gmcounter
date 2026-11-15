"""Start / stop / save / reset buttons and the progress of the running measurement."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.pyqt.ui_measurement_panel import Ui_MeasurementPanel
from gmcounter.ui.i18n import apply_strings

_SHORTCUTS = {"buttonStart": "F5", "buttonStop": "F6"}


class MeasurementPanel(QGroupBox):
    """Emits intent signals; the owner decides what a click means (single or sweep mode)."""

    start_requested = Signal()
    stop_requested = Signal()
    reset_requested = Signal()
    save_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_MeasurementPanel()
        self.ui.setupUi(self)
        self._elapsed_format = "{elapsed} s"
        self.ui.buttonStart.clicked.connect(self.start_requested)
        self.ui.buttonStop.clicked.connect(self.stop_requested)
        self.ui.buttonReset.clicked.connect(self.reset_requested)
        self.ui.buttonSave.clicked.connect(self.save_requested)
        self._apply_shortcuts()

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings."""
        strings = config.section("ui").get("measurement_panel", {})
        apply_strings(self, strings)
        self._apply_shortcuts()
        self._elapsed_format = strings.get("text_elapsed", self._elapsed_format)

    def set_state(self, start: bool, stop: bool, reset: bool, save: bool) -> None:
        """Enable or disable the four buttons."""
        self.ui.buttonStart.setEnabled(start)
        self.ui.buttonStop.setEnabled(stop)
        self.ui.buttonReset.setEnabled(reset)
        self.ui.buttonSave.setEnabled(save)

    def set_progress(self, elapsed: int, total: int) -> None:
        """Show ``elapsed`` seconds; ``total`` <= 0 means unlimited (busy indicator)."""
        self.ui.valueElapsed.setText(self._elapsed_format.format(elapsed=elapsed))
        if total > 0:
            self.ui.progressMeasurement.setMaximum(total)
            self.ui.progressMeasurement.setValue(min(elapsed, total))
        else:
            self.ui.progressMeasurement.setMaximum(0)

    def clear_progress(self) -> None:
        """Reset the progress bar and the elapsed-time label."""
        self.ui.progressMeasurement.setMaximum(1)
        self.ui.progressMeasurement.setValue(0)
        self.ui.valueElapsed.setText(self._elapsed_format.format(elapsed=0))

    def _apply_shortcuts(self) -> None:
        # QAbstractButton.setText() resets the shortcut, so set it after every text change.
        for name, keys in _SHORTCUTS.items():
            getattr(self.ui, name).setShortcut(keys)
