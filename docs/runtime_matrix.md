# Docker Runtime Matrix (Phase 0.1)

## 2026-06-30 V6 quality-safe inference hardening

V6 keeps the exact `frontier-v5` rank artifact and removes repeated work in two
post-retrieval hotspots. The dual V2/main scoring pass is bit-exact and measured
36.8% faster in an isolated 5,000-candidate loop (median 0.0546 s to 0.0345 s).
The 3,000-row model feature matrix is also bit-exact and measured 77.0% faster
(median 0.1848 s to 0.0425 s). These stages are small relative to BM25, so the
claim is reduced CPU work and no regression, not a universal wall-time speedup.

The full 100,000-candidate verification used a Docker-native volume,
`--cpus=2 --memory=16g`, and two workers:

| Image | Pipeline time | Sampled peak | Output SHA-256 | Integrity |
|---|---:|---:|---|---|
| unchanged V5 stress control | 299.2 s | not retained | `8f7f30c68ec30cb6...` | 53 detected / 0 emitted |
| V6 hardened | **197.2 s** | **4,204.5 MiB** | `8f7f30c68ec30cb6...` | 53 detected / 0 emitted |
| V6 fail-closed `--release` | **109.9 s** | **4,232.2 MiB** | `8f7f30c68ec30cb6...` | release verified; 53 / 0 |

The 102-second paired gap is dominated by Docker Desktop host variance: earlier
unchanged V5 runs were 199.0-209.4 s. The defensible result is that V6 matches
the prior normal V5 window, remains under 300 seconds, uses less than the
effective Docker VM memory, and reproduces the artifact byte-for-byte. Although
the container requested 16 GB, this Docker Desktop VM exposed about 7.6 GiB;
the run remained well below even that smaller effective cap.

The final `--release` row exercises the production guard itself, not merely the
profile: it verifies the model SHA-256 before scoring, forces BM25s and
`frontier-v5`, generates into a temporary file, validates full-pool and integrity
counts plus the final SHA-256, and only then atomically publishes the output.

## 2026-06-29 frontier-v5 constrained verification

The exact `frontier-v5` artifact was regenerated twice from all 100,000
candidates using a Docker-native input volume, `--cpus=2 --memory=16g`, and
two workers:

| Pass | Pipeline time | Wall time | Output SHA-256 |
|---|---:|---:|---|
| V5 cold/stress | 209.4 s | 233.8 s | `8f7f30c68ec30cb6...` |
| V5 repeat | **199.0 s** | 241.9 s | `8f7f30c68ec30cb6...` |
| V4 same-image control | 108.6 s | 124.7 s | `79aebff697cbccf0...` |

Both V5 artifacts match the host artifact byte-for-byte, reported no OOM, and
stayed below the 300-second budget. Full-run Docker Desktop timing was noisy:
an isolated 5,000-candidate same-image check measured V5 at 9.1 s and V4 at
10.9 s, confirming that the two final 100-row sorts do not add material
algorithmic cost. The measured full-run spread is retained rather than
presented as a speedup.

## 2026-06-29 dominant-v4 constrained verification

The exact `dominant-v4` artifact was generated from all 100,000 candidates
using a Docker-native input volume and `--cpus=2 --memory=16g`:

| Profile | Pipeline time | Wall time | Output SHA-256 |
|---|---:|---:|---|
| dominant-v4 | **75.4 s** | **79.5 s** | `79aebff697cbccf0b…` |
| loss-aggregate-v3 control | 91.3 s | 95.7 s | `c28857fdba63723e…` |

Both profiles used the same image and input volume. V3 reproduced its prior
artifact byte-for-byte; V4 passed the validator and emitted zero honeypots.
Docker Desktop timings vary with host load, so this establishes no regression
and strong margin under the 300-second limit rather than a universal speedup.

## 2026-06-29 loss-aggregate-v3 query-only BM25 optimization

A controlled before/after run used the same Docker-native volume, pinned image
dependencies, full 100,000-candidate input, and `--cpus=2 --memory=16g`:

| image | pipeline runtime | output SHA-256 |
|---|---:|---|
| loss-aggregate-v3 before optimization | **109.3 s** | `c28857fd...e769c` |
| loss-aggregate-v3 optimized | **69.1 s** | `c28857fd...e769c` |

