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


def _rows_with_top_tie(cid_rank1: str, cid_rank2: str) -> list[dict]:
    """100 valid rows where ranks 1 and 2 share the top score (a tie)."""
    rows = [
        {
            "candidate_id": f"CAND_{idx:07d}",
            "rank": str(idx),
            "score": f"{1.0 - idx / 1000:.6f}",
            "reasoning": "JD-connected reason.",
        }
        for idx in range(1, 101)
    ]
    rows[0]["score"] = rows[1]["score"] = "0.999000"  # equal, still >= rank 3
    rows[0]["candidate_id"] = cid_rank1
    rows[1]["candidate_id"] = cid_rank2
    return rows


def test_validate_rows_flags_tiebreak_descending_candidate_id():
    # Equal adjacent scores with candidate_id DESCENDING violates the official
    # tie-break rule and must be reported.
    errors = validate_rows(_rows_with_top_tie("CAND_0009999", "CAND_0009998"))
    assert any("tie-break" in e for e in errors), errors


def test_validate_rows_accepts_tiebreak_ascending_candidate_id():
    # Equal adjacent scores with candidate_id ASCENDING is allowed.
    assert validate_rows(_rows_with_top_tie("CAND_0009998", "CAND_0009999")) == []


def test_validate_rows_rejects_nonfinite_score_rank_and_blank_reasoning():
    rows = _rows_with_top_tie("CAND_0009998", "CAND_0009999")
    rows[0]["score"] = "nan"
    rows[0]["rank"] = "0"
    rows[0]["reasoning"] = "   "

    errors = validate_rows(rows)

    assert any("not finite" in error for error in errors)
    assert any("Rank out of range" in error for error in errors)
    assert any("Missing reasoning" in error for error in errors)
