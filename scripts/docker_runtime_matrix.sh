#!/usr/bin/env bash
# Phase 0.1: measure the official ranker in the Stage-3 reproduction environment
# (python:3.11-slim) across worst/mid-case CPU budgets, recording wall time,
# peak container memory, and output hash (must equal the golden submission).
#
# Usage: bash scripts/docker_runtime_matrix.sh
# Writes raw results to artifacts/runtime_matrix_raw.txt
set -uo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

REPO="$(cd "$(dirname "$0")/.." && { pwd -W 2>/dev/null || pwd; })"
IMAGE="redrob-hirefit-ranker"
OUT="$REPO/artifacts/runtime_matrix_raw.txt"
mkdir -p "$REPO/artifacts"
: > "$OUT"

echo "== building $IMAGE ==" | tee -a "$OUT"
docker build -t "$IMAGE" "$REPO" >/dev/null 2>&1 && echo "build ok" | tee -a "$OUT"

GOLDEN_HASH="e1a696d1f575908c8544fae294e04dcbf4edd4bad8ee5215aae2072c867493f7"

for cfg in "2 1" "2 2" "4 4"; do
  set -- $cfg; CPUS=$1; W=$2
  NAME="rmatrix_c${CPUS}w${W}"
  CSV="submission_docker_c${CPUS}w${W}.csv"
  docker rm -f "$NAME" >/dev/null 2>&1
  echo "" | tee -a "$OUT"
  echo "== --cpus=$CPUS --workers $W ==" | tee -a "$OUT"
  docker run -d --name "$NAME" --cpus="$CPUS" --memory=6g \
    -v "$REPO:/data" "$IMAGE" \
    --candidates /data/candidates.jsonl --out "/data/$CSV" \
    --bm25-backend bm25s --workers "$W" >/dev/null

  PEAK_MB=0
  while [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = "true" ]; do
    RAW=$(docker stats --no-stream --format '{{.MemUsage}}' "$NAME" 2>/dev/null | awk '{print $1}')
    case "$RAW" in
      *GiB) MB=$(echo "$RAW" | sed 's/GiB//' | awk '{printf "%d", $1*1024}');;
      *MiB) MB=$(echo "$RAW" | sed 's/MiB//' | awk '{printf "%d", $1}');;
      *) MB=0;;
    esac
    [ "${MB:-0}" -gt "$PEAK_MB" ] && PEAK_MB=$MB
    sleep 2
  done

  STARTED=$(docker inspect -f '{{.State.StartedAt}}' "$NAME")
  FINISHED=$(docker inspect -f '{{.State.FinishedAt}}' "$NAME")
  EXITCODE=$(docker inspect -f '{{.State.ExitCode}}' "$NAME")
  WALL=$(python -c "from datetime import datetime as d; import sys; p=lambda s: d.fromisoformat(s.replace('Z','+00:00')[:26]+s[-6:]) if '+' in s[10:] else d.fromisoformat(s[:26]); import re; a='$STARTED'; b='$FINISHED'; f=lambda s: d.fromisoformat(re.sub(r'(\\.\\d{6})\\d*','\\\\1',s).replace('Z','+00:00')); print(round((f(b)-f(a)).total_seconds(),1))" 2>/dev/null)
  echo "exit=$EXITCODE wall=${WALL}s peak_mem=${PEAK_MB}MB (sampled @2s)" | tee -a "$OUT"
  docker logs "$NAME" 2>&1 | grep -E "Runtime|Wrote|WARNING" | tee -a "$OUT"
  docker rm "$NAME" >/dev/null

  ACTUAL=$(sha256sum "$REPO/$CSV" | awk '{print $1}')
  if [ "$ACTUAL" = "$GOLDEN_HASH" ]; then
    echo "hash: MATCHES golden" | tee -a "$OUT"
  else
    echo "hash: MISMATCH ($ACTUAL)" | tee -a "$OUT"
  fi
  rm -f "$REPO/$CSV"
done
echo "" | tee -a "$OUT"
echo "matrix complete" | tee -a "$OUT"
