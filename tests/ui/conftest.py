"""Fixtures for the UI tests (offscreen Qt, isolated QSettings)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from gmcounter.infrastructure.config import AppConfig, load_config
from gmcounter.infrastructure.device_manager import DeviceManager
from gmcounter.ui.windows.main_window import MainWindow


@pytest.fixture(autouse=True)
def layout_settings(tmp_path_factory, monkeypatch):
    """Keep the window layout out of the user's settings: an ini file per test."""
    path = str(tmp_path_factory.mktemp("qsettings") / "layout.ini")

    def settings() -> QSettings:
        return QSettings(path, QSettings.Format.IniFormat)

    monkeypatch.setattr("gmcounter.ui.windows.main_window.layout_settings", settings)
    return settings


@pytest.fixture
def config() -> AppConfig:
    """The packaged config.json (German strings, defaults)."""
    return load_config()


class IdleDevice:
    """Connected device that stays silent: enough for the window, no serial port involved."""

    connected = True
    serial = None

    def get_data(self) -> dict:
        return {}

    def get_information(self) -> dict:
        return {"version": "test-fw", "openbis": "E00000"}

    def set_counting(self, _on: bool) -> None:
        pass

    def close(self) -> None:
        pass


def make_device_manager() -> DeviceManager:
    """A device manager with an idle fake device (no hardware, no serial port, no mock)."""
    manager = DeviceManager()
    manager.device = IdleDevice()  # type: ignore[assignment]
    manager.connected = True
    manager.port = "test"
    return manager


@pytest.fixture
def device_manager() -> DeviceManager:
    return make_device_manager()


@pytest.fixture
def window(qtbot, config, device_manager):
    """The main window on an unconnected device manager; layout and save folder are not persisted."""
    win = MainWindow(config, device_manager, persist=False)
    qtbot.addWidget(win)
    win.show()
    yield win
    win.close()
