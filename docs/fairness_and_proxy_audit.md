# Fairness And Proxy Audit

Branch: `codex/100-score-gap-lab`  
Status: experimental branch evidence, not part of submitted `main`.

This audit measures score movement under controlled counterfactual edits. It does
not claim the model is bias-free. It shows which profile edits do or do not move
the deterministic score, making proxy sensitivity inspectable.

## Method

Command:

```bash
python scripts/counterfactual_proxy_audit.py --candidates candidates.jsonl --out artifacts/counterfactual_proxy_audit_100k.csv --max-candidates 100000
python scripts/summarize_counterfactual_proxy_audit.py --audit artifacts/counterfactual_proxy_audit_100k.csv --out artifacts/counterfactual_proxy_audit_100k_summary.json
```

Run result:

- Candidates audited: 100,000
- Counterfactual rows: 400,000
- Runtime: 556.3 seconds on the local machine
- Ranking path changed: no
- `submission.csv` changed: no

Variants:

- `name_neutralized`: replace profile name fields with "Neutral Candidate".
- `location_undisclosed`: replace location/country with undisclosed/blank.
- `preferred_india_location`: set location to Bengaluru, India.
- `behavioral_neutral`: set recruiter-response and engagement signals to a neutral middle profile.

## Results

| Variant | n | Nonzero deltas | Positive | Negative | Mean delta | Median | p05 | p95 | Max abs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| name_neutralized | 100,000 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| location_undisclosed | 100,000 | 75,093 | 0 | 75,093 | -0.007489 | -0.006076 | -0.021295 | 0.000000 | 0.043805 |
| preferred_india_location | 100,000 | 70,761 | 70,761 | 0 | 0.005677 | 0.003973 | 0.000000 | 0.019989 | 0.043805 |
| behavioral_neutral | 100,000 | 99,967 | 81,623 | 18,344 | 0.008759 | 0.006873 | -0.007646 | 0.031890 | 0.156590 |

## Interpretation

The good result:

- Name fields do not affect the deterministic score on the full 100K pool. That
  closes a concrete review attack: candidate names are present in source data,
  but this scorer does not use them as a ranking signal.

The expected proxy result:

- Location moves scores because the JD and ranker explicitly include preferred
  India locations and relocation logistics.
- Behavioral signals move scores because the JD asks for reachable candidates,
  and Redrob's product context includes recruiter interaction signals.

The risk that remains:

- Location and behavioral telemetry are legitimate job-process signals, but they
  can also act as socioeconomic or geography proxies. This branch makes that
  movement measurable; it does not prove those proxies are always fair.

## Merge Criteria

Do not merge this branch into `main` unless the audit is framed precisely:

- Say "proxy sensitivity audit", not "bias solved".
- Keep the counterfactual tool and summary script tested.
- Do not change ranking output unless a separate ranking-quality gate justifies it.
- If promoted to the final deck, present the name-neutralization result as the
  strongest proof and the location/behavioral deltas as transparent tradeoffs.

