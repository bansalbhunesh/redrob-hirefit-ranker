# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 20,000
- Roles: 5
- Corpus/index preparation seconds: 26.9
- Mean HireFit composite: 0.7899
- Mean keyword-baseline composite: 0.6793

| role | HireFit composite | keyword composite | HireFit NDCG@10 | keyword NDCG@10 | HireFit NDCG@50 | keyword NDCG@50 | HireFit MAP | keyword MAP | HireFit P@10 | keyword P@10 | seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8363 | 0.4932 | 0.8355 | 0.6050 | 0.8603 | 0.3771 | 0.7364 | 0.2171 | 1.0000 | 0.9000 | 18.5 |
| backend_platform_engineer | 0.6702 | 0.7120 | 0.6305 | 0.7159 | 0.6757 | 0.6589 | 0.6814 | 0.7095 | 1.0000 | 1.0000 | 16.9 |
| search_relevance_engineer | 0.8306 | 0.7256 | 0.8685 | 0.6883 | 0.8707 | 0.7760 | 0.5677 | 0.6576 | 1.0000 | 1.0000 | 16.4 |
| data_bi_analyst | 0.8612 | 0.8061 | 0.8698 | 0.7992 | 0.8244 | 0.7347 | 0.8599 | 0.9067 | 1.0000 | 1.0000 | 17.8 |
| devops_cloud_engineer | 0.7510 | 0.6595 | 0.7083 | 0.5978 | 0.7681 | 0.6697 | 0.7760 | 0.7643 | 1.0000 | 0.9000 | 16.2 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
