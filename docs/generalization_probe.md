# JD Generalization Probe

Branch: `codex/100-score-gap-lab`  
Status: experimental branch evidence, not part of submitted `main`.

This probe tests whether the JD compiler changes behavior for related technical
roles and refuses unsupported roles instead of pretending to rank everything.

## Command

```bash
python scripts/jd_generalization_probe.py --out artifacts/jd_generalization_probe.json
```

## Results

| JD | Status | Key compiled behavior |
|---|---|---|
| Senior AI Engineer | compiled | LLM, embeddings, vector DB, ranking, Python concepts active |
| Backend Platform Engineer | compiled | Backend title family, Python + ranking concepts, distributed-systems nice-to-have, Bangalore/Chennai locations |
| Search Relevance Engineer | compiled | Vector DB, ranking/IR, eval-framework concepts active |
| Sales Manager | unsupported | Refused with no must-have skill concepts |

## Why This Matters

The branch does not claim universal hiring generality. It proves a narrower but
more defensible point:

- The challenge JD path remains byte-identical.
- Related technical JDs compile into different ranking programs.
- Unsupported non-technical roles fail closed instead of producing fake scores.

This is stronger than a generic "works for any JD" claim and safer for a judge
who asks where the system's boundaries are.

