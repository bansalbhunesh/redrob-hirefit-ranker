# Decisive Integrity-Aware Evaluation — rrf-lock30 vs the hedge

One frozen, blinded evaluation on ONLY the candidates that differ between rrf-lock30 and the shipped
hedge (56 distinct candidates / 67 differing ranks). A fresh judge (gpt-4.1) scored fit quality
(0-5) WITHOUT seeing our scores or which ranking a candidate came from, and SEPARATELY classified
each tenure-date inconsistency. Scripts: `experiments/decisive_integrity_judge.py`,
`experiments/decisive_eval.py`. Read-only; nothing merged to main.

## Integrity classification (blinded)
- **rrf-only promotions (28): all "ambiguity" — 0 contradictions.** The anachronism candidates rrf
  promotes are judged harmless (plausible rounding/role-overlap), not factual impossibilities.
- hedge-only picks (28): 19 clean, 6 ambiguity, **3 contradictions** (these passed the sev<=1.2 gate
  but the judge deems them real). So the hedge is not contradiction-free either.

## Paired quality (rrf candidate tier - hedge candidate tier, per differing rank, n=14 distinct pairs)
| view | mean d | 95% CI (bootstrap) | rrf>hedge / hedge>rrf / tie |
|---|---:|---|---|
| including flagged | +0.286 | [-0.071, +0.643] | 4 / 1 / 9 |
| integrity-adjusted (drop rrf contradictions) | +0.286 | [-0.071, +0.643] | 4 / 1 / 9 |
| clean only (no contradiction either side) | +0.333 | [-0.083, +0.750] | 4 / 1 / 7 |

Top-rank regressions (rank<=50 where rrf is worse): **0**.

## Decision
rrf-lock30's promotions are *slightly* higher mean quality but **not clearly superior** — every CI
includes 0, and the comparison is mostly ties (9/14). Its higher composite (0.8781 vs 0.8748) came
from the proxy metric rewarding anachronism promotions the judge rates as harmless-but-not-better.

**Per the pre-registered rule → SHIP THE HEDGE.** rrf-lock30 is retained as a documented branch
artifact (`experiments/build_rrf_lock30_submission.py`), not merged, not declared the winner. The
hedge remains shipped on main (`submission/hedge-24f84f4b`); golden is the fallback
(`fallback/golden-af8f2b32`).

*Honest limits:* one judge (gpt-4.1), 14 distinct paired ranks (small n — hence wide CIs), proxy not
official labels. The result is "not clearly better," which under the rule means keep the safer hedge.
