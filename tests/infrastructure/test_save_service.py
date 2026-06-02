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
