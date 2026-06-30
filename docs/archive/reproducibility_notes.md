# Byte-Reproducibility of `submission.csv`

## Guarantee

The committed `submission.csv` is byte-identical to a fresh run of the pinned
Docker image, **regardless of the host's CPU count**. Golden SHA256:

```
fdfd3f3590720e1260822b6729b2851dc8daca9f3f859cefc3df184bbbd4c5db
```

Verify it:

```bash
docker build -t redrob-lab-pinned .
docker run --rm --cpus=2 --memory=16g \
  -v "$(pwd):/data:ro" -v "$(pwd)/_out:/out" \
  redrob-lab-pinned \
  --candidates /data/candidates.jsonl --out /out/submission.csv
sha256sum _out/submission.csv   # -> fdfd3f35...
```

(The image `ENTRYPOINT` is already `python rank.py`, so pass only the args — do
not repeat `python rank.py`.)

## Why this needed fixing (2026-06-14)

The previous golden (`6b284271…`) was minted on a many-core host. BM25 scoring
runs through numpy/BLAS, whose floating-point **reduction order is not
bitwise-stable across thread counts**. A clean `--cpus=2` reproduction therefore
produced a *different* (but still internally deterministic) ranking
(`fdfd3f35…`) — 16 near-tie placements moved, 99/100 normalized scores shifted in
the 6th decimal, honeypots unchanged at 0/53. So the old artifact failed the
"a judge re-running the repro gets the submitted file" test.

## The fix

BLAS/threadpool thread counts are pinned to 1 **before numpy/bm25s import**, in
two places:

- `Dockerfile`: `ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`
- `rank.py`: `os.environ.setdefault(...)` for the same four variables, so the
  native `python rank.py …` reproduce command is also CPU-count-independent.

`submission.csv` was then regenerated inside that pinned image and the golden
hash rolled in `tests/test_submission_gate.py` and `docs/metrics_manifest.json`.

## Verified determinism matrix (pinned image, real 100K pool)

| Config | Output hash | Runtime (local Docker Desktop) |
|---|---|---|
| `--cpus=2`, default workers | `fdfd3f35…` | ~130 s |
| `--cpus=2`, `--workers 1` (serial) | `fdfd3f35…` | ~155 s |
| `--cpus=4` | `fdfd3f35…` | ~135 s |

All identical → reproducible across CPU counts **and** worker counts. (Cloud
2-vCPU Linux runs faster, ~80 s; see `docs/runtime_matrix.md`.) Running fully
unconstrained on a 12-core host exceeds the 16 GB budget (OOM) and is not a valid
evaluation configuration; always run with `--cpus` bounded.

## Scope notes

- The 2K-slice regression golden (`GOLDEN_SLICE2K_SHA256`) is unaffected: the
  2,000-document slice is small enough that BLAS stays single-threaded, so it is
  already CPU-count-independent and the thread pin does not move it.
- The pins are intentionally NOT applied to the FastAPI service process (only to
  `rank.py` and the container env), so interactive demo throughput is unchanged.
