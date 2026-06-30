# Multi-Hypothesis Robustness — How Over-Fit Is the Ranking?

We do not have the hidden human labels the prize is scored on. We **do** have nine independent
proxies for them, spanning three different *kinds* of judgment:

- **Heuristic / availability-aware** — the 100K frozen blind set (`h2_availblind_labels.jsonl`).
- **Deterministic role-rubric** — `second_layer_pack_100k/proxy_labels.jsonl`.
- **Four independent LLM judge families** — gemini, gpt, deepseek, claude
  (`merged_j1/j2/j3`, `relabel_j1..j4`).

Treating each as a hypothesis of *"what the humans might reward,"* we score the shipped hand
pipeline — and the two signals currently computed-and-discarded in `features.py`
(management-track language; off-target current title) — against all nine.
(`scripts/exp_robustness.py`, branch `codex/robustness-defense`; shared
`redrob_ranker.eval_harness`. No production code or golden submission changed.)

## Composite under each hypothesis

| variant | blind | proxy | j-gemini¹ | j-gpt¹ | j-deepseek¹ | gemini | gpt | deepseek | claude | **mean** | **min** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **hand (ship)** | 0.7716 | 0.7771 | 0.8700 | 0.9424 | 0.8957 | 0.8211 | 0.8366 | 0.8579 | 0.9416 | **0.8571** | **0.7716** |
| hand×mgmt(.10) | 0.7705 | 0.7797 | 0.8681 | 0.9429 | 0.8940 | 0.8221 | 0.8170 | 0.8209 | 0.9409 | 0.8507 | 0.7705 |
| hand×mgmt(.20) | 0.7616 | 0.7844 | 0.8742 | 0.9408 | 0.8960 | 0.8221 | 0.8157 | 0.8201 | 0.9388 | 0.8504 | 0.7616 |
| hand×offtgt(.10) | 0.7736 | 0.7771 | 0.8700 | 0.9424 | 0.8957 | 0.8211 | 0.8366 | 0.8579 | 0.9416 | 0.8573 | 0.7736 |
| hand×offtgt(.20) | 0.7751 | 0.7771 | 0.8700 | 0.9424 | 0.8957 | 0.8211 | 0.8366 | 0.8579 | 0.9416 | 0.8575 | 0.7751 |
| hand×both(.15) | 0.7700 | 0.7805 | 0.8697 | 0.9414 | 0.8918 | 0.8222 | 0.8165 | 0.8208 | 0.9394 | 0.8502 | 0.7700 |

¹ `merged_j1/j2/j3` (the three-way merged judge sets). Signal coverage: management language in
67.8% of profiles (max count 2), off-target current title in 57.2%.

Pre-registered gate: adopt a signal only if it raises the **mean** AND does not lower the
**min** (worst-case) across hypotheses.

## Findings

1. **The ranking is not over-fit to one label source.** Across nine heterogeneous proxies the
   hand pipeline holds **0.7716 – 0.9424** composite (mean 0.8571). It scores *lowest* on its own
   strictest hypothesis (the availability-aware blind set) and *highest* on the more generous LLM
   judges — i.e. it is tuned conservatively, to the hardest grader. That spread (range **0.17**)
   is the honest magnitude of label-transfer risk.

2. **Management-track penalty — REJECTED.** Net negative on the mean (0.8571 → 0.8507) and it
   sharply hurts the GPT and DeepSeek hypotheses (0.8366 → 0.8170; 0.8579 → 0.8209). Penalizing
   manager-track language is exactly the kind of "obvious" tweak that the independent judges
   punish. A measured negative.

3. **Off-target-title penalty — passes the gate, but is effectively a no-op.** It raises the
   mean by +0.0004 and the worst case by +0.0035, but it moves *only* the blind hypothesis — the
   other eight are byte-identical, meaning off-target candidates barely surface in those label
   sets. It is a tiny blind-set-only floor-raise, **not** a broad improvement. Not worth
   disturbing the frozen golden submission (`af8f2b32`) for +0.0035 on a single hypothesis.

## Conclusion

The two "obvious next features" were tested across nine independent judgment models: one is a net
negative, the other is within noise. Combined with the ten measured negatives, this is strong
evidence the hand pipeline is **robust, not lucky** — it is not over-fit to the blind set, and
the remaining headroom is bounded by label-transfer risk (a property of the hidden labels we
cannot see), not by an un-tried lever. The frozen submission is retained.
