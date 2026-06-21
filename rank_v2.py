#!/usr/bin/env python3
"""v2 challenge entrypoint — the learned (LambdaMART) ranker.

    PYTHONHASHSEED=0 python rank_v2.py --candidates ./candidates.jsonl --out ./submission.csv

If models/ltr_v2.txt exists it is used; otherwise a transparent linear fallback
runs (so the pipeline works before the model is trained). Same output contract
as rank.py: 100 rows, ranks 1..100, score non-increasing, ties by candidate_id.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

from redrob_ranker_v2.pipeline_v2 import run_ranking_v2


def main() -> None:
    ap = argparse.ArgumentParser(description="Rank candidates with the v2 learned ranker.")
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-k", type=int, default=100)
    ap.add_argument("--model", default=None, help="LightGBM model path (default models/ltr_v2.txt).")
    ap.add_argument("--max-candidates", type=int, default=None)
    args = ap.parse_args()

    start = time.time()
    result = run_ranking_v2(
        Path(args.candidates),
        Path(args.out),
        top_k=args.top_k,
        model_path=Path(args.model) if args.model else None,
        max_candidates=args.max_candidates,
    )
    elapsed = time.time() - start
    print(
        f"Wrote {len(result.rows)} rows to {args.out}. "
        f"Loaded {result.loaded_count}; pool {result.ranked_pool_count}; "
        f"model={result.model_kind}; backend={result.bm25_backend}; "
        f"honeypots_in_output={result.honeypots_in_output}; runtime {elapsed:.1f}s.",
        file=sys.stderr,
    )
    if elapsed > 240:
        print(f"WARNING: runtime {elapsed:.1f}s over 240s safety margin.", file=sys.stderr)


if __name__ == "__main__":
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("WARNING: set PYTHONHASHSEED=0 for byte-deterministic output.", file=sys.stderr)
    main()
