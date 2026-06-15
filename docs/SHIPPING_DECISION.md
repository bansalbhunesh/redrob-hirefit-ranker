# Shipping Decision

**Decision: `NO_RANKING_DOMINATES` → ship the frozen golden submission (`af8f2b32`).**

Golden is not shipped because every alternative was inferior. It is shipped because it is the
only ranking whose current benefits and risks are **verified without depending on unresolved
human assumptions**.

## The fork everything reduces to
A research fusion ranking improves the available proxy (+0.0128), but later audits showed the
gain is **fragile**: the 7 label sets are only ~**1.85 effective independent judges**, and
**56%** of the gain comes from **5 anachronism-flagged candidates**; remove that class and the
gain inverts to **−0.011**. Whether those candidates are genuinely strong (world B) or planted
honeypots (world A) is **unresolved** — no automated label can separate the two.

| | Golden | Fusion | Ω candidate |
|---|---|---|---|
| Frozen / deterministic | Yes / Yes | Research / Yes | Research / Yes |
| Proxy improvement | Baseline | Yes (fragile) | Simulation-dependent |
| Candidate-influence robust | Baseline | Failed (5 candidates) | Simulated |
| Independent human lockbox | Not needed to reproduce | Missing | Missing |
| **Shipped** | **Yes** | No | No |

## What would change the decision
The frozen **Ψ** human panel (24 candidates, `AWAITING HUMAN DATA`) resolves the fork. Per the
pre-registered rule: low integrity-reversal → fusion becomes defensible; high → integrity-
constrained ranking; divided → keep golden. Until then, golden ships.

See: `docs/golden_vs_fusion_decision.md`, `docs/OMEGA_DECISION_SUMMARY.md`,
`docs/PSI_INTEGRITY_PANEL.md`, `docs/rank_fusion_study.md`.
