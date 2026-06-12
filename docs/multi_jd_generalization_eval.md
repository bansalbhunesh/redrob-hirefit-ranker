# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 20,000
- Roles: 5
- Mean HireFit composite: 0.7633
- Mean keyword-baseline composite: 0.6793

| role | HireFit composite | keyword composite | NDCG@10 | P@10 | seconds |
|---|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8351 | 0.4932 | 0.8355 | 1.0000 | 59.0 |
| backend_platform_engineer | 0.6207 | 0.7120 | 0.5664 | 1.0000 | 75.9 |
| search_relevance_engineer | 0.8306 | 0.7256 | 0.8685 | 1.0000 | 75.3 |
| data_bi_analyst | 0.7823 | 0.8061 | 0.7369 | 1.0000 | 72.4 |
| devops_cloud_engineer | 0.7478 | 0.6595 | 0.7083 | 1.0000 | 69.3 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
