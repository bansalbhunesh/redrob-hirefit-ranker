# Cross-Encoder Rerank — Measured Negative #11

**Branch:** `experiment/cross-encoder-rerank` (does NOT touch `src/` or the golden submission).
**Date:** 2026-06-15. **Scripts:** `cross_encoder_rerank.py` (sweep), `cross_encoder_holdout.py` (gate).

## Hypothesis
Field evidence: cross-encoder repos beat our hand pipeline on **NDCG@10** (the 50%-weighted metric) —
WorthyHire 0.857, Redrob-PMP 0.852 vs our 0.829. So a top-K cross-encoder rerank might lift our NDCG@10.

## Method
- Replicated WorthyHire's recipe: `cross-encoder/ms-marco-MiniLM-L-6-v2`, pairs `(JD, candidate_text)`,
  min-max normalize, blend `final = (1-w)·hand_norm + w·CE_norm`, rerank the top-500 pool → top-100.
- Scored every blend weight against the 100K frozen blind arbiter.

## Result 1 — in-sample sweep (MISLEADING)
Baseline reproduced exactly (0.8625). Blending appeared to help across w_ce ∈ [0.10, 0.50] and both JD
representations — peak **+0.014** (0.8768) at w_ce=0.50, NDCG@10 0.829 → 0.845. Looked like a real win.

**But `w_ce` was selected ON the blind arbiter — in-sample / optimistic.**

## Result 2 — train/holdout gate (TRUTH)
Split the 100K blind labels by candidate-id hash: TRAIN=49,702 / TEST=50,298. Select `w_ce` on TRAIN
only; measure on the untouched TEST half.

| w_ce | train | test (holdout) | test vs base |
|---|---|---|---|
| 0.00 baseline | 0.8930 | **0.8461** | — |
| 0.20 | 0.8990 | 0.8447 | −0.0014 |
| **0.40 (w\* on train)** | 0.9033 | **0.8298** | **−0.0163** |
| 0.50 | 0.8938 | 0.8270 | −0.0191 |

**w\* chosen on train (0.40) → −0.0163 on holdout. Every weight ≤ baseline on held-out labels.**

## Verdict: REJECTED — measured negative #11
The in-sample +0.014 was overfitting to the arbiter; under proper train/holdout gating the cross-encoder
rerank is a **net negative (−0.016)**. This is the same failure mode as measured negatives #3/#6/#7/#9
(rerankers that looked good on a selection set and lost on held-out labels). The cross-encoder — the
field's most-hyped weapon, and the only one that beats us on in-sample NDCG@10 — does **not** generalize.

**Double reason to reject:** (1) it loses on held-out labels; (2) it requires `torch` + a downloaded
model, breaking the 100% offline / no-GPU / byte-deterministic / golden-hash guarantees that are our
core differentiator. The frozen hand pipeline (`af8f2b32`) stands. The model lever is empty — now
confirmed even for cross-encoders.
