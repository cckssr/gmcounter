"""Fixtures for the UI tests (offscreen Qt, isolated QSettings)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QFontDatabase

from gmcounter.infrastructure.config import AppConfig, load_config
from gmcounter.infrastructure.device_manager import DeviceManager
from gmcounter.ui.windows.main_window import MainWindow


@pytest.fixture(scope="session", autouse=True)
def reference_font(qapp):
    """Lay the forms out with the same font on every platform.

    The minimum sizes of the windows depend on the font: macOS, Windows and the Linux CI
    runner measure the same form several percent apart, so a width limit that passes on a
    developer machine could fail in CI. DejaVu Sans (shipped with matplotlib, which the
    application needs anyway) is the Linux default and the widest of them.
    """
    ttf = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
    font_id = QFontDatabase.addApplicationFont(str(ttf))
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        font = QFont(families[0])
        font.setPointSizeF(9)
        qapp.setFont(font)
    yield qapp.font()


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
    """The packaged config.json with the expert profile (every control visible)."""
    return load_config(profile="expert")


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
