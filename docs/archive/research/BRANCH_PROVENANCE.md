# Branch Provenance

How preserved results reached `integration/final-research-program`. Original branch history
is **not destroyed** — all research branches remain intact and reachable.

## Method
The research branches are a linear chain off `main`; production is byte-identical on every
one. The integration branch was created from clean `main`, then the curated research paths
were ported from the chain tip via:

```
git checkout integration/final-research-program            # from main (golden af8f2b32)
git checkout research/phi3-human-validation -- docs experiments
```

This copies the cumulative research additions (all `docs/*` study files + `experiments/*`
code + committed result JSON/CSV) without merging branch history and without touching any
production path (`src/`, `submission.csv`, `models/`, `rank.py`, `tests/` were NOT checked
out from the research branch). New consolidation docs, the dashboard, and firewall tests were
then authored directly on the integration branch.

## Provenance of key preserved results
| Result / file | Origin branch | Origin commit | Final path | How |
|---|---|---|---|---|
| measured negatives #1–#13 | rank-fusion / competitor | b5a25f7 | docs/measured_negatives.md | copied |
| rank-fusion study + §7 | rank-fusion | b5a25f7..f5c7d34 | docs/rank_fusion_study.md | copied |
| constrained fusion, golden-vs-fusion, honeypot consensus | competitor-validation | 35a7df2 | docs/*.md | copied |
| evidence channels + audits | competitor-validation | 6bb03e5 | docs/evidence_channels_study.md | copied |
| advanced directions | competitor-validation | 780050f | docs/advanced_directions_validation.md | copied |
| Ω code + outputs | omega | 9cb2801 | experiments/omega_*, omega_outputs/*.json | copied |
| Ψ instrument | omega | 5aaa5f3 | experiments/psi_*, psi_panel/manifest.json | copied |
| Φ / Φ-2 corpus + docs | phi / phi2 | 06bca55 / 9540cf8 | docs/human_opinion/* | copied |
| integrity cards | phi2 | d8daa7f | experiments/integrity_card.py, integrity_cards.json | copied |
| registry, audit, catalog, provenance, dashboard, firewall tests | — | (this integration) | docs/research/*, dashboard/*, tests/* | authored new |

**Numerical reverification:** integrity-card distribution (45/52/3/0), Ω max-regret values,
and the golden hash were re-read from the committed artifacts on the integration branch (not
trusted from prose). Any value in a doc traces to `experiments/registry.json` or a committed
JSON/CSV.

## Conflict resolution
Where a later audit changed an earlier conclusion, **both are kept**: the raw result and its
later (stricter) interpretation, with the earlier marked *superseded* (see FINAL_RESULT_CATALOG.md),
never silently replaced. Example: raw fusion (+0.0128) → judge-dependence (1.85) →
candidate-influence (5 candidates) → final status *fragile, not shipped*.
