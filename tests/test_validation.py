"""Tests for submission validation."""

from redrob_ranker.validation import validate_rows


def test_validate_rows_accepts_csv_string_values():
    rows = [
        {
            "candidate_id": f"CAND_{idx:07d}",
            "rank": str(idx),
            "score": f"{1.0 - idx / 1000:.6f}",
            "reasoning": "JD-connected reason.",
        }
        for idx in range(1, 101)
    ]

    assert validate_rows(rows) == []
