# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 20,000
- Roles: 5
- Mean HireFit composite: 0.7852
- Mean keyword-baseline composite: 0.6793

| role | HireFit composite | keyword composite | NDCG@10 | P@10 | seconds |
|---|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8351 | 0.4932 | 0.8355 | 1.0000 | 72.7 |
| backend_platform_engineer | 0.6509 | 0.7120 | 0.5910 | 1.0000 | 88.8 |
| search_relevance_engineer | 0.8306 | 0.7256 | 0.8685 | 1.0000 | 91.1 |
| data_bi_analyst | 0.8615 | 0.8061 | 0.8698 | 1.0000 | 90.5 |
| devops_cloud_engineer | 0.7478 | 0.6595 | 0.7083 | 1.0000 | 88.9 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
