from datetime import datetime
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gmcounter.core.services import SaveService


def test_create_metadata(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    start = datetime(2023, 1, 1, 12, 0)
    end = datetime(2023, 1, 1, 12, 5)
    meta = manager.create_metadata(start, end, "Autor", "Probe")
    assert meta["dc:creator"] == "Autor"
    assert meta["start_time"] == start.isoformat()
    assert meta["end_time"] == end.isoformat()


def test_save_measurement_creates_files(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    data = [["a", "b"], ["1", "2"]]
    meta = manager.create_metadata(datetime.now(), datetime.now(), "A", "S")
    path = manager.save_measurement("file.csv", data, meta)
    assert path.exists()
    # Sidecar is <stem>_MD.json
    assert (path.parent / (path.stem + "_MD.json")).exists()


def test_unsaved_flag(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    manager.mark_unsaved()
    assert manager.has_unsaved()
    meta = manager.create_metadata(datetime.now(), datetime.now(), "A", "S")
    manager.save_measurement("t.csv", [["i"]], meta)
    manager.mark_saved()
    assert not manager.has_unsaved()


def test_auto_save_measurement(tmp_path):
    manager = SaveService(base_dir=tmp_path, tk_designation="TK47")
    data = [["1", "2"]]
    path = manager.auto_save(
        "Sample",
        "A",
        data,
        datetime.now(),
        datetime.now(),
    )
    assert path and path.exists()
    assert (path.parent / (path.stem + "_MD.json")).exists()
