import cProfile, pstats, io, sys, tempfile
from pathlib import Path
sys.path.insert(0, "src")
def main():
    from redrob_ranker.pipeline import RankerConfig, run_ranking
    with tempfile.TemporaryDirectory() as tmp:
        pr = cProfile.Profile(); pr.enable()
        run_ranking(Path("candidates.jsonl"), Path(tmp)/"o.csv",
                    RankerConfig(top_k=100, candidate_pool_size=0, max_candidates=None, bm25_backend="auto"))
        pr.disable()
    s = io.StringIO(); ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(25); print(s.getvalue())
    s2 = io.StringIO(); pstats.Stats(pr, stream=s2).sort_stats("tottime").print_stats(20)
    print("==== BY TOTTIME ===="); print(s2.getvalue())
if __name__ == "__main__":
    import multiprocessing as mp; mp.freeze_support(); main()
