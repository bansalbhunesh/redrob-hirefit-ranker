#!/usr/bin/env bash
# Golden reproduction — runs ONLY the frozen production path. No research/dashboard code.
set -euo pipefail
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "[1/2] golden production gate + validator"
python -m pytest tests/test_submission_gate.py -q
echo "[2/2] release submission hash (expect 8f7f30c68ec30cb6...)"
python - <<'PY'
import hashlib, sys
h=hashlib.sha256(open("submission.csv","rb").read()).hexdigest()
exp="8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062"
print("sha256:", h); sys.exit(0 if h==exp else 1)
PY
echo "OK: frontier-v5 release artifact (8f7f30c6...) is locked."
echo "Full regeneration: PYTHONHASHSEED=0 python rank.py --release --candidates candidates.jsonl --out submission.csv --workers 2"
