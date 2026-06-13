# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 100,000
- Roles: 5
- Mean HireFit composite: 0.7608
- Mean keyword-baseline composite: 0.6602

| role | HireFit composite | keyword composite | HireFit NDCG@10 | keyword NDCG@10 | HireFit NDCG@50 | keyword NDCG@50 | HireFit MAP | keyword MAP | HireFit P@10 | keyword P@10 | seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8695 | 0.5274 | 0.9262 | 0.5274 | 0.8413 | 0.6399 | 0.6934 | 0.2119 | 1.0000 | 0.8000 | 347.1 |
| backend_platform_engineer | 0.6594 | 0.6660 | 0.6219 | 0.6503 | 0.6506 | 0.6240 | 0.6886 | 0.6911 | 1.0000 | 1.0000 | 284.2 |
| search_relevance_engineer | 0.8192 | 0.7432 | 0.8712 | 0.7448 | 0.8446 | 0.7880 | 0.5352 | 0.5958 | 1.0000 | 0.9000 | 287.7 |
| data_bi_analyst | 0.7823 | 0.7140 | 0.7480 | 0.6529 | 0.7668 | 0.6731 | 0.8551 | 0.9041 | 1.0000 | 1.0000 | 259.1 |
| devops_cloud_engineer | 0.6737 | 0.6506 | 0.6237 | 0.5872 | 0.6513 | 0.6383 | 0.7764 | 0.7697 | 1.0000 | 1.0000 | 284.7 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
