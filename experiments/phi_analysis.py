"""Study Phi -- analysis of the single-coder HN pilot. Produces the severity x action
surface, stance distribution, conditionality rate, anachronism-specific actions, and
thread-clustered + time sensitivity. NO representativeness claims; HN-only, single-coder.
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path("docs/human_opinion")


def main():
    rows = list(csv.DictReader(open(OUT / "corpus_pilot.csv", encoding="utf-8")))
    n = len(rows)
    print(f"=== Phi pilot analysis (HN-only, single-coder, n={n}) ===")

    print("\nA. stance distribution (comment-level):")
    for s, c in Counter(r["stance"] for r in rows).most_common():
        print(f"   {s:<18} {c:>2}  ({100*c/n:.0f}%)")

    print("\nB. severity x recommended-action surface:")
    sev_act = defaultdict(Counter)
    for r in rows:
        sev_act[int(r["severity"])][r["recommended_action"]] += 1
    for sev in sorted(sev_act):
        acts = ", ".join(f"{a}:{c}" for a, c in sev_act[sev].most_common())
        print(f"   severity {sev}: {acts}")

    print("\nC. conditionality rate (explicitly 'depends'/contingent):")
    cond = sum(1 for r in rows if r["conditional_reasoning"] == "yes")
    print(f"   {cond}/{n} ({100*cond/n:.0f}%)  -> low rate here = HN tends to give categorical takes")

    print("\nD. technology-tenure / skill-duration items (directly relevant to our anachronism flag):")
    for r in rows:
        if r["red_flag_type"] in ("technology_anachronism", "inflated_skill_duration"):
            print(f"   {r['item_id']} sev{r['severity']} {r['stance']} -> {r['recommended_action']}  ({r['notes'][:60]})")

    print("\nE. action when severity<=1 (minor) vs severity>=3 (material):")
    minor = Counter(r["recommended_action"] for r in rows if int(r["severity"]) <= 1)
    major = Counter(r["recommended_action"] for r in rows if int(r["severity"]) >= 3)
    print(f"   minor (sev<=1): {dict(minor)}")
    print(f"   material (sev>=3): {dict(major)}")

    print("\nF. thread-level (cluster by thread_id; conservative):")
    by_thread = defaultdict(list)
    for r in rows:
        by_thread[r["thread_id"]].append(r)
    print(f"   {n} comments span {len(by_thread)} threads (max {max(len(v) for v in by_thread.values())}/thread)")
    th_stance = Counter()
    for t, rs in by_thread.items():
        th_stance[Counter(r["stance"] for r in rs).most_common(1)[0][0]] += 1
    print(f"   thread-majority stance: {dict(th_stance)}")

    print("\nG. sensitivity / time strata:")
    strata = defaultdict(Counter)
    for r in rows:
        y = int(r["source_date"][:4]); era = "pre-2023" if y < 2023 else "2023+"
        strata[era][r["stance"]] += 1
    for era, c in strata.items():
        print(f"   {era}: {dict(c)}")

    print("\nH. negative/minority cases (against the dominant capability/verify lean):")
    for r in rows:
        if r["stance"] in ("INTEGRITY_ABSOLUTE", "INTEGRITY_HIGH") and int(r["severity"]) <= 1:
            print(f"   {r['item_id']}: strict on minor -> {r['notes'][:70]}")

    print("\nLIMITS: HN stratum only (engineer/founder-skewed, NOT recruiters); single coder "
          "(no IRR); n=19 pilot; NOT representative; upvotes excluded by design.")


if __name__ == "__main__":
    main()
