#!/usr/bin/env python3
"""Test Signal-Slot connections in DeviceManager."""

import sys
from PySide6.QtCore import QCoreApplication
from gmcounter.device_manager import DeviceManager


def test_signals():
    """Test that DeviceManager signals are properly defined and can be connected."""
    app = QCoreApplication(sys.argv)

    manager = DeviceManager()

    # Test signal attributes exist
    assert hasattr(manager, "status_update"), "status_update signal missing"
    assert hasattr(manager, "data_received"), "data_received signal missing"
    assert hasattr(
        manager, "device_info_received"
    ), "device_info_received signal missing"

    # Test signal connections
    received_status = []
    received_data = []
    received_info = []

    def status_slot(msg, color):
        received_status.append((msg, color))

    def data_slot(index, value):
        received_data.append((index, value))

    def info_slot(info):
        received_info.append(info)

    manager.status_update.connect(status_slot)
    manager.data_received.connect(data_slot)
    manager.device_info_received.connect(info_slot)

    # Emit test signals
    manager.status_update.emit("Test message", "green")
    manager.data_received.emit(1, 42.5)
    manager.device_info_received.emit({"version": "1.0"})

    # Process events
    app.processEvents()

    # Verify signals were received
    assert len(received_status) == 1, "status_update signal not received"
    assert received_status[0] == (
        "Test message",
        "green",
    ), "status_update data incorrect"

    assert len(received_data) == 1, "data_received signal not received"
    assert received_data[0] == (1, 42.5), "data_received data incorrect"

    assert len(received_info) == 1, "device_info_received signal not received"
    assert received_info[0] == {"version": "1.0"}, "device_info_received data incorrect"

    print("✅ Alle Signal-Tests bestanden!")
    return True


if __name__ == "__main__":
    success = test_signals()
    sys.exit(0 if success else 1)
