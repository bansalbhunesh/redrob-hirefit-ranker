# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 20,000
- Roles: 5
- Mean HireFit composite: 0.6920
- Mean keyword-baseline composite: 0.6793

| role | HireFit composite | keyword composite | NDCG@10 | P@10 | seconds |
|---|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8269 | 0.4932 | 0.8365 | 1.0000 | 56.7 |
| backend_platform_engineer | 0.4757 | 0.7120 | 0.4143 | 1.0000 | 51.7 |
| search_relevance_engineer | 0.8289 | 0.7256 | 0.8734 | 1.0000 | 50.8 |
| data_bi_analyst | 0.7328 | 0.8061 | 0.7239 | 1.0000 | 51.6 |
| devops_cloud_engineer | 0.5957 | 0.6595 | 0.6048 | 0.9000 | 51.9 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
