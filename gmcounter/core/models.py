# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MeasurementPoint:
    """A single measurement data point."""

    index: int
    value: float  # microseconds
    timestamp: str


@dataclass
class MeasurementSession:
    """Complete measurement session with metadata."""

    points: list[MeasurementPoint] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    radioactive_sample: str = ""
    subterm: str = ""
    group: str = ""

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def count(self) -> int:
        return len(self.points)


@dataclass
class DeviceSettings:
    """Current desired settings — the source of truth for what the Arduino should have."""

    repeat: bool = False
    auto_query: bool = False
    counting_time: int = 0  # index: 0=∞, 1=1s, 2=10s, 3=60s, 4=100s, 5=300s
    voltage: int = 500

    def to_dict(self) -> dict:
        return {
            "repeat": self.repeat,
            "auto_query": self.auto_query,
            "counting_time": self.counting_time,
            "voltage": self.voltage,
        }


@dataclass
class DeviceInfo:
    """Device identification and version info."""

    port: str
    baudrate: int = 115200
    connected: bool = False
    firmware_version: str = ""
    hardware_version: str = ""
    openbis_code: str = ""


@dataclass(frozen=True)
class Frame:
    """Immutable bundle passed across thread boundaries via Qt signals.

    Carries a single acquired data point from the acquisition thread to
    the controller (and from there to the active experiment tab).
    """

    index: int
    value: float  # microseconds
    timestamp: str


@dataclass
class DesiredState:
    """Snapshot of device settings used for reconnect replay (§5 B5).

    When the connection drops, AppController saves a DesiredState so it
    can re-apply the exact voltage, counting time, repeat mode and stream
    mode after a successful reconnect — instead of whatever the Arduino
    defaults to.
    """

    voltage: int = 500
    counting_time: int = 0
    repeat: bool = False
    stream: int = 1

    def to_device_settings(self) -> DeviceSettings:
        return DeviceSettings(
            voltage=self.voltage,
            counting_time=self.counting_time,
            repeat=self.repeat,
            auto_query=(self.stream == 4),
        )
