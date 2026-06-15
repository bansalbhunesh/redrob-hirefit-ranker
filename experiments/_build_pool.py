"""Cache the top-3000 hand-ranked pool once, so feature experiments iterate fast.
Pickle is NOT committed (contains candidate data). Run from repo root."""
import pickle
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")


def main():
    from redrob_ranker.pipeline import RankerConfig, run_ranking
    from redrob_ranker.text import candidate_text

    N = 3000
    with tempfile.TemporaryDirectory() as tmp:
        res = run_ranking(Path("candidates.jsonl"), Path(tmp) / "o.csv",
                          RankerConfig(top_k=100, candidate_pool_size=0, max_candidates=None, bm25_backend="auto"))
    recs = []
    for cand, feat, score in (res.raw_ranked or [])[:N]:
        recs.append({
            "cid": cand["candidate_id"],
            "hand": float(score),
            "values": dict(feat.values),
            "role_fit": float(feat.role_fit), "ai_depth": float(feat.ai_depth),
            "production_evidence": float(feat.production_evidence),
            "behavior": float(feat.behavior), "logistics": float(feat.logistics),
            "honeypot_mult": float(feat.honeypot_multiplier),
            "disq_mult": float(feat.disqualifier_multiplier),
            "flags": list(feat.flags or []),
            "text": candidate_text(cand),
            "cand": cand,
        })
    base_ids = [r["candidate_id"] for r in res.rows]
    Path("experiments").mkdir(exist_ok=True)
    with open("experiments/_pool.pkl", "wb") as f:
        pickle.dump({"recs": recs, "base_ids": base_ids}, f)
    print(f"cached {len(recs)} pool records; base top100 = {len(base_ids)}")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
