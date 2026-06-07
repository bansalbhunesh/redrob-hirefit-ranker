#!/usr/bin/env python3
"""One-command challenge entrypoint.

Example:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from redrob_ranker.pipeline import RankerConfig, run_ranking


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank Redrob candidates for the released JD.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl/json/jsonl.gz")
    parser.add_argument("--out", required=True, help="Output submission CSV path")
    parser.add_argument("--top-k", type=int, default=100, help="Rows to write; challenge requires 100")
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Optional cap for smoke tests/demo runs.",
    )
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=0,
        help="Optional BM25 pool size. Default 0 scores every loaded candidate.",
    )
    parser.add_argument(
        "--bm25-backend",
        choices=["auto", "bm25s", "rank_bm25"],
        default="auto",
        help="BM25 backend. auto prefers bm25s and falls back to rank_bm25.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = RankerConfig(
        top_k=args.top_k,
        candidate_pool_size=args.candidate_pool,
        max_candidates=args.max_candidates,
        bm25_backend=args.bm25_backend,
    )
    result = run_ranking(Path(args.candidates), Path(args.out), config)
    print(
        f"Wrote {len(result.rows)} rows to {args.out}. "
        f"Loaded {result.loaded_count} candidates; ranked pool {result.ranked_pool_count}; "
        f"BM25 backend {result.bm25_backend}."
    )


if __name__ == "__main__":
    main()
