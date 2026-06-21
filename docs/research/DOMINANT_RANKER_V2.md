# redrob_ranker_v2 — a new (learned) ranking model

This is a **separate model**, built per the directive "make a dominant model, not
upgrade this one." It does **not** reuse the existing pipeline's hand-tuned
`BASE_FEATURE_WEIGHTS`. Where the v1 ranker is a hand-weighted linear blend, v2's
scorer is a **LightGBM LambdaMART** ranker that *learns* the weighting from the
label signal — which is exactly the "learning-to-rank (XGBoost-based or neural)"
the JD lists as a desired skill, and which fits the CPU-only / no-network / 5-min
constraints (gradient-boosted trees are tiny and fast at inference).

## Architecture

```
score = normalize( LambdaMART.relevance(features) ) * honeypot_gate * disqualifier_gate
```

- **Features**: the shared 33-feature vector + normalized BM25 = 34 columns
  (`V2_FEATURES`). The extractor is shared infra (data prep), not the model.
- **Learned scorer** (`model.LearnedRanker`): LightGBM `lambdarank`, optimizing
  NDCG@{10,50} directly. If `models/ltr_v2.txt` is absent, a transparent linear
  fallback (JD-anchored weights, independent of v1) runs so the pipeline works
  before training.
- **Integrity gates stay outside the learned model** (multiplicative, after
  scoring) so a honeypot or disqualified profile can never be promoted into the
  top-100 regardless of what the model learns — this is what keeps the
  "honeypot rate in top-100 <= 10%" disqualifier provably safe.
- Deterministic; ties break by `candidate_id` ascending (matches the official
  validator).

## Files

| File | Role |
|------|------|
| `src/redrob_ranker_v2/model.py` | `LearnedRanker` (LightGBM + fallback) |
| `src/redrob_ranker_v2/pipeline_v2.py` | load → BM25 → features → score → gate → top-k |
| `src/redrob_ranker_v2/train.py` | LambdaMART trainer with k-fold CV |
| `rank_v2.py` | CLI entry point (mirrors `rank.py`) |
| `tests/test_ranker_v2.py` | smoke + contract + gate tests |

## Status (what is verified vs pending)

Verified in this environment, **without** the candidate pool (fallback model):
- Runs end-to-end on the 50 real `sample_candidates.json` profiles: deterministic,
  grounded reasoning, honeypots gated, valid output.
- Full 100K pool at **2 CPU in 122.4 s** (< 300 s budget), **passes the official
  `validate_submission.py`**.
- 4/4 v2 tests pass.

**Pending the 100K `candidates.jsonl` (the only blocker):** training the
LambdaMART model and the head-to-head dominance measurement. "Dominant" is a
*measured* claim and is not asserted until the numbers exist.

## How dominance gets decided (the moment data lands)

```bash
# 1. train the learned model on the proxy labels
PYTHONHASHSEED=0 PYTHONPATH=src python -m redrob_ranker_v2.train \
    --candidates candidates.jsonl \
    --labels docs/llm_judge_eval_labels.jsonl docs/llm_judge_eval_2_labels.jsonl \
             docs/llm_judge_eval_3_labels.jsonl \
    --out models/ltr_v2.txt --folds 5          # prints held-out CV composite

# 2. produce the v2 submission and score it on every label world
PYTHONHASHSEED=0 python rank_v2.py --candidates candidates.jsonl --out v2_submission.csv
PYTHONHASHSEED=0 PYTHONPATH=src python -m redrob_ranker.eval_harness \
    --submission v2_submission.csv \
    --labels docs/llm_judge_eval_labels.jsonl docs/llm_judge_eval_2_labels.jsonl \
             docs/llm_judge_eval_3_labels.jsonl
```

Decision rule: v2 ships only if its **held-out CV** composite beats v1 **and** it
**dominates on every label set** (no per-world regressions) — current v1 bar is
mean composite **0.9379**. If it does not dominate, v1 stays; I will not present
an unmeasured or in-sample-overfit number as a win.
```
