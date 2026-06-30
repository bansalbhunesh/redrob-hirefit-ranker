#!/usr/bin/env python3
"""One-command challenge entrypoint.

Example:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Pin BLAS/threadpool thread counts to 1 BEFORE numpy/bm25s are imported so the
# BM25 float-reduction order (and therefore the generated submission.csv) is
# byte-identical regardless of the host's CPU/thread count. Verified: identical
# output at --cpus=2 and --cpus=4 in the pinned Docker image. setdefault keeps
# any explicit override a caller already set.
for _thread_var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

from redrob_ranker.pipeline import (  # noqa: E402
    CHAMPION_SCORING_PROFILE,
    RankerConfig,
    run_ranking,
)

RELEASE_SHA256 = "8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062"
RELEASE_CANDIDATE_COUNT = 100_000
RELEASE_HONEYPOT_COUNT = 53


def _ensure_deterministic_hash_seed() -> None:
    """Warns if PYTHONHASHSEED is not set to 0.
    
    bm25s assigns vocabulary term-IDs via hash-ordered structures; a random hash
    seed shifts float-accumulation order and can flip one normalized score's 6th
    decimal (rank order is unaffected). Pinning the seed makes the CSV bit-identical
    run-to-run.
    """
    if os.environ.get("PYTHONHASHSEED") != "0":
        print(
            "WARNING: PYTHONHASHSEED is not set to 0. For byte-deterministic output, run:\n"
            "    set PYTHONHASHSEED=0 && python rank.py ...",
            file=sys.stderr
        )


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
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Feature-scoring worker processes. 0=auto (up to 8 cores for the full "
        "pool), 1=serial. Output is identical regardless of worker count.",
    )
    parser.add_argument(
        "--jd",
        default=None,
        help="Optional plaintext JD file. Compiled into a deterministic scoring "
        "program (skill groups, title weights, locations, experience band). "
        "Omitted = the bundled challenge JD; that path is byte-identical to "
        "the historical pipeline.",
    )
    parser.add_argument(
        "--use-embeddings",
        action="store_true",
        help="EXPERIMENTAL: blend a model2vec/potion dense-retrieval feature (needs "
        "model2vec installed; off by default and not part of the official path).",
    )
    parser.add_argument(
        "--embed-model",
        default="minishlab/potion-retrieval-32M",
        help="Static embedding model for --use-embeddings.",
    )
    parser.add_argument(
        "--scoring-profile",
        choices=[
            "main",
            "top23-clean",
            "universal-v2",
            "loss-aggregate-v3",
            "dominant-v4",
            "frontier-v5",
        ],
        default=None,
        help="Scoring profile. Omit for main, or use --release to force the "
        "verified frontier-v5 champion. main preserves the historical scorer; top23-clean "
        "universal-v2, loss-aggregate-v3, dominant-v4, and frontier-v5 enable clean-room "
        "challengers for the bundled JD.",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Fail-closed official 100K reproduction: force frontier-v5 + bm25s, "
        "reject experimental/truncated settings, verify counts, integrity, and "
        "the golden SHA-256 before atomically publishing --out.",
    )
    parser.add_argument(
        "--profile-memory",
        action="store_true",
        help="Print Python tracemalloc peak memory for local profiling.",
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=0,
        help="Print rich ASCII output for the top N candidates.",
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_profile(args: argparse.Namespace) -> str:
    """Validate release-only invariants and return the forced champion profile."""

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise SystemExit("--release requires PYTHONHASHSEED=0")
    if args.scoring_profile not in {None, CHAMPION_SCORING_PROFILE}:
        raise SystemExit(
            f"--release only permits --scoring-profile {CHAMPION_SCORING_PROFILE}"
        )
    incompatible = []
    if args.top_k != 100:
        incompatible.append("--top-k must be 100")
    if args.max_candidates is not None:
        incompatible.append("--max-candidates is forbidden")
    if args.candidate_pool != 0:
        incompatible.append("--candidate-pool must be 0")
    if args.jd is not None:
        incompatible.append("--jd is forbidden")
    if args.use_embeddings:
        incompatible.append("--use-embeddings is forbidden")
    if args.bm25_backend == "rank_bm25":
        incompatible.append("--bm25-backend rank_bm25 is forbidden")
    if incompatible:
        raise SystemExit("Invalid --release configuration: " + "; ".join(incompatible))
    return CHAMPION_SCORING_PROFILE


def _verify_release(result, artifact: Path) -> None:
    """Fail closed unless the complete official artifact was reproduced."""

    errors = []
    if result.loaded_count != RELEASE_CANDIDATE_COUNT:
        errors.append(
            f"loaded {result.loaded_count}, expected {RELEASE_CANDIDATE_COUNT} candidates"
        )
    if result.ranked_pool_count != RELEASE_CANDIDATE_COUNT:
        errors.append(
            f"ranked {result.ranked_pool_count}, expected {RELEASE_CANDIDATE_COUNT} candidates"
        )
    if len(result.rows) != 100:
        errors.append(f"wrote {len(result.rows)}, expected 100 rows")
    if result.honeypots_detected != RELEASE_HONEYPOT_COUNT:
        errors.append(
            f"detected {result.honeypots_detected}, expected {RELEASE_HONEYPOT_COUNT} honeypots"
        )
    if result.honeypots_in_output != 0:
        errors.append(f"emitted {result.honeypots_in_output} honeypots")
    digest = _sha256(artifact)
    if digest != RELEASE_SHA256:
        errors.append(f"SHA-256 {digest}, expected {RELEASE_SHA256}")
    if errors:
        raise RuntimeError("Release verification failed: " + "; ".join(errors))

def print_top_n(result, n: int, elapsed: float, peak_mb: float | None) -> None:
    if not result.raw_ranked or n <= 0:
        return
    print("\n" + "=" * 80)
    print("REDROB HIREFIT RANKER - TOP CANDIDATES")
    print("=" * 80)
    print(f"Pipeline: {result.loaded_count:,} candidates -> {result.ranked_pool_count:,} ranked")
    memory_str = f" | Memory: {peak_mb:.0f}MB" if peak_mb is not None else ""
    print(f"Runtime:  {elapsed:.1f}s{memory_str} | Backend: {result.bm25_backend}")
    print("-" * 80)

    max_score = result.raw_ranked[0][2] if result.raw_ranked else 0.0

    for i, (candidate, features, score) in enumerate(result.raw_ranked[:n]):
        rank = i + 1
        cid = candidate.get("candidate_id", "UNKNOWN")
        p = candidate.get("profile", {})
        
        badge = "[ 1 ]" if rank == 1 else "[ 2 ]" if rank == 2 else "[ 3 ]" if rank == 3 else f"[ {rank} ]"
        
        normalized_score = score / max_score if max_score > 0 else 0.0
        bar_len = int(normalized_score * 40)
        bar = "#" * bar_len + "-" * (40 - bar_len)
        
        print(f"\n{badge} {cid} | Score: {normalized_score:.4f} [{bar}]")
        print(f"   {p.get('current_title', 'No Title')} @ {p.get('current_company', 'No Company')} | {p.get('years_of_experience', 0):.1f}Y | {p.get('location', 'No Location')}")
        
        # Get reasoning from rows
        reasoning = result.rows[i]["reasoning"] if i < len(result.rows) else ""
        print(f"   [REASON] {reasoning}")
        
        # Feature breakdown
        top_dims = sorted(features.values.items(), key=lambda x: -x[1])[:3]
        dim_str = " | ".join([f"{k.replace('_',' ')}: {v:.2f}" for k, v in top_dims])
        print(f"   [FEATURES] {dim_str}")
        
        # Honeypot / behavioral flags
        if features.honeypot_multiplier <= 0.0:
            print("   [HONEYPOT] DETECTED")
        elif features.flags:
            print(f"   [FLAGS] {', '.join(features.flags)}")
        else:
            signals = candidate.get("redrob_signals", {})
            otw = signals.get("open_to_work_flag", False)
            rr = signals.get("recruiter_response_rate", 0.0)
            notice = signals.get("notice_period_days", "unknown")
            print(f"   [SIGNALS] OTW={otw} | RR={rr:.0%} | Notice={notice}d")
    
    print("\n" + "=" * 80)



def main() -> None:
    args = parse_args()
    scoring_profile = _release_profile(args) if args.release else (args.scoring_profile or "main")
    if args.release:
        # Verify the signed champion model before spending minutes scoring 100K rows.
        from redrob_ranker.loss_aggregate import _artifact

        _artifact()
    if args.profile_memory and (args.max_candidates is None or args.max_candidates > 5000):
        raise SystemExit(
            "--profile-memory uses tracemalloc and is intentionally limited to "
            "--max-candidates <= 5000. Do not use it for the official full run."
        )
    compiled_jd = None
    if args.jd:
        from redrob_ranker.jd_compiler import DEFAULT_COMPILED_JD, compile_jd_file

        compiled_jd = compile_jd_file(args.jd)
        if compiled_jd == DEFAULT_COMPILED_JD:
            print(f"Compiled {args.jd}: matches the bundled challenge configuration.",
                  file=sys.stderr)
        else:
            groups = [g for g, _ in compiled_jd.must_have_skills]
            print(f"Compiled {args.jd}: groups={groups} "
                  f"yoe={compiled_jd.yoe_band_lo:.0f}-{compiled_jd.yoe_band_hi:.0f} "
                  f"locations={len(compiled_jd.preferred_locations)}",
                  file=sys.stderr)
    config = RankerConfig(
        top_k=args.top_k,
        candidate_pool_size=args.candidate_pool,
        max_candidates=args.max_candidates,
        bm25_backend="bm25s" if args.release else args.bm25_backend,
        workers=args.workers,
        use_embeddings=args.use_embeddings,
        embed_model=args.embed_model,
        scoring_profile=scoring_profile,
        jd=compiled_jd,
    )
    if args.profile_memory:
        tracemalloc.start()
    start_time = time.time()
    output = Path(args.out)
    if Path(args.candidates).resolve() == output.resolve():
        raise SystemExit("--candidates and --out must be different paths")
    temporary_output = None
    run_output = output
    if args.release:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_path = tempfile.mkstemp(
            dir=output.parent,
            prefix=f".{output.name}.release.",
            suffix=".tmp",
        )
        os.close(descriptor)
        temporary_output = Path(raw_path)
        run_output = temporary_output
    try:
        result = run_ranking(Path(args.candidates), run_output, config)
        if args.release:
            _verify_release(result, run_output)
            os.replace(run_output, output)
            temporary_output = None
            print(
                f"Release verified: {CHAMPION_SCORING_PROFILE}, "
                f"SHA-256 {RELEASE_SHA256}.",
                file=sys.stderr,
            )
    finally:
        if temporary_output is not None:
            temporary_output.unlink(missing_ok=True)
    elapsed = time.time() - start_time
    print(f"Pipeline completed in {elapsed:.1f}s", file=sys.stderr)
    if elapsed > 240:
        print(
            f"WARNING: Runtime {elapsed:.1f}s exceeds 240s safety margin (300s limit).",
            file=sys.stderr,
        )
    peak_mb = None
    if args.profile_memory:
        peak_mb = tracemalloc.get_traced_memory()[1] / 1024 / 1024
        tracemalloc.stop()
    print(
        f"Wrote {len(result.rows)} rows to {output}. "
        f"Loaded {result.loaded_count} candidates; ranked pool {result.ranked_pool_count}; "
        f"BM25 backend {result.bm25_backend}. "
        f"Runtime {elapsed:.1f}s. "
        f"Honeypots detected {result.honeypots_detected}; "
        f"honeypots in output {result.honeypots_in_output}."
    )
    if peak_mb is not None:
        print(f"Peak traced Python memory: {peak_mb:.1f} MB.")
    if args.show_top > 0:
        print_top_n(result, args.show_top, elapsed, peak_mb)


if __name__ == "__main__":
    _ensure_deterministic_hash_seed()
    main()
