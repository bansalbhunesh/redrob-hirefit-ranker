# Obscure Arsenal — Seven "Teams-Don't-Know-This" Techniques, Measured

A second external research dump proposed seven genuinely obscure techniques (test-time
training, compression distance, spectral seriation, hard-negative mixing, integer
programming, MDL, static embeddings) claimed to move NDCG@50 within our CPU-only /
deterministic / offline constraints. Unlike the previous dump (which misread the code),
**every citation here is real** — verified on arXiv / ACL / JMLR. So we tested them on the
arbiter: the 100K frozen blind set (`artifacts/h2_availblind_labels.jsonl`).

**Result: none beats the shipped hand scorer.** The most striking, DART, *faithfully
replicated its paper's claim and still lost by 23% relative* — because it adapts the dense
representation that is structurally inferior here, not the algorithm. This is the central
lesson restated: the bottleneck is representation/feature information content + true labels,
**not the model or the trick.**

Branch: `codex/obscure-arsenal`. Scripts: `scripts/exp_obscure_ncd.py`,
`scripts/exp_obscure_dart.py`, `scripts/exp_obscure_spectral_mdl.py`. Protocol mirrors the
pre-registered blind-gate used for measured negative #8 (leak-safe 60/40 where a tunable
weight exists; direct full-blind evaluation for unsupervised rerankers).

## Citation verification (all real)

