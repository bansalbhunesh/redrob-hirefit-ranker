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

## Results (run after pre-registration; shared harness, policy=exclude)

| floor | composite (independent) | composite (LLM judge) | LLM coverage | mean composite | top-100 rows changed vs shipped | new entrants |
|---|---|---|---|---|---|---|
| 0.25 | 0.8811 | 0.8959 | 100% | 0.8885 | 0 | 0 |
| 0.40 | 0.8811 | 0.8959 | 100% | 0.8885 | 0 | 0 |
| 0.55 | 0.8811 | 0.8959 | 100% | 0.8885 **<- winner** | 0 | 0 |
| 0.70 | 0.8811 | 0.8959 | 99% | 0.8885 | 15 | 1 |
| 0.85 | 0.8805 | 0.9036 | 86% | 0.8920 | 72 | 15 |
| 1.00 | 0.8724 | 0.9258 | 67% | 0.8991 | 93 | 37 |

Unlabeled top-100 entrants across all configurations: **0** (see `artifacts/sweep_unlabeled.jsonl`).

**Comparability guard:** configs with <95% coverage on either label set (floors 0.85, 1.00) are excluded from winner selection -- their LLM-side composite is computed on a shrinking, selection-biased sample (the excluded unlabeled entrants are exactly the unavailable profiles the floor un-demotes), while the full-coverage independent composite *falls*. This is the pre-registered 'label sets disagree' regime: break toward down-weighting.

**Decision per pre-registered rule:** floor = **0.55** (softest configuration among those exactly tied at the best mean composite on full coverage).

The minimum behavioral multiplier inside the shipped top-100 is **0.7398**, so every tied floor (up to that value) yields a **byte-identical `submission.csv`** -- the tied configurations differ only for candidates already outside the top-100.
**Outcome: the shipped artifact is unchanged.** The floor constant is kept at 0.25 in code: switching it to another tied value would not change a single submitted byte, and leaving the golden-locked constant untouched avoids no-op churn on the official path.

## Provenance note (added 2026-06-11)

The decision rule above was written before the first sweep execution, but this
document — rule and results together — landed in a single commit (`2f0e7c7`),
so git history cannot independently prove the ordering. We state that limitation
rather than claim more than the record supports. The protocol was corrected for
the next study: the LTR challenger gate was committed on its own
(`8db18f6`, 2026-06-10 19:41) before the study that evaluated it
(`c47b208`, 2026-06-10 22:03), so that pre-registration is verifiable from
history alone.
