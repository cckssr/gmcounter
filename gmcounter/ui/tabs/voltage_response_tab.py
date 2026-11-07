# Layer: ui/tabs — VoltageResponseTab: measures count/rate vs. GM tube voltage.
#
# All behaviour is inherited from ParameterSweepTabBase. The voltage is not entered here: it
# is taken from the live read-back of the device (context.voltage_readback), and the entered
# device settings are applied by the session controller on each Start.

from __future__ import annotations

from .parameter_sweep_base import ParameterSweepTabBase
from .registry import TabRegistry


@TabRegistry.register
class VoltageResponseTab(ParameterSweepTabBase):
    """Spannungskurve — GM count rate as a function of tube voltage."""

    tab_id = "voltage_response"
    order = 20
    instance = "voltage"

    param_unit = "V"
    param_metadata_key = "gm_voltage_v"
    summary_filename_hint = "spannungskurve"

    # Voltage is an integer; show with zero decimal places in the table
    param_format = "{:.0f}"
    uses_param_input = False
    applies_device_voltage_on_start = True
