import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gmcounter.core.services import SaveService


def test_filename_auto_basic(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    rad_sample = "TestSample"
    result = manager.generate_filename(rad_sample, "A")
    assert result != ""
    # Filename part (after last /) must end with -TestSample.csv
    filename = result.split("/")[-1]
    assert filename.endswith(f"-{rad_sample}.csv")


def test_filename_auto_with_suffix(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    result = manager.generate_filename("Sample", "A", suffix="run1")
    filename = result.split("/")[-1]
    assert filename.endswith("-Sample-run1.csv")


def test_filename_auto_with_suffix_dash(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    result = manager.generate_filename("Sample", "A", suffix="-run2")
    filename = result.split("/")[-1]
    assert filename.endswith("-Sample-run2.csv")


def test_filename_auto_empty_sample(tmp_path):
    manager = SaveService(base_dir=tmp_path)
    result = manager.generate_filename("", "A")
    assert result == ""
