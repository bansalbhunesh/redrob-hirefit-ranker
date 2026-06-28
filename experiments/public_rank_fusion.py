"""Research-only weighted reciprocal-rank fusion for public submissions.

This tool is deliberately outside the production ranking path.  It accepts
local CSVs explicitly, performs no network access, and is useful for measuring
how much complementary signal exists in public rankings.  A result from this
tool is an upper bound, not a competition-ready artifact: it directly depends
on other participants' outputs.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from redrob_ranker.eval_harness import load_submission


def weighted_rrf(
    base: list[str],
    channels: list[tuple[list[str], float]],
    *,
    base_weight: float = 1.0,
    lock: int = 20,
    rrf_k: int = 60,
) -> list[str]:
    """Fuse top-100 orders while preserving a trusted prefix from ``base``."""

    if not 0 <= lock <= len(base):
        raise ValueError("lock must be within the base ranking")
    if rrf_k < 1:
        raise ValueError("rrf_k must be positive")

    scores: dict[str, float] = {}
    for ids, weight in [(base, base_weight), *channels]:
        if weight < 0:
            raise ValueError("channel weights must be non-negative")
        for rank, candidate_id in enumerate(ids, start=1):
            scores[candidate_id] = scores.get(candidate_id, 0.0) + weight / (rrf_k + rank)

    locked = list(base[:lock])
    seen = set(locked)
    fused = locked + [
        candidate_id
        for candidate_id in sorted(scores, key=lambda cid: (-scores[cid], cid))
        if candidate_id not in seen
    ]
    seen = set(fused)
    fused.extend(candidate_id for candidate_id in base if candidate_id not in seen)
    return fused[: len(base)]


def _channel(raw: str) -> tuple[Path, float]:
    try:
        path, weight = raw.rsplit(":", 1)
        return Path(path), float(weight)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("channel must be PATH:WEIGHT") from exc


def _write(ids: list[str], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, candidate_id in enumerate(ids, start=1):
            writer.writerow(
                [
                    candidate_id,
                    rank,
                    f"{1.0 - rank * 0.000001:.6f}",
                    "research-only public rank fusion; not a production submission",
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--channel", action="append", type=_channel, default=[])
    parser.add_argument("--base-weight", type=float, default=1.0)
    parser.add_argument("--lock", type=int, default=20)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    base = load_submission(args.base)
    channels = [(load_submission(path), weight) for path, weight in args.channel]
    fused = weighted_rrf(
        base,
        channels,
        base_weight=args.base_weight,
        lock=args.lock,
        rrf_k=args.rrf_k,
    )
    _write(fused, args.out)
    print(f"wrote {len(fused)} rows to {args.out}")


if __name__ == "__main__":
    main()
