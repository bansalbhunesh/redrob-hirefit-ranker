# Shipping Decision

**Decision: ship the severity-gated Copeland HEDGE (`24f84f4b`); retain golden (`af8f2b32`) as the
one-command fallback (`fallback/golden-af8f2b32`).**

The hedge is golden's **exact top-30**, then ranks 31–100 re-drawn from the pool by Copeland
(Condorcet) score, excluding anachronism candidates with severity > 1.2. Because the head is golden,
**NDCG@10 and P@10 are identical to golden by construction** — every measured gain is a better
ordered *tail*. It is a deterministic, audited post-hoc rerank; production `rank.py` is unchanged and
still reproduces golden byte-for-byte.

## Why the hedge over golden — validated under one frozen protocol
(`docs/golden_vs_hedge_two_studies.md`)

| Evidence | Result |
|---|---|
| 7 label sets (retrospective, full-set) | hedge **7/7**, all NDCG@50/MAP (NDCG@10 unchanged) |
| Out-of-sample holdout (blind arbiter, R=20) | generalizes: mean **+0.012**, 16/20 splits positive |
| Independent judge — gpt-4.1 (lenient) | composite **+0.0197** |
| Independent judge — gemini-2.5-pro (different lab, integrity-strict) | composite **+0.0160** |
| Are the swaps real upgrades? | promoted > dropped under **both** judges (+0.53 / +0.59 tiers) |
| Just the anachronism bet? | no — **23 of 36 promotions are clean**, also rated above the dropped set |
| Added integrity exposure vs golden? | none — gemini flags **32 = 32** integrity issues in both |

## Bounded downside (why this is a safe bet, not a gamble)
- Golden and hedge are **byte-identical through rank 30** → they tie on the top-heavy part of any
  metric; the hedge's only distinct exposure is its promoted tail (ranks 31–100).
- The hedge carries **fewer anachronism candidates than golden** (44 vs 52). So even in the adverse
  world where hidden judges date-check tenure, the hedge is **less** exposed than the fallback — that
  world does not flip the decision to golden (the integrity-strict judge still scored it +0.0160).
- Golden remains byte-reproducible, one command away, if that risk is later judged to dominate.

## The honest limit
Every judge above is a **proxy**, not the official hidden labels; the hedge improves only the tail.
The claim is therefore "**the hedge weakly dominates golden** — ties where it matters most, makes
independently-confirmed tail upgrades, adds no integrity exposure," not "guaranteed to win."

## What would change the decision
The frozen **Ψ** human panel (24 candidates, `AWAITING HUMAN DATA`) is the human resolver: strong
evidence the promoted tail is genuinely strong reinforces the hedge; strong evidence it is
integrity-compromised reverts to golden via the fallback tag.

See: `docs/golden_vs_hedge_two_studies.md`, `docs/best_of_best_meta_study.md`,
`docs/OMEGA_DECISION_SUMMARY.md`, `docs/PSI_INTEGRITY_PANEL.md`.
