# Final Integration Report

Branch: `integration/final-research-program` (from clean `main`, golden `af8f2b32`).
Objective: capture every experiment's knowledge/evidence/result/limitation/provenance in one
navigable repo while the frozen production path stays completely protected.

## Branches inspected (all)
Research chain (linear off main, production-clean): `experiment/rank-fusion-research`,
`research/competitor-validation`, `research/omega-causal-ranking`, `research/phi-hiring-norms`,
`research/phi2-validation`, `research/phi3-human-validation`. Pre-program/unrelated (left
isolated, not merged): `experiment/dense-embeddings`, `codex/*` (×2), `feature/*` (×6),
`wip/perf-experiments-20260610`. Detail: `BRANCH_AUDIT_MATRIX.md`.

## What was integrated
- **Ported** (from chain tip `phi3`, curated paths only): all `docs/*` study files +
  `experiments/*` research code + committed result JSON/CSV. Method + per-file provenance:
  `BRANCH_PROVENANCE.md`.
- **Authored new on the integration branch:** `experiments/registry.json` (12 entries);
  `docs/research/{RESEARCH_PROGRAM_INDEX, BRANCH_AUDIT_MATRIX, EXPERIMENT_REGISTRY,
  FINAL_RESULT_CATALOG, BRANCH_PROVENANCE, EXCLUDED_ARTIFACTS, FINAL_INTEGRATION_REPORT}.md`;
  judge-facing `docs/{SHIPPING_DECISION, OMEGA_DECISION_SUMMARY, PSI_INTEGRITY_PANEL,
  REPRODUCTION, DASHBOARD_GUIDE}.md`; the dashboard (`omega_decision_dashboard.py` +
  `dashboard/`); firewall + dashboard tests.
- **Excluded** (regenerable / unsafe / out-of-scope): `EXCLUDED_ARTIFACTS.md`.

## Production firewall — verified
- `rank.py` and `src/redrob_ranker/**` import no `dashboard`/`experiments`/research module
  (`tests/test_dashboard_no_production_imports.py`).
- Dashboard import-light modules (`constants/data_loader/integrity_cards/charts`) contain no
  streamlit and no production calls; are read-only (no writes/exec).
- Golden submission `submission.csv` sha256 = `af8f2b327f05d30e22aba41e884077071c673082cd4a2647294f0969c0f0536a`
  — **byte-identical before and after integration.**

## Verification results
- Full suite: **187 passed, 0 skipped** (171 production + 16 dashboard/firewall). Anti-drift
  gate updated together: `docs/metrics_manifest.json` (`tests_collected`/`tests_passing` → 187)
  + README badge → 187.
- Golden hash: unchanged (`af8f2b32`).
- Doc sweep: stale/over-claim terms corrected earlier in-program (`52 honeypots` is now always
  the three-way distinction; SE called HR/workplace-process, not recruiter; `1.85 effective
  judges` not "seven independent"; λ qualified as model-specific; no "best in field"/"FDA-grade").

## Final experiment tally (see FINAL_RESULT_CATALOG.md)
Shipped 1 · research-only positive 3 · measured negatives ~14 (#1–#12 + evidence channels +
advanced directions) · fragile 1 (fusion-raw) · explanation-only 3 (cards + 2 audits) ·
awaiting-human 2 (Ψ, Φ second-coder/recruiter-India). Verdict: `NO_RANKING_DOMINATES` → ship golden.

## Remaining human-only dependencies
Ψ candidate panel (0 responses), Φ independent second coder (`AWAITING_SECOND_CODER`), Φ real
recruiter + India strata. No algorithm can honestly supply these.

## Production unchanged
Removing `dashboard/`, `experiments/`, `docs/research/` does not change golden output (firewall
tests). The integration adds knowledge + a demo layer only; the shipped ranker is the same
frozen `af8f2b32`.
