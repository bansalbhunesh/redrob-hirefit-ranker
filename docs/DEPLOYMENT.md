# Deployment guide

The graded ranker and the recruiter demo are deliberately separate:

| Surface | Purpose | Network during ranking |
|---|---|---|
| `rank.py --release` | Official 100K submission path | None |
| FastAPI app | Showpiece, live sample ranking, batch demo, health and metrics | Same-process HTTP only |
| Hugging Face Space | Public recruiter-facing sandbox | Hosted UI |

## Local API

```bash
python -m pip install -e ".[api]"
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Verify:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:8000/api/readyz
curl --fail http://127.0.0.1:8000/api/metrics
```

Use one Uvicorn worker: batch progress uses an in-process SSE channel and the SQLite job
store is designed for one service process. The API applies upload limits, rate limiting,
restricted CORS, security headers, sanitized errors, readiness checks, and optional write
authentication through `REDROB_DEMO_TOKEN`.

## Render Blueprint

The root [`render.yaml`](../render.yaml) is the deployable source of truth. It installs the
API extra, starts one Uvicorn worker, checks `/api/readyz`, pins deterministic thread settings,
and deploys only after GitHub checks pass.

[Deploy to Render](https://render.com/deploy?repo=https://github.com/bansalbhunesh/redrob-hirefit-ranker)

The public Render decision room and its `/api/healthz` and `/api/readyz` gates returned HTTP 200
on 2026-07-02. The Hugging Face Space remains the lightweight sandbox; Render is the full
recruiter workspace. The committed Blueprint makes a fresh deployment reproducible.

## Environment variables

| Variable | Default | Purpose |
|---|---:|---|
| `REDROB_MAX_LIVE_CANDIDATES` | 500 | Live upload candidate cap |
| `REDROB_MAX_BATCH_CANDIDATES` | 5000 | Batch demo cap |
| `REDROB_MAX_EXPANDED_UPLOAD_BYTES` | 33554432 | Expanded gzip safety cap |
| `REDROB_MAX_CANDIDATE_RECORD_BYTES` | 1048576 | Per-record JSONL safety cap |
| `REDROB_RATE_LIMIT_PER_MINUTE` | 120 | Per-client request limit |
| `REDROB_CORS_ORIGINS` | localhost + live Render origin | Comma-separated browser origins |
| `REDROB_DEMO_TOKEN` | unset | Optional `X-Demo-Token` requirement for write endpoints |
| `REDROB_GIT_SHA` | auto-detected | Build identity exposed by health endpoints |

## Deployment acceptance gate

A deployment is judge-ready only when all are true:

- `/api/health` returns 200 with version `6.0.0` and the expected build SHA.
- `/api/readyz` returns 200 with `precomputed_loaded=true` and `dashboard_present=true`.
- `/api/metrics` returns Prometheus text without leaking file paths or candidate data.
- The homepage displays **33 Features** and the committed top-100.
- A desktop and mobile browser pass shows no horizontal overflow or console errors.
- `python -m pytest -q` and the GitHub `gates` check pass on the deployed commit.
