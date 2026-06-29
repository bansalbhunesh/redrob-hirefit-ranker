import inspect

import redrob_ranker.anachronism as anachronism
import redrob_ranker.loss_aggregate as loss_aggregate
from redrob_ranker.anachronism import worst_severity
from redrob_ranker.features import CandidateFeatures
from redrob_ranker.loss_aggregate import _integrity_cleanup, _top_band_rerank


def _item(candidate_id: str, rank: int, *, ir: float = 0.0, years: float = 0.0, skill=None):
    candidate = {
        "candidate_id": candidate_id,
        "profile": {"years_of_experience": years},
        "skills": [skill] if skill else [],
        "career_history": [],
    }
    features = CandidateFeatures(
        candidate_id=candidate_id,
        values={"ir_ranking_experience": ir},
        behavioral_multiplier=1.0,
        honeypot_multiplier=1.0,
        disqualifier_multiplier=1.0,
    )
    return candidate, features, float(101 - rank)


def test_top_band_rule_uses_evidence_and_experience_not_candidate_ids():
    top = [_item(f"X{rank}", rank, ir=1.0, years=7.0) for rank in range(1, 6)]
    top.extend(
        [
            _item("older", 6, ir=1.0, years=16.2),
            _item("direct", 7, ir=0.714, years=7.8),
            _item("balanced", 8, ir=1.0, years=8.9),
        ]
    )

    reranked = _top_band_rerank(top)

    assert [item[0]["candidate_id"] for item in reranked[5:8]] == [
        "balanced",
        "direct",
        "older",
    ]
    assert "CAND_" not in inspect.getsource(loss_aggregate)
    assert "CAND_" not in inspect.getsource(anachronism)


def test_integrity_cleanup_replaces_only_two_lowest_ranked_contradictions():
    top = [_item(f"clean-{rank}", rank) for rank in range(1, 101)]
    top[96] = _item(
        "bad-97",
        97,
        skill={"name": "ChatGPT", "duration_months": 100},
    )
    top[98] = _item(
        "bad-99",
        99,
        skill={"name": "LangGraph", "duration_months": 50},
    )
    top[94] = _item(
        "bad-95",
        95,
        skill={"name": "ChatGPT", "duration_months": 100},
    )
    tail = [_item("backfill-1", 101), _item("backfill-2", 102)]

    cleaned = _integrity_cleanup(top, tail)

    assert cleaned[98][0]["candidate_id"] == "backfill-1"
    assert cleaned[96][0]["candidate_id"] == "backfill-2"
    assert cleaned[94][0]["candidate_id"] == "bad-95"
    assert worst_severity(cleaned[94][0]) > 1.0


def test_anachronism_detector_is_conservative_at_the_duration_boundary():
    boundary = {"skills": [{"name": "ChatGPT", "duration_months": 60}]}
    impossible = {"skills": [{"name": "ChatGPT", "duration_months": 61}]}

    assert worst_severity(boundary) == 0.0
    assert worst_severity(impossible) > 1.0
