# Loss-aggregate-v3 experiment — 2026-06-29

## Verdict

`loss-aggregate-v3` supersedes universal-v2 as the strongest balanced branch
artifact. It keeps v2's exact 100-candidate membership and improves all 15
measured evaluators by reordering that membership with seven shallow,
candidate-ID-free label-family heads.

It still does not beat every public specialist on that specialist's isolated
metric. That stronger claim remains unproven.

## Architecture

- Seven ExtraTrees regression heads, one per internal label family.
- 30 trees per head, depth 6, minimum leaf 3.
- Candidate-hash five-fold predictions used for the leakage-safe gate.
- 130 KB NumPy artifact; scikit-learn is not installed at runtime.
- Model blend uses ungated v2 relevance, then applies the existing honeypot and
  disqualifier multipliers exactly once.
- Weighted RRF (`k=60`, learned-order weight `0.27`) locks v2's exact top-100
  membership and changes ordering only.
- No candidate IDs, public ranks, résumé fingerprints, or competitor code are
  present in the artifact or production path.

## Generalization gate

The initial label-derived oracle could beat all public metric maxima, but its
feature distillation failed candidate-level out-of-fold evaluation and was
rejected. The accepted seven-head architecture was then trained without the
oracle head.

With integrity gates applied after the model, the OOF-selected blend scored:

| metric | universal-v2 | OOF heads |
|---|---:|---:|
| H2 | 0.880144 | **0.880473** |
| seven-world mean | 0.904491 | **0.906974** |
| reviewer | 0.806464 | **0.810971** |
| blind recruiter | 0.896413 | **0.900422** |

The final RRF membership lock was selected to preserve every full-table v2 win.

## Exact 15-axis result

| evaluator | universal-v2 | loss-aggregate-v3 | delta |
|---|---:|---:|---:|
| H2 | 0.880144 | **0.881992** | +0.001849 |
| independent | 0.884182 | **0.885906** | +0.001724 |
| judge1 | 0.931765 | **0.932111** | +0.000345 |
| judge2 | 0.966512 | **0.966594** | +0.000082 |
| judge3 | 0.939426 | **0.942095** | +0.002670 |
| expand | 0.811910 | **0.814569** | +0.002659 |
| silver20k | 0.917502 | **0.917915** | +0.000413 |
| public reviewer | 0.806464 | **0.809603** | +0.003139 |
| blind recruiter | 0.896413 | **0.896915** | +0.000502 |
| merged_j1 | 0.905698 | **0.906120** | +0.000422 |
| merged_j2 | 0.973348 | **0.973531** | +0.000183 |
| merged_j3 | 0.941843 | **0.942544** | +0.000701 |
| relabel_j4 | 0.963291 | **0.963641** | +0.000351 |
| relabel_g25 | 0.838982 | **0.839347** | +0.000365 |
| blind_test_frozen | 0.969095 | **0.969178** | +0.000084 |

Mean7 rises from 0.904491 to **0.905883** and mean15 from 0.908438
to **0.909471**.

## Public-field position

Against 665 valid public outputs, v3 would rank #1 on seven-world mean, #16 on
H2, #113 on the reviewer slice, and #23 on the blind recruiter slice. No public
output dominates it across all four axes. The isolated public maxima remain
H2 0.929965, reviewer 0.934955, and blind 0.966756.

## Production verification

- Host full 100K: 77.4-79.8 seconds.
- Original Docker image, full 100K, `--cpus=2 --memory=16g`: 109.3 seconds on a
  Docker-native volume in the controlled runtime A/B.
- Optimized Docker image under the same A/B conditions: **69.1 seconds**
  (36.8% faster); a loaded Docker Desktop bind-mount run took 254.0 seconds.
- 53 honeypots detected, 0 emitted.
- Host and Docker SHA-256:
  `c28857fdba63723ed13bea35d977a49f3aca7550dc7ea1c2c82d4150279e769c`.
- Pure-NumPy tree predictions match scikit-learn to less than `2e-15`.
- Production and research top-100 orders match in all 100 positions.
