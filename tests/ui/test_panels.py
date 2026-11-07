"""The dock panels build from their forms, show the configured strings and emit intents."""

from __future__ import annotations

import pytest

from gmcounter.infrastructure.config import AppConfig
from gmcounter.ui.panels.device_panel import DevicePanel
from gmcounter.ui.panels.device_status_panel import DeviceStatusPanel
from gmcounter.ui.panels.event_log_panel import EventLogPanel
from gmcounter.ui.panels.measurement_panel import MeasurementPanel
from gmcounter.ui.panels.readout_panel import ReadoutPanel
from gmcounter.ui.panels.sample_panel import SamplePanel

TITLED_PANELS = {
    DevicePanel: "device_panel",
    SamplePanel: "sample_panel",
    MeasurementPanel: "measurement_panel",
    ReadoutPanel: "readout_panel",
    DeviceStatusPanel: "device_status_panel",
}


def _build(qtbot, cls, config: AppConfig):
    panel = cls()
    qtbot.addWidget(panel)
    panel.apply_config(config)
    return panel


@pytest.mark.parametrize("cls", TITLED_PANELS)
def test_each_panel_shows_its_configured_title(qtbot, config, cls) -> None:
    panel = _build(qtbot, cls, config)
    expected = config.section("ui")[TITLED_PANELS[cls]]["self"]
    assert panel.title() == expected != ""  # "&&" in a title is a literal "&"


def test_the_event_log_panel_builds_with_a_german_clear_button(qtbot, config) -> None:
    panel = _build(qtbot, EventLogPanel, config)
    assert panel.ui.buttonClear.text() == "Leeren"


def test_the_duration_combo_lists_the_configured_presets(qtbot, config) -> None:
    panel = _build(qtbot, DevicePanel, config)
    combo = panel.ui.comboDuration
    assert [combo.itemText(i) for i in range(combo.count())] == config.get(
        "ui.device_panel.combo_duration_items"
    )


@pytest.mark.parametrize(
    ("index", "seconds"), [(0, 0), (1, 1), (2, 10), (3, 60), (4, 100), (5, 300)]
)
def test_a_preset_duration_maps_to_its_seconds(qtbot, config, index, seconds) -> None:
    panel = _build(qtbot, DevicePanel, config)
    panel.ui.comboDuration.setCurrentIndex(index)
    assert panel.duration_s() == seconds


@pytest.mark.parametrize(
    ("text", "seconds"),
    [("45", 45), ("2,6", 3), ("-5", 0), ("abc", 0), ("", 0)],
)
def test_a_custom_duration_is_parsed_or_falls_back_to_unlimited(
    qtbot, config, text, seconds
) -> None:
    panel = _build(qtbot, DevicePanel, config)
    panel.ui.comboDuration.setCurrentIndex(-1)
    panel.ui.comboDuration.setEditText(text)
    assert panel.duration_s() == seconds


def test_device_settings_reflect_the_controls(qtbot, config) -> None:
    panel = _build(qtbot, DevicePanel, config)
    panel.ui.radioModeRepeat.setChecked(True)
    panel.ui.radioQueryAuto.setChecked(True)
    panel.ui.spinVoltage.setValue(420)
    assert panel.settings() == {"voltage": 420, "repeat": True, "auto_query": True}


def test_the_count_and_query_mode_radios_are_independent(qtbot, config) -> None:
    panel = _build(qtbot, DevicePanel, config)
    panel.ui.radioModeRepeat.setChecked(True)
    assert panel.ui.radioQueryManual.isChecked()
    assert not panel.ui.radioModeSingle.isChecked()


def test_the_dial_and_the_spin_box_follow_each_other(qtbot, config) -> None:
    panel = _build(qtbot, DevicePanel, config)
    panel.ui.dialVoltage.setValue(400)
    assert panel.ui.spinVoltage.value() == 400
    panel.ui.spinVoltage.setValue(450)
    assert panel.ui.dialVoltage.value() == 450


def test_a_voltage_above_the_threshold_warns_and_a_lower_one_clears_it(
    qtbot, config
) -> None:
    panel = _build(qtbot, DevicePanel, config)
    threshold = config.get("gm_counter.voltage_warning_threshold")
    with qtbot.waitSignal(panel.voltage_warning) as blocker:
        panel.ui.spinVoltage.setValue(threshold + 10)
    assert blocker.args == [threshold + 10]
    assert panel.ui.spinVoltage.styleSheet() != ""
    panel.ui.spinVoltage.setValue(threshold - 10)
    assert panel.ui.spinVoltage.styleSheet() == ""


