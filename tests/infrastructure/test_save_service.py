"""Tests for infrastructure/save_service.py — no Qt required."""

import json
from pathlib import Path
import pytest
from gmcounter.core.export import TabExport
from gmcounter.infrastructure.save_service import SaveService


def test_save_creates_csv_and_sidecar(tmp_path):
    svc = SaveService(base_dir=tmp_path)
    export = TabExport(
        filename_hint="test_exp",
        columns=["A", "B"],
        rows=[["1", "2"], ["3", "4"]],
        metadata={"dc:title": "Test"},
    )
    path = svc.save(export)
    assert path.exists()
    assert path.suffix == ".csv"

    sidecar = path.parent / (path.stem + "_MD.json")
    assert sidecar.exists()
    meta = json.loads(sidecar.read_text())
    assert meta["dc:title"] == "Test"


def test_save_csv_content(tmp_path):
    svc = SaveService(base_dir=tmp_path)
    export = TabExport(
        filename_hint="gm",
        columns=["Index", "Value (µs)", "Time"],
        rows=[["1", "100.0", "12:00:00"]],
        metadata={},
    )
    path = svc.save(export)
    lines = path.read_text().splitlines()
    assert lines[0] == "Index,Value (µs),Time"
    assert lines[1] == "1,100.0,12:00:00"


def test_save_index_increments(tmp_path):
    svc = SaveService(base_dir=tmp_path)
    export = TabExport(filename_hint="x", columns=[], rows=[], metadata={})
    p1 = svc.save(export)
    p2 = svc.save(export)
    assert p1 != p2


def test_save_with_tokens(tmp_path):
    svc = SaveService(base_dir=tmp_path)
    export = TabExport(
        filename_hint="gm",
        columns=[],
        rows=[],
        metadata={},
        filename_tokens=["MoATK08"],
    )
    path = svc.save(export)
    assert "MoATK08" in str(path)


def test_write_export_records_file_info_and_update_metadata_extends_it(tmp_path):
    from gmcounter.infrastructure.save_service import update_metadata, write_export

    export = TabExport("gm", ["A"], [["1"], ["2"]], {"dc:title": "T"})
    path = write_export(export, tmp_path / "m.csv")
    sidecar = tmp_path / "m_MD.json"
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    assert meta["file"]["name"] == "m.csv"
    assert meta["file"]["rows"] == 2
    assert len(meta["file"]["sha256"]) == 64
    assert "file" not in export.metadata  # the caller's dict stays untouched

    update_metadata(path, {"detail_files": ["a.csv"]})
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    assert meta["detail_files"] == ["a.csv"]
    assert meta["dc:title"] == "T"


def test_a_series_gets_a_new_folder_named_after_its_file(tmp_path):
    from gmcounter.infrastructure.save_service import session_folder_path

    target = session_folder_path(tmp_path / "serie.csv")
    assert target == tmp_path / "serie" / "serie.csv"
    assert not (tmp_path / "serie").exists()  # only the path is composed


def test_an_earlier_series_folder_is_never_reused(tmp_path):
    from gmcounter.infrastructure.save_service import session_folder_path

    (tmp_path / "serie").mkdir()
    assert (
        session_folder_path(tmp_path / "serie.csv").parent == tmp_path / "serie"
    )  # empty

    (tmp_path / "serie" / "old.csv").write_text("x", encoding="utf-8")
    assert session_folder_path(tmp_path / "serie.csv") == (
        tmp_path / "serie_2" / "serie.csv"
    )
    (tmp_path / "serie_2").mkdir()
    (tmp_path / "serie_2" / "old.csv").write_text("x", encoding="utf-8")
    assert session_folder_path(tmp_path / "serie.csv").parent.name == "serie_3"
