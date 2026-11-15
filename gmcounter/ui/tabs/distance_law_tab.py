# Layer: ui/tabs — DistanceLawTab: measures count/rate vs. sample distance.
#
# All behaviour is inherited from ParameterSweepTabBase; the texts come from the
# ``text_*_distance`` keys of ``ui.sweep_tab`` in config.json.

from __future__ import annotations

from .parameter_sweep_base import ParameterSweepTabBase
from .registry import TabRegistry


@TabRegistry.register
class DistanceLawTab(ParameterSweepTabBase):
    """Abstandsgesetz — GM count rate as a function of sample distance."""

    tab_id = "distance_law"
    order = 10
    instance = "distance"
    hides_global_distance = True  # the tab has its own distance input

    param_unit = "cm"
    param_metadata_key = "sample_distance_cm"
    summary_filename_hint = "abstandsgesetz"
    clear_param_input_after_stop = True
