"""Tests for core/export.py — no Qt required."""

from datetime import datetime
from pathlib import Path
from gmcounter.core.models import MeasurementPoint, MeasurementSession
from gmcounter.core.export import TabExport, build_gm_tab_export, compose_save_path


def _make_session() -> MeasurementSession:
    return MeasurementSession(
        points=[
            MeasurementPoint(1, 123.0, "12:00:00.000"),
            MeasurementPoint(2, 456.0, "12:00:00.100"),
        ],
        start_time=datetime(2024, 6, 1, 12, 0, 0),
        end_time=datetime(2024, 6, 1, 12, 0, 5),
        radioactive_sample="Ba133",
        subterm="Test",
        group="A",
    )


def test_build_gm_tab_export_columns():
    session = _make_session()
    export = build_gm_tab_export(session, tk_designation="TK08")
    assert export.columns == ["Index", "Value (µs)", "Time", "Duration (s)"]


def test_build_gm_tab_export_rows():
    session = _make_session()
    export = build_gm_tab_export(session)
    assert len(export.rows) == 2
    assert export.rows[0][0] == "1"
    assert export.rows[0][1] == "123.0"


def test_build_gm_tab_export_metadata():
    session = _make_session()
    export = build_gm_tab_export(session, tk_designation="TK08")
    assert export.metadata["radioactive_sample"] == "Ba133"
    assert "dc:date" in export.metadata
    assert "start_time" in export.metadata


def test_build_gm_tab_export_extra_metadata():
    session = _make_session()
    export = build_gm_tab_export(session, extra_metadata={"gui_version": "1.2.3"})
    assert export.metadata["gui_version"] == "1.2.3"


def test_compose_save_path_with_tokens():
    export = TabExport(
        filename_hint="gm_timing",
        columns=[],
        rows=[],
        metadata={},
        filename_tokens=["MoATK08-Test"],
    )
    path = compose_save_path(export, Path("/data"), index=1)
    assert "MoATK08-Test" in str(path)
    assert path.suffix == ".csv"


def test_compose_save_path_no_tokens():
    export = TabExport(
        filename_hint="gm_timing",
        columns=[],
        rows=[],
        metadata={},
    )
    path = compose_save_path(export, Path("/data"), index=3)
    assert path.parent == Path("/data")
    assert "03-gm_timing" in path.name


def test_tab_export_round_trip():
    session = _make_session()
    export = build_gm_tab_export(session, tk_designation="TK08")
    # Verify all rows can be written as CSV (all strings)
    for row in export.rows:
        for cell in row:
            assert isinstance(cell, str)


def test_raw_columns_are_shared_by_every_export():
    from gmcounter.core.export import RAW_COLUMNS, raw_rows

    assert list(RAW_COLUMNS) == build_gm_tab_export(_make_session()).columns
    assert raw_rows([(3, 1.5, "t")], 2.0) == [["3", "1.5", "t", "2.000"]]


def test_gm_export_metadata_has_duration_count_and_statistics():
    meta = build_gm_tab_export(_make_session()).metadata
    assert meta["duration_s"] == 5.0
    assert meta["total_count"] == 2
    assert meta["rate_hz"] == 0.4
    assert meta["statistics_us"]["mean"] == 289.5
    assert meta["columns"] == ["Index", "Value (µs)", "Time", "Duration (s)"]


def test_merge_missing_keeps_existing_values():
    from gmcounter.core.export import merge_missing

    target = {"a": 1}
    assert merge_missing(target, {"a": 2, "b": 3}) == {"a": 1, "b": 3}


def test_build_run_info_snapshots_settings_and_device():
    from gmcounter.core.export import build_run_info

    info = build_run_info(
        experiment="distance_law",
        sample={"detector": "E1", "distance_cm": 4.0},
        device_settings={"voltage": 500, "repeat": True, "auto_query": False},
        voltage_readback_v=498.0,
        target_duration_s=10,
        device_info={"version": "1.2", "openbis": "OB-1"},
        port="COM8",
        baudrate=1000000,
        gui_version="3.0.0",
    )
    assert info["settings"] == {
        "gm_voltage_set_v": 500,
        "gm_voltage_readback_v": 498.0,
        "target_duration_s": 10,
        "count_mode": "repeat",
        "query_mode": "manual",
        "sample_distance_cm": 4.0,
    }
    assert info["device"] == {
        "firmware_version": "1.2",
        "openbis_code": "OB-1",
        "port": "COM8",
        "baudrate": 1000000,
    }
    assert info["detector_code"] == "E1"
    assert info["counter_firmware_version"] == "1.2"  # legacy flat key


def test_every_row_carries_the_duration_of_the_run():
    export = build_gm_tab_export(_make_session())
    assert [row[3] for row in export.rows] == ["5.000", "5.000"]


def test_the_device_time_replaces_the_clock_in_the_duration_column():
    export = build_gm_tab_export(
        _make_session(), extra_metadata={"timing": {"device_time_s": 4.25}}
    )
    assert {row[3] for row in export.rows} == {"4.250"}
    assert export.metadata["duration_s"] == 4.25
