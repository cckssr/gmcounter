#!/usr/bin/env python3
"""Test that the acquisition index resets correctly between measurements."""

import pytest
import sys
import os
import time

pytest.importorskip(
    "PySide6", reason="DataAcquisitionThread requires PySide6 / QThread"
)

from unittest.mock import Mock
from PySide6.QtCore import Qt
from gmcounter.infrastructure.qt_threads import DataAcquisitionThread
from gmcounter.infrastructure.device_manager import DeviceManager
from gmcounter.core.services import MeasurementStateService


def test_index_reset():
    """reset_index() clears the parser index back to 0."""
    mock_manager = Mock()
    mock_manager.device = Mock()
    mock_manager.connected = True
    mock_manager.measurement_state = MeasurementStateService()

    thread = DataAcquisitionThread(mock_manager)

    # Simulate that the parser has advanced to index 5 by feeding a start marker
    # followed by five valid packets (ticks=1000).
    start = b"\xff" * 6
    packet = b"\xaa\xe8\x03\x00\x00\x55"
    thread._parser.feed(start + packet * 5)
    assert thread._parser.index == 5, (
        f"Expected index 5 after feeding, got {thread._parser.index}"
    )

    thread.reset_index()

    assert thread._parser.index == 0, (
        f"Index should be 0 after reset_index(), got {thread._parser.index}"
    )
    assert not thread._first_data_received
    assert not thread._parser.synced


if __name__ == "__main__":
    test_index_reset()


# ---- connection loss detection ----------------------------------------------------------
class _Device:
    """Connected device whose reads return nothing and run ``on_read`` first."""

    connected = True

    def __init__(self, on_read=None):
        self._on_read = on_read

    def read_fast(self, max_bytes, timeout_ms):
        if self._on_read:
            self._on_read()
        return b""


def _run_one_cycle(manager, thread):
    """Run the thread loop until the device was read once, collecting connection_lost."""
    lost = []
    thread.connection_lost.connect(
        lambda: lost.append(1), Qt.ConnectionType.DirectConnection
    )
    original = manager.device.read_fast

    def read_once(max_bytes, timeout_ms):
        result = original(max_bytes, timeout_ms)
        thread._running = False  # end the loop after this read
        return result

    manager.device.read_fast = read_once
    thread.run()  # in this thread: no QThread start needed
    return lost


def test_stopping_a_quiet_measurement_is_not_a_lost_connection():
    """Regression: ABOR after a stretch without data must not trigger a reconnect.

    The measurement turns inactive while the thread waits in a read; the empty read that
    follows used to count as "no data for 3 s" and report the link as lost.
    """
    manager = Mock()
    manager.measurement_state = MeasurementStateService()
    manager.measurement_state.start_measurement()
    thread = DataAcquisitionThread(manager)

    def stop_after_a_quiet_stretch():
        thread._last_data_time = time.time() - 10  # the last packet is long ago
        manager.measurement_state.stop_measurement()

    manager.device = _Device(on_read=stop_after_a_quiet_stretch)
    thread._first_data_received = True  # the start marker came long ago
    assert _run_one_cycle(manager, thread) == []


def test_a_silent_running_measurement_is_not_a_lost_connection():
    """A weak source leaves gaps without any packet; that is not a dead link."""
    manager = Mock()
    manager.measurement_state = MeasurementStateService()
    manager.measurement_state.start_measurement()
    manager.device = _Device()
    thread = DataAcquisitionThread(manager)
    thread._first_data_received = True
    assert _run_one_cycle(manager, thread) == []


def test_a_dead_port_is_still_reported_as_lost():
    manager = Mock()
    manager.measurement_state = MeasurementStateService()
    manager.device = _Device()
    manager.device.connected = False  # what read_fast sets after a serial error
    thread = DataAcquisitionThread(manager)

    lost = []
    thread.connection_lost.connect(
        lambda: lost.append(1), Qt.ConnectionType.DirectConnection
    )
    # the loop reports the loss once, then sleeps: end it from the signal
    thread.connection_lost.connect(
        lambda: setattr(thread, "_running", False), Qt.ConnectionType.DirectConnection
    )
    thread.run()
    assert lost == [1]
