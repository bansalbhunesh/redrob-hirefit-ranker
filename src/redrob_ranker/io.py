"""Input/output helpers for challenge candidate files and CSV submissions."""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
from typing import Iterable, Iterator

try:
    import orjson
except ImportError:  # pragma: no cover - stdlib fallback
    orjson = None


def _loads(line: str | bytes) -> dict:
    if orjson is not None:
        return orjson.loads(line)
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    return json.loads(line)


def iter_candidates(path: Path, max_candidates: int | None = None) -> Iterator[dict]:
    """Yield candidates from JSONL, JSONL.GZ, or pretty JSON sample files."""

    count = 0
    if path.suffix == ".gz":
        opener = lambda p: gzip.open(p, "rb")  # noqa: E731
        with opener(path) as f:
            for raw in f:
                if raw.strip():
                    yield _loads(raw)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return
        return

    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            yield item
            count += 1
            if max_candidates and count >= max_candidates:
                return
        return

    with path.open("rb") as f:
        for raw in f:
            if raw.strip():
                yield _loads(raw)
                count += 1
                if max_candidates and count >= max_candidates:
                    return


def write_submission(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

