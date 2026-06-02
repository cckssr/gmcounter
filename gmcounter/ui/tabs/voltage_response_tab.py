# Layer: ui/tabs — VoltageResponseTab: measures count/rate vs. GM tube voltage.
#
# All behaviour is inherited from ParameterSweepTabBase.
# All static layout (plot container, table, status label) lives in
# mainwindow.ui — injected by MainWindow via inject_ui() before build().
# The voltage parameter is NOT entered here; it is sourced from the device-
# control panel (cVoltage LCD — live device-reported value), and the setpoint
# is applied automatically by MainWindow on each Start press.
#
# Do NOT call TabRegistry.register() — sweep tabs are explicitly wired in
# MainWindow (not auto-discovered via the registry).

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from .parameter_sweep_base import ParameterSweepTabBase


class VoltageResponseTab(ParameterSweepTabBase):
    """Spannungskurve — GM count rate as a function of tube voltage."""

    tab_id = "voltage_response"
    tab_title = "Spannungskurve"
    required_modules: set[str] = set()

    param_label = "Spannung (V)"
    param_unit = "V"
    param_metadata_key = "gm_voltage_v"
    summary_filename_hint = "spannungskurve"
    summary_title = "Spannungskurve — Zusammenfassung"

    # Voltage is an integer; show with zero decimal places in the table
    param_format = "{:.0f}"
    # MainWindow applies the sVoltage setpoint to the device before each Start
    applies_device_voltage_on_start = True

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
