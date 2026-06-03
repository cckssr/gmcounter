# Layer: infrastructure — crash-safe measurement journaling (§5).
#
# Writes an append-only journal to:
#   ~/.gmcounter/sessions/<iso-timestamp>/journal.csv
#
# Each row: epoch_s, kind, index, value_us
# Special rows: kind="gap" on reconnect, kind="finalized" on clean save.
# Startup scans for orphan (unfinalized) journals and offers export.

from __future__ import annotations

import csv
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)

JOURNAL_DIR = Path.home() / ".gmcounter" / "sessions"
FSYNC_INTERVAL_S = 1.0


class SessionJournal:
    """Append-only on-disk journal for one measurement session.

    Thread-safe: a background flush loop calls fsync every ~1 s.
    """

    def __init__(self, session_dir: Optional[Path] = None) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._dir = session_dir or (JOURNAL_DIR / ts)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "journal.csv"
        self._fh = open(self._path, "a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fh)
        self._lock = threading.Lock()
        self._finalized = False

        # Write header if new file
        if self._path.stat().st_size == 0:
            self._writer.writerow(["epoch_s", "kind", "index", "value_us"])

        # Background fsync
        self._closed = False

        self._stop_event = threading.Event()
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

        _log.info("SessionJournal opened: %s", self._path)

    # ------------------------------------------------------------------
    # Public API

    def record(self, index: int, value_us: float) -> None:
        """Append one data point row."""
        with self._lock:
            if self._closed:
                return
            self._writer.writerow([time.time(), "data", index, value_us])

    def mark_gap(self) -> None:
        """Mark a reconnect gap in the journal."""
        with self._lock:
            self._writer.writerow([time.time(), "gap", "", ""])
            self._fh.flush()
        _log.info("Journal gap marker written")

    def finalize(self) -> None:
        """Mark the journal as cleanly saved and stop."""
        if self._finalized:
            return
        with self._lock:
            self._writer.writerow([time.time(), "finalized", "", ""])
            self._fh.flush()
            try:
                os.fsync(self._fh.fileno())
            except OSError:
                pass
        self._finalized = True
        self._stop_event.set()
        _log.info("Journal finalized: %s", self._path)

    def close(self) -> None:
        with self._lock:
            self._closed = True
        self._stop_event.set()
        try:
            self._fh.flush()
            os.fsync(self._fh.fileno())
        except OSError:
            pass
        self._fh.close()

    @property
    def path(self) -> Path:
        return self._path

    # ------------------------------------------------------------------
    # Internal

    def _flush_loop(self) -> None:
        while not self._stop_event.wait(timeout=FSYNC_INTERVAL_S):
            with self._lock:
                try:
                    self._fh.flush()
                    os.fsync(self._fh.fileno())
                except OSError:
                    pass


def find_orphan_journals() -> list[Path]:
    """Return paths to unfinalized journals from today's sessions."""
    if not JOURNAL_DIR.exists():
        return []

    today = datetime.now().strftime("%Y%m%d")
    orphans: list[Path] = []
    for session_dir in sorted(JOURNAL_DIR.iterdir()):
        if not session_dir.name.startswith(today):
            continue
        journal = session_dir / "journal.csv"
        if not journal.exists():
            continue
        try:
            with open(journal, "r", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
            kinds = {row[1] for row in rows[1:] if len(row) >= 2}
            if "finalized" not in kinds and len(rows) > 1:
                orphans.append(journal)
        except Exception as exc:
            _log.error("Error reading journal %s: %s", journal, exc)

    return orphans
