"""Window chrome: dock actions, layout persistence, window modes, close guard, panel wiring."""

from __future__ import annotations

import pytest
from gmcounter.ui.common import dialogs
from gmcounter.ui.windows.main_window import MainWindow

from .conftest import make_device_manager


def test_the_dock_toggle_actions_follow_the_docks_both_ways(window):
    ui = window.ui
    for dock, action in (
        (ui.dockControls, ui.actionToggleControls),
        (ui.dockLive, ui.actionToggleLive),
        (ui.dockLog, ui.actionToggleLog),
    ):
        initially = dock.isVisible()
        assert action.isChecked() == initially
        action.setChecked(not initially)
        assert dock.isVisible() == (not initially)
        dock.setVisible(initially)
        assert action.isChecked() == initially


def test_the_log_dock_is_hidden_by_default_and_the_profile_switch_is_off(window):
    assert not window.ui.dockLog.isVisible()
    assert not window.ui.actionSwitchProfile.isVisible()
    assert not window.ui.actionSwitchProfile.isEnabled()


def test_the_start_state_offers_only_start(window):
    ui = window.ui.measurementPanel.ui
    assert ui.buttonStart.isEnabled()
    assert not any(
        b.isEnabled() for b in (ui.buttonStop, ui.buttonSave, ui.buttonReset)
    )
    assert window.ui.deviceStatusPanel.ui.valueStatus.text() == "Bereit"
    assert window.ui.deviceStatusPanel.ui.ledStatus.state == "ok"


def test_device_state_and_info_reach_the_panels(window):
    window.ctrl.device_state_updated.emit(
        {
            "count": 5,
            "last_count": 9,
            "voltage": 480,
            "counting_time": 10,
            "repeat": True,
        }
    )
    readout, status = window.ui.readoutPanel.ui, window.ui.deviceStatusPanel.ui
    assert (readout.lcdCount.value(), readout.lcdLastCount.value()) == (5, 9)
    assert status.lcdVoltage.value() == 480
    assert status.valueMode.text() == "Wiederholung"
    assert window.context.voltage_readback() == 480.0

    window.ctrl.device_state_updated.emit({"error": True, "count": 0, "last_count": 0})
    assert readout.lcdCount.value() == 5  # a corrupted read never zeroes the displays

    window._on_device_info({"version": "1.2", "openbis": "E1"})
    assert status.valueFirmware.text() == "1.2" and status.valueOpenbis.text() == "E1"


def test_the_context_exposes_the_panels_to_the_tabs(window):
    ctx = window.context
    assert ctx.device_settings() == {
        "voltage": 500,
        "repeat": False,
        "auto_query": False,
    }
    window.ui.samplePanel.ui.editSuffix.setText(" abc ")
    assert ctx.sample_metadata()["suffix"] == "abc"
    assert ctx.timing is window.tabs["gm_timing"]


def test_the_progress_follows_the_controller(window):
    window.ctrl.progress_updated.emit(3, 10)
    ui = window.ui.measurementPanel.ui
    assert (ui.progressMeasurement.value(), ui.progressMeasurement.maximum()) == (3, 10)
    assert ui.valueElapsed.text() == "3 s"


def test_a_session_locks_the_other_tabs_and_unlocks_them_again(window, monkeypatch):
    tabs = window.ui.tabWidget
    sweep = window.tabs["distance_law"]
    tabs.setCurrentWidget(sweep)
    window.ui.devicePanel.ui.comboDuration.setCurrentIndex(2)
    monkeypatch.setattr(window.ctrl, "start_measurement", lambda total_seconds=0: True)
    window.session.start()
    assert [tabs.isTabEnabled(i) for i in range(tabs.count())] == [
        False,
        True,
        False,
        False,
    ]
    window._lock_tabs(None)
    assert all(tabs.isTabEnabled(i) for i in range(tabs.count()))


def test_closing_asks_when_data_is_unsaved(qtbot, config, device_manager, monkeypatch):
    win = MainWindow(config, device_manager, persist=False)
    qtbot.addWidget(win)
    win.show()
    win.context.save_service.mark_unsaved()
    answers = iter([False, True])
    asked = []
    monkeypatch.setattr(
        dialogs,
        "ask_question",
        lambda parent, text, title: asked.append(text) or next(answers),
    )
    assert not win.close()  # the user keeps the window
    assert win.isVisible()
    assert win.close()
    assert asked == [config.message("unsaved_data_end")] * 2


def test_the_layout_is_saved_per_profile_and_restored(
    qtbot, config, tmp_path, layout_settings
):
    config = config.with_overrides({"save": {"base_folder": str(tmp_path)}})
    first = MainWindow(config, make_device_manager(), persist=True)
    qtbot.addWidget(first)
    first.show()
    first.ui.actionToggleLog.setChecked(True)
    first.resize(1100, 700)
    first.close()  # closing releases the device, so the next window gets its own manager
    settings = layout_settings()
    assert settings.value("window/geometry") is not None
    assert settings.value("window/state") is not None

    second = MainWindow(config, make_device_manager(), persist=True)
    qtbot.addWidget(second)
    second.show()
    assert second.ui.dockLog.isVisible() and second.ui.actionToggleLog.isChecked()
    second.close()


def test_the_layout_is_not_touched_without_persistence(window, layout_settings):
    window.close()
    assert layout_settings().value("window/geometry") is None


@pytest.mark.parametrize(
    ("mode", "fullscreen", "maximized"),
    [("fullscreen", True, False), ("maximized", False, True), ("normal", False, False)],
)
def test_the_window_mode_decides_how_the_window_opens(
    qtbot, config, device_manager, mode, fullscreen, maximized
):
    win = MainWindow(config, device_manager, persist=False)
    qtbot.addWidget(win)
    win.show_initial(mode)
    assert win.isFullScreen() is fullscreen
    assert win.isMaximized() is maximized
    assert win.ui.actionFullScreen.isChecked() is fullscreen
    win.close()


def test_the_full_screen_action_toggles_the_window(window):
    window.ui.actionFullScreen.trigger()
    assert window.isFullScreen()
    window.ui.actionFullScreen.trigger()
    assert not window.isFullScreen()


def test_the_voltage_warning_reaches_the_status_bar(window, config):
    window.ui.devicePanel.set_voltage(690)
    assert "690" in window.ui.statusBar.currentMessage()
    assert window.ui.statusBar.currentMessage() == config.message(
        "voltage_warning"
    ).format(690)
