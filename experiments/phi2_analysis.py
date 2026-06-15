"""Phi-2 two-axis analysis + sensitivity (single-coder; HN+SE; NOT representative)."""
import csv
from collections import Counter, defaultdict
from pathlib import Path
OUT = Path("docs/human_opinion")
def main():
    rows=list(csv.DictReader(open(OUT/"corpus_phi2.csv",encoding="utf-8")))
    n=len(rows); print(f"=== Phi-2 (n={n}; strata {dict(Counter(r['stratum'] for r in rows))}) ===")
    print("\nEvidence status x Hiring action surface:")
    grid=defaultdict(Counter)
    for r in rows: grid[r["evidence_status"]][r["hiring_action"]]+=1
    order=["CLEAR","AMBIGUOUS","PROBABLE_CONTRADICTION","CONFIRMED_CONTRADICTION"]
    for ev in order:
        if grid[ev]: print(f"  {ev:<24} "+", ".join(f"{a}:{c}" for a,c in grid[ev].most_common()))
    print("\nBy stratum (hiring_action):")
    for st in sorted(set(r["stratum"] for r in rows)):
        c=Counter(r["hiring_action"] for r in rows if r["stratum"]==st)
        print(f"  {st:<14} {dict(c)}")
    print("\nBy severity -> dominant action:")
    sev=defaultdict(Counter)
    for r in rows: sev[int(r["severity"])][r["hiring_action"]]+=1
    for s in sorted(sev): print(f"  sev{s}: {dict(sev[s])}")
    print("\nBy period:")
    per=defaultdict(Counter)
    for r in rows:
        y=int(r["source_date"][:4]); per["pre-2023" if y<2023 else "2023+"][r["hiring_action"]]+=1
    for p,c in per.items(): print(f"  {p}: {dict(c)}")
    print("\nBy firsthand:")
    fh=defaultdict(Counter)
    for r in rows: fh[r["firsthand_or_secondhand"]][r["hiring_action"]]+=1
    for k,c in fh.items(): print(f"  {k}: {dict(c)}")
    print("\nThread-level: %d units / %d threads (max %d/thread)"%(n,len(set(r['thread_id'] for r in rows)),
          max(Counter(r['thread_id'] for r in rows).values())))
    print("\nAnachronism-decision cell (the decision-critical, NOT-saturated category):")
    for r in rows:
        if r["red_flag_type"] in ("technology_anachronism","inflated_skill_duration"):
            print(f"  {r['item_id']} {r['stratum'][:4]} sev{r['severity']} {r['evidence_status']}->{r['hiring_action']}  {r['notes'][:55]}")
    print("\nLIMITS: single coder (no IRR; run phi2_kappa.py with a real 2nd coder); HN+SE only "
          "(NO recruiter-Reddit/India-Reddit); anachronism cell n=5 (NOT saturated); not representative.")
if __name__=="__main__": main()
