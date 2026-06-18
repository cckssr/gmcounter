"""Tests for infrastructure.session_journal.SessionJournal and find_orphan_journals."""

import csv
import time
from pathlib import Path

import pytest

from gmcounter.infrastructure.session_journal import (
    SessionJournal,
    find_orphan_journals,
)


def test_journal_creates_csv_with_header(tmp_path):
    journal = SessionJournal(session_dir=tmp_path / "sess")
    journal.close()
    rows = list(csv.reader(open(journal.path, encoding="utf-8")))
    assert rows[0] == ["epoch_s", "kind", "index", "value_us"]


def test_journal_record_appends_row(tmp_path):
    journal = SessionJournal(session_dir=tmp_path / "sess")
    journal.record(1, 123.5)
    journal.record(2, 456.0)
    journal.close()
    rows = list(csv.reader(open(journal.path, encoding="utf-8")))
    # rows[0] = header; rows[1], rows[2] = data
    assert len(rows) == 3
    assert rows[1][1] == "data"
    assert rows[1][2] == "1"
    assert float(rows[1][3]) == pytest.approx(123.5)


def test_journal_mark_gap(tmp_path):
    journal = SessionJournal(session_dir=tmp_path / "sess")
    journal.mark_gap()
    journal.close()
    rows = list(csv.reader(open(journal.path, encoding="utf-8")))
    kinds = [r[1] for r in rows[1:]]
    assert "gap" in kinds


def test_journal_finalize_writes_marker(tmp_path):
    journal = SessionJournal(session_dir=tmp_path / "sess")
    journal.record(1, 10.0)
    journal.finalize()
    rows = list(csv.reader(open(journal.path, encoding="utf-8")))
    kinds = [r[1] for r in rows[1:]]
    assert "finalized" in kinds


def test_journal_path_property(tmp_path):
    journal = SessionJournal(session_dir=tmp_path / "sess")
    assert journal.path == tmp_path / "sess" / "journal.csv"
    journal.close()


def test_find_orphan_journals_empty_when_no_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "gmcounter.infrastructure.session_journal.JOURNAL_DIR", tmp_path / "sessions"
    )
    assert find_orphan_journals() == []


def test_find_orphan_journals_detects_unfinalized(tmp_path, monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(
        "gmcounter.infrastructure.session_journal.JOURNAL_DIR", tmp_path / "sessions"
    )
    today = datetime.now().strftime("%Y%m%d")
    sess_dir = tmp_path / "sessions" / f"{today}_120000"
    sess_dir.mkdir(parents=True)
    journal = SessionJournal(session_dir=sess_dir)
    journal.record(1, 42.0)
    journal.close()

    orphans = find_orphan_journals()
    assert len(orphans) == 1
    assert orphans[0] == journal.path


def test_find_orphan_journals_ignores_finalized(tmp_path, monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(
        "gmcounter.infrastructure.session_journal.JOURNAL_DIR", tmp_path / "sessions"
    )
    today = datetime.now().strftime("%Y%m%d")
    sess_dir = tmp_path / "sessions" / f"{today}_130000"
    journal = SessionJournal(session_dir=sess_dir)
    journal.record(1, 10.0)
    journal.finalize()

    orphans = find_orphan_journals()
    assert orphans == []
