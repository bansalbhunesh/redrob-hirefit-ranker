# Ψ Reviewer Protocol — execution controls (do not modify after collection begins)

Operational instrument for running the frozen Ψ panel (`manifest.json`, hash
`34f43b14a3b40a16`, 24 candidates). This is process control, **not** analysis — thresholds
and the shipping rule are already frozen in `psi_analysis.py` and must not be changed.

## Reviewers (9, three independent families)
- 3 recruiters / hiring professionals
- 3 senior software/AI engineers
- 3 neutral, technically-informed reviewers
Each candidate gets ≥3 judgments, ideally one per family.

## Controls (enforce all)
- Reviewers do **not** know the hypothesis, and are **not** told a candidate came from
  golden / fusion / Ω.
- Do **not** tell reviewers there are "52 anomalies" or any count.
- **Stage B is hidden until Stage A is submitted.** Reviewers may **not** revise Stage A
  answers after seeing dates.
- Reviewers may **not** discuss candidates with each other until all responses are in.
- Record reviewer family, completion time, and confidence for every item.
- Preserve raw responses unchanged; run the pre-registered analysis without editing thresholds.

## Two stages (questions are in `reviewer_packet.jsonl`, one record per candidate)
- **Stage A (dates & flags hidden — `stageA_profile_no_dates`):** A1 suitability 0–5;
  A2 belongs in top-100? (yes/no); A3 supporting evidence (free text); A4 confidence (low/med/high).
- **Stage B (full profile — `stageB_profile_full`):** B1 does new info materially change the
  decision? (yes/no); B2 issue class (noise / incomplete / suspicious / decisive_impossibility);
  B3 remain in top-100? (yes/no); B4 reject regardless of career quality? (yes/no); B5 confidence.

## Output schema → `experiments/psi_panel/responses.jsonl`
One JSON object per (reviewer × candidate). Required keys:
```json
{"reviewer_id": 0, "family": "recruiter", "anon_id": "<from packet>",
 "A1_suitability_0to5": 4, "A2_belongs_top100_yes_no": "yes",
 "A3_supporting_evidence": "...", "A4_confidence_low_med_high": "high",
 "B1_decision_materially_changes_yes_no": "no",
 "B2_issue_class_[noise|incomplete|suspicious|decisive_impossibility]": "noise",
 "B3_remain_top100_yes_no": "yes", "B4_reject_regardless_yes_no": "no",
 "B5_confidence_low_med_high": "high"}
```
`anon_id` comes from `reviewer_packet.jsonl`; the anon→candidate map (`anon_key.json`) is
gitignored and used only by the scorer after collection.

## Run the frozen analysis (after all responses are in)
```
python experiments/psi_analysis.py        # prints analyses + decision; writes psi_result.json
```
Primary metric = **integrity reversal rate** (<20% noise → constrained defensible; >50%
penalise → constrained only if gated; mixed/20–50% → ship golden, ambiguity irreducible).
Default on any non-domination = **ship frozen golden (`af8f2b32`)**.
