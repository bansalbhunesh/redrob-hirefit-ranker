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

## The pattern
Three learned rerankers (#3, #6, #7) and three learned/feature alternatives (#1, #2, #8) were
measured against independent labels. **All failed.** Most decisively, #7 *trained on the real
100K blind labels themselves* (the arbiter), optimized the right metric (NDCG@10), and was
validated on an untouched holdout — and it **still** lost to the hand pipeline on the
50%-weight top-10. #8 then showed that even a thoughtfully-chosen *new orthogonal feature* adds
no blind-set signal — confirming the feature set is comprehensive, not just the model class. That rules out the model class under conditions more favorable than the rules
allow: the bottleneck is the feature set's information content + true-label availability, **not
the model**. The hand-tuned linear scorer with multiplicative behavioral / honeypot /
disqualifier guardrails is the only approach that survived independent validation — and it is
what ships (`submission.csv`, golden-hash locked).

**The 100K frozen blind set (`artifacts/h2_availblind_labels.jsonl`) is the arbiter.** It is
full-population and was frozen before any tuning; proxy/curated samples that disagreed with it
(notably the v2 reranker's four-LLM-judge wins on 249 candidates) did not generalize.