def test_the_apply_button_requests_applying_the_settings(qtbot, config) -> None:
    panel = _build(qtbot, DevicePanel, config)
    with qtbot.waitSignal(panel.apply_requested):
        panel.ui.buttonApply.click()


def test_locking_the_device_panel_disables_its_controls(qtbot, config) -> None:
    panel = _build(qtbot, DevicePanel, config)
    panel.set_locked(True)
    assert not panel.ui.buttonApply.isEnabled()
    assert not panel.ui.comboDuration.isEnabled()
    panel.set_locked(False)
    assert panel.ui.buttonApply.isEnabled()


def test_the_suffix_row_is_hidden_until_auto_save_is_checked(qtbot, config) -> None:
    panel = _build(qtbot, SamplePanel, config)
    panel.show()
    assert not panel.ui.editSuffix.isVisible()
    assert not panel.ui.labelSuffix.isVisible()
    panel.ui.checkAutoSave.setChecked(True)
    assert panel.ui.editSuffix.isVisible()
    assert panel.ui.labelSuffix.isVisible()
    panel.ui.checkAutoSave.setChecked(False)
    assert not panel.ui.editSuffix.isVisible()


def test_the_sample_combos_offer_the_configured_lists_without_a_selection(
    qtbot, config
) -> None:
    panel = _build(qtbot, SamplePanel, config)
    assert panel.ui.comboSample.count() == len(config.get("radioactive_samples"))
    assert panel.ui.comboDetector.count() == len(config.get("detektor_codes"))
    assert panel.ui.comboGroup.count() == 24
    assert panel.ui.comboSample.currentIndex() == -1
    assert panel.metadata()["group"] == ""


def test_the_sample_completer_matches_anywhere_in_the_text(qtbot, config) -> None:
    from PySide6.QtCore import Qt

    panel = _build(qtbot, SamplePanel, config)
    completer = panel.ui.comboDetector.completer()
    assert completer.filterMode() == Qt.MatchFlag.MatchContains
    assert completer.caseSensitivity() == Qt.CaseSensitivity.CaseInsensitive


def test_sample_metadata_is_collected_and_stripped(qtbot, config) -> None:
    panel = _build(qtbot, SamplePanel, config)
    panel.ui.comboSample.setCurrentIndex(1)
    panel.ui.comboGroup.setCurrentText("C")
    panel.ui.comboDetector.setCurrentText(" E47438 ")
    panel.ui.spinDistance.setValue(2.5)
    panel.ui.editSuffix.setText("  run1 ")
    meta = panel.metadata()
    assert meta == {
        "sample": config.get("radioactive_samples")[1],
        "group": "C",
        "detector": "E47438",
        "distance_cm": 2.5,
        "suffix": "run1",
    }


def test_hiding_the_distance_row_resets_the_distance(qtbot, config) -> None:
    panel = _build(qtbot, SamplePanel, config)
    panel.show()
    panel.ui.spinDistance.setValue(3.0)
    panel.set_distance_visible(False)
    assert not panel.ui.spinDistance.isVisible()
    assert panel.metadata()["distance_cm"] == 0.0


def test_the_measurement_buttons_emit_their_intent_signals(qtbot, config) -> None:
    panel = _build(qtbot, MeasurementPanel, config)
    panel.set_state(start=True, stop=True, reset=True, save=True)
    for button, signal in (
        (panel.ui.buttonStart, panel.start_requested),
        (panel.ui.buttonStop, panel.stop_requested),
        (panel.ui.buttonReset, panel.reset_requested),
        (panel.ui.buttonSave, panel.save_requested),
    ):
        with qtbot.waitSignal(signal):
            button.click()


def test_set_state_enables_exactly_the_given_buttons(qtbot, config) -> None:
    panel = _build(qtbot, MeasurementPanel, config)
    panel.set_state(start=False, stop=True, reset=False, save=True)
    ui = panel.ui
    assert [
        b.isEnabled()
        for b in (ui.buttonStart, ui.buttonStop, ui.buttonReset, ui.buttonSave)
    ] == [
        False,
        True,
        False,
        True,
    ]


def test_start_and_stop_have_function_key_shortcuts(qtbot, config) -> None:
    panel = _build(qtbot, MeasurementPanel, config)
    assert panel.ui.buttonStart.shortcut().toString() == "F5"
    assert panel.ui.buttonStop.shortcut().toString() == "F6"


