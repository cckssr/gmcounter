"""AppConfig: dotted access, sections, text fallback, overrides, loading."""

from __future__ import annotations

import json
from pathlib import Path

from gmcounter.infrastructure.config import AppConfig, import_config, load_config


def _config() -> AppConfig:
    return AppConfig(
        {
            "ui": {"main_window": {"buttonStart": "Start"}, "greeting": "Hallo {name}"},
            "messages": {"saved": "{n} Punkte gespeichert"},
            "timers": {"gui_update_interval": 200},
        }
    )


def test_get_reads_dotted_paths_and_falls_back_to_the_default() -> None:
    cfg = _config()
    assert cfg.get("timers.gui_update_interval") == 200
    assert cfg.get("timers.missing", 5) == 5
    assert cfg.get("nope.at.all") is None


def test_section_returns_the_mapping_or_an_empty_dict() -> None:
    cfg = _config()
    assert cfg.section("timers") == {"gui_update_interval": 200}
    assert cfg.section("absent") == {}


def test_text_resolves_ui_strings_and_formats_them() -> None:
    cfg = _config()
    assert cfg.text("main_window.buttonStart") == "Start"
    assert cfg.text("greeting", name="Welt") == "Hallo Welt"


def test_text_falls_back_to_the_path_for_unknown_keys() -> None:
    assert _config().text("main_window.unknown") == "main_window.unknown"


def test_message_formats_and_falls_back_to_the_key() -> None:
    cfg = _config()
    assert cfg.message("saved", n=3) == "3 Punkte gespeichert"
    assert cfg.message("unknown") == "unknown"


def test_with_overrides_merges_deeply_without_touching_the_original() -> None:
    cfg = _config()
    other = cfg.with_overrides({"timers": {"extra": 1}, "ui": {"greeting": "Hi"}})
    assert other.get("timers") == {"gui_update_interval": 200, "extra": 1}
    assert other.text("greeting") == "Hi"
    assert cfg.get("timers") == {"gui_update_interval": 200}
    assert cfg.text("greeting") == "Hallo {name}"


def test_profiles_default_to_expert_and_are_optional() -> None:
    cfg = _config()
    assert cfg.profile == "expert"
    assert cfg.profile_names == []
    assert cfg.hidden_tabs() == []
    assert cfg.hidden_widgets() == {}


def test_load_config_unwraps_the_language_key(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"de": {"a": {"b": 1}}}), encoding="utf-8")
    cfg = load_config(path, overrides={"a": {"c": 2}})
    assert cfg.get("a") == {"b": 1, "c": 2}


def test_load_config_applies_the_selected_profile(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    data = {
        "de": {
            "x": 1,
            "profiles": {
                "student": {
                    "name": "Praktikum",
                    "hidden_tabs": ["t"],
                    "overrides": {"x": 2},
                }
            },
        }
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_config(path, profile="student")
    assert (cfg.get("x"), cfg.profile_name, cfg.hidden_tabs()) == (
        2,
        "Praktikum",
        ["t"],
    )
    assert load_config(path, profile="unknown").profile == "expert"


def test_load_config_survives_a_missing_file(tmp_path: Path) -> None:
    assert load_config(tmp_path / "missing.json").data == {}


def test_packaged_config_matches_the_legacy_import_config() -> None:
    cfg = load_config()
    legacy = import_config()
    assert cfg.get("application.name") == legacy["application"]["name"]
    assert cfg.get("application.window_mode") == "maximized"
    assert cfg.section("ui").get("main_window") == {}
