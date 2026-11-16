"""DeviceManager.stop_measurement: ABOR is repeated until the stream is silent."""

from __future__ import annotations

import pytest

from gmcounter.infrastructure.device_manager import DeviceManager


class FakeSerial:
    """Reports ``waiting`` bytes per check; ``reset_input_buffer`` does not clear a live stream."""

    is_open = True

    def __init__(self, waiting_per_check) -> None:
        self.waiting_per_check = list(waiting_per_check)
        self.in_waiting = 0
        self.resets = 0

    def reset_input_buffer(self) -> None:
        self.resets += 1
        self.in_waiting = self.waiting_per_check.pop(0) if self.waiting_per_check else 0


class FakeDevice:
    def __init__(self, waiting_per_check) -> None:
        self.serial = FakeSerial(waiting_per_check)
        self.commands: list[str] = []

    def set_counting(self, value: bool) -> bool:
        self.commands.append("INIT" if value else "ABOR")
        return True

    def clear_register(self) -> bool:
        self.commands.append("SYST:CLR")
        return True


@pytest.fixture
def manager(monkeypatch):
    for name in (
        "STOP_SEQUENCE_DELAY_S",
        "CLEAR_REGISTER_DELAY_S",
        "STOP_QUIET_CHECK_S",
    ):
        monkeypatch.setattr(DeviceManager, name, 0.0)
    manager = DeviceManager()
    manager.connected = True
    return manager


def _stop(manager, waiting_per_check):
    manager.device = FakeDevice(waiting_per_check)
    result = manager.stop_measurement()
    return result, manager.device.commands.count("ABOR")


def test_a_silent_line_confirms_the_stop_after_one_abor(manager):
    assert _stop(manager, [0]) == (True, 1)


def test_abor_is_repeated_while_the_device_keeps_streaming(manager):
    assert _stop(manager, [120, 40, 0]) == (True, 3)


def test_a_device_that_never_stops_is_reported_as_unconfirmed(manager):
    assert _stop(manager, [120, 120, 120, 120]) == (False, DeviceManager.STOP_ATTEMPTS)


def test_stopping_without_a_device_is_not_confirmed(manager):
    manager.device = None
    assert manager.stop_measurement() is False
