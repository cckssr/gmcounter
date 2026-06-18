"""Tests for GUI signal connections — skipped because DeviceManager is now Qt-free.

DeviceManager uses plain Python callbacks instead of Qt signals.
AppController (ui layer) owns the signals and translates them for the UI.
"""

import pytest

pytest.importorskip("PySide6", reason="PySide6 required for Qt signal tests")

pytestmark = pytest.mark.skip(
    reason=(
        "DeviceManager no longer has Qt signals (data_received, status_update, etc.). "
        "It uses plain callbacks; AppController owns the Qt signals."
    )
)

import sys
from PySide6.QtWidgets import QApplication
from gmcounter.infrastructure.device_manager import DeviceManager
