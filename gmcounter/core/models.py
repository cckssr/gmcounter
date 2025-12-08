"""Domain models for GMCounter application - NO Qt dependencies."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Tuple


@dataclass
class MeasurementPoint:
    """A single measurement data point."""

    index: int
    value: float  # in microseconds
    timestamp: str


@dataclass
class MeasurementSession:
    """Complete measurement session with metadata."""

    points: List[MeasurementPoint] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    radioactive_sample: str = ""
    subterm: str = ""
    group: str = ""

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def count(self) -> int:
        """Number of data points."""
        return len(self.points)


@dataclass
class DeviceSettings:
    """GM Counter device settings."""

    repeat: bool = False
    auto_query: bool = False
    counting_time: int = 0  # index, 0 = unlimited
    voltage: int = 500

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "repeat": self.repeat,
            "auto_query": self.auto_query,
            "counting_time": self.counting_time,
            "voltage": self.voltage,
        }


@dataclass
class DeviceInfo:
    """Device information and status."""

    port: str
    baudrate: int = 115200
    connected: bool = False
    firmware_version: str = ""
    hardware_version: str = ""
