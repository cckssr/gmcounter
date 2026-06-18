"""Tests for DeviceManager signal definitions — skipped because DeviceManager is now Qt-free.

DeviceManager uses plain Python callbacks (on_status, on_data, on_device_info).
AppController (ui layer) owns the Qt signals and connects them to the UI.
"""

import pytest

pytest.importorskip("PySide6", reason="PySide6 required for Qt signal tests")

pytestmark = pytest.mark.skip(
    reason=(
        "DeviceManager no longer has Qt signals (status_update, data_received, "
        "device_info_received). It uses plain callbacks set by AppController."
    )
)

import sys
from PySide6.QtCore import QCoreApplication
from gmcounter.infrastructure.device_manager import DeviceManager
