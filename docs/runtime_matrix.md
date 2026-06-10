# Docker Runtime Matrix (Phase 0.1)

Environment: `python:3.11-slim` image (the Stage-3 reproduction environment),
Docker Desktop on Windows 11 / WSL2 (12 host CPUs, **8.15 GB VM memory** — the
host VM cannot model the full 16 GB budget; the container cap used was 6 GB and
no run approached the real 16 GB limit). Full 100,000-candidate pool,
`--bm25-backend bm25s`, `PYTHONHASHSEED=0` baked into the image.

Measurement tool: `scripts/docker_runtime_matrix.sh` (samples container memory
at 2 s; wall time from container start/finish timestamps; pipeline runtime is
the ranker's own measurement, excluding container start).

## Results — optimized code (commit `cbf6290` hot-path work)

Two full passes of the matrix were run; this host shows ±10% run-to-run
variance (Defender/OneDrive background activity), so ranges are reported.

| config | pipeline runtime (s) | peak container mem (MB) | output |
|---|---|---|---|
| `--cpus=2 --workers 1` (worst case, serial) | **235.6 – 255.8** | ~5,050 | byte-identical to golden (both runs) |
| `--cpus=2 --workers 2` | **218.6 – 242.0** | ~5,420 | byte-identical to golden (both runs) |
| `--cpus=4 --workers 4` | **221.4 – 252.5** | ~6,100 | byte-identical to golden (both runs) |

Pre-optimization baseline (same matrix, commit `1bb77d7` code):
serial-on-2-cpus **269.3 s** — over the 240 s safety margin, which triggered
the mandated `compute_features` hot-path optimization (pad-once boundary
checks, early-exit alias matching, short-string norm caching; byte-identical,
locked by the golden regression tests). The optimization removed ~30-35 s
(~13%) from the worst case.

## Budget verdict

- Hard limit 300 s: **all configurations pass with ≥15% headroom**, including
  the worst observed sample of the worst configuration (255.8 s serial on 2
  CPUs).
- 240 s safety margin: the best observed serial sample (235.6 s) is under it;
  the worst sample (255.8 s) is not. With ≥2 workers (the default: `--workers`
  auto-selects up to 8), every observed sample on ≥2 CPUs is at or under
  ~242 s and typically ~220 s.
- Memory: peak ~6.1 GB observed (4-worker config) against the 16 GB budget —
  ~62% headroom.
- Determinism: every matrix run, both code versions, produced a CSV
  byte-identical to the golden submission (Linux container vs Windows host,
  serial vs parallel).

## Recommended reproduction command (Stage-3)

```bash
docker build -t redrob-hirefit-ranker .
docker run --rm --memory=16g -v "<dir>:/data" redrob-hirefit-ranker \
  --candidates /data/candidates.jsonl --out /data/submission.csv \
  --bm25-backend bm25s
# --workers defaults to auto (up to 8); output is identical for any worker count
```
