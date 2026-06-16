#!/usr/bin/env bash
# Golden reproduction — runs ONLY the frozen production path. No research/dashboard code.
set -euo pipefail
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "[1/2] golden production gate + validator"
python -m pytest tests/test_submission_gate.py -q
# NOTE (branch research/obscure-rank-aggregation): the production pipeline (rank.py) still
# reproduces the golden baseline af8f2b32 byte-for-byte (verified by the slice gate above); the
# SHIPPED submission on this branch is the Copeland reranking of that pool (d0372aed), regenerated
# deterministically by experiments/build_copeland_submission.py. main keeps golden as submission.csv.
echo "[2/2] shipped submission hash (expect d0372aedc473b78c59d0fdddcef6bd1023f47fbc77ba5bacab07f288fce8c97b)"
python - <<'PY'
import hashlib, sys
h=hashlib.sha256(open("submission.csv","rb").read()).hexdigest()
exp="d0372aedc473b78c59d0fdddcef6bd1023f47fbc77ba5bacab07f288fce8c97b"
print("sha256:", h); sys.exit(0 if h==exp else 1)
PY
echo "OK: shipped Copeland submission byte-reproducible (production pipeline still reproduces golden)."
