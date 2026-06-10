#!/usr/bin/env python3
"""Inter-judge agreement between judge #1 (gemini-2.5-flash, committed) and
judge #2 (second family, artifacts/llm_labels_judge2.jsonl), plus the ranker's
composite under judge #2. Dev-only."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

j1 = {json.loads(l)["candidate_id"]: int(json.loads(l)["tier"])
      for l in (ROOT / "docs" / "llm_judge_eval_labels.jsonl").open(encoding="utf-8")}
j2 = {json.loads(l)["candidate_id"]: int(json.loads(l)["tier"])
      for l in (ROOT / "artifacts" / "llm_labels_judge2.jsonl").open(encoding="utf-8")}

common = sorted(set(j1) & set(j2))
n = len(common)
a = [j1[c] for c in common]
b = [j2[c] for c in common]

exact = sum(1 for x, y in zip(a, b) if x == y) / n
within1 = sum(1 for x, y in zip(a, b) if abs(x - y) <= 1) / n

mean_a, mean_b = sum(a) / n, sum(b) / n
cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b)) / n
var_a = sum((x - mean_a) ** 2 for x in a) / n
var_b = sum((y - mean_b) ** 2 for y in b) / n
pearson = cov / (var_a * var_b) ** 0.5

# Quadratic-weighted kappa (standard for ordinal raters).
cats = list(range(6))
obs = [[0.0] * 6 for _ in range(6)]
for x, y in zip(a, b):
    obs[x][y] += 1
ra = Counter(a)
rb = Counter(b)
num = den = 0.0
for i in cats:
    for j in cats:
        w = (i - j) ** 2 / 25.0
        e = ra[i] * rb[j] / n
        num += w * obs[i][j]
        den += w * e
qwk = 1 - num / den if den else float("nan")

print(f"common ids: {n}")
print(f"exact tier agreement : {exact:.3f}")
print(f"within-1 agreement   : {within1:.3f}")
print(f"pearson r            : {pearson:.3f}")
print(f"quadratic kappa      : {qwk:.3f}")
print(f"mean tier j1={mean_a:.2f} j2={mean_b:.2f}")

# Top-10 comparison on the shipped submission.
import csv  # noqa: E402

rows = sorted(csv.DictReader((ROOT / "submission.csv").open(encoding="utf-8-sig")),
              key=lambda r: int(r["rank"]))
t10 = [r["candidate_id"] for r in rows[:10]]
print("\ntop-10 tiers  j1:", [j1.get(c, "?") for c in t10])
print("top-10 tiers  j2:", [j2.get(c, "?") for c in t10])

print("\ncomposite under judge #2 (shared harness):")
subprocess.run([sys.executable, str(ROOT / "scripts" / "evaluate_independent.py"),
                "--submission", str(ROOT / "submission.csv"),
                "--labels", str(ROOT / "artifacts" / "llm_labels_judge2.jsonl"),
                "--label-source", "llm-judge-2"], check=False)
