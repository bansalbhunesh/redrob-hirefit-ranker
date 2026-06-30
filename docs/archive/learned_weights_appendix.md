# Appendix: learned weights vs hand-tuned weights (Phase 6)

Pool: 100,000 candidates; binary target = independent tier >= 3 (1,294 positives). L2 logistic regression on the 28 features + clamped BM25 (the exact base-score inputs), stratified 5-fold CV, ranking by OUT-OF-FOLD probability; identical guardrail multipliers applied to both systems.

**Caveat:** the independent labels are rule-derived from profiles, so a model trained on them partially re-learns the labeling heuristic -- the independent column flatters the learned model. LLM-judge shown with coverage.

| base scorer | composite (independent) | composite (LLM judge) | LLM coverage |
|---|---|---|---|
| hand-tuned (shipped) | 0.8811 | 0.8959 | 100% |
| learned LR (OOF) | 0.8238 | 0.7716 | 56% |

Top-100 overlap between the two systems: **54/100**.

## What the model learned (mean |coef| across folds, top 12)

| feature | LR coef | hand weight (normalized) |
|---|---|---|
| production_evidence | +10.031 | 0.115 |
| availability_score | +8.186 | — (not in base score) |
| ir_ranking_experience | +6.538 | 0.106 |
| responsiveness_score | +6.286 | — (not in base score) |
| bm25_score | +4.743 | 0.088 |
| career_trajectory_score | +4.469 | 0.062 |
| yoe_fit_score | +4.083 | 0.053 |
| scale_signal | -3.890 | 0.027 |
| endorsement_trust | +2.162 | 0.018 |
| senior_title_held | +1.659 | 0.035 |
| nice_skill_match | +1.619 | 0.035 |
| consulting_only_flag | -1.382 | — (not in base score) |

## Verdict

The learned base scorer does not beat the hand-tuned weights even on labels that structurally favor it. The hand weights ship: they are explainable per-feature, stable without a training set, and free of label-leakage risk.
