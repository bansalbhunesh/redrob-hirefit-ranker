# Taking HireFit to the Next Level — Research-Grounded Roadmap

**Date:** 2026-06-14. **Shipped baseline:** hand-tuned scorer + multiplicative guardrails,
golden `af8f2b32` (ranking byte-identical to `fdfd3f35`), wins on the 100K frozen blind set.

This roadmap is grounded in two things: (1) what the literature says is SOTA, and (2) what we
have actually **measured** on this dataset. The headline lesson constrains everything below.

## The binding lesson: the bottleneck is labels, not architecture

We built and measured six alternatives ([measured_negatives.md](measured_negatives.md)),
including **two** learned LightGBM rerankers. Both improved a *proxy* and then **failed the
100K frozen blind set** (v2: composite −0.031, NDCG@10 −0.070, despite +0.069–0.137 NDCG@50
across four LLM judges on a curated 249-candidate sample). The failure mode is **proxy
overfitting**: agreement among LLM judges on a narrow, correlated, top-of-pool sample did not
generalize to the full population.

**Therefore the #1 rule for any future work: the 100K blind set
(`artifacts/h2_availblind_labels.jsonl`) is the arbiter — not the LLM-judge sample.** Every
candidate improvement below must be gated on the blind set (or, better, real human labels),
with a pre-registered decision rule, exactly as the existing measured negatives were.

## Tier 1 — most promising, constraint-compatible (CPU / 300s / deterministic)

### 1.1 Re-run the reranker, but gated on the blind set (not the proxy) — DONE, NEGATIVE
We ran exactly this (`scripts/exp_tier1_blind_gated.py`, 2026-06-14): a LambdaMART **trained on
60% of the 100K blind labels**, NDCG@10 objective, evaluated on the untouched 40% holdout.

| Ranker | holdout NDCG@10 | NDCG@50 |
|---|---|---|
| hand pipeline | **0.7123** | 0.7112 |
| lambdarank@10 (31 leaves) | 0.6088 (−0.104) | 0.7072 |
| lambdarank@10 (63 leaves) | 0.6729 (−0.040) | 0.7296 (+0.018) |

**It still loses on the 50%-weight top-10**, even trained on the real labels with honest
validation and the right objective. This is measured negative #7 and the decisive result of this
roadmap: **the learned-model lever is empty.** The bottleneck is the *feature set* and
*true-label availability*, not the model class or label quantity. Corollary: RRF (1.2) over the
same signals will fail for the same reason — there is no orthogonal signal to fuse. Re-prioritize
toward **1.4 (better labels / a genuinely new orthogonal feature)**.

### 1.2 Robust rank fusion (RRF) instead of a single learned reranker
[Cormack et al., SIGIR 2009] show **Reciprocal Rank Fusion** beats Condorcet and individual
learned rankers, and it is **scale-invariant, calibration-free, and robust to score-distribution
differences** — precisely the failure mode that killed our learned reranker under label shift.
Fuse the hand scorer with a few *orthogonal* signals (BM25, depth scores, an offline static-
embedding rank) via RRF. Lower ceiling than a tuned model, but far more robust across label sets.
Caveat from the literature: RRF is "less adaptable than learned convex combinations" and can be
non-smooth under domain shift — so gate it on the blind set and keep the hand scorer as fallback.

### 1.3 Sharpen the top-10 specifically (50% of the score)
The pressure test showed the top of this pool is dense with near-identical elites; the top-10 is
strong but undifferentiated, and it is where 50% of the composite lives. Targeted moves:
**ELO/pairwise calibration** (recent work reports ELO-based pairwise training yields
well-calibrated scores that are **stable across candidate-set sizes and generalize across
domains** — directly addressing our small-sample→full-population gap), applied only to the top-K
boundary, blind-set-gated.

### 1.4 Better labels — the only thing that raises the ceiling
Architecture is saturated; label quality is not. Options, cheapest first:
- **Consensus-weighted multi-judge labels** (weight judges by blind-set agreement, not equally).
- **Active learning**: spend the LLM-judge budget on candidates where the hand scorer and judges
  *disagree* near the top-10 boundary, not on easy consensus cases.
- **A small human-validated set** (even 100–200 recruiter labels) would be worth more than any
  model change — it is the one thing that closes the proxy→hidden-human gap.

## Tier 2 — research-interesting, constraint-risky (offline/build-time only)

- **ConFit v3 (arXiv 2605.09760, 2026): LLM-based re-ranking for person-job fit** — the current
  SOTA, and explicitly *re-ranking*, not embeddings. It needs an LLM at re-rank time, which
  violates the no-network / 300s / deterministic rules at inference. Feasible only as an
  **offline, cached, build-time** feature (label/feature distillation), never live. Determinism
  and the JD's own "GPT-per-candidate doesn't scale" point still apply.
- **ELO/pairwise listwise training** (Tier 1.3) as a full scorer rather than a top-K patch.

## Tier 3 — measured negatives (do not revisit without new evidence)
Dense embeddings (+0.0000, 2.2× runtime), learned LR weights (0.8238 vs 0.8811), LambdaMART v1
(−0.0061 proxy), LambdaMART v2 (−0.031 blind), availability hedge, consensus calibration. See
[measured_negatives.md](measured_negatives.md) and [why_not_reranker.md](why_not_reranker.md).

## The one-line strategy
We are at the **model ceiling** for this feature set — proven by experiment 1.1, where a
LambdaMART *trained on the real blind labels* still could not beat the hand pipeline on held-out
NDCG@10. The remaining levers are therefore **(a) a genuinely new orthogonal feature/signal**
(more information, not a re-weighting of what we already have) and **(b) real human labels** (the
only thing that closes the proxy→hidden-human gap). Reranking, fusion, and calibration over the
*current* signals are exhausted. Every measured negative we shipped is itself a Stage-5 asset: it
proves we validate against ground truth, not vibes — and #7 shows we stress-tested even the
favorable case.

**Sources:** [ConFit v3](https://arxiv.org/html/2605.09760v1) ·
[ConFit v2](https://arxiv.org/pdf/2502.12361) ·
[Reciprocal Rank Fusion, SIGIR 2009](https://dl.acm.org/doi/10.1145/1571941.1572114) ·
[Explainable person–job recommendation, Frontiers 2025](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1660548/full)
