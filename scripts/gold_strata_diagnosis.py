"""Where do the planted-gold-strata profiles rank, and why are some excluded?"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.features import compute_features, final_score  # noqa: E402
from redrob_ranker.io import iter_candidates  # noqa: E402
from redrob_ranker.retrieval import retrieve_pool  # noqa: E402

GOLD_TEMPLATES = ("senior ai engineer with # years", "senior engineer who has spent the")


def main() -> None:
    feats = {}
    for line in (ROOT / "artifacts" / "forensics_features.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["summary_template"] in GOLD_TEMPLATES:
            feats[r["candidate_id"]] = r

    print(f"gold-strata profiles: {len(feats)}")

    top100 = {r["candidate_id"]: int(r["rank"])
              for r in csv.DictReader((ROOT / "submission.csv").open(encoding="utf-8-sig"))}
    j1 = {json.loads(l)["candidate_id"]: json.loads(l)
          for l in (ROOT / "docs" / "llm_judge_eval_labels.jsonl").open(encoding="utf-8")}

    # Re-rank the full pool serially to find global ranks of gold profiles.
    print("loading + ranking 100K (serial)...", file=sys.stderr)
    cands = list(iter_candidates(ROOT / "candidates.jsonl"))
    scores, _ = retrieve_pool(cands, 0, backend="bm25s")
    ranked = []
    for i, c in enumerate(cands):
        f = compute_features(c)
        s = final_score(f, scores.get(i, 0.0))
        ranked.append((c["candidate_id"], s, f))
    ranked.sort(key=lambda t: (-t[1], t[0]))
    pos = {cid: i + 1 for i, (cid, _, _) in enumerate(ranked)}
    fobj = {cid: f for cid, _, f in ranked}

    print("\ncid              rank  judge1  behav  honey  disq  flags / key signals")
    for cid, fr in sorted(feats.items(), key=lambda kv: pos.get(kv[0], 10**9)):
        f = fobj[cid]
        in100 = "IN " if cid in top100 else "OUT"
        tier = j1.get(cid, {}).get("tier", "?")
        print(f"{cid} {in100} #{pos[cid]:6d} t={tier}  b={f.behavioral_multiplier:.2f} "
              f"h={f.honeypot_multiplier:.2f} d={f.disqualifier_multiplier:.2f} "
              f"rr={fr['response_rate']:.2f} otw={int(fr['open_to_work'])} "
              f"flags={','.join(f.flags) or '-'}")


if __name__ == "__main__":
    main()
