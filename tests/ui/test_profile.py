"""Profile tests.

The student profile hides expert controls; the window can be rebuilt with the other
profile while the connected device manager stays in use.
"""

from __future__ import annotations

import pytest

from gmcounter.infrastructure.config import load_config
from gmcounter.ui.launcher import Launcher
from gmcounter.ui.profile import apply_profile, next_profile
from gmcounter.ui.windows.main_window import MainWindow

from .conftest import make_device_manager

HIDDEN_IN_STUDENT = {
    "device_panel": ("labelQueryMode", "radioQueryManual", "radioQueryAuto"),
    "device_status_panel": (
        "labelQueryReadback",
        "valueQueryMode",
        "labelFirmware",
        "valueFirmware",
        "labelOpenbis",
        "valueOpenbis",
    ),
}


@pytest.fixture
def student(qtbot, device_manager):
    win = MainWindow(load_config(profile="student"), device_manager, persist=False)
    qtbot.addWidget(win)
    win.show()
    yield win
    win.close()


def _panel_ui(win, root):
    return {
        "device_panel": win.ui.devicePanel.ui,
        "device_status_panel": win.ui.deviceStatusPanel.ui,
    }[root]


def test_the_expert_window_keeps_every_control(window):
    assert window.config.profile == "expert"
    for root, names in HIDDEN_IN_STUDENT.items():
        for name in names:
            assert not getattr(_panel_ui(window, root), name).isHidden(), name


def test_the_student_window_hides_the_expert_controls(student):
    assert student.config.profile_name == "Praktikum"
    for root, names in HIDDEN_IN_STUDENT.items():
        for name in names:
            assert getattr(_panel_ui(student, root), name).isHidden(), name
    assert student.ui.devicePanel.ui.comboDuration.isVisible()
    assert student.ui.deviceStatusPanel.ui.lcdVoltage.isVisible()


def test_every_hidden_widget_of_every_profile_exists(qtbot, device_manager):
    for profile in load_config().profile_names:
        win = MainWindow(load_config(profile=profile), device_manager, persist=False)
        qtbot.addWidget(win)
        assert apply_profile(win) == [], profile
        assert win.missing_profile_names == [], profile


def test_a_misspelled_widget_name_is_reported(student):
    hidden = student.config.data["profiles"]["student"]["hidden_widgets"]
    hidden["device_panel"].append("noSuchBox")
    hidden["no_root"] = ["x"]
    assert apply_profile(student) == ["device_panel.noSuchBox", "no_root"]


def test_hidden_controls_fall_back_to_the_defaults(student):
    settings = student.ui.devicePanel.settings()
    assert settings["auto_query"] is False  # query mode: manual


def test_the_student_window_fits_the_small_screen(qtbot, student):
    student.resize(1280, 800)
    qtbot.wait(50)
    assert student.minimumSizeHint().width() <= 1280
    assert student.minimumSizeHint().height() <= 800


def test_the_cli_profile_selects_the_student_profile():
    from gmcounter.main import parse_args

    assert parse_args(["--profile", "student"]).profile == "student"
    assert parse_args([]).profile is None


def test_the_default_profile_is_expert_and_next_profile_cycles():
    assert load_config().profile == "expert"
    assert next_profile("expert", ["expert", "student"]) == "student"
    assert next_profile("student", ["expert", "student"]) == "expert"


def test_the_switch_action_names_the_target_profile(window, student):
    assert "Praktikum" in window.ui.actionSwitchProfile.text()
    assert "Experte" in student.ui.actionSwitchProfile.text()
    assert window.ui.actionSwitchProfile.isEnabled()


# ---- launcher ----------------------------------------------------------------------------
@pytest.fixture
def launcher():
    """A launcher with its first window.

    Closed without a question at teardown (the windows are not registered with qtbot,
    whose plain close would ask about unsaved data).
    """
    launcher = Launcher(make_device_manager(), persist=False)
    launcher.start()
    yield launcher
    if launcher.window is not None:
        launcher.window.close_for_switch()


def test_the_switch_rebuilds_the_window_and_keeps_the_device_manager(launcher):
    old = launcher.window
    manager = old.device_manager
    new = launcher.switch_to("student")
    assert new is not old and new is launcher.window
    assert new.config.profile == "student"
    assert new.device_manager is manager
    assert (
        manager.connected and manager.device is not None
    )  # not disconnected by the close
    assert not old.isVisible()


def test_the_switch_keeps_the_window_mode(launcher):
    launcher.window.showNormal()
    new = launcher.switch_to("student")
    assert not new.isFullScreen() and not new.isMaximized()


def test_the_switch_does_not_ask_about_unsaved_data(launcher, monkeypatch):
    asked = []
    monkeypatch.setattr(
        launcher.window.session._prompt, "ask", lambda *a: asked.append(a) or False
    )
    launcher.switch_to("student")
    assert asked == []


def test_no_switch_while_measuring(launcher, monkeypatch):
    old = launcher.window
    monkeypatch.setattr(type(old.ctrl), "is_measuring", property(lambda _s: True))
    assert launcher.switch_to("student") is old
    assert launcher.window is old and old.config.profile == "expert"
    assert (
        old.config.message("profile_switch_busy")
        in old.ui.eventLogPanel.ui.editLog.toPlainText()
    )


def test_no_switch_with_unsaved_data(launcher, monkeypatch):
    old = launcher.window
    monkeypatch.setattr(old.session, "has_unsaved", lambda: True)
    assert launcher.switch_to("student") is old
    assert (
        old.config.message("profile_switch_unsaved")
        in old.ui.eventLogPanel.ui.editLog.toPlainText()
    )
