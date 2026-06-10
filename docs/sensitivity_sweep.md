# Behavioral-Multiplier Sensitivity Sweep

## Pre-registered decision rule (committed BEFORE the first sweep run)

> We ship the behavioral-multiplier configuration that maximizes the mean challenge composite
> across BOTH label sets (LLM-judge and independent heuristic). Ties or disagreements between
> label sets break toward the JD's explicit instruction to down-weight unavailable candidates,
> at the softest floor that does not lose composite. NDCG@10 alone is never the objective
> (too noisy at n≈249 labels).

Composite: `0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10`.

Unlabeled-candidate policy: **exclude** unlabeled candidates from metric computation and
report coverage %. Missing labels are never treated as tier 0.

## Sweep design

- Parameter: lower clamp (floor) of `compute_behavioral_multiplier`
  (shipped behavior: `clamp(mult, 0.25, 1.10)`).
- Floors swept: `0.25 (current)`, `0.40`, `0.55`, `0.70`, `0.85`, `1.00 (multiplier effectively off as a demotion)`.
- For each floor: re-rank the full pool, capture the top-100, score against both label sets
  via the shared harness (`src/redrob_ranker/eval_harness.py`).
- Unlabeled entrants: the union of candidates appearing in any configuration's top-100 with no
  label in either set is written to `artifacts/sweep_unlabeled.jsonl` and labeled by ONE
  incremental LLM-judge pass before scoring. No faked labels.

## Results

_(to be filled by `scripts/sensitivity_sweep.py` — not yet run)_
