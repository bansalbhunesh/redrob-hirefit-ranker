# Reproduction

There is **no `reproduce.sh`**; reproduction is the golden gate test + hash check.

```bash
# 1. golden reproduction + full production gate (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 171 production + dashboard/firewall tests pass
# 2. golden hash (must be byte-identical)
sha256sum submission.csv                    # -> af8f2b327f05d30e22aba41e884077071c673082cd4a2647294f0969c0f0536a
```

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change golden output (enforced by `tests/test_dashboard_no_production_imports.py`).
The dashboard is read-only and never runs the production ranker.
