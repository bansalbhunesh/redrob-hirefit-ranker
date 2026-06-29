# Dominant V4 experiment

Date: 2026-06-29

Branch: `codex/dominant-v4`

Artifact SHA-256: `79aebff697cbccf0b03137998d0b6faf2da61caebaa0ae34f0e5fc876650127e`

## Decision

Promote `dominant-v4` as this branch's opt-in champion. Keep `main` as the
unchanged default and retain V3 as the byte-reproducible fallback.

V4 starts from loss-aggregate-v3 and makes two deliberately small changes:

1. Reorder only the first eight candidates using original rank, direct
   search/ranking experience, and a smooth experience-fit band.
2. Replace at most the two lowest-ranked top-100 profiles with a severe,
   high-confidence technology-timeline contradiction, using the highest clean
   candidates from V2's existing tail.

The production rule contains no candidate IDs, public ranks, resume text
fingerprints, competitor artifacts, or label lookups.

## Exact full-100K result

| Evaluator | Main | V3 | V4 |
|---|---:|---:|---:|
| H2 | 0.874834 | 0.881992 | **0.884206** |
| independent | 0.881061 | 0.885906 | **0.888246** |
| judge 1 | 0.922722 | **0.932111** | **0.932111** |
| judge 2 | 0.963277 | **0.966594** | **0.966594** |
| judge 3 | 0.927608 | **0.942095** | **0.942095** |
| expanded labels | 0.664808 | **0.814569** | **0.814569** |
| silver 20K | 0.874490 | **0.917915** | **0.917915** |
| public reviewer | 0.710627 | **0.809603** | **0.809603** |
| public blind recruiter | 0.871825 | **0.896915** | **0.896915** |
| merged judge 1 | 0.891534 | 0.906120 | **0.906120** |
| merged judge 2 | 0.959117 | **0.973531** | **0.973531** |
| merged judge 3 | 0.919047 | 0.942544 | **0.942545** |
| relabel judge 4 | 0.948109 | **0.963641** | **0.963641** |
| relabel G25 | 0.787073 | 0.839347 | **0.839347** |
| frozen blind test | 0.932442 | 0.969178 | **0.969412** |
| mean, first seven | 0.872686 | 0.905883 | **0.906534** |
| mean, all 15 | 0.875238 | 0.909471 | **0.909790** |

Across the 15 evaluators × four component metrics, V4 records **9 wins,
51 ties, and 0 losses** versus V3. It improves or ties every composite versus
V3 and beats main on all 15 composites.

V3's only component losses to main were H2 and independent NDCG@10. V4 reduces
those gaps from about 0.0040/0.0042 to 0.00040/0.00042 without surrendering any
V3 metric.

## Robustness and anti-overfit checks

- A grid of 11,340 nearby rule settings produced only 234 distinct orders.
- The exact selected order occurs under 296 settings.
- 2,539 settings preserve all 60 V3 component metrics.
- 492 settings preserve every V3 composite while improving both weak NDCG@10
  slices.
- A fresh exhaustive 4,950-pair scan found tempting extra gains, but its best
  remaining swap was supported only by judge 1 and a derivative of judge 1.
  It was rejected as single-family overfit.
- Earlier order fusion, RRF, Borda, minimax, opposite-direction fusion,
  quantile/trimmed/geometric model aggregation, and broad model-weight sweeps
  produced no V3 dominator. V4 is the smallest cross-family-supported change.

These are development proxies. They establish measured dominance over the
checked baselines, not certainty about an unseen official score.

## Integrity and runtime

| Check | Main | V3 | V4 |
|---|---:|---:|---:|
| temporal contradictions in top 100 | 44 | 59 | **57** |
| standard flags/disqualifications | 15 | 6 | **6** |
| honeypots emitted | 0 | 0 | **0** |

The exact artifact passed the submission validator. In Docker with a native
input volume, `--cpus=2 --memory=16g`, and the same image for both profiles:

- V4: 75.4 s pipeline, 79.5 s wall time.
- V3 control: 91.3 s pipeline, 95.7 s wall time.
- V3 control hash: `c28857fd...`, byte-identical to the prior artifact.

Docker Desktop timing is noisy, so the defensible conclusion is **no speed
regression and comfortably below the 300-second budget**, not a guaranteed
17% speedup on every machine.

## Reproduce

```bash
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl \
  --out submission.csv --workers 2 --scoring-profile dominant-v4
sha256sum submission.csv
# 79aebff697cbccf0b03137998d0b6faf2da61caebaa0ae34f0e5fc876650127e
```
