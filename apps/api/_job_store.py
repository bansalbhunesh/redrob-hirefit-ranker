"""SQLite-backed job store for the Redrob API batch ranking pipeline.

Replaces the previous in-memory ``job_store`` / ``results_store`` dicts.
The SQLite backend survives uvicorn restarts and enables single-file audit
inspection (``sqlite3 data/jobs.db`` in the container).

Schema
------
jobs        — one row per batch job, lifecycle state machine.
results     — one row per ranked candidate payload (JSON blob), ordered by rank.
audit_log   — append-only event log for each job lifecycle transition.

Thread safety
-------------
All writes acquire the internal ``threading.RLock``. SQLite is opened with
``check_same_thread=False``; WAL mode allows concurrent readers without
blocking the writer thread.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path


_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS jobs (
    job_id              TEXT PRIMARY KEY,
    status              TEXT NOT NULL DEFAULT 'queued',
    started_at          TEXT,
    completed_at        TEXT,
    total               INTEGER DEFAULT 0,
    processed           INTEGER DEFAULT 0,
    current_stage       TEXT,
    bm25_backend        TEXT,
    honeypots           INTEGER DEFAULT 0,
    honeypots_in_output INTEGER DEFAULT 0,
    ranked_pool_count   INTEGER DEFAULT 0,
    processing_time_ms  INTEGER DEFAULT 0,
    file_path           TEXT,
    output_path         TEXT,
    error               TEXT
);

CREATE TABLE IF NOT EXISTS results (
    job_id       TEXT NOT NULL,
    rank         INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (job_id, rank)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id  TEXT,
    event   TEXT,
    ts      TEXT,
    detail  TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status  ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_started ON jobs(started_at);
CREATE INDEX IF NOT EXISTS idx_audit_jid    ON audit_log(job_id);
"""


class JobStore:
    """Thread-safe SQLite-backed persistent job and result store.

    Public interface mirrors the old in-memory dict API so callers in
    ``main.py`` need minimal changes.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    # ── internal ──────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(_SCHEMA)

    # ── writes ────────────────────────────────────────────────────────────

    def create_job(
        self,
        job_id: str,
        total: int,
        file_path: str,
        output_path: str,
        started_at: str,
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO jobs
                       (job_id, status, started_at, total, current_stage,
                        file_path, output_path)
                   VALUES (?, 'queued', ?, ?, 'Load', ?, ?)""",
                (job_id, started_at, total, file_path, output_path),
            )
            conn.execute(
                "INSERT INTO audit_log (job_id, event, ts, detail) VALUES (?, 'created', ?, ?)",
                (job_id, started_at, f"total={total}"),
            )

    def update_job(self, job_id: str, **kwargs: object) -> None:
        if not kwargs:
            return
        with self._lock, self._connect() as conn:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            vals = list(kwargs.values()) + [job_id]
            conn.execute(f"UPDATE jobs SET {sets} WHERE job_id = ?", vals)  # nosec B608

    def add_results(self, job_id: str, payloads: list[dict]) -> None:
        with self._lock, self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO results (job_id, rank, payload_json) VALUES (?, ?, ?)",
                [(job_id, i + 1, json.dumps(p)) for i, p in enumerate(payloads)],
            )

    def log_event(self, job_id: str, event: str, detail: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_log (job_id, event, ts, detail) VALUES (?, ?, ?, ?)",
                (job_id, event, datetime.now().isoformat(), detail),
            )

    # ── reads ─────────────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_results(self, job_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM results WHERE job_id = ? ORDER BY rank",
                (job_id,),
            ).fetchall()
            return [json.loads(r[0]) for r in rows]

    def count_active(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('queued', 'processing')"
            ).fetchone()
            return row[0] if row else 0

    def count_stored(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
            return row[0] if row else 0

    def is_writable(self) -> bool:
        """Return True if the DB file is reachable and queryable."""
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1 FROM jobs LIMIT 1")
            return True
        except Exception:
            return False

    # ── maintenance ───────────────────────────────────────────────────────

    def prune(self, max_jobs: int, job_dir: Path) -> None:
        """Delete the oldest jobs (plus their filesystem artifacts) beyond *max_jobs*."""
        with self._lock, self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            if count <= max_jobs:
                return
            to_remove = count - max_jobs
            old_rows = conn.execute(
                "SELECT job_id, file_path FROM jobs ORDER BY started_at ASC LIMIT ?",
                (to_remove,),
            ).fetchall()
            for row in old_rows:
                jid, fpath = row["job_id"], row["file_path"]
                conn.execute("DELETE FROM jobs      WHERE job_id = ?", (jid,))
                conn.execute("DELETE FROM results   WHERE job_id = ?", (jid,))
                conn.execute("DELETE FROM audit_log WHERE job_id = ?", (jid,))
                if fpath:
                    try:
                        job_path = Path(fpath).parent.resolve()
                        root = job_dir.resolve()
                        if job_path != root and root in job_path.parents:
                            shutil.rmtree(job_path, ignore_errors=True)
                    except (OSError, RuntimeError):
                        pass
