"""Connection retry logic service - domain layer for reconnection strategy."""

import time
from typing import Callable, Optional
from ..infrastructure.logging import Debug


class ReconnectStrategy:
    """Encapsulates retry logic with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 5,
        initial_delay_ms: float = 500,
        max_delay_ms: float = 5000,
        backoff_factor: float = 1.5,
    ):
        """Initialize reconnection strategy.

        Args:
            max_attempts: Maximum number of reconnection attempts
            initial_delay_ms: Initial delay between attempts in milliseconds
            max_delay_ms: Maximum delay between attempts in milliseconds
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_factor = backoff_factor
        self.attempt_count = 0

    def reset(self) -> None:
        """Reset attempt counter after successful connection."""
        self.attempt_count = 0
        Debug.info("Reconnection attempt counter reset")

    def should_retry(self) -> bool:
        """Check if more retry attempts are available."""
        return self.attempt_count < self.max_attempts

    def get_next_delay_ms(self) -> float:
        """Get delay for next retry with exponential backoff.

        Returns:
            Delay in milliseconds with exponential backoff applied.
        """
        delay = self.initial_delay_ms * (self.backoff_factor**self.attempt_count)
        delay = min(delay, self.max_delay_ms)
        self.attempt_count += 1
        return delay

    def get_attempt_info(self) -> str:
        """Get human-readable attempt information."""
        return f"Attempt {self.attempt_count}/{self.max_attempts}"


class ConnectionRetryService:
    """Service for managing connection retry logic.

    This service handles the domain-level logic for retrying connections
    with exponential backoff, separate from the infrastructure/hardware layer.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        initial_delay_ms: float = 500,
    ):
        """Initialize the retry service.

        Args:
            max_attempts: Maximum number of reconnection attempts
            initial_delay_ms: Initial delay between attempts in milliseconds
        """
        self.strategy = ReconnectStrategy(
            max_attempts=max_attempts, initial_delay_ms=initial_delay_ms
        )

    def attempt_reconnect(
        self,
        reconnect_fn: Callable[[], bool],
        status_callback: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Attempt to reconnect using the provided function with retry logic.

        Args:
            reconnect_fn: Callable that attempts connection. Should return bool.
            status_callback: Optional callback(message, color) for status updates.

        Returns:
            True if connection successful, False if all attempts exhausted.
        """
        self.strategy.reset()

        while self.strategy.should_retry():
            delay = self.strategy.get_next_delay_ms()
            attempt_info = self.strategy.get_attempt_info()

            if status_callback:
                status_callback(
                    f"Wiederverbindung... {attempt_info}",
                    "orange",
                )

            Debug.info(f"Reconnection {attempt_info} - delay: {delay:.0f}ms")

            # Wait before attempting
            time.sleep(delay / 1000.0)

            try:
                if reconnect_fn():
                    Debug.info(
                        f"Reconnection successful after {self.strategy.attempt_count} attempts"
                    )
                    if status_callback:
                        status_callback("Wiederverbunden", "green")
                    return True
            except Exception as e:
                Debug.error(f"Reconnection attempt {attempt_info} failed: {e}")

        # All attempts exhausted
        Debug.error(f"Reconnection failed after {self.strategy.max_attempts} attempts")
        if status_callback:
            status_callback(
                f"Wiederverbindung fehlgeschlagen nach {self.strategy.max_attempts} Versuchen",
                "red",
            )
        return False
