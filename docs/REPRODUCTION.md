# Reproduction

```bash
# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 209 passed, 6 environment skips
# 2. committed branch-champion hash (must be byte-identical)
sha256sum submission.csv                    # -> c28857fdba63723ed13bea35d977a49f3aca7550dc7ea1c2c82d4150279e769c
# 3. omitting --scoring-profile still preserves main's default scorer and fixed-slice hash
```

## Regenerate the shipped submission from scratch (deterministic, no manual edits)

```bash
# requires candidates.jsonl in the repo root; CPU-only, offline
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl --out submission.csv \
  --workers 2 --scoring-profile loss-aggregate-v3
sha256sum submission.csv                                      # -> c28857fdba63723e…  (byte-identical)
```
There are no hidden steps or manual edits. The opt-in profile completed the full 100K pool in
77.4-79.8 seconds on the host and 152.8-226.9 seconds in Docker with `--cpus=2 --memory=16g`; all runs matched
the committed hash. Omitting `--scoring-profile loss-aggregate-v3` retains `main`'s historical behavior.

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
