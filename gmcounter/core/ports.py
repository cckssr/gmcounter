# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
#
# Logger Protocol: lets core services log without importing infrastructure.logging.
# The infrastructure Debug singleton satisfies this protocol at runtime.
"""Structural ports (Protocols) used by the core layer.

Keeping these here lets ``core/`` accept logger and other collaborator types
without importing anything from ``infrastructure/``.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Logger(Protocol):
    """Structural interface for a logger — satisfied by infrastructure.Debug."""

    @classmethod
    def error(cls, message: str, exc_info=None) -> None:  # noqa: E704
        """Log an error message, optionally with exception info."""
        ...

    @classmethod
    def info(cls, message: str) -> None:  # noqa: E704
        """Log an informational message."""
        ...

    @classmethod
    def debug(cls, message: str) -> None:  # noqa: E704
        """Log a debug-level message."""
        ...

    @classmethod
    def warning(cls, message: str) -> None:  # noqa: E704
        """Log a warning message."""
        ...
