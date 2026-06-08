"""Measure ranker wall time and peak RSS without changing the official CLI."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover - local profiling helper only
    psutil = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile rank.py runtime and peak RSS.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl.")
    parser.add_argument("--out", default="submission.csv", help="Output CSV path.")
    parser.add_argument("--result-json", default="artifacts/runtime_memory.json")
    parser.add_argument("--bm25-backend", default="bm25s", choices=["auto", "bm25s", "rank_bm25"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if psutil is None:
        raise RuntimeError("psutil is required for peak RSS measurement")

    result_path = Path(args.result_json)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = result_path.with_suffix(".stdout.txt")
    stderr_path = result_path.with_suffix(".stderr.txt")

    env = os.environ.copy()
    env["PYTHONPATH"] = "src" + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [
        sys.executable,
        "rank.py",
        "--candidates",
        args.candidates,
        "--out",
        args.out,
        "--bm25-backend",
        args.bm25_backend,
    ]

    def tree_rss(proc: "psutil.Process") -> int:
        # Sum parent + worker-process RSS so the parallel path is measured honestly
        # against the 16 GB constraint (children are spawned by ProcessPoolExecutor).
        total = 0
        try:
            procs = [proc] + proc.children(recursive=True)
        except psutil.Error:
            procs = [proc]
        for p in procs:
            try:
                total += p.memory_info().rss
            except psutil.Error:
                pass
        return total

    start = time.perf_counter()
    peak_rss = 0
    with stdout_path.open("w", encoding="utf-8") as stdout_f, stderr_path.open("w", encoding="utf-8") as stderr_f:
        process = subprocess.Popen(cmd, stdout=stdout_f, stderr=stderr_f, env=env)
        ps_process = psutil.Process(process.pid)
        while process.poll() is None:
            peak_rss = max(peak_rss, tree_rss(ps_process))
            time.sleep(0.25)
        peak_rss = max(peak_rss, tree_rss(ps_process))

    elapsed = time.perf_counter() - start
    result = {
        "exit_code": process.returncode,
        "wall_seconds": round(elapsed, 1),
        "peak_rss_gb": round(peak_rss / (1024**3), 2),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "command": " ".join(cmd),
    }
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return int(process.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
