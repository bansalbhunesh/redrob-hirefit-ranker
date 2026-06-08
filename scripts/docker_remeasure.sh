#!/usr/bin/env bash
# Re-measure the official ranker inside the Python 3.11 Docker image -- i.e. the
# Stage-3 reproduction environment. This is the number that actually matters for
# the runtime constraint (the dev machine runs 3.14; reproduction runs 3.11), and
# it exercises multiprocessing under Linux `fork` rather than Windows `spawn`.
#
# Usage:
#   bash scripts/docker_remeasure.sh [/abs/path/to/candidates.jsonl] [MAX_CANDIDATES]
#
# Examples:
#   bash scripts/docker_remeasure.sh ./candidates.jsonl            # full 100K
#   bash scripts/docker_remeasure.sh ./candidates.jsonl 5000       # quick smoke test
set -euo pipefail

# On Windows Git Bash, MSYS rewrites /data -> C:/Program Files/Git/data. Disable it
# so container-side paths and args pass through untouched.
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

CANDIDATES="${1:-./candidates.jsonl}"
MAX="${2:-}"
IMAGE="redrob-hirefit-ranker"
# `pwd -W` yields a Windows path (C:/...) under Git Bash, which Docker Desktop
# accepts for -v; falls back to POSIX pwd on Linux/macOS.
HOSTDIR="$(cd "$(dirname "$CANDIDATES")" && { pwd -W 2>/dev/null || pwd; })"
FILE="$(basename "$CANDIDATES")"

echo "== building $IMAGE (python:3.11-slim) =="
docker build -t "$IMAGE" .

ARGS=(--candidates "/data/$FILE" --out "/data/submission_docker.csv" --bm25-backend bm25s)
[ -n "$MAX" ] && ARGS+=(--max-candidates "$MAX")

echo "== running ranker in container (16g mem cap, all cpus) =="
START=$(date +%s)
docker run --rm --memory=16g \
  -v "$HOSTDIR:/data" \
  "$IMAGE" "${ARGS[@]}"
END=$(date +%s)

echo "== wall time (incl. container start): $((END - START))s =="
echo "Compare the pipeline's own 'Runtime Xs' line above against the 300s budget."
echo "If it is uncomfortably close, pin --workers or cut per-candidate cost; do NOT"
echo "rely on the dev-machine number for the constraint."
