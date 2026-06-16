# Reproduction

```bash
# 0. one-shot: production gate + shipped-hash check
./reproduce.sh

# 1. full suite (deterministic env)
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m pytest -q                       # expect: 198 production + dashboard/firewall tests pass, 0 skipped
# 2. shipped submission hash (the severity-gated Copeland hedge, must be byte-identical)
sha256sum submission.csv                    # -> 24f84f4b6160a4bcb164369c7f6ab27a060953ec7cfc0d33ed4849eab1194aea
# 3. production pipeline still reproduces the golden baseline byte-for-byte (verified by the slice gate)
#    golden -> af8f2b327f05d30e22aba41e884077071c673082cd4a2647294f0969c0f0536a
#    (retained as the fallback tag fallback/golden-af8f2b32)
```

The shipped submission is the hedge (`24f84f4b`); the production ranker `rank.py` is unchanged and
deterministically reproduces golden (`af8f2b32`). The hedge is a deterministic, audited post-hoc
rerank built by `experiments/build_hedge_submission.py` (golden top-30 + Copeland tail, sev≤1.2).
Constrained-runtime check: `docker run --cpus=2 --memory=16g` reproduces golden in 165 s
(`docs/runtime_matrix.md`).

**Production firewall:** `rank.py` and `src/redrob_ranker/` never import `dashboard/`,
`omega_decision_dashboard.py`, or `experiments/`. Removing `dashboard/`, `experiments/`, and
`docs/research/` does not change production output (enforced by
`tests/test_dashboard_no_production_imports.py`). The dashboard is read-only and never runs the
production ranker.
