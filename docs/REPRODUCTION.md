# Reproduction

```bash
# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 216 passed, 6 environment skips
# 2. committed branch-champion hash (must be byte-identical)
sha256sum submission.csv                    # -> 79aebff697cbccf0b03137998d0b6faf2da61caebaa0ae34f0e5fc876650127e
# 3. omitting --scoring-profile still preserves main's default scorer and fixed-slice hash
```

## Regenerate the shipped submission from scratch (deterministic, no manual edits)

```bash
# requires candidates.jsonl in the repo root; CPU-only, offline
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl --out submission.csv \
  --workers 2 --scoring-profile dominant-v4
sha256sum submission.csv                                      # -> 79aebff697cbccf0b…  (byte-identical)
```
There are no hidden steps or manual edits. The opt-in profile completed the full 100K pool in
75.4 seconds in the constrained Docker pipeline (79.5 seconds wall clock) with
`--cpus=2 --memory=16g`. A same-image V3 control took 91.3 seconds; its output
still matched the historical V3 hash. Omitting `--scoring-profile dominant-v4`
retains `main`'s historical behavior.

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
