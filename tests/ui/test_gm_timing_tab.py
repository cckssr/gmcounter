"""High-speed acquisition of the timing tab and the frame routing of the window."""

from __future__ import annotations

import pytest

from gmcounter.core.models import Frame

QUEUE_SIZE = 10_000


def _frames(count: int, start: int = 0, value: float = 500.0) -> list[Frame]:
    return [
        Frame(index=start + i, value=value, timestamp="00:00:00.000")
        for i in range(count)
    ]


@pytest.fixture
def timing(window):
    return window.tabs["gm_timing"]


def _drive_into_high_speed(tab, batch: int = 200) -> None:
    """Deliver ``batch`` frames per GUI tick until the batch history triggers high-speed."""
    for tick in range(tab._hs_history):  # pylint: disable=protected-access
        tab.on_frames(_frames(batch, start=tick * batch))
        tab._process_queue()  # pylint: disable=protected-access
    assert tab.high_speed_active


def test_every_frame_is_exported_when_a_batch_overflows_the_gui_queue(timing):
    total = QUEUE_SIZE * 2 + 345
    timing.on_frames(_frames(total))
    assert len(timing.export().rows) == total
    assert (
        timing._queue.qsize() == QUEUE_SIZE
    )  # only the hand-over to the GUI was cut off


def test_the_device_time_accumulator_counts_frames_the_queue_dropped(timing):
    timing.on_frames(_frames(QUEUE_SIZE + 500, value=1000.0))
    assert timing._cum_us == pytest.approx((QUEUE_SIZE + 500) * 1000.0)


def test_nothing_is_enqueued_while_high_speed_is_active(timing):
    _drive_into_high_speed(timing)
    timing.on_frames(_frames(5000, start=10_000))
    assert timing._queue.qsize() == 0
    assert len(timing.export().rows) == 5 * 200 + 5000


def test_high_speed_switches_the_readout_and_the_histogram_view(window, timing):
    readout = window.ui.readoutPanel.ui
    assert readout.ledHighSpeed.state == "off"
    seen = []
    timing.high_speed_changed.connect(seen.append)

    _drive_into_high_speed(timing)

    assert seen == [True]
    assert readout.ledHighSpeed.state == "busy"
    assert readout.valueHighSpeed.text() == "aktiv"
    assert timing.ui.tabViews.currentWidget() is timing.ui.pageHistogram
    assert timing._hist_timer is not None and timing._hist_timer.isActive()
    assert not timing._gui_timer.isActive()  # line plot and table are paused


def test_count_and_rate_keep_updating_in_high_speed(window, timing):
    readout = window.ui.readoutPanel.ui
    _drive_into_high_speed(timing)
    timing.on_frames(_frames(3000, start=5000, value=100.0))
    timing._refresh_high_speed_view()  # what the 2 s histogram timer does

    events = len(timing.export().rows) + 1
    assert readout.lcdCount.value() == events
    expected_rate = round(events / (timing._cum_us / 1e6), 1)
    assert readout.lcdRate.value() == pytest.approx(expected_rate)
    assert readout.lcdRate.value() > 0
    assert readout.lcdCount.value() != 100.0  # not the last delta any more


def test_high_speed_announces_itself_in_the_status_texts(window, timing):
    messages = []
    timing.status_message.connect(lambda level, text: messages.append((level, text)))
    _drive_into_high_speed(timing)
    assert messages == [("warning", window.config.text("timing_tab.text_high_speed"))]
    assert window.ui.eventLogPanel.ui.editLog.toPlainText().endswith(messages[0][1])


def test_a_new_measurement_leaves_high_speed(window, timing):
    _drive_into_high_speed(timing)
    timing.on_reset()
    assert not timing.high_speed_active
    assert window.ui.readoutPanel.ui.ledHighSpeed.state == "off"
    assert window.ui.readoutPanel.ui.valueHighSpeed.text() == "inaktiv"
    assert timing._gui_timer.isActive()


def test_the_view_does_not_switch_during_a_sweep_session(window, timing, monkeypatch):
    sweep_tab = window.tabs["distance_law"]
    window.ui.tabWidget.setCurrentWidget(sweep_tab)
    window.ui.devicePanel.ui.comboDuration.setCurrentIndex(2)  # finite: no question
    monkeypatch.setattr(window.ctrl, "start_measurement", lambda total_seconds=0: True)
    window.session.start()
    assert window.session.session_tab is sweep_tab

    _drive_into_high_speed(timing)

    assert timing.ui.tabViews.currentWidget() is timing.ui.pageTime
    assert window.ui.tabWidget.currentWidget() is sweep_tab
    assert (
        window.ui.readoutPanel.ui.ledHighSpeed.state == "busy"
    )  # the indicator still works


def test_the_inner_view_switches_without_a_session(timing):
    assert timing.ui.tabViews.currentWidget() is timing.ui.pageTime
    _drive_into_high_speed(timing)
    assert timing.ui.tabViews.currentWidget() is timing.ui.pageHistogram


