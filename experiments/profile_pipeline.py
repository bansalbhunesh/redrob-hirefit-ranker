"""Per-stage wall-clock profile of the production pipeline (read-only; answers 'why slow')."""
import sys, time
from pathlib import Path
sys.path.insert(0, "src")
from redrob_ranker.io import iter_candidates
from redrob_ranker.retrieval import bm25_scores, candidate_text
from redrob_ranker.pipeline import run_ranking, RankerConfig
import tempfile


def main(n=None):
    lab = "FULL-100K" if n is None else f"{n//1000}K"
    t = time.time()
    cands = list(iter_candidates(Path("candidates.jsonl"), max_candidates=n))
    t_load = time.time() - t
    t = time.time()
    texts = [candidate_text(c) for c in cands]
    t_text = time.time() - t
    t = time.time()
    bm25_scores(texts)
    t_bm25 = time.time() - t
    t = time.time()
    res = run_ranking(Path("candidates.jsonl"), Path(tempfile.gettempdir()) / "prof.csv",
                      RankerConfig(top_k=100, max_candidates=n, bm25_backend="bm25s"))
    t_total = time.time() - t
    print(f"[{lab}] candidates={len(cands)}")
    print(f"  load jsonl           {t_load:6.2f}s")
    print(f"  build candidate_text {t_text:6.2f}s")
    print(f"  BM25 (tokenize+index+score) {t_bm25:6.2f}s   <-- dominant stage")
    print(f"  full run_ranking (load+bm25+features+sort+write) {t_total:6.2f}s")
    print(f"  => features+score+sort+write ~= {t_total - t_load - t_bm25:6.2f}s")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
    main(n)
