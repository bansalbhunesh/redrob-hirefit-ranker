# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 20,000
- Roles: 5
- Mean HireFit composite: 0.7501
- Mean keyword-baseline composite: 0.6793

| role | HireFit composite | keyword composite | NDCG@10 | P@10 | seconds |
|---|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8218 | 0.4932 | 0.8128 | 1.0000 | 56.9 |
| backend_platform_engineer | 0.5970 | 0.7120 | 0.5330 | 1.0000 | 49.6 |
| search_relevance_engineer | 0.8464 | 0.7256 | 0.9009 | 1.0000 | 51.1 |
| data_bi_analyst | 0.7452 | 0.8061 | 0.6835 | 1.0000 | 53.0 |
| devops_cloud_engineer | 0.7399 | 0.6595 | 0.7083 | 1.0000 | 50.5 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
