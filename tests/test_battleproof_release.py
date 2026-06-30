from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import rank
from redrob_ranker.io import iter_candidates
from redrob_ranker.pipeline import RankerConfig, _validate_config
from redrob_ranker.validation import validate_rows


def _release_args():
    return SimpleNamespace(
        scoring_profile=None,
        top_k=100,
        max_candidates=None,
        candidate_pool=0,
        jd=None,
        use_embeddings=False,
        bm25_backend="auto",
    )


def _main_args(tmp_path: Path, output: Path):
    return SimpleNamespace(
        candidates=str(tmp_path / "candidates.jsonl"),
        out=str(output),
        top_k=100,
        max_candidates=None,
        candidate_pool=0,
        bm25_backend="auto",
        workers=2,
        jd=None,
        use_embeddings=False,
        embed_model="minishlab/potion-retrieval-32M",
        scoring_profile=None,
        release=True,
        profile_memory=False,
        show_top=0,
    )


def _set_release_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    for name in rank.DETERMINISTIC_THREAD_ENV:
        monkeypatch.setenv(name, "1")


@pytest.mark.parametrize(
    "name",
    ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"],
)
def test_release_rejects_nondeterministic_thread_environment(
    monkeypatch: pytest.MonkeyPatch, name: str
):
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    monkeypatch.setenv(name, "2")

    with pytest.raises(SystemExit, match=name):
        rank._release_profile(_release_args())


def test_release_rejects_wrong_candidate_artifact(tmp_path: Path):
    source = tmp_path / "candidates.jsonl"
    source.write_text('{"candidate_id":"CAND_0000001"}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="candidate input SHA-256"):
        rank._verify_release_input(source)


def test_failed_postrun_verification_preserves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import redrob_ranker.loss_aggregate as loss_aggregate

    output = tmp_path / "submission.csv"
    output.write_bytes(b"known-good\n")
    _set_release_env(monkeypatch)
    monkeypatch.setattr(rank, "parse_args", lambda: _main_args(tmp_path, output))
    monkeypatch.setattr(rank, "_verify_release_input", lambda _path: None)
    monkeypatch.setattr(loss_aggregate, "_artifact", lambda: {})

    def bad_run(_source, run_output, _config):
        run_output.write_bytes(b"wrong artifact\n")
        return SimpleNamespace(
            loaded_count=100_000,
            ranked_pool_count=100_000,
            rows=[{}] * 100,
            bm25_backend="bm25s",
            honeypots_detected=53,
            honeypots_in_output=0,
        )

    monkeypatch.setattr(rank, "run_ranking", bad_run)

    with pytest.raises(RuntimeError, match="Release verification failed"):
        rank.main()

    assert output.read_bytes() == b"known-good\n"
    assert list(tmp_path.glob(".submission.csv.release.*.tmp")) == []


def test_interrupted_release_preserves_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import redrob_ranker.loss_aggregate as loss_aggregate

    output = tmp_path / "submission.csv"
    output.write_bytes(b"known-good\n")
    _set_release_env(monkeypatch)
    monkeypatch.setattr(rank, "parse_args", lambda: _main_args(tmp_path, output))
    monkeypatch.setattr(rank, "_verify_release_input", lambda _path: None)
    monkeypatch.setattr(loss_aggregate, "_artifact", lambda: {})

    def interrupted_run(_source, run_output, _config):
        run_output.write_bytes(b"partial\n")
        raise KeyboardInterrupt

    monkeypatch.setattr(rank, "run_ranking", interrupted_run)

    with pytest.raises(KeyboardInterrupt):
        rank.main()

    assert output.read_bytes() == b"known-good\n"
    assert list(tmp_path.glob(".submission.csv.release.*.tmp")) == []


def test_atomic_release_publish_preserves_existing_file_on_copy_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source = tmp_path / "verified.csv"
    source.write_bytes(b"new verified bytes\n")
    output_dir = tmp_path / "mounted-output"
    output_dir.mkdir()
    output = output_dir / "submission.csv"
    output.write_bytes(b"known-good\n")

    def broken_copy(*_args, **_kwargs):
        raise OSError("simulated destination failure")

    monkeypatch.setattr(rank.shutil, "copyfileobj", broken_copy)

    with pytest.raises(OSError, match="simulated destination failure"):
        rank._publish_verified_release(source, output)

    assert output.read_bytes() == b"known-good\n"
    assert list(output_dir.glob(".submission.csv.publish.*.tmp")) == []


def test_release_verifier_rejects_backend_drift():
    result = SimpleNamespace(
        loaded_count=100_000,
        ranked_pool_count=100_000,
        rows=[{}] * 100,
        honeypots_detected=53,
        honeypots_in_output=0,
        bm25_backend="rank_bm25",
    )

    with pytest.raises(RuntimeError, match="BM25 backend"):
        rank._verify_release(result, Path(rank.ROOT / "submission.csv"))


@pytest.mark.parametrize(
    "config",
    [
        RankerConfig(top_k=True),
        RankerConfig(top_k=1.5),
        RankerConfig(candidate_pool_size=float("nan")),
        RankerConfig(max_candidates=True),
        RankerConfig(workers=float("nan")),
        RankerConfig(use_embeddings=1),
        RankerConfig(embed_model=""),
    ],
)
def test_programmatic_config_rejects_exotic_types(config: RankerConfig):
    with pytest.raises((TypeError, ValueError)):
        _validate_config(config)


def test_validator_requires_score_and_row_rank_alignment():
    rows = [
        {
            "candidate_id": "CAND_0000002",
            "rank": "2",
            "score": "0.900000",
            "reasoning": "Grounded evidence.",
        },
        {
            "candidate_id": "CAND_0000001",
            "rank": "1",
            "reasoning": None,
        },
    ]

    errors = validate_rows(rows, expected=2)

    assert any("row position" in error for error in errors)
    assert any("Missing score" in error for error in errors)
    assert any("Missing reasoning" in error for error in errors)


@pytest.mark.parametrize("payload", ["[]\n", "null\n", "42\n", '"text"\n'])
def test_jsonl_rejects_non_object_records_with_clear_error(tmp_path: Path, payload: str):
    source = tmp_path / "bad.jsonl"
    source.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        list(iter_candidates(source))


def test_json_file_rejects_non_array_root(tmp_path: Path):
    source = tmp_path / "bad.json"
    source.write_text('{"candidate_id":"CAND_0000001"}', encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a JSON array"):
        list(iter_candidates(source))
