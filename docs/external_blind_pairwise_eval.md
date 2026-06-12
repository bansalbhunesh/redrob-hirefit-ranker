# External Blind Pairwise Fit Evaluation

This is external public-label evidence, not official Redrob hidden-label evidence.

- Source: https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit
- Split: `test.csv`
- Rows read: 1,759
- Supported technical rows scored: 1,317
- Unsupported rows skipped: 442
- Coverage: 74.9%

## Metrics

| metric | HireFit | keyword-overlap baseline |
|---|---:|---:|
| AUC, Good/Potential vs No Fit | 0.5458 | 0.5549 |
| AUC, Good Fit vs rest | 0.5267 | 0.5643 |
| Spearman vs 0/3/5 tier | 0.0719 | 0.1078 |

## Label Means

| external label | mean HireFit score |
|---|---:|
| Good Fit | 0.3083 |
| No Fit | 0.2822 |
| Potential Fit | 0.3057 |

## Decile Lift

- Top decile Good/Potential rate: 59.5%
- Bottom decile Good/Potential rate: 45.0%

## Limits

- The public dataset labels are external, but they are not the hackathon hidden labels.
- This is pairwise fit scoring across many JDs, not a same-JD top-100 ranking leaderboard.
- Unsupported non-technical JDs are skipped by design because this ranker targets technical hiring.
