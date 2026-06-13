#!/usr/bin/env python3
"""Gate evaluation: challenger vs shipped top-100 against the three pre-registered
scoring sources (docs/ltr_challenger_gate.md criterion 1). Uses the shared harness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from redrob_ranker.eval_harness import evaluate_many, load_labels  # noqa: E402

GATE_DELTA = 0.005

SOURCES = [
    (ROOT / "artifacts" / "independent_labels_100k.jsonl", "independent"),
    (ROOT / "docs" / "llm_judge_eval_labels.jsonl", "judge1-gemini"),
    (ROOT / "docs" / "llm_judge_eval_2_labels.jsonl", "judge2-gpt41mini"),
]


def main() -> None:
    data = json.loads((ROOT / "artifacts" / "challenger_top100.json").read_text(encoding="utf-8"))
    sets = [load_labels(p, name) for p, name in SOURCES if p.exists()]

    means = {}
    for which in ("shipped", "challenger"):
        print(f"\n=== {which} top-100 ===")
        results, mean = evaluate_many(data[which], sets, unlabeled="exclude")
        for r in results:
            row = r.as_row()
            print(f"  {row['label_set']:<18} NDCG@10={row['ndcg10']:.4f} "
                  f"NDCG@50={row['ndcg50']:.4f} MAP={row['map']:.4f} "
                  f"P@10={row['p10']:.4f} composite={row['composite']:.4f} "
                  f"coverage={row['coverage']:.1%}")
        means[which] = mean
        print(f"  mean composite: {mean:.4f}")

    delta = means["challenger"] - means["shipped"]
    print(f"\noverlap: {data['overlap']}/100")
    print(f"gate criterion 1: challenger - shipped = {delta:+.4f} "
          f"(adopt requires >= +{GATE_DELTA})")
    print("GATE: " + ("PASSES criterion 1 — continue to runtime/determinism criteria"
                      if delta >= GATE_DELTA else "FAILS — shipped scorer stands"))


if __name__ == "__main__":
    main()
