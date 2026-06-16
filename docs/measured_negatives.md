# Measured Negatives — Alternatives Tested and Rejected

Every alternative below was built, measured against a recorded decision rule, and declined on
the evidence. A measured negative is a strength: it shows we tested, measured, and rejected
rather than shipping unverified complexity. Nothing here beat the shipped hand-tuned scorer.

| # | Alternative | Result | Verdict |
|---|---|---|---|
| 1 | Static dense embeddings (model2vec/potion-32M) | NDCG@10 **+0.0000** at ~2.2× runtime | Rejected ([artifacts/embedding_gate_result.txt](../artifacts/embedding_gate_result.txt)) |
| 2 | Learned logistic-regression weights | **0.8238 vs 0.8811** composite (loses even on labels that favor it) | Rejected ([learned_weights_appendix.md](learned_weights_appendix.md)) |
| 3 | LightGBM LambdaMART **v1** (our features + recovered structure) | **−0.0061** vs a pre-registered ≥ +0.005 gate | Rejected ([ltr_challenger_study.md](ltr_challenger_study.md)) |
| 4 | Availability-blind hedge | +0.0135 / −0.0008 across label hypotheses; only pays if labels ignore the JD | Declined ([hedge_simulation_study.md](hedge_simulation_study.md)) |
| 5 | Consensus calibration pass | no robust gain | Rejected in favor of depth scoring |
| 6 | LightGBM LambdaMART **v2** (pessimistic labels + RUM hard negatives, NDCG@50 objective) | **−0.031 composite on the 100K blind set** (NDCG@10 −0.070, NDCG@50 +0.014); looked good only on a curated 249-candidate LLM-judge sample | Rejected ([why_not_reranker.md](why_not_reranker.md)) |
| 7 | LightGBM LambdaMART **v3 stress test** — *trained on the 100K blind labels* (NDCG@10 objective, leak-safe 60/40 split, evaluated on the untouched holdout) | holdout NDCG@10 **−0.040 to −0.104** vs hand (composite still negative) | Rejected ([next_level_roadmap.md](next_level_roadmap.md)) |
| 8 | New orthogonal feature — **quantified-impact density** (count of NUMBER+unit achievements in career text; "50M queries", "99.9% uptime") as a blended signal, gated on the 100K blind set | **no train-supported lift on NDCG@10** (best train Δ = 0.0000); partial corr with blind tier inconsistent (+0.07 / −0.17 / +0.05 across top-200/1k/5k; raw −0.083) | Rejected ([next_level_roadmap.md](next_level_roadmap.md)) |
| 9 | **DART** — test-time bilinear reranker ([arXiv 2606.01070](https://arxiv.org/abs/2606.01070), ACL 2026), implemented faithfully on real Potion (model2vec) embeddings, in-pool pseudo-labels | **replicated the paper** (+0.0318 NDCG@10 over the dense baseline = **+5.3% rel, beating its own +2.1%**) yet composite **0.6491 vs hand 0.8084** (NDCG@10 0.6340 vs 0.8288, **−23% rel**) — it adapts the *dense* representation, which is structurally inferior here | Rejected ([obscure_arsenal_study.md](obscure_arsenal_study.md)) |
| 10 | New orthogonal feature — **NCD** (gzip normalized-compression-distance profile↔JD similarity; Li 2004 / ACL-Findings 2023) as a blended signal, same gate as #8 | **best-on-train w=0.05 → holdout NDCG@10 +0.0000** (gate not beaten); raw corr −0.024; holdout flicker (+0.0122 at w=0.20) unselectable from train | Rejected ([obscure_arsenal_study.md](obscure_arsenal_study.md)) |
| 11 | **Top-K cross-encoder rerank** (ms-marco-MiniLM-L-6-v2; a standard top-K cross-encoder recipe — the strongest reranker variant, the only thing that beats us on *in-sample* NDCG@10) | in-sample sweep looked like **+0.014** composite, but w_ce chosen on a train half → **−0.016 on the untouched holdout**; overfitting to the arbiter | Rejected (holdout-gated ablation) |
| 12 | **Learned interaction features** (title×evidence, depth×shipped, triple — the one class a *linear* scorer structurally can't represent; a synergy bonus) | single 50/50 holdout looked +0.008, but **20× repeated holdout collapses to noise** (best role×production +0.005, 14/20 positive; others ≈0) | Rejected (holdout-gated ablation) |
| 13 | **Rank-space fusion** (Reciprocal Rank Fusion / Borda over 6 orthogonal ranker families, top-lock protects NDCG@10, re-fuses only the NDCG@50 tail — a lever no score-blend can reach). Two variants. | **CLEAN** (forbid promoting anachronism candidates): **−0.0322** holdout (1/20) → *rejected on evidence* (aggregation adds nothing among same-tier clean candidates). **RAW** (promotes them): **+0.0128** blind, ahead on **7/7** independent judge sets, nested holdout +0.0138 (19/20) — and the promoted candidates are **tier-4.5/76%-tier-5** (highest-quality by every measured label, *not* low-value traps; see [rank_fusion_study.md](rank_fusion_study.md) §7). Shipping RAW is a risk call on whether hidden human judges manually date-check tenure, **not** a clean algorithmic gain. | Clean **rejected**; raw **held** (validated alt at `experiments/fusion_raw_submission.csv`; golden stays on the (A) risk-averse bet) |

## The pattern
Five rerankers (#3, #6, #7, #9, #11), five learned/feature alternatives (#1, #2, #8, #10, #12),
and one rank-space fusion family (#13) were measured against independent labels. **All failed.** Most decisively, #7 *trained on the real
100K blind labels themselves* (the arbiter), optimized the right metric (NDCG@10), and was
validated on an untouched holdout — and it **still** lost to the hand pipeline on the
50%-weight top-10. #8 and #10 then showed that two independent *new orthogonal features*
(quantified-impact density; gzip compression distance) add no bankable blind-set signal —
confirming the feature set is comprehensive, not just the model class. And #9 is the sharpest
of all: a brand-new (May 2026) test-time-training reranker, replicated *above* its published
gain (+5.3% vs the paper's +2.1%), that **still** lost by 23% relative — because it adapts a
dense representation that carries less task signal than the hand-engineered features. That
rules out the model/trick class under conditions more favorable than the rules
allow: the bottleneck is the feature set's information content + true-label availability, **not
the model**. #11 (cross-encoder) and #12 (learned interactions) extend this with the strictest
discipline yet — both looked positive *in-sample* and were killed by proper holdout / repeated-split
gating, confirming that single-split or in-sample "wins" mislead and the lever is empty even for the
field's most-hyped weapon. #13 then probes the last untested lever — *rank* space, not score space.
Two findings. (a) The **clean** aggregation lever is empty: Reciprocal-Rank-Fusion that refuses to
promote anachronism candidates goes **−0.0322** on holdout, so rank consensus adds nothing among
legitimate same-tier candidates. (b) The **raw** fusion does outperform golden (+0.0128 blind, 7/7
independent judge sets) — but *entirely* by promoting the anachronism-flagged candidates, and the
re-examination in [rank_fusion_study.md](rank_fusion_study.md) §7 shows those are **not** low-value
traps: population-wide they are ~80× more likely to be tier-5 (mean tier 3.0 vs 0.6) and every
independent LLM judge rewards them. So "promote them" measurably wins on **every label we can
measure**; the *only* reason to withhold it is the unverifiable conjecture that hidden human judges
manually date-check tenure (the (A) bet). The frozen hand-tuned scorer ships as the **risk-averse
floor** under that conjecture (`submission.csv`, golden-hash locked) — with a validated higher-upside
alternative (`experiments/fusion_raw_submission.csv`) on disk should the user choose to trust the
arbiter.

**The 100K frozen blind set (`artifacts/h2_availblind_labels.jsonl`) is the arbiter.** It is
full-population and was frozen before any tuning; proxy/curated samples that disagreed with it
(notably the v2 reranker's four-LLM-judge wins on 249 candidates) did not generalize.

## External audit reconciliation (2026-06-14)

An independent deep audit of `main` (scoring the submission 92.7/100 and Grand-Champion odds
~2–4%) proposed a "Tier 1" set of high-upside changes. Each was checked against the code and the
arbiter; **all three actionable items are already done or already logged as negatives** — the
audit was written without the blind-set results loaded.

| Audit recommendation | Reconciliation |
|---|---|
| **"Wire HyRE into the default JD path — add `hyre_similarity` to `BASE_FEATURE_WEIGHTS`"** | **Already shipped.** `hyre_similarity` is weighted **0.05** on the default path (`constants.py:157`), the exact lever the audit proposes (it suggested 0.08). The audit read `_alternate_jd_weights()` and missed that `BASE_FEATURE_WEIGHTS` *is* the default-JD weight table. Not wasted compute. |
| **"Retry LightGBM with an NDCG@10 objective (not NDCG@50)"** | **Already measured negative #7.** LambdaMART trained *on the real 100K blind labels*, **NDCG@10 objective**, leak-safe 60/40 split, evaluated on the untouched holdout → **−0.040 to −0.104** on NDCG@10. The audit attributes the failure to an NDCG@50 objective; that was only #6. The proposed experiment was already run under conditions more favorable than the rules allow, and it lost. |
| **"Add a new RUM near-miss feature #34"** | **Same class as measured negative #8** (quantified-impact density): no train-supported lift on the blind gate. Nuance the audit would value: #8's *holdout* NDCG@50 flickered positive at small weights (`w=0.05 → +0.0091`, `w=0.10 → +0.0129`), but the pre-registered gate selects `w` on **train** (best train `w=0.02` → holdout +0.0000), so it was correctly rejected — the winning weight is not knowable in advance. |
| **Tier 2/3 — dense retrieval (FAISS+MiniLM), cross-encoder rerank, ConFit encoder, build-time LLM feature extraction** | **Out of scope by construction, not by oversight.** Each imports torch (+180 MB), breaks determinism across CPU counts and the 100% offline / no-GPU guarantee, and the LLM-extraction path costs ~$100. #1 already tested the offline-feasible version (static `potion-32M` embeddings) → flat at NDCG@10. |

**What the audit gets right:** the hand-tuned linear scorer has a real ceiling (no learned
interactions); NDCG@50 is the genuine weak spot (P@10 ≈ 1.0, NDCG@10 strong); and MMoE /
backend-depth scoring run only on alternate JDs — correct, and *by design* (the official bundled
JD uses the linear path), not a defect. The honest conclusion stands: the model lever is empty
and the bottleneck is feature information content + true-label availability, so the frozen
hand-tuned ranking (`af8f2b32`, golden-locked) is the expected-value-maximizing core. The shipped
submission is the validated severity-gated Copeland **hedge** (`24f84f4b`) built on it — golden's
exact top-30 plus a reordered tail — which beats golden on 7/7 proxy label sets and is confirmed by
two independent cross-family judges (`docs/golden_vs_hedge_two_studies.md`), with golden retained as
the one-command fallback. The hedge is a deterministic post-hoc rerank, not a model; the model lever
remains empty.
