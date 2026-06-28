from __future__ import annotations

from experiments.public_field_benchmark import parse_submission, strong_repository_names, tree_signals


def _csv(rows: int = 100) -> str:
    body = "\n".join(
        f"CAND_{index:07d},{index},0.5,reason" for index in range(1, rows + 1)
    )
    return "candidate_id,rank,score,reasoning\n" + body + "\n"


def test_parse_submission_accepts_exact_valid_artifact() -> None:
    ids = parse_submission(_csv())

    assert ids is not None
    assert len(ids) == len(set(ids)) == 100


def test_parse_submission_rejects_sample_or_duplicate_artifact() -> None:
    assert parse_submission(_csv(10)) is None
    duplicate = _csv().replace("CAND_0000002,2", "CAND_0000001,2")
    assert parse_submission(duplicate) is None


def test_tree_signals_reward_real_engineering_evidence() -> None:
    strong_score, signals = tree_signals(
        [
            "README.md",
            "src/ranker.py",
            "src/features.py",
            "src/io.py",
            "tests/test_ranker.py",
            "Dockerfile",
            ".github/workflows/tests.yml",
            "requirements.txt",
            "docs/evaluation.md",
            "submission.csv",
        ]
    )
    weak_score, _ = tree_signals(["solution.ipynb", "submission.csv"])

    assert signals["tests"] and signals["docker"] and signals["ci"]
    assert strong_score > weak_score


def test_strong_repository_union_covers_each_axis() -> None:
    rows = [
        {
            "repo": "proxy",
            "engineering_score": 1,
            "best": {
                "h2": 1.0,
                "mean7": 0.1,
                "reviewer": 0.1,
                "reviewer_coverage": 1.0,
                "blind": 0.1,
                "blind_coverage": 1.0,
            },
        },
        {
            "repo": "human",
            "engineering_score": 1,
            "best": {
                "h2": 0.1,
                "mean7": 0.1,
                "reviewer": 1.0,
                "reviewer_coverage": 1.0,
                "blind": 1.0,
                "blind_coverage": 1.0,
            },
        },
        {"repo": "engineering", "engineering_score": 20, "best": None},
    ]

    assert set(strong_repository_names(rows, limit=1)) == {"proxy", "human", "engineering"}
