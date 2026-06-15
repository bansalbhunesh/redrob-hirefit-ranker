# Branch Audit Matrix

All research branches form a **linear chain off `main`** (each created from the previous);
none modify production. Verified: `git diff main <branch> -- src/ submission.csv models/
rank.py tests/` is **empty** for every branch → golden `af8f2b32` byte-identical throughout.

| Branch | Head | Base | Experiment(s) | Result | Merge category | Production risk |
|---|---|---|---|---|---|---|
| `experiment/rank-fusion-research` | f5c7d34 | main | rank-space fusion #13, fusion-raw, §7 reinterpretation | fragile | A (docs) + B (code) | none |
| `research/competitor-validation` | 780050f | rank-fusion | competitor stress-test, constrained fusion, evidence channels, audits, advanced dirs | mixed (mostly negative/fragile) | A + B | none |
| `research/omega-causal-ranking` | d68f96d | competitor-validation | Ω (causal/DRO), Ψ instrument | research-only / awaiting-human | A + B | none |
| `research/phi-hiring-norms` | 06bca55 | omega | Φ pilot (HN, n=19) | qualitative/awaiting | A + B | none |
| `research/phi2-validation` | d8daa7f | phi | Φ-2 (SE stratum, two-axis), integrity cards | qualitative + explanation feature | A + B | none |
| `research/phi3-human-validation` | 18eb945 | phi2 | Φ-3 plan (human-only continuations) | awaiting-human | A (docs) | none |
| `experiment/dense-embeddings` | 32aabf4 | main (stale, pre-program) | dense embeddings (= measured negative #1) | negative, superseded | C (summary in measured_negatives.md) | none |
| `codex/*`, `feature/*`, `wip/*` | various | main | perf/infra experiments predating this program | not part of decision arc | C/D (left isolated) | none — none merged |

**Consolidation method:** because the chain is linear and production-clean, the integration
branch ports the *curated research paths* (`docs/`, `experiments/`) from the chain tip
(`phi3`, which contains all cumulative additions) — not a blind branch merge. See
`BRANCH_PROVENANCE.md`.

**Left isolated (not merged):** the `codex/*`, `feature/*`, `wip/*` branches are pre-program
perf/infra experiments unrelated to the ranking-decision arc; their knowledge is not part of
this submission narrative and they carry no result needed here.
