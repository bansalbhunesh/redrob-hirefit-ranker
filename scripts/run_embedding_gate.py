#!/usr/bin/env python3
"""Decision gate for the dense-embeddings experiment.

Runs the ranker WITHOUT and WITH the model2vec/potion semantic feature, scores
both against the independent (non-circular) labels, and prints a PASS/FAIL verdict.

Merge rule (pre-committed, so the decision is not post-hoc):
    PASS  iff   NDCG@10(embeddings) > NDCG@10(baseline)   AND   runtime < 180s
    FAIL  otherwise  ->  ship the simpler/faster system and say so in the pitch.

Either outcome is a defensible interview story; the point is the measurement.

Needs model2vec installed (no Python 3.14 wheel yet -> run in the 3.11 Docker image
or a 3.11 venv). The official ranking path is unchanged and never imports model2vec.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RUNTIME_BUDGET_S = 180.0


def _run(candidates: Path, out: Path, use_embeddings: bool, model: str, max_candidates=None) -> float:
    from redrob_ranker.pipeline import RankerConfig, run_ranking
    cfg = RankerConfig(use_embeddings=use_embeddings, embed_model=model, max_candidates=max_candidates)
    t0 = time.time()
    run_ranking(candidates, out, cfg)
    return time.time() - t0


def _eval(submission: Path, labels: Path) -> dict:
    # Score via the shared harness — the same code path every doc reports from.
    # ("zero" policy matches evaluate_independent.py's published numbers.)
    from redrob_ranker.eval_harness import evaluate, load_labels, load_submission

    ranked = load_submission(submission)
    result = evaluate(ranked, load_labels(labels, name="independent"), unlabeled="zero")
    return {
        "ndcg10": result.ndcg10,
        "ndcg50": result.ndcg50,
        "map": result.map,
        "p10": result.p10,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Gate the dense-embeddings experiment.")
    ap.add_argument("--candidates", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path, help="independent labels JSONL")
    ap.add_argument("--model", default="minishlab/potion-retrieval-32M")
    ap.add_argument("--baseline-out", type=Path, default=ROOT / "artifacts" / "sub_baseline.csv")
    ap.add_argument("--embed-out", type=Path, default=ROOT / "artifacts" / "sub_embeddings.csv")
    ap.add_argument("--max-candidates", type=int, default=None,
                    help="Subset for a fast directional read; omit for the full pool.")
    args = ap.parse_args()

    try:
        import model2vec  # noqa: F401
    except ImportError:
        print("[skip] model2vec not installed (no Python 3.14 wheel). Run this gate in the\n"
              "       3.11 Docker image or a 3.11 venv:  pip install model2vec\n"
              "       The official ranker does not need it; this is an experiment-only gate.",
              file=sys.stderr)
        return 2

    print("running baseline (no embeddings) ...")
    t_base = _run(args.candidates, args.baseline_out, False, args.model, args.max_candidates)
    print("running with embeddings ...")
    t_emb = _run(args.candidates, args.embed_out, True, args.model, args.max_candidates)

    base = _eval(args.baseline_out, args.labels)
    emb = _eval(args.embed_out, args.labels)

    def row(name, b, e):
        d = e - b
        return f"  {name:8s} baseline={b:.4f}  embeddings={e:.4f}  delta={d:+.4f}"

    print("\n=== independent-eval comparison ===")
    print(row("NDCG@10", base["ndcg10"], emb["ndcg10"]))
    print(row("NDCG@50", base["ndcg50"], emb["ndcg50"]))
    print(row("MAP", base["map"], emb["map"]))
    print(row("P@10", base["p10"], emb["p10"]))
    print(f"\n  runtime baseline={t_base:.1f}s  embeddings={t_emb:.1f}s  (budget {RUNTIME_BUDGET_S:.0f}s)")

    ndcg_up = emb["ndcg10"] > base["ndcg10"]
    within_budget = t_emb < RUNTIME_BUDGET_S
    verdict = "PASS -> merge embeddings" if (ndcg_up and within_budget) else "FAIL -> ship simpler system"
    print(f"\n=== GATE: {verdict} ===")
    print(f"    NDCG@10 improved: {ndcg_up} | runtime<{RUNTIME_BUDGET_S:.0f}s: {within_budget}")
    return 0 if (ndcg_up and within_budget) else 1


if __name__ == "__main__":
    raise SystemExit(main())
