# Reproduction

```bash
# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 240 passed, 6 environment skips
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
There are no hidden steps or manual edits. `--release` forces `frontier-v5` and `bm25s`, rejects
truncation, alternate JDs, embeddings, and incompatible profiles, verifies the model artifact,
candidate/honeypot counts, and final SHA-256, then atomically publishes the CSV. The champion
completed the full 100K pool in
199.0-209.4 seconds in the constrained Docker pipeline (233.8-241.9 seconds wall clock) with
`--cpus=2 --memory=16g`. Both artifacts matched the host hash and remained under
the 300-second budget. Omitting `--release` retains `main`'s historical behavior.

Final fail-closed Docker verification (2026-06-30): 109.9 s pipeline,
4,232.2 MiB sampled peak, 100,000 loaded/ranked, 53 honeypots detected, zero
emitted, and exact SHA-256 `8f7f30c68ec30cb6...` before atomic publication.

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
