"""Sample, group, detector, distance and automatic-save settings."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QWidget

from gmcounter.infrastructure.config import AppConfig
from gmcounter.pyqt.ui_sample_panel import Ui_SamplePanel
from gmcounter.ui.i18n import apply_strings
from gmcounter.ui.panels import fill_combo, set_contains_completer


class SamplePanel(QGroupBox):
    """Metadata that ends up in the saved file names and headers."""

    auto_save_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_SamplePanel()
        self.ui.setupUi(self)
        # The toggled signal only fires on a change, so set the initial visibility here.
        self._set_suffix_visible(self.ui.checkAutoSave.isChecked())
        self.ui.checkAutoSave.toggled.connect(self._on_auto_save_toggled)

    def apply_config(self, config: AppConfig) -> None:
        """Apply the German strings, group items and sample / detector completers."""
        strings = config.section("ui").get("sample_panel", {})
        apply_strings(self, strings)
        fill_combo(
            self.ui.comboGroup, strings.get("combo_group_items", []), keep_empty=True
        )
        for combo, key in (
            (self.ui.comboSample, "radioactive_samples"),
            (self.ui.comboDetector, "detektor_codes"),
        ):
            items = config.get(key, [])
            fill_combo(combo, items, keep_empty=True)
            set_contains_completer(combo, items)

    def metadata(self) -> dict:
        """Entered metadata: ``sample``, ``group``, ``detector``, ``distance_cm``, ``suffix``."""
        return {
            "sample": self.ui.comboSample.currentText(),
            "group": self.ui.comboGroup.currentText(),
            "detector": self.ui.comboDetector.currentText().strip(),
            "distance_cm": float(self.ui.spinDistance.value()),
            "suffix": self.ui.editSuffix.text().strip(),
        }

    def auto_save(self) -> bool:
        """Whether finished measurements are saved automatically."""
        return self.ui.checkAutoSave.isChecked()

    def set_distance_visible(self, visible: bool) -> None:
        """Show or hide the distance row; hiding resets it to 0 (the sweep tab sets it itself)."""
        self.ui.labelDistance.setVisible(visible)
        self.ui.spinDistance.setVisible(visible)
        if not visible:
            self.ui.spinDistance.setValue(0.0)

    def _on_auto_save_toggled(self, checked: bool) -> None:
        self._set_suffix_visible(checked)
        self.auto_save_toggled.emit(checked)

    def _set_suffix_visible(self, visible: bool) -> None:
        self.ui.labelSuffix.setVisible(visible)
        self.ui.editSuffix.setVisible(visible)
