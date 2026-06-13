"""Tests for prune_job_stores() — now backed by the SQLite JobStore.

The test creates a temporary DB, populates it with two jobs (old + new),
patches MAX_STORED_JOBS=1 and JOB_DIR, then verifies that prune_job_stores()
removes the older job's directory and DB row while keeping the newer one.
"""

from pathlib import Path

import pytest

pytest.importorskip("fastapi")


def test_prune_job_stores_removes_old_job_directory(tmp_path, monkeypatch):
    from apps.api import main
    from apps.api._job_store import JobStore

    # Give this test its own isolated DB so it doesn't touch the real one.
    test_store = JobStore(tmp_path / "test_jobs.db")
    monkeypatch.setattr(main, "_store", test_store)
    monkeypatch.setattr(main, "MAX_STORED_JOBS", 1)
    monkeypatch.setattr(main, "JOB_DIR", tmp_path)

    # Prepare two job directories with a real file each.
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    old_file = old_dir / "candidates.jsonl"
    old_file.write_text("{}", encoding="utf-8")

    new_dir = tmp_path / "new"
    new_dir.mkdir()
    new_file = new_dir / "candidates.jsonl"
    new_file.write_text("{}", encoding="utf-8")

    # Insert both jobs into the test store.
    test_store.create_job(
        job_id="old",
        total=10,
        file_path=str(old_file),
        output_path=str(old_dir / "out.csv"),
        started_at="2026-06-08T00:00:00",
    )
    test_store.create_job(
        job_id="new",
        total=10,
        file_path=str(new_file),
        output_path=str(new_dir / "out.csv"),
        started_at="2026-06-09T00:00:00",
    )

    main.prune_job_stores()

    # The old job's DB row and directory should be gone.
    assert test_store.get_job("old") is None, "Old job row should have been pruned"
    assert not old_dir.exists(), "Old job directory should have been deleted"

    # The newer job must be preserved.
    surviving = test_store.get_job("new")
    assert surviving is not None, "New job should survive pruning"
    assert Path(surviving["file_path"]).exists(), "New job's file should still exist"
