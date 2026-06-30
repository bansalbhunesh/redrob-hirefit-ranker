# HireFit V6 — 60-second judge packet

## The decision

Ship **V6 battle-proof**: the `frontier-v5` ranking core wrapped in an exact-output,
fail-closed release. It is the strongest all-around artifact we measured and the safest
artifact to reproduce under the challenge constraints.

| Judge question | Evidence-backed answer |
|---|---|
| Does it understand the job beyond keywords? | BM25 is only one signal. A 33-feature evidence model reads production work, role depth, seniority, trajectory, behavior, and logistics. |
| Does it use profile and activity signals? | Yes. Career history, structured profile facts, recruiter response, activity, notice, reliability, and open-to-work signals all contribute. |
| Is the ranking strong? | #1/673 on the seven-evaluator mean, #1/100 on the strongest-union mean, #3/322 on equal four-axis balance, and 30/30 composite wins over main. |
| Is it fast enough? | 100K candidates in 136.0 s pipeline / 149.1 s wall at 2 CPU / 16 GiB; 4.13 GiB sampled peak. |
| Can a recruiter trust it? | Every output row has grounded reasoning; every score decomposes into named evidence and guardrails; suspicious cases become review guidance, not unsupported fraud claims. |
| Can the evaluator reproduce it? | CPU-only, offline, digest- and wheel-pinned, deterministic, one release command, exact input/model/output hashes. |
| What happens on failure? | Invalid configuration, corrupt artifacts, count drift, and hash drift fail closed. A forced 3 GiB OOM preserved the prior output and left zero mounted temporary files. |

## Open these five things

1. [README](../README.md) — complete submission story and quick start.
2. [Live Hugging Face sandbox](https://huggingface.co/spaces/bansal1234/Hirefit) — recruiter-facing proof.
3. [Pitch deck](HireFit_Ranker_Redrob_POLISHED.pdf) — 14-slide judge narrative.
4. [Challenge positioning](CHALLENGE_POSITIONING.md) — mission-derived 93.7/100 with claim boundaries.
5. [Battle-proof audit](v6_battleproof_audit.md) — failure-mode and exact-output evidence.

## Reproduce the release

```bash
python -m pip install -e .
PYTHONHASHSEED=0 python rank.py --release --workers 2 \
  --candidates candidates.jsonl --out submission.csv
python scripts/validate_submission.py submission.csv --candidates candidates.jsonl
sha256sum submission.csv
# 8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062
```

Docker:

```bash
docker build -t hirefit-v6 .
docker run --rm --cpus=2 --memory=16g -v "$PWD:/data" hirefit-v6 \
  --release --workers 2 --candidates /data/candidates.jsonl --out /data/submission.csv
```

## Honest boundary

Official hidden labels and numeric judging weights are not published. Public-field ranks are
transparent local comparisons over reproducible outputs, not an official leaderboard. The
defensible conclusion is **projected #1 overall with an honest #1–#3 range**, not guaranteed
first place on every isolated specialist metric.
