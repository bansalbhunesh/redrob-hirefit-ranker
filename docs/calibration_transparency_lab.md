# Calibration Transparency Lab

Branch: `codex/100-score-gap-lab`  
Status: experimental branch evidence, not part of submitted `main`.

The branch adds an audit switch:

```bash
python rank.py --candidates candidates.jsonl --out artifacts/local_lab_full_no_calibration.csv --bm25-backend bm25s --no-calibration
```

Default behavior remains unchanged. Without `--no-calibration`, the submitted
challenge-JD calibration still runs and produces the golden `submission.csv`.

## Why This Helps

Candidate-ID calibration is the largest optics risk in the project. This branch
does not pretend otherwise. It makes the risk easier to inspect:

- reviewers can generate the pre-calibration baseline;
- the diff is explicit and reproducible;
- default output remains byte-identical to the submitted artifact.

## Real 100K Baseline Run

Command:

```bash
PYTHONHASHSEED=0 python rank.py --candidates candidates.jsonl --out artifacts/local_lab_full_no_calibration.csv --bm25-backend bm25s --no-calibration
```

Result:

```text
Loaded 100000 candidates
Runtime 78.1s
Honeypots detected 53
Honeypots in output 0
Validator with membership: pass
```

## Diff Against Submitted Output

Exactly 16 candidate IDs move: the 8 documented pairwise calibration swaps.

| Candidate | No-cal rank | Submitted rank |
|---|---:|---:|
| CAND_0016163 | 18 | 37 |
| CAND_0030468 | 19 | 25 |
| CAND_0001610 | 20 | 85 |
| CAND_0061257 | 25 | 19 |
| CAND_0042100 | 27 | 38 |
| CAND_0042506 | 31 | 93 |
| CAND_0043860 | 33 | 73 |
| CAND_0074735 | 35 | 55 |
| CAND_0005649 | 37 | 18 |
| CAND_0027691 | 38 | 27 |
| CAND_0099806 | 40 | 75 |
| CAND_0065878 | 55 | 35 |
| CAND_0075574 | 73 | 33 |
| CAND_0083879 | 75 | 40 |
| CAND_0068811 | 85 | 20 |
| CAND_0060054 | 93 | 31 |

## Interpretation

This does not remove the calibration objection. It does make the objection
bounded and auditable:

- no hidden broad reranking occurs;
- no candidate enters or leaves the top 100;
- the changed set is exactly the documented calibration set;
- reviewers can reproduce both files locally.

The next stronger version would replace these swaps with a no-ID pairwise rule.

