# Hedge Simulation Study — label-hypothesis insurance, measured (read-only)

2026-06-11 adversarial-audit follow-up, kill-list #1. `submission.csv` was
**not** modified by this study. Tool: `scripts/hedge_simulation_study.py`;
shared harness, policy=exclude, challenge composite.

## Question

The shipped ranking behaviorally demotes 11 gold-stratum "perfect-on-paper but
unavailable" profiles out of the top-100 (docs/generator_forensics.md). That is
optimal if the hidden labels encode availability (the JD instructs it) and
costly if they are fit-only. What would hedged orderings actually score?

## Setup

- Insertable set: the 11 demoted gold-template profiles minus the gold-clothed
  honeypot `CAND_0093547` → **10 profiles**. A hedge must never insert a
  honeypot.
- **HEDGE-TAIL**: shipped top-90 + the 10 at ranks 91–100.
- **HEDGE-MID**: shipped top-40 + the 10 at ranks 41–50 (41–90 shift down,
  91–100 displaced).
- Scored under: independent labels (100K coverage), judge 1, judge 2, and a new
  **H2-availblind** label set — the independent labeler re-run over all 100K
  with every candidate's reachability signals normalized to identical
  "reachable" values, so availability cancels and labels reflect fit only
  (`artifacts/h2_availblind_labels.jsonl`). This is the availability-blind
  label hypothesis made concrete; fit/seniority/honeypot/disqualifier logic
  untouched.

## Coverage fact discovered

**9 of the 10 demoted golds carry no judge label** — they never entered any
judged sample (only `CAND_0007411`, the known judge-blind-spot case, was
judged: tier 5 by both judges). Judge-side deltas for the hedges are therefore
mostly exclusion-policy artifacts; the committed judge labels cannot
adjudicate this decision. The full-coverage sources can.

## Results (composite deltas vs shipped)

| source | HEDGE-TAIL | HEDGE-MID |
|---|---|---|
| independent (availability-aware, 100% cov) | +0.0000 | −0.0008 |
| judge 1 (91% cov on hedged lists) | −0.0002 | +0.0028 |
| judge 2 (91% cov) | −0.0000 | +0.0033 |
| **H2-availblind (fit-only, 100% cov)** | **+0.0000** | **+0.0135** |

## Reading

1. **The tail hedge is dead.** Below rank 50 the composite has almost no
   resolution: NDCG@10/@50 don't see ranks 91–100, and MAP is already
   saturated (every shipped top-100 row is tier ≥ 3 under both full-coverage
   sources, so MAP = 1.0 with or without the swap). Zero cost, zero benefit —
   not worth a hash roll.
2. **The mid hedge is the real decision**, and it is now priced: it pays
   **+0.0135** if the hidden labels are availability-blind (all of it
   NDCG@50: 0.8270 → 0.8720) and costs **−0.0008** if they are
   availability-aware. Roughly a 17:1 payoff ratio; expected-value positive
   whenever P(availability-blind labels) exceeds ~6%.
3. The non-composite cost is human review: ranks 41–50 would hold profiles
   with response rates as low as 0.07 and open_to_work=false, and their
   grounded reasoning rows would say so. A judge sampling mid-rank rows sees
   the system ranking visibly-unavailable candidates above available ones —
   the opposite of the deck's thesis.

## Status

No change adopted. If a hash roll is undertaken (see
docs/top100_ordering_audit.md for the stronger candidate), the mid hedge is a
separate, explicitly hypothesis-betting add-on whose price is recorded above.
