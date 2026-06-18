# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.

import logging
import time
from typing import Callable, Optional

_log = logging.getLogger(__name__)


class ReconnectStrategy:
    """Exponential backoff parameters and attempt tracking.

    Pure value object — no I/O, no threading.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        initial_delay_ms: float = 500,
        max_delay_ms: float = 5000,
        backoff_factor: float = 1.5,
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_factor = backoff_factor
        self.attempt_count = 0

    def reset(self) -> None:
        self.attempt_count = 0
        _log.info("Reconnection attempt counter reset")

    def should_retry(self) -> bool:
        return self.attempt_count < self.max_attempts

    def get_next_delay_ms(self) -> float:
        delay = self.initial_delay_ms * (self.backoff_factor**self.attempt_count)
        delay = min(delay, self.max_delay_ms)
        self.attempt_count += 1
        return delay

    def get_attempt_info(self) -> str:
        return f"Attempt {self.attempt_count}/{self.max_attempts}"


class ConnectionRetryService:
    """Retry a connection function with exponential backoff.

    Runs synchronously — callers that need non-blocking behaviour should
    execute this in a background thread (see infrastructure.qt_threads
    ReconnectWorker).
    """

    def __init__(
        self,
        max_attempts: int = 8,
        initial_delay_ms: float = 500,
        max_delay_ms: float = 16000,
        backoff_factor: float = 2.0,
    ) -> None:
        self.strategy = ReconnectStrategy(
            max_attempts=max_attempts,
            initial_delay_ms=initial_delay_ms,
            max_delay_ms=max_delay_ms,
            backoff_factor=backoff_factor,
        )

    def attempt_reconnect(
        self,
        reconnect_fn: Callable[[], bool],
        status_callback: Optional[Callable[[str, str], None]] = None,
        abort_flag: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Try *reconnect_fn* up to max_attempts times with backoff.

        Args:
            reconnect_fn: Returns True on success.
            status_callback: Called with (message, color) on each attempt.
            abort_flag: Callable returning True when the caller wants to stop.
        """
        self.strategy.reset()

        while self.strategy.should_retry():
            if abort_flag and abort_flag():
                _log.info("Reconnect aborted by caller")
                return False

            delay = self.strategy.get_next_delay_ms()
            info = self.strategy.get_attempt_info()

            if status_callback:
                status_callback(f"Wiederverbindung... {info}", "orange")

            _log.info("Reconnection %s — delay: %.0f ms", info, delay)
            time.sleep(delay / 1000.0)

            try:
                if reconnect_fn():
                    _log.info(
                        "Reconnection successful after %d attempts",
                        self.strategy.attempt_count,
                    )
                    if status_callback:
                        status_callback("Wiederverbunden", "green")
                    return True
            except Exception as exc:
                _log.error("Reconnection %s failed: %s", info, exc)

        _log.error("Reconnection failed after %d attempts", self.strategy.max_attempts)
        if status_callback:
            status_callback(
                f"Wiederverbindung fehlgeschlagen nach {self.strategy.max_attempts} Versuchen",
                "red",
            )
        return False
