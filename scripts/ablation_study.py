#!/usr/bin/env python3
"""Phase 3: ablation ladder — what each layer of the system earns.

Rungs (each scored on top-100 against both label sets via the shared harness,
policy=exclude, 20K dev slice by default):

  1. naive-keywords : count of JD keyword hits in the raw profile text
                      (the strawman recruiters effectively use)
  2. bm25-only      : lexical BM25 ordering alone
  3. bm25+features  : weighted 28-feature matrix, all multipliers forced to 1.0
  4. full-system    : shipped configuration (must equal the official pipeline)
  5. +embeddings    : NOT re-run — recorded gate result, tested & rejected
                      (artifacts/embedding_gate_result.txt: NDCG@10 +0.0000,
                      ~2.2x runtime)

Usage:
    PYTHONHASHSEED=0 python scripts/ablation_study.py [--max-candidates 20000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.constants import BASE_FEATURE_WEIGHTS, JD_QUERY  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, rank_candidates  # noqa: E402
from redrob_ranker.retrieval import retrieve_pool  # noqa: E402
from redrob_ranker.text import tokenize  # noqa: E402

INDEPENDENT_LABELS = ROOT / "artifacts" / "independent_labels_100k.jsonl"
LLM_LABELS = ROOT / "docs" / "llm_judge_eval_labels.jsonl"
DOC_OUT = ROOT / "docs" / "ablation_ladder.md"

EMBEDDING_GATE_NOTE = (
    "tested, rejected: NDCG@10 +0.0000, ~2.2x runtime "
    "(recorded gate result, artifacts/embedding_gate_result.txt; not re-run)"
)


def _top100(scored: list[tuple[float, str]]) -> list[str]:
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [cid for _, cid in scored[:100]]


def rung_naive_keywords(candidates: list[dict]) -> list[str]:
    jd_tokens = set(tokenize(JD_QUERY))
    scored = []
    for c in candidates:
        raw = json.dumps(c).lower()
        hits = sum(raw.count(tok) for tok in jd_tokens if len(tok) > 2)
        scored.append((float(hits), c["candidate_id"]))
    return _top100(scored)


def rung_bm25_only(candidates: list[dict]) -> list[str]:
    retrieval, _ = retrieve_pool(candidates, 0, backend="bm25s")
    scored = [(retrieval.get(i, 0.0), c["candidate_id"]) for i, c in enumerate(candidates)]
    return _top100(scored)


def rung_features_no_multipliers(ranked, bm25_by_id: dict[str, float]) -> list[str]:
    # Recompute the weighted base exactly as final_score does, but with the
    # behavioral/honeypot/disqualifier multipliers forced to 1.0.
    scored = []
    for candidate, features, _score in ranked:
        weighted = BASE_FEATURE_WEIGHTS["bm25_score"] * bm25_by_id[candidate["candidate_id"]]
        total_w = BASE_FEATURE_WEIGHTS["bm25_score"]
        for name, weight in BASE_FEATURE_WEIGHTS.items():
            if name == "bm25_score":
                continue
            weighted += weight * features.values.get(name, 0.0)
            total_w += weight
        scored.append((weighted / total_w, candidate["candidate_id"]))
    return _top100(scored)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, default=ROOT / "candidates.jsonl")
    ap.add_argument("--max-candidates", type=int, default=20000)
    args = ap.parse_args()

    candidates = list(iter_candidates(args.candidates, max_candidates=args.max_candidates))
    print(f"loaded {len(candidates)}", file=sys.stderr)

    # One full-system pass provides rungs 3 and 4 (features are reused).
    from redrob_ranker.features import clamp  # noqa: E402

    retrieval, _ = retrieve_pool(candidates, 0, backend="bm25s")
    ranked, _backend = rank_candidates(candidates, RankerConfig(bm25_backend="bm25s"))
    by_id_retrieval = {c["candidate_id"]: clamp(retrieval.get(i, 0.0))
                       for i, c in enumerate(candidates)}

    rungs: list[tuple[str, list[str] | None, str]] = []
    rungs.append(("1. naive JD-keyword count", rung_naive_keywords(candidates), ""))
    rungs.append(("2. BM25 only", rung_bm25_only(candidates), ""))
    rungs.append(("3. BM25 + 28 features (multipliers off)",
                  rung_features_no_multipliers(ranked, by_id_retrieval), ""))
    full_ids = [c["candidate_id"] for c, _, _ in ranked[:100]]
    rungs.append(("4. full system (shipped)", full_ids, ""))
    rungs.append(("5. + dense embeddings", None, EMBEDDING_GATE_NOTE))

    independent = load_labels(INDEPENDENT_LABELS, name="independent")
    llm = load_labels(LLM_LABELS, name="llm-judge")

    rows = []
    prev_mean = None
    for name, ids, note in rungs:
        if ids is None:
            rows.append((name, None, None, None, None, note))
            continue
        r_ind = evaluate(ids, independent, unlabeled="exclude")
        r_llm = evaluate(ids, llm, unlabeled="exclude")
        mean_c = (r_ind.composite + r_llm.composite) / 2
        delta = None if prev_mean is None else mean_c - prev_mean
        prev_mean = mean_c
        rows.append((name, r_ind, r_llm, mean_c, delta, note))
        print(f"{name:<45} ind={r_ind.composite:.4f} llm={r_llm.composite:.4f} "
              f"(cov {r_llm.coverage:.0%}) mean={mean_c:.4f}", file=sys.stderr)

    # Primary metric: independent composite (full coverage on any slice). The
    # LLM column is reported for transparency but is not comparable across
    # rungs on a dev slice (its labels were sampled around the full-pool
    # submission -> 25-35% coverage, selection-biased under exclude policy).
    lines = ["# Ablation Ladder (Phase 3)", ""]
    lines.append(f"Dev slice: first {len(candidates):,} candidates; top-100 per rung; "
                 "shared harness, policy=exclude; composite = challenge formula.")
    lines.append("")
    lines.append("**Primary metric: independent-heuristic composite (full coverage).** "
                 "The LLM-judge column is selection-biased at dev-slice coverage and "
                 "not comparable across rungs.")
    lines.append("")
    lines.append("| rung | composite (independent, full coverage) | delta | LLM judge (cov) |")
    lines.append("|---|---|---|---|")
    prev_ind = None
    for name, r_ind, r_llm, mean_c, delta, note in rows:
        if r_ind is None:
            lines.append(f"| {name} | — | {note} | — |")
            continue
        d = "—" if prev_ind is None else f"**{r_ind.composite - prev_ind:+.4f}**"
        prev_ind = r_ind.composite
        lines.append(f"| {name} | {r_ind.composite:.4f} | {d} "
                     f"| {r_llm.composite:.4f} ({r_llm.coverage:.0%}) |")
    lines.append("")
    lines.append("Rung 4 is the shipped configuration by construction (same "
                 "rank_candidates code path and default config; the full-pool "
                 "equivalent reproduces the golden submission hash).")
    DOC_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {DOC_OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