| Technique | Source | Verified |
|---|---|---|
| DART — test-time reranking | [arXiv 2606.01070](https://arxiv.org/abs/2606.01070), Liu & Li, 31 May 2026 | ✅ real; +2.1% rel NDCG@10 over a **dense** baseline, <10ms/query |
| SerialRank — spectral seriation | [JMLR v17 16-035](https://jmlr.org/papers/volume17/16-035/16-035.pdf), Fogel/d'Aspremont/Vojnovic | ✅ real; Fiedler vector of similarity Laplacian |
| gzip NCD | [ACL-Findings 2023](https://aclanthology.org/2023.findings-acl.426.pdf) (Jiang et al.); NCD: Li et al. 2004 | ✅ real |
| MoCHi — hard-negative mixing | [arXiv 2010.01028](https://arxiv.org/abs/2010.01028), NeurIPS 2020 | ✅ real (computer-vision contrastive) |
| Integer programming selection | scipy `milp` / OR | ✅ standard |
| MDL feature selection | information theory (Rissanen) | ✅ standard |
| Model2Vec / Potion | [github.com/MinishLab/model2vec](https://github.com/MinishLab/model2vec) | ✅ real (= our measured negative #1) |

## 1. NCD (gzip compression distance) — FAILS the gate

`similarity = 1 − NCD(profile, JD)` as feature #34, exact protocol as #8.

```
partial corr(ncd|hand):  top-200 -0.067 | top-1000 +0.137 | top-5000 +0.072   (raw -0.024)
hand holdout: NDCG@10 0.7123
  best-on-train w=0.05  -> HOLDOUT NDCG@10 +0.0000     <= GATE NOT BEATEN
  (flicker: w=0.20 holdout +0.0122, w=0.50 +0.0113 — but train can't select that weight)
```

Identical signature to quantified-impact density (#8): a faint orthogonal signal the
pre-registered, leak-safe gate cannot bank, because the train split doesn't identify the
weight at which holdout improves. Honest verdict: **rejected.**

## 2. DART (test-time bilinear adaptation) — REPLICATES, still loses by 23%

Implemented faithfully in DART's actual setting: a bilinear matrix `W` over real Potion
(model2vec, 512-d) embeddings of JD and all 100K candidates, `W=I` at step 0 (= dense
cosine baseline = measured negative #1), margin-rank loss with confidence weighting,
in-pool pseudo-labels on the dense top-200. Unsupervised (pseudo-labels from base scores,
never the blind labels), so evaluated directly on the full blind set.

```
method                  NDCG@10   NDCG@50   composite
hand (ship)              0.8288    0.8270      0.8084
dense baseline (#1)      0.6022    0.6895      0.6257
DART best (lr=0.05)      0.6340    0.6980      0.6491   (moved 195/200)
```

DART **works** — +0.0318 NDCG@10 over dense (**+5.3% relative, exceeding the paper's
+2.1%**), order demonstrably changed (195/200 candidates re-ranked). But it adapts the
*dense representation*, which on the blind set sits 23% below the hand scorer. Test-time
adaptation cannot close a structural representation gap: best DART composite **0.6491 vs
hand 0.8084**; even DART's paper-ceiling (+2.1% on dense) → NDCG@10 ~0.6149 vs hand 0.8288.
**Rejected** — the technique is real and replicates; the lever it pulls is the wrong one.

## 3. Spectral seriation (SerialRank) — catastrophic

Re-order the contested hand top-K by the Fiedler vector of the feature-cosine Laplacian.

```
hand:               NDCG@10 0.8288  (17,811 exact-tie groups, max group 22 — ties are real)
seriation top-50:   0.7781  (-0.0508)
seriation top-100:  0.5435  (-0.2853)
seriation top-200:  0.5108  (-0.3180)
```

Seriation recovers an ordering consistent with *pairwise similarity structure*, which is
orthogonal to JD-relevance — so the more it reorders, the worse it gets. The audit's
"tie-breaking" premise is real (ties exist), but ordering ties by cluster structure is
anti-correlated with relevance. **Rejected.**

## 4. MDL feature pruning — validates the set, doesn't shrink it

Greedy forward selection over the 21 weighted features minimizing
`L = k·log₂n + n·log₂(RSS/n + 1)` against the blind tier.

- Min-MDL at **15 / 21** features; the 15→21 gap is **~0.1%** (69305 → 69380).
- Order of marginal information: `career_trajectory_score`, `production_evidence`,
  `code_writing_recent`, `product_company_ratio`, `yoe_fit_score`, `ml_ai_tenure_score`,
  **`hyre_similarity` (#7)**, … — independently confirming HyRE is a genuine default-path
  contributor (refutes the earlier audit's "wasted compute" claim).
- Features ranked last (`core_skill_match`, `ir_ranking_experience`) are not useless — they
  are highly correlated with already-selected features, so they add little *marginal linear*
  signal, but they carry guardrail/multiplicative interactions a linear MDL proxy can't see.

Pruning 6 features for a 0.1% MDL gain would risk the hand-tuned multiplicative interactions
that survived blind validation, for no measurable benefit. **Not adopted** — the submission
stays at 21 weighted features.

## 5–6. Reasoned out (not implemented)

- **MoCHi synthetic hard negatives** — proposed to rescue the LightGBM reranker. But the
  reranker is already a *triple* measured negative (#3/#6/#7), and #7 trained on the *real*
  blind labels with the right objective and still lost. Synthetic negatives change the
  training distribution, not the underlying label-information bottleneck. Declined.
- **Integer programming top-100 selection** — proposed for diversity/fairness. It maximizes
  a constrained objective by *sacrificing* score-optimal picks, which directly lowers
  NDCG@10/@50 (the 80%-weighted metrics) by construction; and its fairness constraints
  depend on *inferred gender*, which is neither in the candidate data nor ethically sound to
  impute. We already enforce fairness via 12 counterfactual tests, not by quota. Declined.

## The pattern (extended)

Seven obscure, correctly-cited techniques — and the score-moving ones (NCD, DART, spectral)
all failed on the arbiter; the analysis ones (MDL) validated the existing design. DART is the
sharpest data point yet: a brand-new (May 2026) test-time method, replicated *above* its
published gain, that still loses by 23% relative — because the hand-engineered 33-feature
representation carries more task signal than dense embeddings do here. The model/trick lever
is empty; the open levers remain feature information content and access to true human labels.
The frozen hand-tuned submission (`af8f2b32`, golden-locked) is the expected-value ship.
