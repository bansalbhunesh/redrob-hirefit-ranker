# Reproduction

```bash
# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 205 passed, 6 environment skips
# 2. committed branch-champion hash (must be byte-identical)
sha256sum submission.csv                    # -> c00f708ab63265b73eb280d058ad72376df94c66dc49c50e2027e62ef894e7f3
# 3. omitting --scoring-profile still preserves main's default scorer and fixed-slice hash
```

## Regenerate the shipped submission from scratch (deterministic, no manual edits)

```bash
# requires candidates.jsonl in the repo root; CPU-only, offline
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl --out submission.csv \
  --workers 2 --scoring-profile universal-v2
sha256sum submission.csv                                      # -> c00f708ab63265b7…  (byte-identical)
```
There are no hidden steps or manual edits. The opt-in profile completed the full 100K pool in
130.1 seconds on the host and 164.1 seconds in Docker with `--cpus=2 --memory=16g`; both runs matched
the committed hash. Omitting `--scoring-profile universal-v2` retains `main`'s historical behavior.

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
