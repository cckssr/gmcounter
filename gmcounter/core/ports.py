# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.
#
# Logger Protocol: lets core services log without importing infrastructure.logging.
# The infrastructure Debug singleton satisfies this protocol at runtime.

from typing import Protocol, runtime_checkable


@runtime_checkable
class Logger(Protocol):
    """Structural interface for a logger — satisfied by infrastructure.Debug."""

    @classmethod
    def error(cls, message: str, exc_info=None) -> None: ...  # noqa: E704

    @classmethod
    def info(cls, message: str) -> None: ...  # noqa: E704

    @classmethod
    def debug(cls, message: str) -> None: ...  # noqa: E704

    @classmethod
    def warning(cls, message: str) -> None: ...  # noqa: E704
