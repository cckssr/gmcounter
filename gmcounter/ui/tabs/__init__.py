# Layer: ui/tabs — PlotTabBase contract, TabRegistry, experiment implementations.
# May import: infrastructure/, core/, PySide6.
# Experiment specifics live here — MainWindow must NOT grow per-experiment branches.
# Importing the modules registers the tabs (``@TabRegistry.register``).

from . import (  # noqa: F401  (imported for their registration side effect)
    distance_law_tab,
    gm_timing_tab,
    interval_repeat_tab,
    voltage_response_tab,
)
