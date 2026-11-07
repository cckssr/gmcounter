"""Fixtures for the UI tests (offscreen Qt, isolated QSettings)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from gmcounter.infrastructure.config import AppConfig, load_config


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path_factory):
    """Redirect QSettings to a temporary directory so tests never touch real settings."""
    settings_dir = tmp_path_factory.mktemp("qsettings")
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    for scope in (QSettings.Scope.UserScope, QSettings.Scope.SystemScope):
        QSettings.setPath(QSettings.Format.IniFormat, scope, str(settings_dir))
    yield


@pytest.fixture
def config() -> AppConfig:
    """The packaged config.json (German strings, defaults)."""
    return load_config()
