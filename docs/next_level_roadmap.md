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

### 1.1 Re-run the reranker, but gated on the blind set (not the proxy)
Our reranker failed *because we validated it on the wrong target*. The same retrieve-then-rerank
machinery, **trained on a held-out split and selected by blind-set NDCG@10 + composite**, would
either (a) clear the bar honestly, or (b) be rejected early — both outcomes are wins. Critically,
optimize for **NDCG@10** (50% weight), not NDCG@50 (where the proxy lured us). Risk: using the
blind set for *selection* can leak; mitigate with nested CV and a final untouched hold-out slice.

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
We are at the **architecture ceiling** for this label regime. The next real gains come from
**better labels and blind-set-gated robustness (RRF, ELO calibration, top-10 focus)** — not from
a fancier model validated on a proxy. Every measured negative we shipped is itself a Stage-5
asset: it proves we validate against ground truth, not vibes.

**Sources:** [ConFit v3](https://arxiv.org/html/2605.09760v1) ·
[ConFit v2](https://arxiv.org/pdf/2502.12361) ·
[Reciprocal Rank Fusion, SIGIR 2009](https://dl.acm.org/doi/10.1145/1571941.1572114) ·
[Explainable person–job recommendation, Frontiers 2025](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1660548/full)
