# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
"""GMCounter exception hierarchy.

All application exceptions inherit from :exc:`GMCounterError` so callers
can catch the whole family with a single ``except GMCounterError`` clause.
"""


class GMCounterError(Exception):
    """Base exception for all GMCounter errors."""


class DeviceError(GMCounterError):
    """Raised when a hardware operation fails."""


class ConnectionError(GMCounterError):  # noqa: A001
    """Raised when the device cannot be reached."""


class ProtocolError(GMCounterError):
    """Raised when the binary protocol is violated."""


class ConfigurationError(GMCounterError):
    """Raised for invalid configuration values."""


class SaveError(GMCounterError):
    """Raised when saving data to disk fails."""