def test_the_readout_is_throttled_but_follows_the_events(window, timing):
    timing.on_frames(_frames(30))
    timing._process_queue()
    assert window.ui.readoutPanel.ui.lcdRate.value() > 0
    timing.on_measurement_stopped()  # final flush shows the exact count
    assert window.ui.readoutPanel.ui.lcdCount.value() == 31


def test_statistics_update_the_histogram_labels(timing):
    timing.on_statistics({"count": 12, "min": 3, "max": 900, "avg": 120.4, "stdev": 7})
    assert timing.ui.valueStatCount.text() == "12"
    assert timing.ui.valueStatMax.text() == "900"
    assert timing.ui.valueStatMean.text() == "120"


def test_the_plot_controls_live_in_the_timing_tab(timing):
    timing.ui.checkAutoScroll.setChecked(False)
    assert not timing.ui.timePlot._auto_scroll_enabled
    timing.ui.checkAutoScroll.setChecked(True)
    assert timing.ui.timePlot._auto_scroll_enabled


def test_the_histogram_sliders_drive_the_spin_boxes(timing):
    timing.on_frames(_frames(50, value=700.0))
    timing.ui.sliderBinSize.setValue(250)
    assert timing.ui.spinBinSize.value() == 250
    assert timing._user_adjusted_hist


# ---------------------------------------------------------------- tabs and frame routing


def test_the_tabs_appear_in_order_with_their_configured_titles(window, config):
    tabs = window.ui.tabWidget
    assert [tabs.tabText(i) for i in range(tabs.count())] == [
        config.text(f"tabs.{tab_id}")
        for tab_id in (
            "gm_timing",
            "distance_law",
            "voltage_response",
            "interval_repeat",
        )
    ]
    assert list(window.tabs) == [
        "gm_timing",
        "distance_law",
        "voltage_response",
        "interval_repeat",
    ]
    assert [tab.order for tab in window.tabs.values()] == [0, 10, 20, 30]
    assert window.context.timing is window.tabs["gm_timing"]


def test_frames_go_to_the_interval_tab_while_it_is_selected(window, timing):
    interval = window.tabs["interval_repeat"]
    window.ui.tabWidget.setCurrentWidget(interval)
    interval.on_reset()
    window.ctrl.frames_ready.emit(_frames(20, value=100_000.0))  # 20 x 0.1 s
    assert interval.has_data()
    assert timing.export() is None

    window.ui.tabWidget.setCurrentWidget(timing)
    window.ctrl.frames_ready.emit(_frames(7))
    assert len(timing.export().rows) == 7


def test_the_global_distance_row_is_hidden_on_the_distance_tab(window):
    sample = window.ui.samplePanel.ui
    window.ui.tabWidget.setCurrentWidget(window.tabs["gm_timing"])
    assert sample.spinDistance.isVisibleTo(window)
    sample.spinDistance.setValue(12.5)
    window.ui.tabWidget.setCurrentWidget(window.tabs["distance_law"])
    assert not sample.spinDistance.isVisibleTo(window)
    assert sample.spinDistance.value() == 0.0


# ---------------------------------------------------------------- against the PTY mock


@pytest.mark.integration
def test_a_measurement_on_the_mock_device_runs_through_the_window(
    qtbot, config, gm_adapter, tmp_path, monkeypatch
):
    """Start -> frames reach the timing tab -> the 1 s budget ends the run -> Save is offered."""
    from gmcounter.infrastructure.device_manager import DeviceManager
    from gmcounter.infrastructure.session_journal import SessionJournal
    from gmcounter.ui.controllers import app_controller
    from gmcounter.ui.windows.main_window import MainWindow

    monkeypatch.setattr(
        app_controller,
        "SessionJournal",
        lambda: SessionJournal(session_dir=tmp_path / "journal"),
    )
    manager = DeviceManager()
    manager.device = gm_adapter
    manager.connected = True
    win = MainWindow(config, manager, persist=False)
    qtbot.addWidget(win)
    win.show()

    panel = win.ui.measurementPanel
    win.ui.devicePanel.ui.comboDuration.setCurrentIndex(1)  # 1 s of device time
    with qtbot.waitSignal(win.ctrl.measurement_started, timeout=5000):
        panel.ui.buttonStart.click()
    assert panel.ui.buttonStop.isEnabled() and not panel.ui.buttonStart.isEnabled()
    assert not win.ui.devicePanel.ui.buttonApply.isEnabled()  # settings are locked

    with qtbot.waitSignal(win.ctrl.measurement_stopped, timeout=40_000):
        pass
    timing = win.tabs["gm_timing"]
    assert len(timing.export().rows) > 0
    assert panel.ui.buttonSave.isEnabled() and not panel.ui.buttonStart.isEnabled()
    assert win.ui.devicePanel.ui.buttonApply.isEnabled()
    win.context.save_service.mark_saved()  # do not ask on close
    win.close()
