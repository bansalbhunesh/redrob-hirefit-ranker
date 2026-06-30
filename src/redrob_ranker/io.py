"""Input/output helpers for challenge candidate files and CSV submissions."""

from __future__ import annotations

import csv
import gzip
import json
import os
import tempfile
from pathlib import Path
from typing import Iterable, Iterator

try:
    import orjson
except ImportError:  # pragma: no cover - stdlib fallback
    orjson = None


# Docker Desktop bind mounts make small host<->VM reads disproportionately
# expensive. A large userspace buffer turns the 487 MB JSONL input into dozens
# of filesystem reads instead of tens of thousands, with no parsing changes.
JSONL_READ_BUFFER_BYTES = 8 * 1024 * 1024


def _loads(line: str | bytes) -> dict:
    if isinstance(line, bytes) and line.startswith(b"\xef\xbb\xbf"):
        line = line[3:]
    elif isinstance(line, str) and line.startswith("\ufeff"):
        line = line[1:]
    if orjson is not None:
        return orjson.loads(line)
    if isinstance(line, bytes):
        line = line.decode("utf-8-sig")
    return json.loads(line)


def iter_candidates(path: Path, max_candidates: int | None = None) -> Iterator[dict]:
    """Yield candidates from JSONL, JSONL.GZ, or pretty JSON sample files."""

    count = 0
    if path.suffix == ".gz":
        opener = lambda p: gzip.open(p, "rb")  # noqa: E731
        with opener(path) as f:
            for raw in f:
                if raw.strip():
                    item = _loads(raw)
                    if not item.get("candidate_id"):
                        item["candidate_id"] = f"UNKNOWN_ROW_{count}"
                    yield item
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return
        return

    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in data:
            if not item.get("candidate_id"):
                item["candidate_id"] = f"UNKNOWN_ROW_{count}"
            yield item
            count += 1
            if max_candidates and count >= max_candidates:
                return
        return

    with path.open("rb", buffering=JSONL_READ_BUFFER_BYTES) as f:
        for raw in f:
            if raw.strip():
                item = _loads(raw)
                if not item.get("candidate_id"):
                    item["candidate_id"] = f"UNKNOWN_ROW_{count}"
                yield item
                count += 1
                if max_candidates and count >= max_candidates:
                    return


def write_submission(path: Path, rows: Iterable[dict]) -> None:
    """Atomically replace a submission so failures never leave a partial CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["candidate_id", "rank", "score", "reasoning"],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
