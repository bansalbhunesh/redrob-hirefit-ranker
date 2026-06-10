#!/usr/bin/env python3
"""LTR challenger vs shipped scorer, per the pre-registered gate
(docs/ltr_challenger_gate.md). Dev-only; never part of the ranking path unless
adopted via the documented golden-hash-roll protocol.

Pipeline:
  1. Assemble training labels: judge tiers where available (judge #1 + expansion;
     judge #2 reserved for scoring only), generator-rule labels elsewhere.
  2. Train LightGBM (lambdarank) on shipped 28 features + BM25 + forensics features,
     5-fold OOF over labeled ids; unlabeled ids scored by the fold-ensemble mean.
  3. Final challenger score = model base score x behavioral x honeypot x disqualifier
     (guardrails identical to shipped).
  4. Score challenger AND shipped top-100s against the three gate sources and print
     the gate verdict. No re-tuning after this evaluation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from redrob_ranker.constants import FEATURE_NAMES  # noqa: E402
from redrob_ranker.features import compute_features, final_score  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.retrieval import retrieve_pool  # noqa: E402

SEED = 13
N_FOLDS = 5

STRATUM_BASE = {
    "senior ai engineer with # years": 4.7,
    "senior engineer who has spent the": 4.2,
    "machine learning engineer with # years": 4.1,
    "data scientist / ml engineer with": 2.4,
    "software / data professional with #": 2.0,
    "software engineer with # years of": 1.2,
}
FORENSIC_NUM = ["yoe_field", "history_months", "n_roles", "history_gap_months",
                "span_gap_max", "frac_sitcom", "frac_services", "frac_bigtech",
                "frac_in_product", "expert_zero_count", "n_skills", "edu_tier1",
                "edu_tier2", "completeness", "response_rate"]


def load_labels() -> dict[str, float]:
    """Judge tiers (j1 + expansion mean). Judge #2 is scoring-only per the gate."""
    tiers: dict[str, list[float]] = {}
    for p in (ROOT / "docs" / "llm_judge_eval_labels.jsonl",
              ROOT / "artifacts" / "llm_labels_expand.jsonl"):
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                tiers.setdefault(r["candidate_id"], []).append(float(r["tier"]))
    return {cid: sum(v) / len(v) for cid, v in tiers.items()}


def rule_label(fr: dict) -> float:
    """Generator-rule label: stratum prior + JD availability adjustment."""
    base = STRATUM_BASE.get(fr["summary_template"], 0.0)
    if base <= 0:
        return 0.0
    rr, otw = fr["response_rate"], fr["open_to_work"]
    if not otw and rr < 0.15:
        base -= 2.5
    elif not otw and rr < 0.3:
        base -= 2.0
    elif rr < 0.3:
        base -= 1.0
    if fr["stated_gap"] is not None and fr["stated_gap"] > 3.0:
        base = 0.0  # fabricated-field tell
    return max(0.0, base)


