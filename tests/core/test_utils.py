"""Tests for core/utils.py — no Qt required."""

import pytest
from gmcounter.core.utils import (
    sanitize_subterm_for_folder,
    create_group_name,
    calculate_statistics,
)


def test_sanitize_short():
    assert sanitize_subterm_for_folder("Mueller") == "Mueller"


def test_sanitize_special_chars():
    result = sanitize_subterm_for_folder("A. Müller!")
    assert "!" not in result
    assert "." not in result


def test_sanitize_too_long():
    long_name = "Very_Long_Subterm_That_Exceeds_The_Limit"
    result = sanitize_subterm_for_folder(long_name, max_length=20)
    assert len(result) <= 20


def test_sanitize_empty():
    assert sanitize_subterm_for_folder("") == ""


def test_calculate_statistics_basic():
    stats = calculate_statistics([10.0, 20.0, 30.0])
    assert stats["count"] == 3
    assert stats["min"] == 10.0
    assert stats["max"] == 30.0
    assert abs(stats["mean"] - 20.0) < 1e-9


def test_calculate_statistics_empty():
    stats = calculate_statistics([])
    assert stats["count"] == 0
    assert stats["mean"] == 0.0


def test_calculate_statistics_single():
    stats = calculate_statistics([42.0])
    assert stats["std"] == 0.0


def test_create_group_name_valid():
    name = create_group_name("A")
    assert "A" in name
    assert len(name) > 3


def test_create_group_name_invalid():
    name = create_group_name("1")
    assert name == "Ungültige Gruppe"
