# Reproduction

```bash
# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 198 passed, 6 environment skips in this worktree
# 2. committed branch-champion hash (must be byte-identical)
sha256sum submission.csv                    # -> 7d9dd8efc7483852c0fd9ae1eb4b3894c8f17c945c7faf31b3764384d40c0a3b
# 3. omitting --scoring-profile still preserves main's default scorer and fixed-slice hash
```

## Regenerate the shipped submission from scratch (deterministic, no manual edits)

```bash
# requires candidates.jsonl in the repo root; CPU-only, offline
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl --out submission.csv \
  --workers 2 --scoring-profile top23-clean
sha256sum submission.csv                                      # -> 7d9dd8efc7483852…  (byte-identical)
```
There are no hidden steps or manual edits. The opt-in profile completed the full 100K pool in
80.0 seconds on the host and 221.4 seconds in Docker with `--cpus=2 --memory=16g`; both runs matched
the committed hash. Omitting `--scoring-profile top23-clean` retains `main`'s historical behavior.

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
