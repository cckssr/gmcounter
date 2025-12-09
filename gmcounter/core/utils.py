"""Core utilities - NO Qt dependencies allowed."""

import re
from datetime import datetime
from typing import Optional
import statistics
from ..infrastructure.logging import Debug


def sanitize_subterm_for_folder(subterm: str, max_length: int = 20) -> str:
    """Sanitize and shorten subterm for use in folder names.

    - Replaces special characters with underscores
    - Limits length to max_length characters
    - If too long, abbreviates each word to first 3 letters
    - If still too long, returns "xxx"

    Args:
        subterm: The subterm to sanitize
        max_length: Maximum allowed length (default 20)

    Returns:
        Sanitized and shortened subterm
    """
    if not subterm:
        return ""

    # Replace special characters with underscores
    # Keep only alphanumeric, spaces, hyphens, and underscores
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_äöüÄÖÜß]", "_", subterm)

    # Replace multiple consecutive underscores/spaces with single underscore
    sanitized = re.sub(r"[_\s]+", "_", sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # If already short enough, return it
    if len(sanitized) <= max_length:
        return sanitized

    # Try abbreviating each word to first 3 letters
    words = sanitized.split("_")
    abbreviated = "_".join(word[:3] for word in words if word)

    if len(abbreviated) <= max_length:
        return abbreviated

    # Still too long, use abbreviated + "_xxx"
    return abbreviated[: max_length - 4] + "_xxx"


def create_dropbox_foldername(
    group_letter: str, tk_designation: str, subgroup: Optional[str] = None
) -> str:
    """Create a folder name for the custom GP-OpenBIS-Dropbox structure.

    The syntax is: <current_day><group_letter><tk_designation>-<subgroup>
    Example: "MoA01-Gyroskop"

    Args:
        group_letter (str): The group letter (A-Z).
        tk_designation (str): The designation of the experiment (e.g., "TK8").
        subgroup (str): The subgroup name (e.g., "A. Mueller") for differentiation.

    Returns:
        str: The created folder name.
    """
    # Ensure German weekday abbreviation independent of system locale
    day = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][datetime.now().weekday()]

    if not group_letter or not re.match(r"^[A-Z]$", group_letter):
        Debug.error(f"Invalid group letter: {group_letter}")
        return ""
    if not tk_designation or not re.match(r"^TK\d{1,2}$", tk_designation):
        Debug.error(f"Invalid TK designation: {tk_designation}")
        return ""

    folder_name = f"{day}{group_letter.upper()}{tk_designation}"
    if subgroup:
        folder_name += f"-{subgroup}"
    return folder_name


def create_group_name(letter: str) -> str:
    """Create a group name based on the letter.

    Args:
        letter: Single letter (A-Z)

    Returns:
        Group name in format "SoSe2024_Mo_A"
    """

    semester = "SoSe"
    if datetime.now().month >= 10 and datetime.now().month <= 12:
        semester = "WiSe"
    day = datetime.now().strftime("%a")[:2]
    year = datetime.now().year

    if not letter or not re.match(r"^[A-Z]$", letter):
        Debug.error(f"Invalid group letter: {letter}")
        return "Ungültige Gruppe"

    return f"{semester}{year}_{day}_{letter.upper()}"


def calculate_statistics(values: list[float]) -> dict:
    """Calculate statistical measures for a list of values.

    Args:
        values: List of measurement values

    Returns:
        Dictionary with mean, std, min, max, count
    """
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "count": 0}

    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "count": len(values),
    }
