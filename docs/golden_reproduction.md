# Golden Submission Reproduction Record

## Current golden artifact

- `submission.csv` SHA-256: `e1a696d1f575908c8544fae294e04dcbf4edd4bad8ee5215aae2072c867493f7`
- Produced by: `PYTHONHASHSEED=0 python rank.py --candidates ./candidates.jsonl --out ./submission.csv --bm25-backend bm25s`
- Verified byte-identical from two independent environments:
  - Windows 11 local (Python 3.14, 70.3s wall, 8 workers)
  - python:3.11-slim Docker container (Linux, `submission_docker.csv`, 2026-06-10 01:56 run)
- Locked by `tests/test_submission_gate.py` (validator gate + full-file hash + 2K-slice
  re-rank regression, slice hash `455d08d4...`).

## 2026-06-10 drift incident (resolved)

**What happened.** `submission.csv` was last regenerated at commit `bea0bfd`. Two later
audit commits changed code without regenerating it:

- `6a643dc` — behavior-neutral for valid data (env-overridable REFERENCE_DATE with the
  same pinned default, exception narrowing, malformed-candidate guard).
- `c6bd5c9` — **behavior-changing**: added BM25 stopword filtering in `text.py::tokenize`
  and a senior-tenure exemption in the `features.py` hop_signal. Result: 19 of 100 ranks
  differed between HEAD output and the committed CSV (old golden
  `1bcbf705...`).

**Measurement.** Both orderings were scored against both label sets with the challenge
composite (0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10):

| Ordering | Independent heuristic (100K labels) | LLM judge (249 labels) | Mean |
|---|---|---|---|
| Old golden (`bea0bfd` behavior) | 0.8810 | 0.8959 | 0.88845 |
| HEAD (`c6bd5c9` behavior) | 0.8811 | 0.8959 | 0.88850 |

Top-10 identical under both label sets (tiers `[5,5,4,4,5,5,5,5,5,5]` LLM-judge;
all tier-5 heuristic). NDCG@10 unchanged to 4 decimals. The orderings are
statistically indistinguishable; differences are confined to lower ranks.

**Resolution.** Kept HEAD behavior and regenerated `submission.csv` (new golden hash
above), because (a) measured quality is equal, (b) `c6bd5c9` also carries genuine
robustness fixes that should not be reverted, and (c) HEAD output is already verified
byte-identical across Windows and Linux/Docker. The uncommitted overnight perf rewrite
of `candidate_text` (unverified against golden output) was moved off main to branch
`wip/perf-experiments-20260610`.

**Prevention.** `tests/test_submission_gate.py` now fails any commit whose code changes
ranking bytes on a fixed 2K slice, and any commit that touches `submission.csv` without
updating the recorded hash. Intentional changes must cite the pre-registered decision
rule in `docs/sensitivity_sweep.md` and update both hashes in the same commit.

## Determinism notes

- `rank.py` does NOT re-exec to pin `PYTHONHASHSEED` (removed in `6a643dc`); it only
  warns. Always run with `PYTHONHASHSEED=0` (the Dockerfile sets it; set it manually
  for local runs). Without it, one normalized score's 6th decimal can wobble (rank
  order unaffected).
- `submission.csv` uses CRLF row terminators on all platforms (csv module with
  `newline=""`), so hashes are OS-independent.
