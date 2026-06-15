"""Does the competitors' blind-proxy LEAD come from a superior technique, or from
promoting the high-tenure / anachronism candidates our integrity guard demotes?

For each submission ranked at/around ours (extracted disk-safely by
_competitor_extract.py), plus our golden and our fusion-raw, compute:
  - blind composite on the 100K arbiter
  - anachronism exposure (impossible-tenure candidates in top-100)
  - mean blind tier of picks
Then correlate exposure vs composite. If higher exposure => higher composite, the
'lead' is the proxy-inflation lever (the same one fusion-raw uses), not a genuine
technique -- and it is matchable instantly / suspect under (A).
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from anachronism import is_anachronistic  # noqa: E402
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402

CX = Path("C:/Users/bhune/_cx/competitor_top100.json")
GOLDEN = Path("submission.csv")
FUSION = Path("experiments/fusion_raw_submission.csv")
LABELS = Path("artifacts/h2_availblind_labels.jsonl")


def read_ids(p):
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))
    km = {(k or "").strip().lower(): k for k in rows[0].keys()}
    cid, rk = km.get("candidate_id"), km.get("rank")
    if rk:
        rows.sort(key=lambda r: int(float(r.get(rk) or 1e9)))
    return [(r.get(cid) or "").strip() for r in rows][:100]


def main():
    rankings = {}
    comp = json.load(open(CX))
    # de-name in output: label competitors C1..Cn by descending prior blind score order in the file
    for i, (repo, ids) in enumerate(comp.items(), 1):
        rankings[f"C{i}"] = ids
    rankings["GOLDEN(us)"] = read_ids(GOLDEN)
    if FUSION.exists():
        rankings["fusion-raw"] = read_ids(FUSION)

    union = {c for ids in rankings.values() for c in ids}
    print(f"loading candidate records for {len(union)} unique top-100 cids...", flush=True)
    cand_by = {}
    for cand in iter_candidates(Path("candidates.jsonl")):
        cid = cand.get("candidate_id")
        if cid in union:
            cand_by[cid] = cand
            if len(cand_by) == len(union):
                break

    anach = {c for c in union if c in cand_by and is_anachronistic(cand_by[c])}
    labels = load_labels(LABELS)
    print(f"\n{'ranking':<14}{'composite':>11}{'anachron/100':>14}{'mean_tier':>11}")
    rows = []
    for name, ids in rankings.items():
        ev = evaluate(ids, labels)
        exp = sum(1 for c in ids if c in anach)
        mt = np.mean([labels.tiers.get(c, 0.0) for c in ids])
        rows.append((name, ev.composite, exp, mt))
        print(f"{name:<14}{ev.composite:>11.4f}{exp:>14d}{mt:>11.2f}")

    comps = np.array([r[1] for r in rows])
    exps = np.array([r[3] for r in rows], dtype=float)  # use mean_tier? no, exposure
    exps = np.array([r[2] for r in rows], dtype=float)
    if len(rows) > 2:
        r = np.corrcoef(exps, comps)[0, 1]
        print(f"\ncorr(anachronism exposure, blind composite) across {len(rows)} submissions: {r:+.3f}")
    print("-> if strongly positive, the blind 'lead' tracks honeypot exposure, not technique.")


if __name__ == "__main__":
    main()
