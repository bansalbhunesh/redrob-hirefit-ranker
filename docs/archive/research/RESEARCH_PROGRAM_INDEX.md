# Research Program Index

One navigable map of the entire Golden → Fusion → Ω → Ψ → Φ arc. Every result here traces
to `experiments/registry.json` or a committed study doc. **Production is untouched: golden
`af8f2b32` is byte-identical across the whole program.**

## Spine
- `experiments/registry.json` — machine-readable registry (12 experiment groups).
- `docs/research/EXPERIMENT_REGISTRY.md` — human-readable categorisation.
- `docs/research/FINAL_RESULT_CATALOG.md` — every experiment classified.
- `docs/research/BRANCH_AUDIT_MATRIX.md` — per-branch forensic audit.
- `docs/research/BRANCH_PROVENANCE.md` — where each preserved result came from.
- `docs/research/EXCLUDED_ARTIFACTS.md` — what was deliberately not merged, and why.
- `docs/research/FINAL_INTEGRATION_REPORT.md` — integration + firewall + verification.

## Study docs (detail)
- Fusion: `docs/rank_fusion_study.md`, `docs/measured_negatives.md` (#1–#13)
- Constrained fusion: `docs/constrained_rank_fusion_study.md`, `docs/golden_vs_fusion_decision.md`
- Evidence channels + audits: `docs/evidence_channels_study.md`
- Advanced directions: `docs/advanced_directions_validation.md`
- Honeypot counts: `docs/honeypot_detector_consensus.md`
- Ω: `docs/omega_causal_ranking_study.md`
- Ψ: `docs/experiment_psi_human_calibration.md`
- Φ: `docs/human_opinion/` (LANDSCAPE, INTEGRITY_DECISION_ATLAS, EXTERNAL_TRIANGULATION_WITH_PSI, PHI2_VALIDATION, PHI3_PLAN)

## Judge-facing entry points
`docs/SHIPPING_DECISION.md` · `docs/OMEGA_DECISION_SUMMARY.md` · `docs/PSI_INTEGRITY_PANEL.md` ·
`docs/REPRODUCTION.md` · `docs/DASHBOARD_GUIDE.md` · `omega_decision_dashboard.py`

## Verdict
`NO_RANKING_DOMINATES` → **ship golden**. No alternative has cleared every preregistered gate
using independent human evidence; the deciding instrument (Ψ) is `AWAITING HUMAN DATA`.
