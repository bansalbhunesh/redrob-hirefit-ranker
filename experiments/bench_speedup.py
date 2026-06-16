"""A/B benchmark: time + output-hash a 20K rank. Run before & after an optimization to prove
byte-identity and measure the delta. Read-only."""
import sys, time, hashlib, tempfile
from pathlib import Path
sys.path.insert(0, "src")
from redrob_ranker.pipeline import run_ranking, RankerConfig


def main(n=20000, reps=2):
    out = Path(tempfile.gettempdir()) / f"bench{n}.csv"
    times = []
    h = None
    for _ in range(reps):
        t = time.time()
        run_ranking(Path("candidates.jsonl"), out,
                    RankerConfig(top_k=100, max_candidates=n, bm25_backend="bm25s"))
        times.append(time.time() - t)
        h = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
    print(f"{n//1000}K rank: best {min(times):.2f}s of {reps}  (all {[round(x,2) for x in times]})  hash={h}")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
