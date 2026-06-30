#!/usr/bin/env python
"""Generate the deterministic explainability report (SHAP-summary + rank CI).

Opt-in and read-only: it re-derives the universal-v2 relevance that underlies the
shipped frontier-v5 order and writes a markdown report + a per-candidate CSV. It
does not run the production scorer, touch submission.csv, or affect the golden
hash.

    PYTHONHASHSEED=0 python scripts/explain_report.py \
        --candidates candidates.jsonl \
        --out-md docs/explainability_report.md \
        --out-csv artifacts/attributions.csv \
        --top-k 100

Apples-to-apples with SHRE's SHAP/stability page, but exact and reproducible:
the global table is mean |Shapley| (not sampled), and the rank band is a
leave-one-feature-out interval (not seed variance).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Resolve this worktree's src/ first (the editable install may point elsewhere),
# matching the bootstrap in scripts/validate_submission.py.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from redrob_ranker.explain import (  # noqa: E402  (import follows src/ path bootstrap)
    CandidateRecord,
    final_score_from_relevance,
    gate_log_effects,
    global_importance,
    rank_stability,
    relevance_attributions,
)
from redrob_ranker.features import compute_features  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.retrieval import retrieve_pool  # noqa: E402


def _build_records(candidates_path: Path) -> list[CandidateRecord]:
    candidates = list(iter_candidates(candidates_path))
    retrieval_scores, _ = retrieve_pool(candidates, 0)
    records: list[CandidateRecord] = []
    for idx, candidate in enumerate(candidates):
        features = compute_features(candidate)
        records.append(
            CandidateRecord(
                candidate_id=candidate["candidate_id"],
                values=dict(features.values),
                retrieval_score=retrieval_scores.get(idx, 0.0),
                semantic_score=None,  # embeddings are off in the shipped path
                behavioral_multiplier=features.behavioral_multiplier,
                honeypot_multiplier=features.honeypot_multiplier,
                disqualifier_multiplier=features.disqualifier_multiplier,
            )
        )
    return records


def _write_markdown(path: Path, importance, top_records, bands) -> None:
    lines = [
        "# Explainability report (deterministic, exact)",
        "",
        "Per-feature attributions are exact Shapley values for the linear "
        "universal-v2 relevance (each feature's contribution is its own additive "
        "term), so this report is byte-reproducible under `PYTHONHASHSEED=0`. The "
        "rank band is a label-free leave-one-feature-out interval: re-rank the pool "
        "with each signal removed and record where the candidate lands.",
        "",
        "## Global feature importance (mean |contribution|)",
        "",
        "| feature | mean &#124;Shapley&#124; |",
        "| --- | ---: |",
    ]
    for name, value in importance:
        lines.append(f"| {name} | {value:.5f} |")
    lines += ["", "## Top candidates: drivers and rank confidence", ""]
    for rec, score, rel in top_records:
        base_rank, lo, hi = bands[rec.candidate_id]
        contributions, _ = relevance_attributions(
            rec.values, rec.retrieval_score, rec.semantic_score
        )
        drivers = sorted(contributions.items(), key=lambda kv: -kv[1])[:5]
        gates = gate_log_effects(
            rec.behavioral_multiplier,
            rec.honeypot_multiplier,
            rec.disqualifier_multiplier,
        )
        penalties = [g for g, v in gates.items() if v < -1e-9]
        driver_str = ", ".join(f"{n} (+{v:.3f})" for n, v in drivers)
        band = f"rank {base_rank} [{lo}–{hi}]"
        note = f" · gated by: {', '.join(penalties)}" if penalties else ""
        lines.append(
            f"- **{rec.candidate_id}** — {band}, score {score:.4f}{note}\n"
            f"  - top drivers: {driver_str}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, top_records, bands) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["candidate_id", "rank", "rank_lo", "rank_hi", "score", "relevance", "top_drivers"]
        )
        for rec, score, rel in top_records:
            base_rank, lo, hi = bands[rec.candidate_id]
            contributions, _ = relevance_attributions(
                rec.values, rec.retrieval_score, rec.semantic_score
            )
            drivers = "|".join(
                f"{n}:{v:.4f}"
                for n, v in sorted(contributions.items(), key=lambda kv: -kv[1])[:5]
            )
            writer.writerow(
                [rec.candidate_id, base_rank, lo, hi, f"{score:.6f}", f"{rel:.6f}", drivers]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, default=Path("docs/explainability_report.md"))
    parser.add_argument("--out-csv", type=Path, default=Path("artifacts/attributions.csv"))
    parser.add_argument("--top-k", type=int, default=100)
    args = parser.parse_args()

    records = _build_records(args.candidates)
    importance = global_importance(records)
    bands = rank_stability(records, top_k=args.top_k)

    scored = []
    for rec in records:
        _, rel = relevance_attributions(rec.values, rec.retrieval_score, rec.semantic_score)
        score = final_score_from_relevance(
            rel, rec.behavioral_multiplier, rec.honeypot_multiplier, rec.disqualifier_multiplier
        )
        scored.append((rec, score, rel))
    scored.sort(key=lambda item: (-item[1], item[0].candidate_id))
    top_records = scored[: args.top_k]

    _write_markdown(args.out_md, importance, top_records, bands)
    _write_csv(args.out_csv, top_records, bands)
    print(f"Wrote {args.out_md} and {args.out_csv} ({len(top_records)} candidates explained).")


if __name__ == "__main__":
    main()