def main() -> None:
    import lightgbm as lgb

    forensics: dict[str, dict] = {}
    for line in (ROOT / "artifacts" / "forensics_features.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        forensics[r["candidate_id"]] = r
    templates = sorted({r["summary_template"] for r in forensics.values()})
    t_index = {t: i for i, t in enumerate(templates)}

    import os

    max_c = int(os.environ.get("REDROB_CHALLENGER_MAX", "0")) or None
    print(f"loading + featurizing {'100K' if not max_c else max_c} (serial)...", file=sys.stderr)
    cands = list(iter_candidates(ROOT / "candidates.jsonl", max_candidates=max_c))
    retr, _ = retrieve_pool(cands, 0, backend="bm25s")

    cids, X, mults, shipped_scores = [], [], [], []
    for i, c in enumerate(cands):
        f = compute_features(c)
        fr = forensics[c["candidate_id"]]
        row = [f.values.get(n, 0.0) for n in FEATURE_NAMES]
        row.append(min(1.0, max(0.0, retr.get(i, 0.0))))
        row.extend(float(fr[k] or 0) for k in FORENSIC_NUM)
        row.append(float(fr["stated_gap"]) if fr["stated_gap"] is not None else -99.0)
        row.append(t_index[fr["summary_template"]])
        X.append(row)
        mults.append(f.behavioral_multiplier * f.honeypot_multiplier * f.disqualifier_multiplier)
        shipped_scores.append(final_score(f, retr.get(i, 0.0)))
        cids.append(c["candidate_id"])
    X = np.asarray(X, dtype=np.float64)
    mults = np.asarray(mults)
    feat_names = list(FEATURE_NAMES) + ["bm25"] + FORENSIC_NUM + ["stated_gap", "stratum"]

    judge = load_labels()
    idx = {cid: i for i, cid in enumerate(cids)}
    labeled = sorted(judge.keys() & idx.keys())
    y_lab = np.array([judge[c] for c in labeled])
    li = np.array([idx[c] for c in labeled])
    print(f"judge-labeled training ids: {len(labeled)}")

    # Add seeded rule-labeled rows from unjudged target strata + control filler.
    rng = np.random.default_rng(SEED)
    rule_pool = [c for c, fr in forensics.items()
                 if c in idx and c not in judge
                 and (STRATUM_BASE.get(fr["summary_template"], 0) > 0
                      or rng.random() < 0.02)]
    rule_pool = sorted(rule_pool)
    rng.shuffle(rule_pool)
    rule_pool = rule_pool[:6000]
    y_rule = np.array([rule_label(forensics[c]) for c in rule_pool])
    ri = np.array([idx[c] for c in rule_pool])
    print(f"rule-labeled training ids: {len(rule_pool)}")

    train_idx = np.concatenate([li, ri])
    train_y = np.concatenate([y_lab, y_rule])
    train_w = np.concatenate([np.full(len(li), 3.0), np.ones(len(ri))])

    # 5-fold OOF over the combined training set; full-pool prediction = fold mean,
    # but trained rows take their OOF fold's prediction (no self-scoring).
    order = rng.permutation(len(train_idx))
    folds = np.array_split(order, N_FOLDS)
    pred_sum = np.zeros(len(cids))
    pred_cnt = np.zeros(len(cids))
    oof = np.full(len(train_idx), np.nan)

    params = dict(objective="lambdarank", metric="ndcg", ndcg_eval_at=[10, 50],
                  learning_rate=0.05, num_leaves=31, min_data_in_leaf=20,
                  feature_fraction=0.9, bagging_fraction=0.9, bagging_freq=1,
                  lambdarank_truncation_level=100, deterministic=True,
                  num_threads=1, seed=SEED, verbosity=-1)

    for k, fold in enumerate(folds):
        mask = np.ones(len(train_idx), bool)
        mask[fold] = False
        tr_rows = train_idx[mask]
        ds = lgb.Dataset(X[tr_rows], label=np.rint(train_y[mask]).astype(int),
                         weight=train_w[mask], group=[len(tr_rows)],
                         feature_name=feat_names,
                         categorical_feature=["stratum"], free_raw_data=True)
        model = lgb.train(params, ds, num_boost_round=300)
        p_all = model.predict(X, num_iteration=model.best_iteration)
        oof[fold] = p_all[train_idx[fold]]
        pred_sum += p_all
        pred_cnt += 1
        print(f"  fold {k + 1}/{N_FOLDS} trained", file=sys.stderr)

    base = pred_sum / pred_cnt
    base[train_idx] = oof  # OOF for every trained row

    # Normalize base to [0,1] and apply the unchanged guardrail multipliers.
    lo, hi = base.min(), base.max()
    challenger = (base - lo) / (hi - lo) * mults

    order_ch = np.lexsort((np.array(cids), -challenger))
    top_ch = [cids[i] for i in order_ch[:100]]
    order_sh = np.lexsort((np.array(cids), -np.asarray(shipped_scores)))
    top_sh = [cids[i] for i in order_sh[:100]]
    overlap = len(set(top_ch) & set(top_sh))
    print(f"\ntop-100 overlap challenger vs shipped: {overlap}/100")

    out = ROOT / "artifacts" / "challenger_top100.json"
    out.write_text(json.dumps({"challenger": top_ch, "shipped": top_sh,
                               "overlap": overlap}, indent=1), encoding="utf-8")

    fi = sorted(zip(feat_names, model.feature_importance("gain")), key=lambda t: -t[1])[:15]
    print("\ntop-15 features by gain (last fold):")
    for n, g in fi:
        print(f"  {g:12.0f}  {n}")
    print(f"\nwrote {out}; score both lists with scripts/score_challenger.py")


if __name__ == "__main__":
    main()
