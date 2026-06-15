# Competitive Landscape

Strict-validation finding (detail: `docs/research/` + `competitor_validation_report.md`):
the competitors ranked above us on the blind proxy have **no genuine, transferable, or
statistically significant advantage** — their leads are proxy-overfit noise.

- Top cluster is razor-thin (~0.006 composite); top submissions share only 50–55/100
  candidates yet score the same → the proxy is **saturated** near the top.
- Cross-label: submission ordering **shuffles** across 7 independent judge sets (our rank
  swings #2↔#6); no stable lead. Bootstrap: the blind #1 beats us only 11/50.
- Honeypot-count cross-verification: a calibrated hard detector flags ~0.29% of 100K (order
  of the ~80 planted); competitor counts of 7.6–56% detect generic low quality, not traps.

Terminology is canonical throughout: `detector-flagged anomaly` ≠ `confirmed hard
contradiction` ≠ `official planted honeypot`. Competitor repo names are not reproduced here.
