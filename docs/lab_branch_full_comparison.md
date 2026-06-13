# Lab Branch Full Comparison

Generated on 2026-06-13 from local worktrees:

- `main`: `C:\Users\bhune\india-runs-compare-main`
- `codex/performance-optimization`: `C:\Users\bhune\india-runs` working tree, dirty before this audit
- `codex/100-score-gap-lab`: `C:\Users\bhune\india-runs-compare-lab`

## Executive Verdict

The lab branch is stronger than both main and the performance branch on backend surface, security scan cleanliness, transfer-eval evidence, and host runtime. It is not "100/100 objection-proof." The previous 100K backend transfer loss is now closed: backend is `0.7064` versus keyword `0.6660`. The remaining backend caveat is the smaller 20K slice, where backend is `0.7058` versus keyword `0.7120`.

Brutal score after this pass: **89/100 versus main**, **87/100 versus the performance working tree**, **83/100 versus an imaginary champion with real blind human labels**.

## Test Matrix

| target | result | note |
|---|---:|---|
| main | 114 passed, 1 skipped | full suite |
| performance working tree | 127 passed | full suite |
| lab final | 152 passed, 1 skipped | full suite after security/cgroup/backend-transfer fixes |
| lab focused cgroup/security tests | 9 passed + 11 passed | retrieval cgroup, independent labeler, external eval, research fetch |

The lab manifest now declares **153 collected**, **152 passing**, **1 skipped** because security, cgroup-tokenizer, and backend-transfer regression tests were added after the earlier 148-test baseline.

## API / Demo Surface

| target | FastAPI routes |
|---|---:|
| main | 7 |
| performance working tree | 7 |
| lab | 12 |

Lab adds production-style readiness/status/download/metrics endpoints:

- `GET /api/batch/{job_id}`
- `GET /api/batch/{job_id}/download`
- `GET /api/healthz`
- `GET /api/readyz`
- `GET /api/metrics`

This is a real backend-infra improvement over main. It is still not a production SaaS backend: stores are process-local, there is no auth, durable queue, tenant isolation, persistent audit log, or ATS integration.

## Official 100K Runtime

All three host runs produced the same golden hash:

`a2882cd2ae637dde59244d9c5596bc529356c843281862ceefa2f9dfb0da9922`

| target | host wall | pipeline time | peak RSS | verdict |
|---|---:|---:|---:|---|
| main | 126.6s | 122.8s | 4.54 GB | pass |
| performance working tree | 120.4s | 116.7s | 4.57 GB | pass |
| lab | 95.0s | 92.8s | 4.56 GB | best |

Lab is ~25% faster than main and ~21% faster than the performance working tree on the same host run.

## Docker / VM Runtime

Image: `redrob-lab-audit:local`, base digest pinned, non-root `appuser`, 2 CPUs, 16 GB memory. All successful outputs were byte-identical to the golden submission and validator-clean.

| run | input path | wall | pipeline | verdict |
|---|---|---:|---:|---|
| before retrieval cgroup patch | Windows bind mount | 226.1s | 221.0s | misses sub-200 |
| after retrieval cgroup patch | Windows bind mount | 214.0s | 205.0s | still misses sub-200 |
| forced `--workers 1` | Windows bind mount | 224.3s | 219.7s | worse |
| after retrieval cgroup patch | Docker named volume | 146.1s | 141.6s | pass |

Plain truth: the ranker is sub-200 in a VM-local filesystem. Docker Desktop Windows bind-mount I/O can push it above 200. Do not advertise the bind-mount number as fixed; advertise the VM-local number and explain the mount overhead if asked.

## Security / Vulnerability Scan

Bandit scan over `apps`, `src`, and `scripts`:

| target | high | medium | low | result count |
|---|---:|---:|---:|---:|
| main | 0 | 0 | 15 | 15 |
| performance working tree | 0 | 0 | 14 | 14 |
| lab | 0 | 0 | 0 | 0 |

Lab dependency audits with `pip-audit --no-deps`:

- `requirements.txt`: clean
- `requirements-api.txt`: clean
- `requirements-demo.txt`: clean
- `requirements-research.txt`: clean after removing direct `torch` and adding `defusedxml`
- `hf_space/requirements.txt`: clean after moving to `gradio>=6.7,<7` and `pillow>=12.2,<13`

One audit limitation remains: the HF Space file references `git+https://github.com/bansalbhunesh/redrob-hirefit-ranker.git@main`; `pip-audit` cannot audit that package as a PyPI artifact. This is acceptable for local evidence, but deployment still depends on what is pushed to `main`.

## Multi-JD Transfer Evaluation

20K prepared benchmark:

| role | HireFit | keyword | result |
|---|---:|---:|---|
| senior AI engineer | 0.8363 | 0.4932 | win |
| backend platform engineer | 0.7058 | 0.7120 | narrow loss |
| search relevance engineer | 0.8306 | 0.7256 | win |
| data/BI analyst | 0.8612 | 0.8061 | win |
| devops/cloud engineer | 0.7510 | 0.6595 | win |
| mean | 0.7970 | 0.6793 | win |

100K prepared benchmark:

| role | HireFit | keyword | role seconds | result |
|---|---:|---:|---:|---|
| senior AI engineer | 0.8695 | 0.5274 | 74.5s | win |
| backend platform engineer | 0.7064 | 0.6660 | 67.5s | win |
| search relevance engineer | 0.8192 | 0.7432 | 75.5s | win |
| data/BI analyst | 0.7823 | 0.7140 | 66.5s | win |
| devops/cloud engineer | 0.6737 | 0.6506 | 71.8s | win |
| mean | 0.7702 | 0.6602 | prep 108.4s | win |

This closes the 100K generalization gap for all five technical families. Backend remains the family to watch because the 20K slice still trails keyword by `0.0062`.

## Changes Executed In This Pass

- Removed `torch` from research requirements to eliminate the research-only CVE surface.
- Added `defusedxml` and switched ArXiv XML parsing to `defusedxml.ElementTree`.
- Added URL scheme guards for public research and external dataset downloads.
- Patched `hf_space` to Gradio/Pillow vulnerability-fixed floors.
- Cleaned Bandit findings to zero across app/source/scripts.
- Added tests for non-http URL rejection and cgroup-aware tokenization.
- Changed multi-JD benchmark default to full pool unless `--max-candidates` is explicitly set.
- Added cgroup-aware tokenization worker resolution in BM25 retrieval.
- Added backend transfer role routing: production credit now requires career-history delivery evidence, senior software delivery gets a backend-role boost, and AI/ML-title bleed is down-weighted for backend JDs.

## Remaining Gaps

1. **No real hidden-label proof.** The repo has strong proxy evidence, not Redrob/human blind labels on the actual candidate pool.
2. **Backend transfer is improved, not invulnerable.** It now wins on 100K, but the 20K slice still narrowly trails keyword.
3. **Docker Desktop bind-mount runtime is not sub-200.** VM-local is sub-200; Windows bind mount is not.
4. **HF Space deploy is not updated until pushed.** Local `hf_space` requirements are fixed, but the Space installs from GitHub `main`.
5. **Backend service is demo-strong, not production-complete.** No auth, durable jobs, tenant isolation, or persistent audit logs.

## Next Highest-ROI Plan

1. Generate a small external blind label pack with multiple judges/humans for the five role families. Without this, 95+ is not credible.
2. Add a tiny persisted job/audit layer for the FastAPI demo: SQLite job store, immutable request/result manifest, and one auth/header gate for demo protection.
3. Tighten backend transfer further on the 20K slice without sacrificing the now-winning 100K result.
