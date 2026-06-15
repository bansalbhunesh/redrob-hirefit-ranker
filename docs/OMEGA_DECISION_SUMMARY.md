# Ω Decision Summary

We formalised the final submission decision as a **minimax-regret** problem across plausible
quality-versus-integrity utility worlds (parameter λ). Simulated experiments showed the
preferred ranking changes sharply with λ, proving **no algorithmic proxy can resolve the
decision honestly**. Because simulated reviewers cannot validate their own assumptions, the
system correctly **refused to declare a winner** and identified real human integrity
calibration (Ψ) as the only remaining high-value information.

- Max regret (simulated): Ω 0.00 (by construction), constrained-fusion 3.83, golden 34.46, fusion-raw 37.63.
- Golden is minimax-optimal only for λ<0.10 (humans nearly integrity-blind); the boundary is
  **model-specific**, NOT an empirical human threshold.
- Ω's zero regret is **by construction** (optimised under the same simulated framework) — not
  independent validation. The `SHIP_OMEGA` gate (real human lockbox) is unmet by construction.

**Verdict:** `NO_RANKING_DOMINATES`. Detail: `docs/omega_causal_ranking_study.md`.
