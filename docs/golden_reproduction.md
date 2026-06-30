# Golden Submission Reproduction Record

## Current golden artifact

- `submission.csv` SHA-256: `8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`
  (2026-06-30: `frontier-v5` ranking with V6 exact-output hardening and a fail-closed
  `rank.py --release` gate; byte-identical in the pinned Docker image).
  The release path verifies `models/loss_aggregate_v3.npz`, forces BM25s and the
  champion profile, rejects partial/experimental configuration, verifies all
  counts and integrity outcomes, checks this hash, and only then atomically
  replaces the requested output. Earlier lineage below is retained as history.
  Lineage: `e1a696d1` → `ecb1fc5b` (Phase-4 reasoning) → `a2882cd2` (consensus
  ordering pass, since removed) → `6b284271` (HyRE/MMoE wiring) → `fdfd3f35`
  (reproducibility fix).

## 2026-06-10 Phase 4 reasoning upgrade (sanctioned text-only change)

Per the hardening brief's Phase 4: each top-100 row now carries one concrete,
verbatim-grounded career fact (company + the specific ranking/search/recsys
sentence quoted from that candidate's own `career_history`), plus wider
deterministic variety in the behavioral sentence. Hallucination guard locked
by tests (`tests/test_reasoning.py`): every injected company/snippet must be a
substring of the source candidate dict; same candidate -> same reason; 600-char
cap respected (observed max 516).

Verified before promoting: `candidate_id`, `rank`, and `score` columns are
byte-identical to the previous golden — only `reasoning` text changed (100/100
rows). Previous golden: `e1a696d1...`.

## Previous golden artifact (superseded 2026-06-10 by Phase 4)

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
- BLAS/threadpool thread counts are pinned to 1 (Dockerfile `ENV` + `rank.py`),
  so BM25 float-reduction order — and the output hash — is identical regardless
  of host CPU count (verified at `--cpus=2` and `--cpus=4`). Earlier goldens
  (e.g. `6b284271`) were minted at a higher thread count and did not reproduce at
  `--cpus=2`; the pin removes that dependency (docs/reproducibility_notes.md).
