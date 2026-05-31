# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.

from typing import Optional


def format_value_us(value: float, decimals: int = 0) -> str:
    """Format a microsecond value for display."""
    return f"{value:.{decimals}f}"


def format_duration(seconds: float) -> str:
    """Format elapsed seconds as a human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}m {secs:02d}s"


def format_stat(value: float, decimals: int = 0) -> str:
    """Format a statistics value for display."""
    return f"{value:,.{decimals}f}"


def counting_time_label(index: int, labels: Optional[list[str]] = None) -> str:
    """Return a human-readable label for a counting-time index.

    Default labels match the Arduino firmware: 0=∞, 1=1s, 2=10s,
    3=60s, 4=100s, 5=300s.
    """
    default = ["∞", "1 s", "10 s", "60 s", "100 s", "300 s"]
    table = labels if labels is not None else default
    if 0 <= index < len(table):
        return table[index]
    return str(index)
