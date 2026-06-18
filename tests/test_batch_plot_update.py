"""Tests for the old PlotWidget.update_plot_batch() API — skipped because PlotWidget
was replaced by GeneralPlot which uses update_plot_data() / set_summary_points().
"""

import pytest

pytest.importorskip(
    "pyqtgraph", reason="pyqtgraph + Qt required for plot tests", exc_type=ImportError
)

pytestmark = pytest.mark.skip(
    reason=(
        "PlotWidget.update_plot_batch() was replaced by GeneralPlot.update_plot_data(). "
        "Rewrite tests against the GeneralPlot API and run with QT_QPA_PLATFORM=offscreen."
    )
)

import sys
import time
import numpy as np
from PySide6.QtWidgets import QApplication
from gmcounter.ui.widgets.plot import GeneralPlot
from gmcounter.ui.controllers.data_controller import DataController
