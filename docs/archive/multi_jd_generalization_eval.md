# Multi-JD Generalization Evaluation

This is a Redrob-pool transfer benchmark using independent role rubrics.
It is not official hidden-label evidence and it does not tune the ranker.

- Candidates scored per JD: 80
- Roles: 5
- Corpus/index preparation seconds: 0.2
- Mean HireFit composite: 0.8471
- Mean keyword-baseline composite: 0.7912

| role | HireFit composite | keyword composite | HireFit NDCG@10 | keyword NDCG@10 | HireFit NDCG@50 | keyword NDCG@50 | HireFit MAP | keyword MAP | HireFit P@10 | keyword P@10 | seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| senior_ai_engineer | 0.8636 | 0.9045 | 0.8619 | 0.9334 | 0.9256 | 0.9425 | 1.0000 | 1.0000 | 0.1000 | 0.1000 | 0.1 |
| backend_platform_engineer | 0.8085 | 0.5922 | 0.8044 | 0.5541 | 0.8549 | 0.7236 | 0.7985 | 0.4871 | 0.6000 | 0.5000 | 0.1 |
| search_relevance_engineer | 0.9177 | 0.8312 | 0.9426 | 0.9041 | 0.9546 | 0.9092 | 1.0000 | 0.6429 | 0.2000 | 0.2000 | 0.1 |
| data_bi_analyst | 0.7702 | 0.7565 | 0.7459 | 0.7125 | 0.8075 | 0.8175 | 1.0000 | 1.0000 | 0.1000 | 0.1000 | 0.1 |
| devops_cloud_engineer | 0.8753 | 0.8717 | 0.8642 | 0.8532 | 0.8981 | 0.8954 | 0.9583 | 0.9762 | 0.6000 | 0.6000 | 0.1 |

## Limits

- Labels are role-specific proxy labels built from raw profile fields, not hidden judge labels.
- No candidate IDs or submitted ranks are used in the labeler.
- The challenge JD remains governed by the golden submission; this benchmark is transfer evidence.
