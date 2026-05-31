# Layer: core — pure Python, zero Qt/serial/vendor SDK imports.

import logging
import re
import statistics
from datetime import datetime
from typing import Optional

_log = logging.getLogger(__name__)


def sanitize_subterm_for_folder(subterm: str, max_length: int = 20) -> str:
    """Sanitize and shorten a subterm for use in folder names.

    Replaces special characters with underscores, limits length.
    Abbreviates each word to 3 letters if still too long.
    """
    if not subterm:
        return ""

    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_äöüÄÖÜß]", "_", subterm)
    sanitized = re.sub(r"[_\s]+", "_", sanitized).strip("_")

    if len(sanitized) <= max_length:
        return sanitized

    abbreviated = "_".join(word[:3] for word in sanitized.split("_") if word)
    if len(abbreviated) <= max_length:
        return abbreviated

    return abbreviated[: max_length - 4] + "_xxx"


def create_dropbox_foldername(
    group_letter: str,
    tk_designation: str,
    subgroup: Optional[str] = None,
) -> str:
    """Create a Dropbox-compatible folder name for the GP-OpenBIS structure.

    Format: <German weekday><group_letter><tk_designation>[-<subgroup>]
    Example: "MoATK08-Mueller"
    """
    day = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][datetime.now().weekday()]

    if not group_letter or not re.match(r"^[A-Z]$", group_letter):
        _log.error("Invalid group letter: %s", group_letter)
        return ""
    if not tk_designation or not re.match(r"^TK\d{1,2}$", tk_designation):
        _log.error("Invalid TK designation: %s", tk_designation)
        return ""

    name = f"{day}{group_letter.upper()}{tk_designation}"
    if subgroup:
        name += f"-{subgroup}"
    return name


def create_group_name(letter: str) -> str:
    """Create a group name from a single letter.

    Returns a string like "SoSe2024_Mo_A".
    """
    month = datetime.now().month
    semester = "WiSe" if 10 <= month <= 12 else "SoSe"
    day = datetime.now().strftime("%a")[:2]
    year = datetime.now().year

    if not letter or not re.match(r"^[A-Z]$", letter):
        _log.error("Invalid group letter: %s", letter)
        return "Ungültige Gruppe"

    return f"{semester}{year}_{day}_{letter.upper()}"


def calculate_statistics(values: list[float]) -> dict:
    """Return count/mean/std/min/max for a list of values."""
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "count": 0}

    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "count": len(values),
    }
