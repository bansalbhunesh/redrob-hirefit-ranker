from pathlib import Path

import pytest

pytest.importorskip("fastapi")


def test_prune_job_stores_removes_old_job_directory(tmp_path, monkeypatch):
    from apps.api import main

    monkeypatch.setattr(main, "MAX_STORED_JOBS", 1)
    monkeypatch.setattr(main, "JOB_DIR", tmp_path)
    main.job_store.clear()
    main.results_store.clear()

    old_dir = tmp_path / "old"
    old_dir.mkdir()
    old_file = old_dir / "candidates.jsonl"
    old_file.write_text("{}", encoding="utf-8")

    new_dir = tmp_path / "new"
    new_dir.mkdir()
    new_file = new_dir / "candidates.jsonl"
    new_file.write_text("{}", encoding="utf-8")

    main.job_store.update(
        {
            "old": {
                "started_at": "2026-06-08T00:00:00",
                "file_path": str(old_file),
            },
            "new": {
                "started_at": "2026-06-09T00:00:00",
                "file_path": str(new_file),
            },
        }
    )
    main.results_store.update({"old": [{"candidate_id": "C1"}], "new": [{"candidate_id": "C2"}]})

    main.prune_job_stores()

    assert "old" not in main.job_store
    assert "old" not in main.results_store
    assert not old_dir.exists()
    assert Path(main.job_store["new"]["file_path"]).exists()
