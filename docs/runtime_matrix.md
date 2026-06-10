# Docker Runtime Matrix (Phase 0.1)

Environment: `python:3.11-slim` image (the Stage-3 reproduction environment),
Docker Desktop on Windows 11 / WSL2 (12 host CPUs, **8.15 GB VM memory** — the
host VM cannot model the full 16 GB budget; the container cap used was 6 GB and
no run approached the real 16 GB limit). Full 100,000-candidate pool,
`--bm25-backend bm25s`, `PYTHONHASHSEED=0` baked into the image.

Measurement tool: `scripts/docker_runtime_matrix.sh` (samples container memory
at 2 s; wall time from container start/finish timestamps; pipeline runtime is
the ranker's own measurement, excluding container start).

## Results — current code (token-set matching, commit `8e20cbf`)

| config | pipeline runtime (s) | peak container mem (MB) | output |
|---|---|---|---|
| `--cpus=2 --workers 1` (worst case, serial) | **193.4** | ~4,880 | byte-identical to golden |
| `--cpus=2 --workers 2` | **194.1** | ~5,410 | byte-identical to golden |
| `--cpus=4 --workers 4` | **177.3** | ~6,100 | byte-identical to golden |

Optimization history, same matrix, worst case (serial on 2 CPUs):

| code version | serial-2cpu runtime |
|---|---|
| pre-optimization (`1bb77d7`) | 269.3 s — over the 240 s margin, triggered the mandated work |
| pad-once / early-exit / norm caching (`cbf6290`) | 235.6 – 255.8 s (±10% host variance across two passes) |
| + token-set matching (`8e20cbf`) | **193.4 s** |
| + multi-word token-set prefilter + feature hoists (2026-06-10 audit) | **163.0 s** min-of-3; 215.1 s worst observed under host load (see docs/performance_audit.md) |

Every optimization was proven byte-identical via the golden regression tests
and a full-100K hash comparison before merging (the 2K gate caught one real
semantic divergence — whitespace-class tokenization — during development).

## Budget verdict

- Hard limit 300 s: **worst case passes with ~28-46% headroom** (2026-06-10 audit:
  163.0 s min-of-3, 215.1 s worst observed under host load, serial on 2 CPUs).
- 240 s safety margin: all configurations and all observed runs under it.
- Memory: peak ~6.1 GB observed (4-worker config) against the 16 GB budget —
  ~62% headroom.
- Determinism: every matrix run, all three code versions, produced a CSV
  byte-identical to the then-current golden submission (Linux container vs
  Windows host, serial vs parallel).

## Recommended reproduction command (Stage-3)

```bash
docker build -t redrob-hirefit-ranker .
docker run --rm --memory=16g -v "<dir>:/data" redrob-hirefit-ranker \
  --candidates /data/candidates.jsonl --out /data/submission.csv \
  --bm25-backend bm25s
# --workers defaults to auto (up to 8); output is identical for any worker count
```
