# Layer: ui/tabs — DistanceLawTab: measures count/rate vs. sample distance.
"""Distance-law (1/r²) parameter-sweep experiment tab."""
#
# All behaviour is inherited from ParameterSweepTabBase.
# All static layout (spinbox, plot container, table, status label) lives in
# mainwindow.ui — injected by MainWindow via inject_ui() before build().
#
# To add a "Spannungskurve" tab in the future:
#   1. Add a new QWidget page to mainwindow.ui with the same widget pattern
#      (paramInput QDoubleSpinBox, paramPlot QWidget native, paramTable
#       QTableView, paramStatus QLabel).
#   2. Subclass ParameterSweepTabBase, set the class attributes below.
#      Do NOT call TabRegistry.register() — sweep tabs are explicitly wired.
#   3. Wire inject_ui() + build() in MainWindow.__init__.

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from .parameter_sweep_base import ParameterSweepTabBase


class DistanceLawTab(ParameterSweepTabBase):
    """Abstandsgesetz — GM count rate as a function of sample distance."""

    tab_id = "distance_law"
    tab_title = "Abstandsgesetz"
    required_modules: set[str] = set()

    param_label = "Probenabstand (cm)"
    param_unit = "cm"
    param_metadata_key = "sample_distance_cm"
    summary_filename_hint = "abstandsgesetz"
    summary_title = "Abstandsgesetz — Zusammenfassung"
    clear_param_input_after_stop = True

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
