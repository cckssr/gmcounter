"""Tests for core/models.py — no Qt required."""

from datetime import datetime
from gmcounter.core.models import (
    MeasurementPoint,
    MeasurementSession,
    DeviceSettings,
    DeviceInfo,
    Frame,
    DesiredState,
)


def test_measurement_session_count():
    session = MeasurementSession()
    session.points.append(MeasurementPoint(1, 100.0, "12:00:00"))
    assert session.count == 1


def test_measurement_session_duration():
    session = MeasurementSession(
        start_time=datetime(2024, 1, 1, 12, 0, 0),
        end_time=datetime(2024, 1, 1, 12, 0, 5),
    )
    assert session.duration_seconds == 5.0


def test_device_settings_to_dict():
    s = DeviceSettings(repeat=True, voltage=600)
    d = s.to_dict()
    assert d["repeat"] is True
    assert d["voltage"] == 600


def test_frame_is_frozen():
    f = Frame(index=1, value=42.5, timestamp="12:00:00")
    try:
        f.index = 2  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass


def test_desired_state_to_device_settings():
    ds = DesiredState(voltage=550, counting_time=2, repeat=True, stream=4)
    settings = ds.to_device_settings()
    assert settings.voltage == 550
    assert settings.repeat is True
    assert settings.auto_query is True


def test_device_info_defaults():
    info = DeviceInfo(port="/dev/ttyUSB0")
    assert not info.connected
    assert info.baudrate == 115200
