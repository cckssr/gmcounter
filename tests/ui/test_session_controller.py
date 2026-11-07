"""SessionController: single / sweep / interval sessions without a window (fake tabs and ctrl)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gmcounter.core.export import TabExport
from gmcounter.core.services import SaveService
from gmcounter.ui.controllers.session_controller import SessionController

META = {
    "sample": "E87198",
    "group": "C",
    "detector": "E47438",
    "distance_cm": 12.5,
    "suffix": "run1",
}


class FakeCtrl:
    def __init__(self) -> None:
        self.is_measuring = False
        self.start_ok = True
        self.calls: list[tuple] = []

    def start_measurement(self, total_seconds: int = 0) -> bool:
        self.calls.append(("start", total_seconds))
        return self.start_ok

    def stop_measurement(self) -> None:
        self.calls.append(("stop",))

    def finalize_journal(self) -> None:
        self.calls.append(("finalize",))

    def set_active_tab(self, tab) -> None:
        self.calls.append(("active", tab))


class FakeTiming:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.rows = [["0", "100.0", "t"], ["1", "120.0", "t"]]

    def set_measurement_metadata(self, rad_sample, group, subterm) -> None:
        self.calls.append(("metadata", rad_sample, group, subterm))

    def set_high_speed_autoswitch(self, enabled: bool) -> None:
        self.calls.append(("autoswitch", enabled))

    def on_reset(self) -> None:
        self.calls.append(("reset",))

    def export(self):
        if not self.rows:
            return None
        return TabExport("gm_timing", ["Index", "Value (µs)", "Time"], self.rows, {})


class FakeTab:
    receives_frames = False
    applies_device_voltage_on_start = False

    def __init__(self, kind: str) -> None:
        self.session_kind = kind
        self.calls: list[str] = []
        self.data = False
        self.width_s = 2.0
        self.repeat_count = 5

    def has_data(self) -> bool:
        return self.data

    def has_unsaved_data(self) -> bool:
        return self.data

    def on_measurement_started(self) -> None:
        self.calls.append("started")

    def on_measurement_stopped(self) -> None:
        self.calls.append("stopped")
        self.data = True

    def mark_saved(self) -> None:
        self.calls.append("saved")

    def reset_session(self) -> None:
        self.calls.append("reset")
        self.data = False

    def summary_export(self):
        return TabExport("summary", ["a"], [["1"], ["2"]], {})

    def session_exports(self):
        return [
            TabExport("detail", ["a"], [["1"]], {"p": 1}),
            TabExport("detail", ["a"], [["2"]], {"p": 2}),
        ]

    def session_file_name(self, export, index) -> str:
        return f"m{index + 1:02d}"


class SweepTab(FakeTab):
    def __init__(self) -> None:
        super().__init__("sweep")


class IntervalTab(FakeTab):
    receives_frames = True

    def __init__(self) -> None:
        super().__init__("interval")

    def session_file_name(self, export, index) -> str:
        return f"interval_{index:03d}"


class FakePrompt:
    def __init__(self) -> None:
        self.answer = True
        self.shown: list[tuple[str, str, str]] = []

    def ask(self, text, title) -> bool:
        self.shown.append(("ask", text, title))
        return self.answer

    def warn(self, text, title) -> None:
        self.shown.append(("warn", text, title))

    def info(self, text, title) -> None:
        self.shown.append(("info", text, title))

    def error(self, text, title) -> None:
        self.shown.append(("error", text, title))

    def kinds(self) -> list[str]:
        return [kind for kind, _, _ in self.shown]


class FakeFileDialogs:
    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.cancel = False
        self.calls: list[tuple] = []
        self.exports: list[TabExport] = []

    def manual_save_export(self, parent, export, sample, group, suffix):
        self.calls.append((export.filename_hint, sample, group, suffix))
        self.exports.append(export)
        if self.cancel:
            return None
        path = self.folder / "summary.csv"
        path.write_text("x", encoding="utf-8")
        return path


class Harness:
    """Controller plus fakes; ``events`` records the emitted signals."""

    def __init__(self, config, tmp_path: Path) -> None:
        self.config = config
        self.ctrl = FakeCtrl()
        self.timing = FakeTiming()
        self.save_service = SaveService(base_dir=tmp_path / "base")
        self.dialogs = FakeFileDialogs(tmp_path)
        self.prompt = FakePrompt()
        self.current = FakeTab("single")
        self.duration = 10
        self.applied = 0
        self.session = SessionController(
            config,
            self.ctrl,
            self.timing,
            self.save_service,
            self.dialogs,
            self.prompt,
            current_tab=lambda: self.current,
            duration_s=lambda: self.duration,
            sample_metadata=lambda: dict(META),
            apply_settings=self._apply,
        )
        self.buttons: list[tuple] = []
        self.status: list[tuple] = []
        self.locked: list = []
        self.settings: list[bool] = []
        self.messages: list[tuple] = []
        s = self.session
        s.buttons_changed.connect(lambda *state: self.buttons.append(state))
        s.status_changed.connect(
            lambda text, colour: self.status.append((text, colour))
        )
        s.tabs_locked.connect(self.locked.append)
        s.settings_locked.connect(self.settings.append)
        s.message.connect(lambda text, ms: self.messages.append((text, ms)))

    def _apply(self) -> None:
        self.applied += 1

    def measure(self) -> None:
        """One start / stop cycle as the ctrl signals would deliver it."""
        self.session.start()
        self.session.on_measurement_started()
        self.session.on_measurement_stopped()


@pytest.fixture
def h(qtbot, config, tmp_path) -> Harness:
    return Harness(config, tmp_path)


def _m(h: Harness, key: str, **fmt) -> str:
    return h.config.message(key, **fmt)


# ---------------------------------------------------------------- single sessions


def test_the_initial_state_offers_only_start(h):
    h.session.initial_state()
    assert h.buttons[-1] == (True, False, False, False)
    assert h.status[-1] == (_m(h, "status_ready"), "green")


def test_start_passes_the_duration_and_the_sample_metadata(h):
    h.session.start()
    assert h.ctrl.calls == [("start", 10)]
    assert h.timing.calls == [("metadata", "E87198", "C", "run1")]


def test_start_is_refused_while_unsaved_data_exists(h):
    h.save_service.mark_unsaved()
    h.session.start()
    assert h.ctrl.calls == []
    assert h.prompt.shown == [
        ("warn", _m(h, "save_or_discard_first"), _m(h, "title_warning"))
    ]


def test_the_measurement_lifecycle_drives_buttons_status_and_the_unsaved_flag(h):
    h.session.on_measurement_started()
    assert h.buttons[-1] == (False, True, False, False)
    assert h.settings[-1] is True
    assert h.status[-1] == (_m(h, "status_measuring"), "blue")

    h.session.on_measurement_stopped()
    assert h.buttons[-1] == (False, False, True, True)  # Start waits for save / reset
    assert h.settings[-1] is False
    assert h.status[-1] == (_m(h, "status_stopped"), "yellow")
    assert h.save_service.has_unsaved()


def test_stop_asks_the_ctrl(h):
    h.session.stop()
    assert h.ctrl.calls == [("stop",)]


def test_saving_a_single_measurement_writes_it_and_frees_start(h):
    h.session.set_device_info({"version": "fw1", "openbis": "unknown"})
    h.measure()
    h.session.save()

    assert h.dialogs.calls == [("gm_timing", "E87198", "C", "run1")]
    meta = h.dialogs.exports[0].metadata
    assert meta["detector_code"] == "E47438"
    assert meta["sample_distance_cm"] == 12.5
    assert meta["counter_firmware_version"] == "fw1"
    assert "counter_openbis_code" not in meta  # "unknown" is not written
    assert meta["total_count"] == 2
    assert not h.save_service.has_unsaved()
    assert ("finalize",) in h.ctrl.calls
    assert h.buttons[-1][0] is True and h.buttons[-1][3] is False
    assert h.messages[-1] == (_m(h, "saved"), 3000)


def test_a_cancelled_save_keeps_the_data_unsaved(h):
    h.measure()
    h.dialogs.cancel = True
    h.session.save()
    assert h.save_service.has_unsaved()
    assert h.prompt.shown[-1][0] == "error"


def test_saving_without_unsaved_data_only_informs(h):
    h.session.save()
    assert h.prompt.shown == [("info", _m(h, "no_unsaved_data"), _m(h, "title_info"))]
    assert h.dialogs.calls == []


def test_reset_asks_before_discarding_unsaved_data(h):
    h.measure()
    h.prompt.answer = False
    h.session.reset()
    assert h.save_service.has_unsaved()
    assert ("reset",) not in h.timing.calls

    h.prompt.answer = True
    h.session.reset()
    assert not h.save_service.has_unsaved()
    assert ("reset",) in h.timing.calls
    assert h.status[-1] == (_m(h, "status_ready"), "green")


def test_reset_is_refused_while_measuring(h):
    h.ctrl.is_measuring = True
    h.session.reset()
    assert h.prompt.kinds() == ["warn"]
    assert h.timing.calls == []


def test_closing_asks_only_when_data_is_unsaved(h):
    assert h.session.confirm_close() is True
    assert h.prompt.shown == []
    h.save_service.mark_unsaved()
    h.prompt.answer = False
    assert h.session.confirm_close() is False
    assert h.prompt.shown[-1][1] == _m(h, "unsaved_data_end")


# ---------------------------------------------------------------- sweep sessions


def test_a_sweep_session_locks_the_tabs_and_suppresses_the_autoswitch(h):
    sweep = h.current = SweepTab()
    h.session.start()
    assert h.locked == [sweep]
    assert ("autoswitch", False) in h.timing.calls
    assert h.session.session_tab is sweep
    assert h.ctrl.calls == [("start", 10)]


def test_an_infinite_sweep_asks_once_at_the_first_point(h):
    h.current = SweepTab()
    h.duration = 0
    h.prompt.answer = False
    h.session.start()
    assert h.prompt.kinds() == ["ask"] and h.ctrl.calls == [] and h.locked == []

    h.prompt.answer = True
    h.session.start()
    assert h.ctrl.calls == [("start", 0)]
    h.session.on_measurement_stopped()
    h.session.start()  # second point of the session: no question
    assert h.prompt.kinds() == ["ask", "ask"]
    assert h.ctrl.calls == [("start", 0), ("start", 0)]


def test_a_sweep_forwards_the_lifecycle_and_allows_the_next_point(h):
    sweep = h.current = SweepTab()
    h.measure()
    assert sweep.calls == ["started", "stopped"]
    assert h.buttons[-1] == (True, False, True, True)  # Start stays enabled
    assert not h.save_service.has_unsaved()  # unsaved state is tracked by the sweep tab
    h.measure()
    assert sweep.calls == ["started", "stopped"] * 2
    assert h.locked == [sweep]  # locked once per session


def test_a_voltage_sweep_applies_the_device_settings_on_every_start(h):
    sweep = h.current = SweepTab()
    sweep.applies_device_voltage_on_start = True
    h.measure()
    h.measure()
    assert h.applied == 2


def test_saving_a_sweep_writes_the_summary_and_named_detail_files(h, tmp_path):
    sweep = h.current = SweepTab()
    h.measure()
    h.session.save()

    assert sorted(p.name for p in tmp_path.glob("summary_*.csv")) == [
        "summary_m01.csv",
        "summary_m02.csv",
    ]
    assert h.dialogs.exports[0].metadata["sample_distance_cm"] == 12.5
    assert h.dialogs.exports[0].metadata["detector_code"] == "E47438"
    assert sweep.calls[-2:] == ["saved", "reset"]
    assert h.session.session_tab is None
    assert h.locked == [sweep, None]
    assert ("reset",) in h.timing.calls
    assert ("autoswitch", True) in h.timing.calls
    assert ("finalize",) in h.ctrl.calls
    assert h.messages[-1] == (_m(h, "summary_saved_sweep", ok=2, total=2), 5000)
    assert h.buttons[-1][0] is True and h.buttons[-1][3] is False


def test_a_cancelled_sweep_save_keeps_the_session(h):
    sweep = h.current = SweepTab()
    h.measure()
    h.dialogs.cancel = True
    h.session.save()
    assert h.session.session_tab is sweep
    assert "reset" not in sweep.calls


def test_resetting_a_sweep_discards_it_after_confirmation(h):
    sweep = h.current = SweepTab()
    h.measure()
    h.prompt.answer = False
    h.session.reset()
    assert h.session.session_tab is sweep

    h.prompt.answer = True
    h.session.reset()
    assert h.session.session_tab is None
    assert sweep.calls[-1] == "reset"
    assert h.locked == [sweep, None]
    assert ("reset",) in h.timing.calls


def test_closing_during_a_sweep_with_unsaved_points_asks(h):
    h.current = SweepTab()
    h.measure()
    h.prompt.answer = False
    assert h.session.confirm_close() is False


def test_a_failed_first_start_does_not_leave_the_session_locked(h):
    h.current = SweepTab()
    h.ctrl.start_ok = False
    h.session.start()
    assert h.session.session_tab is None
    assert h.locked == [h.locked[0], None]
    assert ("autoswitch", True) in h.timing.calls


# ---------------------------------------------------------------- interval sessions


def test_an_interval_session_runs_for_width_times_repeats(h):
    interval = h.current = IntervalTab()
    h.session.start()
    assert h.ctrl.calls == [("start", 10)]  # 2.0 s x 5
    assert h.locked == [interval]
    assert ("autoswitch", False) in h.timing.calls


def test_an_interval_tab_gets_its_lifecycle_from_the_ctrl_not_the_session(h):
    interval = h.current = IntervalTab()
    h.measure()
    assert interval.calls == []  # the ctrl delivers these to the frame-receiving tab
    assert h.buttons[-1] == (False, False, True, True)


def test_saving_an_interval_session_names_the_files_after_the_intervals(h, tmp_path):
    interval = h.current = IntervalTab()
    h.measure()
    interval.data = True  # the binned frames, delivered by the ctrl
    h.session.save()

    assert sorted(p.name for p in tmp_path.glob("summary_*.csv")) == [
        "summary_interval_000.csv",
        "summary_interval_001.csv",
    ]
    assert "sample_distance_cm" not in h.dialogs.exports[0].metadata
    assert interval.calls[-2:] == ["saved", "reset"]
    assert ("reset",) not in h.timing.calls  # the timing tab was not used
    assert h.messages[-1] == (_m(h, "summary_saved_interval", ok=2, total=2), 5000)
    assert h.locked[-1] is None


def test_resetting_an_interval_session_unlocks_without_touching_the_timing_tab(h):
    interval = h.current = IntervalTab()
    h.measure()
    interval.data = True
    h.session.reset()
    assert h.session.session_tab is None
    assert interval.calls[-1] == "reset"
    assert ("reset",) not in h.timing.calls


# ---------------------------------------------------------------- routing and connection


def test_frames_go_to_the_selected_frame_tab_else_to_the_timing_tab(h):
    interval, sweep = IntervalTab(), SweepTab()
    h.session.on_tab_changed(interval)
    h.session.on_tab_changed(sweep)
    h.session.on_tab_changed(None)
    assert h.ctrl.calls == [("active", interval), ("active", h.timing)]


def test_the_timing_tab_does_not_steal_the_frames_during_an_interval_session(h):
    h.current = IntervalTab()
    h.session.start()
    h.ctrl.calls.clear()
    h.session.on_tab_changed(SweepTab())
    assert h.ctrl.calls == []


def test_a_lost_connection_shows_an_error_and_a_red_status(h):
    h.session.on_connection_lost()
    assert h.status[-1] == (_m(h, "status_disconnected"), "red")
    assert h.prompt.shown == [
        ("error", _m(h, "connection_lost_terminal"), _m(h, "title_connection_error"))
    ]


def test_a_reconnect_enables_start_again(h):
    h.session.on_reconnect_succeeded()
    assert h.buttons[-1][0] is True
    assert h.status[-1] == (_m(h, "status_connected"), "green")
