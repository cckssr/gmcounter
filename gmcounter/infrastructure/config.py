"""Configuration loading and management."""

import json
import sys
from pathlib import Path


def import_config(language: str = "de") -> dict:
    """
    Imports the language-specific configuration from config.json.

    Args:
        language (str): The language code to load the configuration for (default is "de").

    Returns:
        dict: The configuration dictionary.
    """
    from .logging import Debug

    # Mögliche Pfade für config.json (in Prioritätsreihenfolge)
    possible_paths = [
        Path(__file__).parent.parent / "config.json",  # Im gmcounter/ Verzeichnis
        Path(__file__).parent.parent.parent / "config.json",  # Projektroot
        Path("config.json"),  # Aktuelles Verzeichnis
        Path(sys.prefix) / "config.json",  # Installation prefix
    ]

    # Falls als Package installiert, nutze importlib.resources (Python 3.9+)
    try:
        if sys.version_info >= (3, 9):
            from importlib.resources import files

            package_config = files("gmcounter").joinpath("config.json")
            if hasattr(package_config, "read_text"):
                config = json.loads(package_config.read_text(encoding="utf-8"))
                return config.get(language, config.get("de", {}))
    except Exception:
        pass  # Fallback zu Dateipfaden

    for config_path in possible_paths:
        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    Debug.debug(f"Config loaded from: {config_path}")
                    return config.get(language, config.get("de", {}))
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    Debug.error("config.json not found. Please ensure it exists in the project root.")
    return {}


def get_config(language: str = "de") -> dict:
    """Convenience function to get configuration."""
    return import_config(language)
