"""Tests for the old PlotWidget API — skipped because PlotWidget was replaced by GeneralPlot.

To write new plot tests, use GeneralPlot / PlotConfig from gmcounter.ui.widgets.plot.
Run with QT_QPA_PLATFORM=offscreen.
"""

import pytest

pytest.importorskip(
    "pyqtgraph", reason="pyqtgraph + Qt required for plot tests", exc_type=ImportError
)

pytestmark = pytest.mark.skip(
    reason="PlotWidget class was replaced by GeneralPlot — these tests need a full rewrite"
)

import numpy as np
from gmcounter.ui.widgets.plot import GeneralPlot, PlotConfig
