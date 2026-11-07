"""The main window builds from its forms with the German strings of config.json."""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QAbstractButton, QGroupBox, QLabel


def test_window_constructs_with_german_strings(window):
    ui = window.ui
    assert window.windowTitle() == "GM-Counter"
    assert ui.actionToggleControls.text() == "Steuerung"
    assert ui.actionFullScreen.text() == "Vollbild"
    assert ui.devicePanel.title() == "Gerätesteuerung"
    assert ui.measurementPanel.ui.buttonStart.text() == "Start"
    assert ui.readoutPanel.ui.labelHighSpeed.text() == "High-Speed-Modus"
    assert ui.deviceStatusPanel.ui.valueStatus.text() == "Bereit"
    assert ui.eventLogPanel.ui.buttonClear.text() == "Leeren"
    assert ui.dockLog.windowTitle() == "Ereignisprotokoll"


def test_every_string_key_resolves_to_a_widget(window, config):
    """A typo in config.json must not silently leave a widget untranslated."""
    forms = {
        "main_window": window,
        "device_panel": window.ui.devicePanel,
        "sample_panel": window.ui.samplePanel,
        "measurement_panel": window.ui.measurementPanel,
        "readout_panel": window.ui.readoutPanel,
        "device_status_panel": window.ui.deviceStatusPanel,
        "event_log_panel": window.ui.eventLogPanel,
        "timing_tab": window.tabs["gm_timing"],
        "sweep_tab": window.tabs["distance_law"],
        "interval_tab": window.tabs["interval_repeat"],
    }
    for form, root in forms.items():
        for key in config.section("ui")[form]:
            name = key.partition("@")[0]
            if "_" in name or name == "self":
                continue
            assert root.findChild(QObject, name) is not None, f"{form}.{key}"


def test_no_text_left_empty_or_raw_key(window):
    for widget in window.findChildren(QAbstractButton):
        if widget.objectName().startswith(("button", "check", "radio")):
            assert widget.text() and "." not in widget.text(), widget.objectName()
    for group in window.findChildren(QGroupBox):
        assert group.title()
    for label in window.findChildren(QLabel):
        # a tab may hide labels it does not need (explicitly hidden, so not visible to the window)
        if label.objectName().startswith("label") and label.isVisibleTo(window):
            assert label.text(), label.objectName()


def test_sweep_tabs_show_their_own_texts(window):
    distance = window.tabs["distance_law"].ui
    voltage = window.tabs["voltage_response"].ui
    assert distance.labelParam.text() == "Probenabstand"
    assert distance.spinParam.suffix() == " cm"
    assert not distance.labelHint.isVisibleTo(window.tabs["distance_law"])
    assert (
        voltage.labelHint.text() == "Spannung wird in der Gerätesteuerung eingestellt."
    )
    assert not voltage.spinParam.isVisibleTo(window.tabs["voltage_response"])
    assert not voltage.labelParam.isVisibleTo(window.tabs["voltage_response"])


def test_plot_labels_and_table_headers_come_from_config(window, config):
    timing = window.tabs["gm_timing"]
    assert timing.ui.timePlot.getAxis("bottom").labelText == "Ereignis k"
    assert timing.ui.histogramPlot.getAxis("left").labelText == "Anzahl Ereignisse"
    model = timing.ui.tableEvents.model()
    assert [
        model.headerData(i, Qt.Orientation.Horizontal)
        for i in range(model.columnCount())
    ] == config.get("ui.timing_tab.table_events_headers")
    sweep = window.tabs["voltage_response"]
    assert sweep.ui.sweepPlot.getAxis("bottom").labelText == "Spannung (V)"
    assert (
        sweep.ui.tableSummary.model().headerData(0, Qt.Orientation.Horizontal)
        == "Spannung (V)"
    )
