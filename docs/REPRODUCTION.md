# Reproduction

```bash
# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 262 passed, 6 environment skips
# 2. committed branch-champion hash (must be byte-identical)
sha256sum submission.csv                    # -> 8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062
# 3. omitting --release still preserves main's default scorer and fixed-slice hash
```

## Regenerate the shipped submission from scratch (deterministic, no manual edits)

```bash
# requires candidates.jsonl in the repo root; CPU-only, offline
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl --out submission.csv \
  --workers 2 --release
sha256sum submission.csv                                      # -> 8f7f30c68ec30cb6…  (byte-identical)
```
There are no hidden steps or manual edits. The `--release` path forces the frontier-v5 ranking core and `bm25s`, rejects
truncation, alternate JDs, embeddings, and incompatible profiles, verifies the model artifact,
the exact official candidate-input SHA-256, candidate/honeypot counts, the BM25s backend,
and final output SHA-256, then atomically publishes the CSV. The final
the release reproduction completed in **136.0 s pipeline / 149.1 s wall** at
`--cpus=2 --memory=16g`, exact champion hash, no OOM, and zero output-directory
temporary files. A deliberate 3-GiB OOM preserved the existing output and also
left zero mounted temps because expensive work now stays container-local.
Sampled peak memory in the release matrix was 4,232.2 MiB. Omitting `--release`
retains `main`'s historical behavior.

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
