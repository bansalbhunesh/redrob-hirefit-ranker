"""Score golden vs hedge on the Study 3b fresh, independent judge labels."""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "src")
from redrob_ranker.eval_harness import evaluate, load_labels  # noqa: E402

LAB = Path("experiments/fresh_judge_study3b.jsonl")


def ids(text):
    return [r["candidate_id"] for r in csv.DictReader(text.splitlines())]


def main():
    hedge = ids(Path("submission.csv").read_text(encoding="utf-8"))
    golden = ids(subprocess.run(["git", "show", "fallback/golden-af8f2b32:submission.csv"],
                                capture_output=True, text=True).stdout)
    L = load_labels(LAB)
    n = len(L.tiers)
    g, h = evaluate(golden, L), evaluate(hedge, L)
    print(f"Study 3b - fresh independent judge (gpt-4.1), {n} labeled candidates (golden+hedge union)")
    print(f"{'metric':>10}{'golden':>9}{'hedge':>9}{'delta':>9}")
    for m in ("composite", "ndcg10", "ndcg50", "map", "p10"):
        gv, hv = getattr(g, m), getattr(h, m)
        print(f"{m:>10}{gv:>9.4f}{hv:>9.4f}{hv - gv:>+9.4f}")
    verdict = ("HEDGE confirmed on independent labels" if h.composite > g.composite + 1e-4
               else "GOLDEN better/tied on independent labels — reconsider"
               if g.composite > h.composite + 1e-4 else "effectively tied")
    print(f"\nverdict: {verdict}")


if __name__ == "__main__":
    main()
