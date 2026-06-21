# Pipeline audit — strength, speed, stability (2 CPU / 16 GB target)

Branch: `claude/audit-g2dv7y-pipeline`. Target runtime envelope: `docker run --cpus=2
--memory=16g`, 300 s hard limit (240 s safety margin). All numbers below are measured
on a 100K-candidate pool, `PYTHONHASHSEED=0`, BLAS threads pinned to 1, pinned to 2 CPUs
with `taskset -c 0,1`.

## TL;DR

The production ranker is already heavily optimized and runs **~92–100 s on the full 100K
pool at 2 CPU — about 3× under the 300 s budget**. Three candidate speed ideas were
prototyped and *measured*; two were rejected because they were slower, one shipped. Output
stays **byte-identical** to the golden baseline after every change (verified by the golden
submission gate and a direct 100K diff). The larger "make the ranking *significantly
stronger*" goal is **blocked by missing data**, not by the code — see the last section.

## Baseline (before changes)

| Stage (2 CPU, 100K pool)            | Time   | Parallel? |
|-------------------------------------|--------|-----------|
| load JSONL                          | ~5 s   | serial    |
| candidate_text build loop           | ~15 s  | serial    |
| BM25 (tokenize + index + score)     | ~37 s  | tokenize parallel; index/score serial |
| compute_features + final_score      | ~43 s  | parallel (ProcessPool) |
| **total (auto workers)**            | **100.2 s** | — |
| total (serial, workers=1)           | 131.9 s | — |

Current submission quality (shipped `submission.csv`, shared eval harness, `exclude` policy):

| label set                | NDCG@10 | NDCG@50 | MAP   | P@10  | composite |
|--------------------------|---------|---------|-------|-------|-----------|
| llm_judge_eval_labels    | 0.8943  | 0.9260  | 0.9853| 1.000 | 0.9227    |
| llm_judge_eval_2_labels  | 1.0000  | 0.8776  | 1.0000| 1.000 | 0.9633    |
| llm_judge_eval_3_labels  | 0.9432  | 0.8682  | 0.9704| 1.000 | 0.9276    |
| **mean composite**       |         |         |       |       | **0.9379**|

## Experiments run (the "keep experimenting" part)

1. **Parallelize `candidate_text` by shipping candidates to the worker pool** — REJECTED.
   Pickling 100K rich candidate dicts to workers costs more than building the text
   serially: 42.9 s vs 31.2 s for the text+tokenize phase. The existing design (serial
   text → parallel tokenize on lightweight *strings*) is already the right call at 2 CPU.

2. **Precompiled alternation regex for `semantic_concept_markers`** (50 substring scans
   per candidate) — REJECTED. Python's `in` substring test is already near-optimal and
   short-circuits; the alternation regex was 0.43× (slower). Markers were verified
   identical before rejecting.

3. **Cache the constant HyRE role-template token set** — SHIPPED. On the default path
   `jd_text` is a single constant, yet the template was re-tokenized once per candidate
   (100K times). Caching it is a pure function of the input and byte-identical. Verified
   identical scores to 1e-12 on the demo sample.

## Changes shipped on this branch

- `src/redrob_ranker/hyre_prompts.py`: `_hyre_token_set(jd_text)` (`lru_cache`) removes the
  redundant per-candidate re-tokenization of the constant role template. Byte-identical.
- `src/redrob_ranker/pipeline.py`: removed a duplicated `jd: object | None = None` field
  (with its duplicated comment) in `RankerConfig`. Dataclass-correctness cleanup; no
  behavior change.

## Verification (exhaustive, within this environment)

- **Byte-identical output**: 100K full-pipeline run after changes diffs clean against the
  pre-change baseline, and serial == auto-parallel == pinned-2-CPU all produce identical
  `submission.csv`.
- **Golden-hash + output gates pass**: `test_submission_gate`, `test_pipeline`,
  `test_features`, `test_reasoning`, `test_validation`, `test_jd_compiler` — 55 passed,
  1 skipped.
- **Full suite**: 160 passed, 9 skipped, 1 failed. The single failure is
  `test_metrics_manifest` (expects 198 collected tests, this environment collects 167
  because the torch / sentence-transformers optional-dependency test modules don't import
  here). The count is **167 both before and after** the change, so the failure is
  environment-driven and independent of this branch.

## The real blocker for "significantly stronger ranking"

To change *ranking quality* and prove it improved, you must be able to re-rank labeled
candidates and re-score the composite. That requires the candidate **profiles**. In this
repo:

- The full 100K `candidates.jsonl` is gitignored and not present (only the gitignored
  `data/` path and the `reproduce.sh` notes reference it).
- `demo_sample.jsonl` has 80 candidates *with* profiles but **zero overlap** with the 249
  labeled candidate IDs in `docs/llm_judge_eval_*_labels.jsonl`.
- The label files and `artifacts/h2_availblind_labels.jsonl` (100K) carry tiers/relevance
  but **no profiles**.

So any scoring-logic change can be applied, but its effect on NDCG/MAP cannot be measured
or validated here — and shipping an unmeasured ranking change would be exactly the kind of
unverifiable claim to avoid. **Unblock:** drop the real `candidates.jsonl` into the repo
root (or point `rank.py --candidates` at it). With that present, the experiment loop is:
vary weights/features → `rank.py` → `python -m redrob_ranker.eval_harness --submission … 
--labels docs/llm_judge_eval_*_labels.jsonl` → keep only changes that dominate across all
label sets, then test exhaustively.
