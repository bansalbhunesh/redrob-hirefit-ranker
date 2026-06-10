#!/usr/bin/env python3
"""Phase 6 appendix: learned base-score weights vs the hand-tuned weights.

Trains an L2 logistic regression on the 28 feature values + clamped BM25
(the exact inputs of the hand-tuned weighted base score) against binary
relevance (independent-label tier >= 3), with stratified 5-fold
cross-validation; ranking uses OUT-OF-FOLD probabilities so no candidate is
scored by a model that saw its label. The three guardrail multipliers are
applied identically to both systems, so the comparison isolates the base
scorer.

Honesty caveat (printed into the appendix): the independent labels are
themselves rule-derived from profiles, so a model trained on them partially
re-learns the labeling heuristic -- agreement flatters the learned model.
The LLM-judge column is reported with its coverage. This study justifies the
shipped hand weights; it does not gate any change.

Usage:
    PYTHONHASHSEED=0 python scripts/learned_weights_study.py [--max-candidates N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.constants import BASE_FEATURE_WEIGHTS, FEATURE_NAMES  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from redrob_ranker.features import clamp  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.pipeline import RankerConfig, rank_candidates  # noqa: E402
from redrob_ranker.retrieval import retrieve_pool  # noqa: E402

INDEPENDENT_LABELS = ROOT / "artifacts" / "independent_labels_100k.jsonl"
LLM_LABELS = ROOT / "docs" / "llm_judge_eval_labels.jsonl"
DOC_OUT = ROOT / "docs" / "learned_weights_appendix.md"
SEED = 0


def main() -> None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold

    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, default=ROOT / "candidates.jsonl")
    ap.add_argument("--max-candidates", type=int, default=None)
    args = ap.parse_args()

    candidates = list(iter_candidates(args.candidates, max_candidates=args.max_candidates))
    retrieval, _ = retrieve_pool(candidates, 0, backend="bm25s")
    bm25_by_idx = {i: clamp(retrieval.get(i, 0.0)) for i in range(len(candidates))}
    ranked, _ = rank_candidates(candidates, RankerConfig(bm25_backend="bm25s"))
    print(f"featurized {len(ranked)} candidates", file=sys.stderr)

    idx_by_id = {c["candidate_id"]: i for i, c in enumerate(candidates)}
    independent = load_labels(INDEPENDENT_LABELS, name="independent")
    llm = load_labels(LLM_LABELS, name="llm-judge")

    feat_cols = ["bm25_score"] + list(FEATURE_NAMES)
    ids, X, y, mults = [], [], [], []
    for candidate, features, _score in ranked:
        cid = candidate["candidate_id"]
        ids.append(cid)
        row = [bm25_by_idx[idx_by_id[cid]]] + [features.values[n] for n in FEATURE_NAMES]
        X.append(row)
        y.append(1 if independent.tiers.get(cid, 0.0) >= 3.0 else 0)
        mults.append(
            features.behavioral_multiplier
            * features.honeypot_multiplier
            * features.disqualifier_multiplier
        )
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.int32)
    mults = np.asarray(mults, dtype=np.float64)
    print(f"positives (tier>=3): {int(y.sum()):,} / {len(y):,}", file=sys.stderr)

    # Out-of-fold probabilities.
    oof = np.zeros(len(y))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    coefs = []
    for tr, te in skf.split(X, y):
        lr = LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced",
                                random_state=SEED)
        lr.fit(X[tr], y[tr])
        oof[te] = lr.predict_proba(X[te])[:, 1]
        coefs.append(lr.coef_[0])
    mean_coef = np.mean(coefs, axis=0)

    learned_final = oof * mults
    order = sorted(range(len(ids)), key=lambda i: (-learned_final[i], ids[i]))
    learned_top100 = [ids[i] for i in order[:100]]
    shipped_top100 = [c["candidate_id"] for c, _, _ in ranked[:100]]

    rows = {}
    for name, top in (("hand-tuned (shipped)", shipped_top100), ("learned LR (OOF)", learned_top100)):
        r_ind = evaluate(top, independent, unlabeled="exclude")
        r_llm = evaluate(top, llm, unlabeled="exclude")
        rows[name] = (r_ind, r_llm)
        print(f"{name:<22} ind={r_ind.composite:.4f} llm={r_llm.composite:.4f} "
              f"(cov {r_llm.coverage:.0%})", file=sys.stderr)
    overlap = len(set(learned_top100) & set(shipped_top100))

    weight_norm = {k: v / sum(BASE_FEATURE_WEIGHTS.values()) for k, v in BASE_FEATURE_WEIGHTS.items()}
    coef_rank = sorted(zip(feat_cols, mean_coef), key=lambda t: -abs(t[1]))

    lines = ["# Appendix: learned weights vs hand-tuned weights (Phase 6)", ""]
    lines.append(f"Pool: {len(y):,} candidates; binary target = independent tier >= 3 "
                 f"({int(y.sum()):,} positives). L2 logistic regression on the 28 features "
                 "+ clamped BM25 (the exact base-score inputs), stratified 5-fold CV, "
                 "ranking by OUT-OF-FOLD probability; identical guardrail multipliers "
                 "applied to both systems.")
    lines.append("")
    lines.append("**Caveat:** the independent labels are rule-derived from profiles, so a "
                 "model trained on them partially re-learns the labeling heuristic -- the "
                 "independent column flatters the learned model. LLM-judge shown with coverage.")
    lines.append("")
    lines.append("| base scorer | composite (independent) | composite (LLM judge) | LLM coverage |")
    lines.append("|---|---|---|---|")
    for name, (r_ind, r_llm) in rows.items():
        lines.append(f"| {name} | {r_ind.composite:.4f} | {r_llm.composite:.4f} | {r_llm.coverage:.0%} |")
    lines.append("")
    lines.append(f"Top-100 overlap between the two systems: **{overlap}/100**.")
    lines.append("")
    lines.append("## What the model learned (mean |coef| across folds, top 12)")
    lines.append("")
    lines.append("| feature | LR coef | hand weight (normalized) |")
    lines.append("|---|---|---|")
    for name, coef in coef_rank[:12]:
        hw = weight_norm.get(name)
        hw_s = f"{hw:.3f}" if hw is not None else "— (not in base score)"
        lines.append(f"| {name} | {coef:+.3f} | {hw_s} |")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    ship = rows["hand-tuned (shipped)"][0].composite
    learned = rows["learned LR (OOF)"][0].composite
    if learned <= ship + 0.002:
        lines.append("The learned base scorer does not beat the hand-tuned weights even on "
                     "labels that structurally favor it. The hand weights ship: they are "
                     "explainable per-feature, stable without a training set, and free of "
                     "label-leakage risk.")
    else:
        lines.append(f"The learned scorer outperforms on the independent labels "
                     f"({learned:.4f} vs {ship:.4f}) -- but given the circularity caveat and "
                     "the LLM-judge coverage limits, hand weights still ship; revisit only "
                     "with truly held-out labels.")
    DOC_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {DOC_OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
