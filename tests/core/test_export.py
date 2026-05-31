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
    assert export.columns == ["Index", "Value (µs)", "Time"]


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
