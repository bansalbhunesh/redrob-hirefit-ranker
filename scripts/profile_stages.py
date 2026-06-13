"""Per-stage wall-time breakdown of the ranking pipeline (dev profiling only).

Replicates run_ranking()'s serial path stage by stage so each phase can be
timed independently. NOT part of the official path -- rank.py is untouched.

Usage:
    set PYTHONHASHSEED=0
    python scripts/profile_stages.py --candidates candidates.jsonl [--max N]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import psutil
except ImportError:
    psutil = None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default=str(ROOT / "candidates.jsonl"))
    parser.add_argument("--max", type=int, default=None)
    parser.add_argument("--out", default=str(ROOT / "outputs" / "stage_profile.csv"))
    args = parser.parse_args()

    from redrob_ranker import pipeline as pl
    from redrob_ranker.io import iter_candidates, write_submission
    from redrob_ranker.retrieval import retrieve_pool
    from redrob_ranker.validation import validate_rows

    stages: dict[str, float] = {}
    t_all = time.perf_counter()

    t = time.perf_counter()
    candidates = list(iter_candidates(Path(args.candidates), max_candidates=args.max))
    stages["load_parse"] = time.perf_counter() - t

    t = time.perf_counter()
    retrieval_scores, backend = retrieve_pool(candidates, 0, backend="bm25s")
    stages["bm25_total(text+tokenize+index+query+norm)"] = time.perf_counter() - t

    t = time.perf_counter()
    pl._WORKER_JD = None
    ranked = []
    for idx in range(len(candidates)):
        features, score = pl._score_one((candidates[idx], retrieval_scores.get(idx, 0.0), None))
        ranked.append((candidates[idx], features, score))
    stages["compute_features+score (serial)"] = time.perf_counter() - t

    t = time.perf_counter()
    ranked.sort(key=lambda item: (-item[2], item[0]["candidate_id"]))
    stages["sort"] = time.perf_counter() - t

    t = time.perf_counter()
    rows = pl.rows_from_ranked(ranked, 100)
    stages["reasoning+rows (top-100)"] = time.perf_counter() - t

    t = time.perf_counter()
    errors = validate_rows(rows, expected=min(100, len(rows)))
    if errors:
        raise RuntimeError(f"invalid generated rows: {errors}")
    write_submission(Path(args.out), rows)
    stages["validate+csv_write"] = time.perf_counter() - t

    stages["TOTAL"] = time.perf_counter() - t_all

    rss_gb = None
    if psutil is not None:
        rss_gb = psutil.Process().memory_info().rss / (1024 ** 3)

    print(json.dumps({
        "n_candidates": len(candidates),
        "backend": backend,
        "stages_seconds": {k: round(v, 2) for k, v in stages.items()},
        "rss_gb_at_end": round(rss_gb, 2) if rss_gb is not None else None,
    }, indent=2))


if __name__ == "__main__":
    main()
