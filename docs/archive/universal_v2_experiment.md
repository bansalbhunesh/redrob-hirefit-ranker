# Universal-v2 experiment — 2026-06-29

## Verdict

`universal-v2` is the strongest balanced artifact measured in this repository.
It beats current `main` and `top23-clean` on all 15 full-table evaluators, stays
inside the CPU/memory budget, preserves the existing integrity gates, and
reproduces byte-for-byte across host and Docker.

This is not proof that it beats every public specialist on every isolated
metric or that it will win an unknown hidden evaluator.

## Public field audit

`experiments/public_field_benchmark.py` searched the live public GitHub field
without executing competitor code:

- 1,361 unique repositories discovered;
- 1,272 eligible public, non-fork, non-archived repositories;
- 665 repositories with at least one valid 100-row output;
- 69 multi-axis leaders cloned and inspected;
- no competitor candidate IDs, public ranks, or paragraph fingerprints enter
  the production model.

The recurring transferable ideas were: career/project evidence over skill-list
volume, relevance separated from trust/integrity, availability as a bounded
nudge, and hard guardrails outside the relevance sum. Pool-specific lookup
tables and exact-profile fingerprints were rejected.

Among the 665 valid public outputs, universal-v2 would place #1 on the
seven-world mean, #17 on H2, #119 on the public reviewer slice, and #24 on the
blind recruiter slice. No public output dominates it across all four axes.
Specialists still lead individual axes.

## Exact evaluator matrix

All values are development composites, not official hidden scores.

| evaluator | main | top23-clean | universal-v2 |
|---|---:|---:|---:|
| H2 | 0.874834 | 0.877655 | **0.880144** |
| independent | 0.881061 | 0.884043 | **0.884182** |
| judge1 | 0.922722 | 0.924395 | **0.931765** |
| judge2 | 0.963277 | 0.966443 | **0.966512** |
| judge3 | 0.927608 | 0.929329 | **0.939426** |
| expand | 0.664808 | 0.788678 | **0.811910** |
| silver20k | 0.874490 | 0.908888 | **0.917502** |
| public reviewer | 0.710627 | 0.782810 | **0.806464** |
| blind recruiter | 0.871825 | 0.874630 | **0.896413** |
| merged_j1 | 0.891534 | 0.898142 | **0.905698** |
| merged_j2 | 0.959117 | 0.968990 | **0.973348** |
| merged_j3 | 0.919047 | 0.927312 | **0.941843** |
| relabel_j4 | 0.948109 | 0.961633 | **0.963291** |
| relabel_g25 | 0.787073 | 0.838419 | **0.838982** |
| blind_test_frozen | 0.932442 | 0.960371 | **0.969095** |
| mean, first 7 | 0.872686 | 0.897062 | **0.904491** |
| mean, all 15 | 0.875238 | 0.899449 | **0.908438** |

Universal-v2 overlaps 91 of top23-clean's 100 candidates and 71 of main's.

## Stability and limitations

The final configuration was refined against the full 15-axis matrix, so 15/15
is an in-sample multi-objective result. It is not presented as a fresh lockbox.

Across 50 deterministic candidate-ID splits (both halves, 100 comparisons),
universal-v2 beat main frequently on most axes: judge1 94/100, judge2 90/100,
judge3 97/100, expand 92/100, silver20k 86/100, reviewer 89/100, merged_j1
93/100, merged_j2 93/100, merged_j3 99/100, relabel_j4 96/100,
relabel_g25 97/100, and blind_test_frozen 100/100. H2 was 76/100 and the
small blind recruiter slice 63/100. The independent set was only 45/100 despite
the positive full-table delta, so that gain is not called robust.

Against top23-clean, the strongest split stability was blind_test_frozen
98/100, judge3 and blind recruiter 86/100, merged_j3 80/100, reviewer 75/100,
and silver20k 71/100. Several small judge slices were noisy.

## Exact production verification

- Host, 100K candidates, 2 workers: 130.1 seconds.
- Docker, `--cpus=2 --memory=16g`: 164.1 seconds.
- Honeypots: 53 detected, 0 in output.
- Tests: 205 passed, 6 environment skips.
- Host/Docker SHA-256:
  `c00f708ab63265b73eb280d058ad72376df94c66dc49c50e2027e62ef894e7f3`.
- The search-harness order and production order matched in all 100 positions.
- Omitting `--scoring-profile universal-v2` preserves the default main path.

## Clean-room boundary

Production contains only generic feature multipliers and the existing feature
extractor. It contains no competitor code, public submission ranks, candidate
ID rules, exact résumé fingerprints, network calls, or runtime dependency on
the cloned repositories.
