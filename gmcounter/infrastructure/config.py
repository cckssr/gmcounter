"""Configuration loading and management."""

from __future__ import annotations

import copy
import json
import logging
import sys
from functools import lru_cache
from pathlib import Path
from importlib.resources import files
from typing import Any

from .logging import Debug

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
DEFAULT_PROFILE = "expert"
LANGUAGE_KEY = "de"
_log = logging.getLogger(__name__)


def import_config(language: str = "de") -> dict:
    """Imports the language-specific configuration from config.json.

    Args:
        language (str): The language code to load the configuration for (default is "de").

    Returns:
        dict: The configuration dictionary.
    """
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
            package_config = files("gmcounter").joinpath("config.json")
            if hasattr(package_config, "read_text"):
                config = json.loads(package_config.read_text(encoding="utf-8"))
                Debug.debug("Config loaded from package resources (fallback).")
                return config.get(language, config.get("de", {}))
    except Exception as e:  # pylint: disable=broad-except
        Debug.debug(f"Failed to load config from package resources: {e}")

    Debug.error("config.json not found. Please ensure it exists in the project root.")
    return {}


def get_config(language: str = "de") -> dict:
    """Convenience function to get configuration."""
    return import_config(language)


# ---------------------------------------------------------------------------
# AppConfig: dotted-path access, UI strings, profiles
# ---------------------------------------------------------------------------


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (in place) and return ``base``."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


class AppConfig:
    """Read-only view on the parsed config.json with dotted-path access.

    ``profile`` names the entry of the ``profiles`` section that is active: its ``overrides``
    are already merged into the data, ``hidden_tabs`` / ``hidden_widgets`` are read by the UI.
    The data is the content below the language key (``"de"``) of config.json.
    """

    def __init__(self, data: dict[str, Any], profile: str = DEFAULT_PROFILE) -> None:
        self._data = data
        self.profile = profile

    @property
    def data(self) -> dict[str, Any]:
        """The underlying dictionary."""
        return self._data

    def get(self, path: str, default: Any = None) -> Any:
        """Look up ``"section.key.subkey"``; ``default`` if any part is missing."""
        node: Any = self._data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def section(self, name: str) -> dict[str, Any]:
        """Top-level section ``name`` (an empty dict if missing or not a mapping)."""
        value = self._data.get(name, {})
        return value if isinstance(value, dict) else {}

    def text(self, path: str, **fmt: Any) -> str:
        """German UI string at ``ui.<path>``; falls back to the path itself (visible, not fatal)."""
        value = self.get(f"ui.{path}", path)
        text = value if isinstance(value, str) else path
        return text.format(**fmt) if fmt else text

    def message(self, key: str, **fmt: Any) -> str:
        """Message (status/warning/error) by key from the ``messages`` section."""
        value = self.section("messages").get(key, key)
        value = value if isinstance(value, str) else key
        return value.format(**fmt) if fmt else value

    def with_overrides(self, overrides: dict[str, Any]) -> AppConfig:
        """Copy with a nested dict merged on top (used by tests and simulation tweaks)."""
        return AppConfig(_merge(copy.deepcopy(self._data), overrides), self.profile)

    # ---- profiles ----------------------------------------------------------------------
    @property
    def profile_name(self) -> str:
        """German display name of the active profile."""
        return str(self.get(f"profiles.{self.profile}.name", self.profile))

    @property
    def profile_names(self) -> list[str]:
        """Ids of all configured profiles."""
        return list(self.section("profiles"))

    def hidden_tabs(self) -> list[str]:
        """Tab ids the active profile leaves out."""
        return list(self.get(f"profiles.{self.profile}.hidden_tabs", []))

    def hidden_widgets(self) -> dict[str, list[str]]:
        """Designer object names the active profile hides, per root (a panel or a tab id)."""
        value = self.get(f"profiles.{self.profile}.hidden_widgets", {})
        return (
            {root: list(names) for root, names in value.items()}
            if isinstance(value, dict)
            else {}
        )


def load_config(
    path: Path | None = None,
    overrides: dict[str, Any] | None = None,
    profile: str | None = None,
) -> AppConfig:
    """Load config.json (UTF-8) and unwrap the ``"de"`` language key.

    A missing or broken file yields an empty config (logged). ``profile`` (default:
    ``application.profile``, else ``"expert"``) selects the entry of ``profiles`` whose
    ``overrides`` are merged over the defaults; the caller's ``overrides`` come last. An unknown
    profile is logged and replaced by the default one; the ``profiles`` section may be absent.
    """
    cfg_path = path or CONFIG_PATH
    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _log.error("Cannot load %s: %s", cfg_path, exc)
        raw = {}
    data = raw.get(LANGUAGE_KEY, raw) if isinstance(raw, dict) else {}
    profiles = data.get("profiles", {})
    name = profile or data.get("application", {}).get("profile", DEFAULT_PROFILE)
    if name not in profiles and name != DEFAULT_PROFILE:
        _log.warning("unknown profile %r, using %r", name, DEFAULT_PROFILE)
        name = DEFAULT_PROFILE
    profile_overrides = profiles.get(name, {}).get("overrides", {})
    if profile_overrides:
        _merge(data, copy.deepcopy(profile_overrides))
    if overrides:
        _merge(data, copy.deepcopy(overrides))
    return AppConfig(data, name)


@lru_cache(maxsize=1)
def _packaged_config() -> AppConfig:
    return load_config()


def default_config() -> AppConfig:
    """The packaged config.json with the default profile (cached; do not mutate)."""
    return _packaged_config()
