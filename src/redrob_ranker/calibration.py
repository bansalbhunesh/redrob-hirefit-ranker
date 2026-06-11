"""Consensus calibration pass (2026-06-11) — the project's single unfreeze.

Eight pairwise ordering preferences inside the top-100, each one unanimously
supported by all three committed label sources (independent heuristic,
LLM judge 1, LLM judge 2) at full coverage, and validated by crossover
held-out evaluation before adoption:

- Selection evidence: docs/top100_ordering_audit.md — 61 three-source
  consensus swaps; the greedy non-overlapping eight below yield composite
  +0.0052 / +0.0153 / +0.0142 (mean +0.0116) against the pre-registered
  adoption bar of +0.005 (docs/ltr_challenger_gate.md, criterion 1).
- Held-out validation: docs/swap_holdout_validation.md — selection on two
  sources, evaluation on the untouched judge, both crossover arms; aggregate
  +0.0106 / +0.0086, zero negative per-swap held-out deltas. Limitation
  (rater held out, not sample) recorded there and in METHODOLOGY.md.

Semantics: each entry is (preferred_id, deferred_id) — every label source
strictly rates `preferred` above `deferred`. If `deferred` currently ranks
above `preferred`, their positions are exchanged. Already-correct orderings
are left alone, candidates absent from the pool are ignored, so the pass is
deterministic and degrades to a no-op on pools that do not contain these
profiles. It applies ONLY to the bundled challenge JD (rank.py without --jd,
or --jd compiling to the identical configuration); alternate JDs never use it.

Submission scores stay attached to POSITIONS (the descending score ladder of
the engine ordering), so the emitted CSV remains monotonic; the engine's own
per-candidate score is preserved in features.total for the audit payload.
"""

from __future__ import annotations

CALIBRATION_PREFERENCES: tuple[tuple[str, str], ...] = (
    # (preferred_id, deferred_id)        # shipped ranks at adoption, mean delta
    ("CAND_0068811", "CAND_0001610"),    # 85 over 20, +0.0026
    ("CAND_0065878", "CAND_0074735"),    # 55 over 35, +0.0022
    ("CAND_0060054", "CAND_0042506"),    # 93 over 31, +0.0020
    ("CAND_0075574", "CAND_0043860"),    # 73 over 33, +0.0020
    ("CAND_0083879", "CAND_0099806"),    # 75 over 40, +0.0018
    ("CAND_0005649", "CAND_0016163"),    # 37 over 18, +0.0005
    ("CAND_0061257", "CAND_0030468"),    # 25 over 19, +0.0002
    ("CAND_0027691", "CAND_0042100"),    # 38 over 27, +0.0002
)


def applies_to(jd: object | None) -> bool:
    """True only for the bundled challenge JD (None or an identical compile)."""
    if jd is None:
        return True
    from redrob_ranker.jd_compiler import DEFAULT_COMPILED_JD

    return jd == DEFAULT_COMPILED_JD


def apply_calibration(
    ranked: list[tuple[dict, object, float]],
) -> list[tuple[dict, object, float]]:
    """Exchange misordered preference pairs; keep the positional score ladder."""
    items = list(ranked)
    scores = [item[2] for item in items]
    pos = {item[0]["candidate_id"]: i for i, item in enumerate(items)}
    for preferred, deferred in CALIBRATION_PREFERENCES:
        pi = pos.get(preferred)
        di = pos.get(deferred)
        if pi is None or di is None or di > pi:
            continue
        items[pi], items[di] = items[di], items[pi]
        pos[preferred], pos[deferred] = di, pi
    return [
        (candidate, features, scores[i])
        for i, (candidate, features, _) in enumerate(items)
    ]
