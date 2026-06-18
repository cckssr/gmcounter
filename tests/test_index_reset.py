#!/usr/bin/env python3
"""Test that the acquisition index resets correctly between measurements."""

import pytest
import sys
import os

pytest.importorskip(
    "PySide6", reason="DataAcquisitionThread requires PySide6 / QThread"
)

from unittest.mock import Mock
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
