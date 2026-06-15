# Ψ Integrity Panel (frozen instrument — AWAITING HUMAN DATA)

The minimal human experiment that resolves the golden-vs-fusion fork: does revealing
impossible dates flip a reviewer who picked a candidate on career quality?

- **Panel:** 24 candidates, frozen (hash `34f43b14`), selected on pre-Ω signals (5 fusion-gain
  drivers + 5 matched clean + 4 hard controls + 4 ambiguous + 3 strong-clean + 3 weak-clean).
- **Design:** two-stage blinded — Stage A (career quality, dates/flags hidden) → Stage B (full
  timeline). 9 reviewers in 3 families (recruiter / engineer / neutral).
- **Primary metric:** integrity reversal rate (<20% noise → fusion defensible; >50% penalise →
  integrity-constrained; mixed → ship golden). Pre-registered shipping rule frozen in `psi_analysis.py`.
- **Status:** 0 human responses → `AWAITING HUMAN DATA`. No synthetic results are presented as human.

Detail: `docs/experiment_psi_human_calibration.md`. Run after collection:
`python experiments/psi_analysis.py`.
