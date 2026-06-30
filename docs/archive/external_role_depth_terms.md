# External Role-Depth Term Mining

This report scans the locally downloaded public recruiting/resume datasets.
It is provenance for deterministic backend and data/BI depth lexicons; it is not hidden-label evidence.

- External dir: `C:\Users\bhune\india-runs-compare-lab\data\external`
- Max rows per CSV: `40000`
- Max CSV size: `220.0 MB`

## Role Rows

- `backend_platform`: 20,668 matched rows
- `data_bi`: 17,163 matched rows

## Top Terms

### backend_platform

- `api`: `rest api` 3765, `spring boot` 2375, `microservices` 2006, `nodejs` 1901, `django` 1820, `flask` 1283, `api gateway` 431, `graphql` 313, `websocket` 180
- `database_cache`: `database` 14633, `sql` 14509, `mysql` 7442, `mongodb` 3621, `postgresql` 3322, `cassandra` 2730, `kafka` 1762, `postgres` 1268, `redis` 941, `dynamodb` 857, `caching` 781, `rabbitmq` 722
- `scale_reliability`: `scale` 5325, `high availability` 1268, `load balancing` 662, `throughput` 528, `fault tolerant` 328, `latency` 310, `rps` 15
- `infra`: `aws` 7982, `deployment` 7294, `jenkins` 5453, `docker` 4410, `azure` 3165, `kubernetes` 1344, `ci/cd` 1251, `gcp` 1223, `terraform` 505, `github actions` 82

### data_bi

- `sql`: `sql` 13139, `stored procedure` 3571, `query optimization` 609, `cte` 114, `window function` 60, `index tuning` 40
- `warehouse`: `data warehouse` 3938, `snowflake` 1607, `redshift` 1477, `star schema` 685, `databricks` 577, `dbt` 379, `bigquery` 309, `fact table` 165, `dimension table` 132
- `visualization`: `reporting` 11000, `tableau` 5796, `dashboard` 5770, `metrics` 2664, `power bi` 2441, `kpi` 1057, `looker` 318, `superset` 57, `metabase` 20
- `etl_quality`: `etl` 5289, `data model` 5038, `data quality` 3854, `data modeling` 2901, `data pipeline` 2516, `airflow` 945, `elt` 794, `dagster` 252
- `business_impact`: `decision` 5298, `stakeholders` 3446, `revenue` 1785, `business users` 1405, `saved` 868, `adoption` 709, `self service` 519, `executives` 326, `cost reduction` 116

## Files Scanned

- `huggingface\0xnbk__resume-ats-score-v1-en\train.csv`: 5,099 rows; backend_platform=2581, data_bi=2427
- `huggingface\0xnbk__resume-ats-score-v1-en\validation.csv`: 1,275 rows; backend_platform=626, data_bi=589
- `huggingface\bwbayu__job_cv_supervised\data_supervised.csv`: 31,203 rows; backend_platform=8658, data_bi=6184
- `huggingface\cnamuangtoun__resume-job-description-fit\test.csv`: 1,759 rows; backend_platform=929, data_bi=819
- `huggingface\cnamuangtoun__resume-job-description-fit\train.csv`: 6,241 rows; backend_platform=3140, data_bi=2953
- `huggingface\layan009__RESUMES-JOBS-FIT-LABELS\resume_metadata.csv`: 100 rows; backend_platform=78, data_bi=19
- `huggingface\layan009__RESUMES-JOBS-FIT-LABELS\test.csv`: 1,759 rows; backend_platform=929, data_bi=819
- `huggingface\layan009__RESUMES-JOBS-FIT-LABELS\train.csv`: 6,241 rows; backend_platform=3140, data_bi=2953
- `kaggle\ckshetty__candidate-job-role-dataset\extracted\candidate_job_role_dataset.csv`: 1,000 rows; backend_platform=125, data_bi=50
- `kaggle\mirzayasirabdullah07__resume-dataset-for-job-role-classification\extracted\resume_dataset.csv`: 300 rows; backend_platform=57, data_bi=58
- `kaggle\surendra365__recruitement-dataset\extracted\job_applicant_dataset.csv`: 10,000 rows; backend_platform=405, data_bi=292
