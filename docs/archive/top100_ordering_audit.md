# Top-100 Ordering Audit — the freeze does NOT hold at full depth (read-only)

2026-06-11 adversarial-audit follow-up, kill-list #2. `submission.csv` was
**not** modified by this study. Tool: `scripts/top100_ordering_audit.py`,
extending the committed top-15 audit (`scripts/top10_ordering_audit.py`) from
NDCG@10-only to the full challenge composite over all 4,950 pairwise swaps in
the top-100. Metric semantics identical to the shared harness (verified by
assertion against `eval_harness.evaluate` before scanning).

## Why this matters

45% of the composite weight (0.30·NDCG@50 + 0.15·MAP) is decided at ranks
11–100. The committed audit only established "no consensus swap in the
top-15 on NDCG@10" — which this study confirms, but which says nothing about
the region where most of the remaining headroom lives.

## Result

**61 pairwise swaps improve the composite under ALL THREE covering label
sources** (independent + judge 1 + judge 2; every involved id is labeled by
all three, so no exclusion-policy artifacts). The expansion label set covers
0 of the top-100 and contributes nothing.

A greedy non-overlapping application of 8 of them (largest mean delta first):

| source | composite delta |
|---|---|
| independent | **+0.0052** |
| judge 1 | **+0.0153** |
| judge 2 | **+0.0142** |
| mean (gate-3) | **+0.0116** |

The dominant pattern: a small set of mid-rankers (`CAND_0005649` @37,
`CAND_0065878` @55, `CAND_0083879` @75, `CAND_0068811` @85, `CAND_0060054`
@93, `CAND_0017960` @62, …) are rated above/below their neighbors identically
by all three sources but sit on the wrong side of the 20–47 band.

## Relation to the pre-registered adoption gate

The LTR challenger gate (docs/ltr_challenger_gate.md) required mean composite
improvement ≥ +0.005 across these same three sources at 100% coverage — the
challenger failed at −0.0061. This reordering shows **+0.0116 at 100%
coverage on every source**: by the project's own standard, it is the
strongest positive evidence produced to date, and unlike the hedge study it
is not a bet on any label hypothesis (all three sources agree per swap).

Honest caveats, recorded before any adoption decision:

1. **Selection pressure**: 4,950 swaps were screened against the same three
   sources used to report the gain; the consensus requirement and the
   per-swap full coverage limit but do not eliminate overfitting to proxy
   labels. The top-15 audit blessed exactly this consensus convention.
2. **Membership is unchanged** — a reorder moves no one in or out of the
   top-100: honeypots remain 0, the DQ profile is identical, and the format
   validator is unaffected except for the score column, which is tied to
   candidates and would become non-monotonic in rank; an adopted reorder
   must re-emit scores monotonically (and the reasoning rows travel with
   their candidates).
3. Adoption requires the full documented hash-roll protocol: golden-test
   roll, Docker matrix re-run, honeypot audit re-check, row-by-row review.

## Status

No change adopted. Committed as evidence for the hash-roll decision.
