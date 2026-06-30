# Frontier V5 experiment

Date: 2026-06-29

Branch: `codex/public-frontier-v5`

Artifact SHA-256: `8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`

## Decision

Promote `frontier-v5` as this experiment branch's opt-in champion. Keep
`main` unchanged and retain `dominant-v4` as the conservative fallback.

V5 locks V4's exact top-100 membership and applies two feature-only local
tie-breaks:

1. Behavior quality within ranks 11-13.
2. Recruiter responsiveness within ranks 65-74.

The rules contain no candidate IDs, resume fingerprints, label lookups,
competitor weights, or public ranking files.

## Exact full-100K comparison

| Evaluator | Main | V4 | V5 |
|---|---:|---:|---:|
| H2 | 0.874834 | **0.884206** | **0.884206** |
| independent | 0.881061 | 0.888246 | **0.888380** |
| judge 1 | 0.922722 | **0.932111** | **0.932111** |
| judge 2 | 0.963277 | **0.966594** | **0.966594** |
| judge 3 | 0.927608 | **0.942095** | **0.942095** |
| expanded labels | 0.664808 | **0.814569** | **0.814569** |
| silver 20K | 0.874490 | **0.917915** | **0.917915** |
| public reviewer | 0.710627 | 0.809603 | **0.809768** |
| public blind recruiter | 0.871825 | 0.896915 | **0.905858** |
| merged judge 1 | 0.891534 | **0.906120** | **0.906120** |
| merged judge 2 | 0.959117 | **0.973531** | **0.973531** |
| merged judge 3 | 0.919047 | **0.942545** | **0.942545** |
| relabel judge 4 | 0.948109 | **0.963641** | **0.963641** |
| relabel G25 | 0.787073 | **0.839347** | **0.839347** |
| frozen blind test | 0.932442 | **0.969412** | **0.969412** |
| mean, first seven | 0.872686 | 0.906534 | **0.906553** |
| mean, all 15 | 0.875238 | 0.909790 | **0.910406** |
| equal four-axis mean | 0.832493 | 0.874314 | **0.876596** |

Across the 15 evaluators times four component metrics, V5 records **6 wins,
54 ties, and 0 losses** versus V4. It changes 12 rank positions while keeping
membership, scores, integrity counts, and all default-main behavior unchanged.

## Public-field effect

Using the refreshed 672-output census:

- Seven-evaluator mean remains #1.
- H2 remains about #14.
- Reviewer rises slightly and remains around #115.
- Blind recruiter improves from #23 to an estimated #20.
- Equal four-axis mean rises from 0.874314 to 0.876596, still #3.

These are coverage-filtered development proxies, not official hidden results.

## Robustness and rejected alternatives

- 5,790 nearby band configurations produced 4,396 distinct orders; 269
  configurations across 144 orders preserved all 60 V4 component cells.
- The selected order was checked across 100 repeated candidate half-splits on
  all 15 evaluators. Mean deltas were non-negative for every evaluator; the
  largest gain was blind recruiter at +0.00525 per split on average.
- An eight-rule bundle looked stronger in-sample and would have reached about
  #13 H2, #20 blind, and #2 four-axis. It was rejected because relabel-G25 lost
  on 54 of 100 repeated splits with a negative mean.
- Order oracles, ExtraTrees, TF-IDF ridge, public-output fusion, job-evidence
  specialists, generic score-confidence rules, and opposite-direction fusion
  all failed the no-loss generalization gate.

The narrow behavior tie-break is less parameter-stable than the responsiveness
rule. For that reason V5 remains an opt-in experiment branch, not a silent
change to `main`.

## Reproduction and runtime

```bash
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl \
  --out submission.csv --workers 2 --scoring-profile frontier-v5
sha256sum submission.csv
# 8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062
```

The host and Docker artifacts are byte-identical. Two Docker-native full runs
under `--cpus=2 --memory=16g` measured 199.0-209.4 s pipeline and
233.8-241.9 s wall, with no OOM and zero honeypots emitted. Both remained under
the 300-second budget. A 5K same-image isolation check measured V5 at 9.1 s and
V4 at 10.9 s; the broad full-run spread is Docker Desktop host variance, not a
claim of a V5 speedup.
