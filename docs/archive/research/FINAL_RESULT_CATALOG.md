# Final Result Catalog

Every experiment classified. Full detail + metrics in `experiments/registry.json`.

## Shipped
- **Golden ranking** (`af8f2b32`) — frozen, reproducible, deterministic; 171-test gate.

## Measured negatives (rejected on the blind arbiter / holdout)
- Dense/static embeddings (#1) · learned linear/logistic weights (#2) · LambdaMART v1/v2/v3
  (#3/#6/#7, incl. trained on the blind labels) · availability hedge (#4) · consensus
  calibration (#5) · quantified-impact density (#8) · gzip-NCD (#10) · DART test-time
  reranker (#9) · top-K cross-encoder (#11) · learned interactions (#12).
- **Evidence channels** (BM25F, requirement→evidence Hungarian, counterfactual masking):
  independent but no proxy gain (EXP-004).
- **Advanced directions**: dual-head graded integrity (−0.11), correlation-aware weighted RRF
  (−0.07) — refuted (EXP-007).

## Positive but NOT shipped (research-only)
- **Rank-space fusion** (EXP-001): +0.0108 nested, but anachronism-driven.
- **Integrity-constrained fusion** (EXP-003): 0 hard honeypots in top-10/100, but −0.13 proxy.
- **Ω causal/DRO** (EXP-008): formalises the decision; verdict `NO_RANKING_DOMINATES`.

## Fragile / downgraded
- **fusion-raw** (EXP-002): +0.0128 proxy, but 1.85 effective judges + 56% of gain from 5
  candidates; inverts to −0.011 without the anachronism class.

## Positive audits (explanation-only findings)
- **Judge-dependence** (EXP-005): 7 label sets ≈ 1.85 effective independent judges.
- **Candidate-influence** (EXP-006): fusion gain concentrated in 5 candidates.
- **Honeypot-count cross-verification**: our hard detector flags 0.29% of 100K (order of the
  ~80 planted); competitor 7.6–56% counts detect generic low quality.

## Awaiting human data
- **Ψ** (EXP-009): 24-candidate frozen panel; 0 responses; `AWAITING HUMAN DATA`.
- **Φ second coder** (EXP-010): `AWAITING_SECOND_CODER`.
- **Φ recruiter + India strata**: frozen protocol; not bulk-retrieved (ToS).

## Explanation-only product features
- **Integrity audit cards** (EXP-011): CLEAR/AMBIGUOUS/PROBABLE/CONFIRMED × CONTINUE/CLARIFY/
  VERIFY/DOWNRANK/BLOCK; golden top-100 = 45 CONTINUE / 52 VERIFY / 3 CLARIFY / 0 BLOCK.

## Superseded
- "fusion is a robust win on 7/7 judges" — superseded by EXP-005/006 (fragile).
- "anachronism candidates are honeypots to remove" — superseded by §7 (they are top-tier by
  every measurable label; the (A)/(B) question is unresolved, not settled).
- Dense-embeddings branch result — superseded by/duplicated in measured-negative #1.
