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
    # WICHTIG: Dateipfade haben Vorrang vor Package-Resources,
    # damit während Development/Release die aktuelle Config verwendet wird
    possible_paths = [
        Path(__file__).parent.parent / "config.json",  # Im gmcounter/ Verzeichnis
        Path(__file__).parent.parent.parent / "config.json",  # Projektroot
        Path("config.json"),  # Aktuelles Verzeichnis
        Path(sys.prefix) / "config.json",  # Installation prefix
    ]

    # ZUERST: Versuche config.json von Dateipfaden zu laden
    for config_path in possible_paths:
        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    Debug.debug(f"Config loaded from: {config_path}")
                    return config.get(language, config.get("de", {}))
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    # FALLBACK: Falls keine Datei gefunden, nutze importlib.resources (Package-Ressource)
    try:
        if sys.version_info >= (3, 9):
            from importlib.resources import files

            package_config = files("gmcounter").joinpath("config.json")
            if hasattr(package_config, "read_text"):
                config = json.loads(package_config.read_text(encoding="utf-8"))
                Debug.debug("Config loaded from package resources (fallback).")
                return config.get(language, config.get("de", {}))
    except Exception as e:
        Debug.debug(f"Failed to load config from package resources: {e}")

    Debug.error("config.json not found. Please ensure it exists in the project root.")
    return {}


def get_config(language: str = "de") -> dict:
    """Convenience function to get configuration."""
    return import_config(language)
