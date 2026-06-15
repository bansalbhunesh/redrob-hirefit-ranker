#!/usr/bin/env bash
# Golden reproduction — runs ONLY the frozen production path. No research/dashboard code.
set -euo pipefail
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "[1/2] golden production gate + validator"
python -m pytest tests/test_submission_gate.py -q
echo "[2/2] golden output hash (expect af8f2b327f05d30e22aba41e884077071c673082cd4a2647294f0969c0f0536a)"
python - <<'PY'
import hashlib, sys
h=hashlib.sha256(open("submission.csv","rb").read()).hexdigest()
exp="af8f2b327f05d30e22aba41e884077071c673082cd4a2647294f0969c0f0536a"
print("sha256:", h); sys.exit(0 if h==exp else 1)
PY
echo "OK: golden byte-reproducible."
