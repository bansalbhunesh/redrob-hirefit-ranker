# Branch Retention Audit

Date: 2026-06-16 · Audited against `main` @ `75f900d` · Golden `af8f2b32` (unchanged).

## Method

For every remote branch: (1) ahead/behind vs `main`; (2) reachability of its commits from
`main`; (3) **files present in the branch but absent from `main`**; (4) **lines present in the
branch but absent from `main`** (`git diff --numstat main origin/<b>`, "added" column). A
branch is only eligible for deletion once its evidence is confirmed present in the consolidated
repo, and its unique commit history is preserved by an annotated tag where not already
reachable from `main`.

## Key finding

Across **all five** research branches, the only branch-unique content is:
- `README.md` (390 lines) — the **old monolithic README**, reorganized in `main` into dedicated
  docs (`docs/ARCHITECTURE.md`, `docs/ai_usage.md`, `docs/measured_negatives.md`,
  `METHODOLOGY.md`, `RESEARCH.md`, `GAPS.md`) with the HuggingFace live-demo link retained in
  `main`'s README and `apps/`.
- `docs/metrics_manifest.json` (2 lines) — the **superseded test count** (171; `main` is 198).

**Every research artifact** — `experiments/*.py`, `experiments/omega_outputs/*`,
`docs/human_opinion/*` (corpora, codebooks, manifests, logs), `experiments/registry.json`,
`docs/research/*` provenance — has **zero** branch-unique lines: fully present in `main`.
No file exists in any branch that is absent from `main`. Therefore no research evidence,
findings, manifests, code, documentation, or provenance is lost by removing these branches.

## Classification

| Branch | Tip | Ahead/Behind | Unique evidence? | Reachable from main | Class | Rationale |
|---|---|---|---|---|---|---|
| `main` | 75f900d | — | — | — | **KEEP** | Consolidated source of truth; frozen golden + full research program. |
| `integration/final-research-program` | 88958af | 0 / 4 | none | yes | **TAG-AND-DELETE** | Consolidation backbone; fully merged into `main`. Tagged `provenance/integration-final-research-program` for a named provenance anchor. |
| `research/competitor-validation` | 780050f | 7 / 9 | only superseded README+count | no | **TAG-AND-DELETE** | All evidence ported; unique commits preserved via `provenance/research-competitor-validation`. |
| `research/omega-causal-ranking` | d68f96d | 10 / 9 | only superseded README+count | no | **TAG-AND-DELETE** | Ω artifacts/outputs fully in `main`; history tagged `provenance/research-omega-causal-ranking`. |
| `research/phi-hiring-norms` | 06bca55 | 11 / 9 | only superseded README+count | no | **TAG-AND-DELETE** | Φ corpus/analysis fully in `main`; tagged `provenance/research-phi-hiring-norms`. |
| `research/phi2-validation` | d8daa7f | 13 / 9 | only superseded README+count | no | **TAG-AND-DELETE** | Φ-2 validation fully in `main`; tagged `provenance/research-phi2-validation`. |
| `research/phi3-human-validation` | 18eb945 | 14 / 9 | only superseded README+count | no | **TAG-AND-DELETE** | Φ-3 plan/placeholder fully in `main`; tagged `provenance/research-phi3-human-validation`. |
| `fix/final-ci-dashboard-verification` | (merged) | 0 / 3 | none | yes | **DELETE-AS-REDUNDANT** | Transient CI fix; 0 unique commits, reachable from `main`. No tag needed. |
| `frontend/judge-polish` | 754ee1c | 0 / 2 | none | yes | **DELETE-AS-REDUNDANT** | Merged via `--no-ff` (75f900d); reachable from `main`. No tag needed. |

## Outcome

- **Tags pushed (annotated, preserve full history + the superseded README):** the 5
  `provenance/research-*` tags + `provenance/integration-final-research-program`.
- **Branches deleted after tagging/verification:** the 5 research branches, `integration/…`,
  `fix/…`, `frontend/judge-polish`.
- **Retained:** `main` only. (A separate submission branch was judged unnecessary — the frozen
  golden lives in `main`; a `submission/golden-af8f2b32` tag anchors it.)

Recovery: any deleted research branch is restorable with
`git checkout -b <name> provenance/<tag>`.

## Invariants verified

- Golden `submission.csv` sha256 `af8f2b32…` byte-identical before and after.
- Full suite green (198 passed, 0 skipped). Production ranking untouched.
- No force-push; deletions are branch-ref removals only; all research history retained via tags.