That is **40.2 seconds / 36.8% less runtime** (1.58x throughput) with byte-for-byte
identical output. The optimized path computes Lucene-BM25 statistics only for
the single JD query instead of building an unused full-corpus vocabulary and
sparse index. Large read buffering, fork-shared candidate/text data, parallel
text rendering, and cached constant HyRE tokens remove additional I/O and IPC.

Docker Desktop bind-mount timing remains host-I/O-sensitive. The optimized image
also completed a deliberately loaded bind-mount run in **254.0 s**, below the
300-second limit, with the same hash, 53 honeypots detected, and 0 emitted.

## 2026-06-29 loss-aggregate-v3 constrained reproduction

The exact branch artifact (`c28857fd…`) was regenerated from all 100,000
candidates. Host runs were **77.4-79.8 s**. Two pinned Linux container passes
completed in **152.8 s** and **226.9 s** under `--cpus=2 --memory=16g`, detected 53 honeypots, emitted 0,
and produced the byte-identical SHA-256
`c28857fdba63723ed13bea35d977a49f3aca7550dc7ea1c2c82d4150279e769c`.

> **Note.** Dated entries below reference earlier goldens (`a2882cd2…`). The
> current golden is `fdfd3f35…` (2026-06-14 reproducibility fix), byte-identical
> across CPU counts — see `docs/reproducibility_notes.md`.

## 2026-06-29 universal-v2 constrained reproduction

The exact branch artifact (`c00f708a…`) was regenerated from all 100,000
candidates with `PYTHONHASHSEED=0` and two scoring workers:

| environment | constraint | pipeline runtime | result |
|---|---|---:|---|
| Windows host | 2 workers | **130.1 s** | 53 honeypots detected, 0 emitted |
| pinned Linux Docker | `--cpus=2 --memory=16g` | **164.1 s** | byte-identical to host |

Both outputs have SHA-256
`c00f708ab63265b73eb280d058ad72376df94c66dc49c50e2027e62ef894e7f3`.
The Docker run is 135.9 seconds inside the 300-second limit.

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
| `--cpus=4 --workers 4` | **88.6** | N/A | Native Windows (2 cores) |

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

## 2026-06-11 calibration-roll reproduction

Fresh `--no-cache` build of the calibrated submission (consensus calibration
pass + reasoning-variety pass), full 100K, `--cpus=2 --workers 1` (worst-case
serial): **124.7 s** pipeline, byte-identical to the committed
`submission.csv` (`a2882cd2…`), honeypots in output 0. Best worst-case serial
figure recorded to date.

## 2026-06-11 pinned-image hardening reproduction

The Dockerfile now pins the base image by digest
(`python:3.11-slim@sha256:ef442c44…`) and installs exact-pinned deps from
requirements.txt (numpy 2.4.6, orjson 3.11.9, bm25s 0.3.9, rank-bm25 0.2.2) so
a July evaluation rebuild resolves the verified environment instead of
whatever the tag points to that week. Verification: fresh `--no-cache` build
on the pinned digest, full 100K, default workers: **138.3 s** pipeline,
honeypots 53 detected / 0 emitted, output **byte-identical** to the committed
`submission.csv` (`a2882cd2…`).

## 2026-06-16 constrained reproduction (cpu2 / 16 GB)

Fresh build + full 100K run under the exact Stage-3 constraint
`docker run --cpus=2 --memory=16g`, default workers, `--bm25-backend bm25s`:
**165 s** pipeline wall, output **byte-identical to golden `af8f2b32`**
(`af8f2b327f05d30e…`), well inside both the 300 s hard limit and the 240 s
safety margin. Confirms the production pipeline still reproduces golden under
the constrained runtime even though the shipped `submission.csv` is the
severity-gated Copeland hedge (a deterministic post-hoc rerank, not part of the
timed pipeline).

## Budget verdict

- Hard limit 300 s: **worst case passes with ~38-56% headroom** (2026-06-10 audit,
  quiet-host min-of-5 on a fresh no-cache build: 133.1-187.2 s serial on 2 CPUs;
  215.1 s worst ever observed under heavy host load).
- 240 s safety margin: all configurations and all observed runs under it; even a
  15%-slower evaluator box stays inside the margin.
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
