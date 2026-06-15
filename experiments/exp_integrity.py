"""Experiment 3 — integrity/honeypot penalties internally.

anachronism check: technology anachronism (claiming a tech longer than it has existed).
world-consistency (impossible tenure). Applied as multiplicative demotions,
holdout-gated. Even if blind-flat, these are JD-faithful precision (the JD warns on traps).
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
sys.path.insert(0, "experiments")
from _lib import load_pool, gate_cv

# earliest mainstream year a skill could plausibly have been practiced
TECH_YEAR = {
    "rag": 2023, "retrieval augmented": 2023, "retrieval-augmented": 2023,
    "langchain": 2022, "llamaindex": 2022, "llama index": 2022, "chatgpt": 2022,
    "gpt-4": 2023, "gpt4": 2023, "prompt engineering": 2022, "stable diffusion": 2022,
    "llm": 2019, "large language model": 2019, "gpt-3": 2020, "fine-tuning llm": 2020,
    "fine tuning llm": 2020, "vector database": 2019, "vector search": 2019,
    "pinecone": 2019, "weaviate": 2020, "chroma": 2022, "sentence transformer": 2019,
    "sbert": 2019, "diffusion model": 2021,
}
NOW_Y = 2026
REF = dt.date(2026, 6, 7)


def anachronism_factor(cand):
    viol = 0
    for s in cand.get("skills", []) or []:
        name = str(s.get("name", "")).lower()
        dur = float(s.get("duration_months", 0) or 0)
        for key, yr in TECH_YEAR.items():
            if key in name:
                allowed = (NOW_Y - yr) * 12 + 12  # +1yr slack
                if dur > allowed:
                    viol += 1
                break
    return 0.8 ** viol  # 1.0 clean, 0.8/0.64/... per impossible-duration skill


def overclaim_factor(cand):
    prof = cand.get("profile", {})
    yoe = float(prof.get("years_of_experience", 0) or 0)
    starts, ends = [], []
    for j in cand.get("career_history", []) or []:
        try:
            starts.append(dt.date.fromisoformat(str(j.get("start_date"))[:10]))
        except Exception:
            pass
        ed = j.get("end_date")
        ends.append(REF if (ed in (None, "None", "") or j.get("is_current")) else _safe(ed))
    ends = [e for e in ends if e]
    if not starts or not ends:
        return 1.0
    span_yrs = (max(ends) - min(starts)).days / 365.25
    if span_yrs <= 0:
        return 1.0
    # claimed YoE materially exceeds the actual career span -> implausible
    if yoe > span_yrs + 2.0:
        return 0.7
    return 1.0


def _safe(d):
    try:
        return dt.date.fromisoformat(str(d)[:10])
    except Exception:
        return None


def main():
    recs, base_ids = load_pool()
    anach = np.array([anachronism_factor(r["cand"]) for r in recs])
    over = np.array([overclaim_factor(r["cand"]) for r in recs])
    combo = anach * over
    n_anach = int((anach < 1.0).sum())
    n_over = int((over < 1.0).sum())
    print(f"pool=3000  anachronism-flagged={n_anach}  overclaim-flagged={n_over}", flush=True)

    res = []
    res.append(gate_cv(recs, base_ids, anach, "tech_anachronism penalty", mode="mult", weights=[0.5, 1.0, 2.0]))
    res.append(gate_cv(recs, base_ids, over, "yoe_overclaim penalty", mode="mult", weights=[0.5, 1.0, 2.0]))
    res.append(gate_cv(recs, base_ids, combo, "anachronism x overclaim", mode="mult", weights=[0.5, 1.0, 2.0]))

    print("\n================ CV SUMMARY (integrity) ================")
    for r in sorted(res, key=lambda x: -x["mean"]):
        print(f"{r['name']:<28} mean {r['mean']:+.4f}  min {r['min']:+.4f}  [{r['robust']}]")
    # how many of the current top-100 would these penalties flag?
    base_set = set(base_ids)
    top_anach = sum(1 for r in recs if r["cid"] in base_set and anachronism_factor(r["cand"]) < 1.0)
    top_over = sum(1 for r in recs if r["cid"] in base_set and overclaim_factor(r["cand"]) < 1.0)
    print(f"\nIn OUR current top-100: anachronism-flagged={top_anach}, overclaim-flagged={top_over} "
          f"(if >0, these are traps we currently rank highly)")


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()
