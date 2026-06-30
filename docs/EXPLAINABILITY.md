# Explainability: exact attributions, ablation, and rank stability

This system explains *why* a candidate is ranked where it is, using methods that are **analytic and
byte-reproducible** rather than sampled approximations. Everything here is opt-in and read-only with
respect to ranking: it re-derives the shipped relevance and never mutates `submission.csv` or the
golden hash.

Module: [`src/redrob_ranker/explain.py`](../src/redrob_ranker/explain.py) ·
CLI: [`scripts/explain_report.py`](../scripts/explain_report.py) ·
Tests: [`tests/test_explain.py`](../tests/test_explain.py)

## Why the attributions are exact (not sampled)

The shipped relevance is a normalized weighted sum of features:

```
relevance = ( w_bm25 · clamp(bm25) + Σ_i w_i · feature_i  [+ w_sem · clamp(semantic)] ) / Z
final     = relevance · behaviour^β · honeypot_mult · disqualifier_mult
```

For an additive (linear) function, the Shapley value of each input is exactly its own term. So we can
attribute each candidate's relevance to its features **analytically** — no surrogate model, no kernel
sampling, no random seed. The contributions sum back to the relevance to floating-point exactness, and
`final` is reconstructed exactly from `relevance` and the multiplicative gates.

This is verified, not asserted: `tests/test_explain.py::test_reconstructs_universal_v2` checks that the
attribution path reproduces the shipped `universal_v2_score` (`rel_tol 1e-9`) on real candidates, and
`test_attributions_sum_to_relevance` checks the additive identity (`abs_tol 1e-12`).

## What you get

1. **Per-candidate attributions** — relevance decomposed into exact additive feature contributions,
   plus the multiplicative integrity gates (behaviour, honeypot, disqualifier) reported as log-space
   effects. A negative gate effect shows exactly which guardrail held a candidate down.
2. **Global feature importance** — mean `|contribution|` across the pool. This is the SHAP-summary
   equivalent, computed exactly over every candidate rather than a sample.
3. **Rank-stability band** — a deterministic, label-free confidence interval. For each feature we
   re-rank the whole pool with that feature removed and record where each top-k candidate lands; the
   reported `[lo, hi]` band is the spread across all single-feature ablations. A tight band means no
   single signal is carrying the rank; a wide band flags a position that one feature dominates.

Unlike accuracy/stability figures trained on self-generated labels, none of these require labels — they
describe the shipped scorer itself, so they cannot drift from what actually ships.

## How to run

```bash
PYTHONHASHSEED=0 python scripts/explain_report.py \
  --candidates candidates.jsonl \
  --out-md docs/explainability_report.md \
  --out-csv artifacts/attributions.csv \
  --top-k 100
```

Outputs:
- `docs/explainability_report.md` — global importance table + per-candidate drivers and rank bands.
- `artifacts/attributions.csv` — machine-readable `candidate_id, rank, rank_lo, rank_hi, score,
  relevance, top_drivers`.

## Ablation summary

The repository ships a pre-registered **measured-negatives ladder** — the ablation record of what was
tried and rejected on a frozen 100K blind arbiter (frozen before tuning):

| Alternative | Measured result on the blind arbiter | Verdict |
|---|---|---|
| Static dense embeddings (potion-32M) | NDCG@10 +0.0000 at ~2.2× runtime | Rejected |
| Learned logistic-regression weights | composite 0.8238 vs 0.8811 | Rejected |
| LightGBM LambdaMART v2 | composite −0.031, NDCG@10 −0.070 | Rejected |
| LambdaMART v3 (blind labels, leak-safe) | holdout NDCG@10 −0.040 to −0.104 | Rejected |
| Top-K cross-encoder (ms-marco-MiniLM) | in-sample +0.014 → −0.016 holdout | Rejected |
| Rank-space fusion (raw / Copeland) | +0.013 blind (anachronism-driven) | Not shipped |

Full detail and reproduction: [`docs/measured_negatives.md`](measured_negatives.md) ·
[`docs/why_not_reranker.md`](why_not_reranker.md). This is also why the semantic/embedding path is
**built but disabled by default** (`--use-embeddings` opt-in): the measurements do not support a
semantic-edge claim, so the claim is not made.

## Honesty boundary

All ranking-quality numbers cited here and elsewhere are **development proxies** (independent heuristic
and LLM-judge labels). No official hidden labels were available before submission. The attribution and
stability tooling is exact with respect to the shipped scorer; it does not claim to predict the official
hidden score.