def test_progress_shows_elapsed_time_and_a_bounded_bar(qtbot, config) -> None:
    panel = _build(qtbot, MeasurementPanel, config)
    panel.set_progress(5, 60)
    assert panel.ui.valueElapsed.text() == "5 s"
    assert (
        panel.ui.progressMeasurement.value(),
        panel.ui.progressMeasurement.maximum(),
    ) == (5, 60)


def test_an_unlimited_measurement_shows_a_busy_bar_until_it_is_cleared(
    qtbot, config
) -> None:
    panel = _build(qtbot, MeasurementPanel, config)
    panel.set_progress(5, 0)
    assert panel.ui.progressMeasurement.maximum() == 0
    panel.clear_progress()
    bar = panel.ui.progressMeasurement
    assert (bar.value(), bar.maximum()) == (0, 1)
    assert panel.ui.valueElapsed.text() == "0 s"


def test_the_high_speed_indicator_toggles_led_and_text(qtbot, config) -> None:
    panel = _build(qtbot, ReadoutPanel, config)
    assert panel.ui.ledHighSpeed.state == "off"
    assert panel.ui.valueHighSpeed.text() == "inaktiv"
    panel.set_high_speed(True)
    assert panel.ui.ledHighSpeed.state == "busy"
    assert panel.ui.valueHighSpeed.text() == "aktiv"
    panel.set_high_speed(False)
    assert panel.ui.ledHighSpeed.state == "off"
    assert panel.ui.valueHighSpeed.text() == "inaktiv"


def test_the_readout_displays_count_rate_and_last_count(qtbot, config) -> None:
    panel = _build(qtbot, ReadoutPanel, config)
    panel.set_count(42)
    panel.set_rate(12.5)
    panel.set_last_count(7)
    assert panel.ui.lcdCount.intValue() == 42
    assert panel.ui.lcdRate.value() == 12.5
    assert panel.ui.lcdLastCount.intValue() == 7


def test_the_device_state_updates_the_readback(qtbot, config) -> None:
    panel = _build(qtbot, DeviceStatusPanel, config)
    panel.set_device_state({"voltage": 500, "counting_time": 10, "repeat": True})
    assert panel.ui.lcdVoltage.intValue() == 500
    assert panel.ui.lcdDuration.intValue() == 10
    assert panel.ui.valueMode.text() == "Wiederholung"
    panel.set_device_state({"voltage": 500, "counting_time": 10, "repeat": False})
    assert panel.ui.valueMode.text() == "Einzel"


def test_a_device_state_with_an_error_is_ignored(qtbot, config) -> None:
    panel = _build(qtbot, DeviceStatusPanel, config)
    panel.set_device_state({"voltage": 500, "counting_time": 10, "repeat": True})
    panel.set_device_state({"error": "corrupt", "voltage": 0, "counting_time": 0})
    assert panel.ui.lcdVoltage.intValue() == 500
    assert panel.ui.lcdDuration.intValue() == 10
    assert panel.ui.valueMode.text() == "Wiederholung"


@pytest.mark.parametrize(
    ("colour", "state"),
    [
        ("green", "ok"),
        ("blue", "busy"),
        ("yellow", "busy"),
        ("red", "error"),
        ("white", "off"),
    ],
)
def test_the_status_colour_selects_the_led_state(qtbot, config, colour, state) -> None:
    panel = _build(qtbot, DeviceStatusPanel, config)
    panel.set_status("Text", colour)
    assert panel.ui.ledStatus.state == state
    assert panel.ui.valueStatus.text() == "Text"


def test_the_device_info_shows_firmware_and_openbis_code(qtbot, config) -> None:
    panel = _build(qtbot, DeviceStatusPanel, config)
    panel.set_device_info({"version": "1.2.3", "openbis": "ABC"})
    assert panel.ui.valueFirmware.text() == "1.2.3"
    assert panel.ui.valueOpenbis.text() == "ABC"


def test_the_event_log_appends_timestamped_lines_and_clears(qtbot, config) -> None:
    import re

    panel = _build(qtbot, EventLogPanel, config)
    panel.append("Messung läuft", "green")
    panel.append("<b>no html</b>")
    text = panel.ui.editLog.toPlainText()
    lines = text.splitlines()
    assert re.fullmatch(r"\[\d\d:\d\d:\d\d\] Messung läuft", lines[0])
    assert lines[1].endswith("<b>no html</b>")
    panel.ui.buttonClear.click()
    assert panel.ui.editLog.toPlainText() == ""
