# Backend Infra Hardening

Scope: FastAPI demo/API surface only. The deterministic ranking path, `submission.csv`,
golden hash, and offline Docker reproduction are unchanged.

## What Was Weak

The earlier backend story was demo-acceptable but not judge-proof:

- live ranking ran CPU work directly inside the async request handler;
- no request IDs or request timing headers;
- no metrics endpoint;
- no readiness endpoint for deployment health checks;
- no rate limiting on expensive POST routes;
- batch jobs had SSE/results, but no sanitized status endpoint or CSV artifact download;
- upload extension policy was implicit;
- the in-memory job-store constraint was documented but not visible from the running service.

## What Is Now Stronger

### Operational surface

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Liveness plus build SHA, artifact status, job counts, limits, uptime |
| `GET /api/healthz` | Liveness alias for deployment platforms |
| `GET /api/readyz` | Readiness; returns `503` if the dashboard/precomputed artifact is missing |
| `GET /api/metrics` | Prometheus-style text metrics: request totals, latency sum, status counts, active jobs, rate-limit rejects, live/batch counters |
| `GET /api/batch/{job_id}` | Sanitized job status; no filesystem paths leaked |
| `GET /api/batch/{job_id}/download` | Completed batch CSV download |

### Safety and reliability

- Every response gets `X-Request-ID`, `Server-Timing`, and hardened browser/security headers.
- Expensive POST routes use an in-process rate limit:
  `REDROB_RATE_LIMIT_PER_MINUTE` over `REDROB_RATE_LIMIT_WINDOW_SECONDS`.
- Live ranking now uses `asyncio.to_thread(...)`, so a demo ranking request does not block the
  FastAPI event loop.
- Batch active concurrency is env-controlled with `REDROB_MAX_ACTIVE_BATCH_JOBS`.
- Uploads are explicitly limited to `.jsonl`, `.json`, `.jsonl.gz`, and `.gz`.
- JSON, JSONL, and gzipped candidate counts are checked before ranking so caps fail early.
- Gzip expansion and individual JSONL records have independent byte caps, preventing a small compressed upload from expanding without bound.
- Rate-limit identity comes from the ASGI server's resolved client address; raw, user-supplied `X-Forwarded-For` values are not trusted by application code.
- Candidate-controlled strings are HTML-escaped in the browser before insertion into dynamic cards and dossiers.
- Batch rejected uploads still delete partial job directories.
- Failed jobs expose sanitized errors only; internals stay in server logs.

## Env Controls

| Env var | Default | Meaning |
|---|---:|---|
| `REDROB_MAX_LIVE_CANDIDATES` | `500` | Sync/live candidate cap |
| `REDROB_MAX_BATCH_CANDIDATES` | `5000` | Batch/demo candidate cap |
| `REDROB_MAX_LIVE_UPLOAD_BYTES` | `2097152` | Live upload byte cap |
| `REDROB_MAX_BATCH_UPLOAD_BYTES` | `16777216` | Batch upload byte cap |
| `REDROB_MAX_EXPANDED_UPLOAD_BYTES` | `33554432` | Maximum expanded bytes read from a gzip upload |
| `REDROB_MAX_CANDIDATE_RECORD_BYTES` | `1048576` | Maximum bytes in one JSONL candidate record (plain or gzip) |
| `REDROB_MAX_STORED_JOBS` | `20` | In-memory job retention cap |
| `REDROB_MAX_ACTIVE_BATCH_JOBS` | `2` | Active queued/processing batch cap |
| `REDROB_RATE_LIMIT_PER_MINUTE` | `120` | Per-client POST limit for `/api/rank` and `/api/batch`; set `0` to disable |
| `REDROB_RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window |
| `REDROB_CORS_ORIGINS` | localhost + Render origin | Comma-separated CORS allowlist |
| `REDROB_GIT_SHA` | auto-detected | Build identity override |

## What This Still Is Not

This is not a multi-worker production cluster. Batch jobs are still in process memory, so
`uvicorn` must run with one worker unless Redis/Postgres is added. That is a documented
constraint, not a hidden failure.

A true production version would add:

- Redis/Postgres-backed job store;
- object storage for uploaded files and CSV artifacts;
- authentication and per-user quotas;
- centralized logs/metrics/traces;
- deployment-managed secrets and audit logs.

Those are real product items, but they are not safe deadline changes unless the whole app
is deployed and tested around them.

## Verification

Targeted backend tests:

```powershell
python -m py_compile apps\api\main.py
python -m pytest tests\test_api_endpoints.py tests\test_api_cleanup.py
```

Current full-suite result: `275 passed`.
