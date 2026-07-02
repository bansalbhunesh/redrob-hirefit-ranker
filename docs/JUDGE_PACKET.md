# HireFit — 60-second judge packet

## The decision

Ship the **`main` `--release` artifact**: the `frontier-v5` ranking profile wrapped in an
exact-output, fail-closed release. It sits in the **top cluster** of our development-proxy comparisons
and is fully reproducible under the challenge constraints. Quality figures below
are dev proxies, **not** an official score.

| Judge question | Evidence-backed answer |
|---|---|
| Does it understand the job beyond keywords? | BM25 is only one signal. A 33-feature evidence model reads production work, role depth, seniority, trajectory, behavior, and logistics. |
| Does it use profile and activity signals? | Yes. Career history, structured profile facts, recruiter response, activity, notice, reliability, and open-to-work signals all contribute. |
| Is the ranking strong? | On our development proxies (independent heuristic + LLM-judge labels) it sits in the **top cluster** of the public field. These are self-run proxies, not an official leaderboard. |
| Is it fast enough? | 100K candidates in 136.0 s pipeline / 149.1 s wall at 2 CPU / 16 GiB; 4.13 GiB sampled peak. Budget 300 s. |
| Can a recruiter trust it? | Every output row has grounded reasoning; every candidate's evidence score decomposes into **exact** named-feature contributions and guardrails; suspicious cases become review guidance, not unsupported fraud claims. |
| Can the evaluator reproduce it? | CPU-only, offline, digest- and wheel-pinned, deterministic, **one release command**, exact input/model/output hashes; serial and parallel output byte-identical. |
| What happens on failure? | Invalid configuration, corrupt artifacts, count drift, and hash drift fail closed. A forced 3 GiB OOM preserved the prior output and left zero mounted temporary files. |

## Open these five things

1. [README](../README.md) — complete submission story and quick start.
2. [Live Hugging Face sandbox](https://huggingface.co/spaces/bansal1234/Hirefit) — recruiter-facing proof.
3. [Explainability](EXPLAINABILITY.md) — exact per-feature attributions, ablation, rank-stability bands.
4. [What we rejected](measured_negatives.md) — the pre-registered measured-negatives ladder.
5. [Reproduce / runtime](REPRODUCTION.md) — full-pool reproduction and the Docker runtime matrix.

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
docker build -t hirefit-ranker .
docker run --rm --cpus=2 --memory=16g -v "$PWD:/data" hirefit-ranker \
  --release --workers 2 --candidates /data/candidates.jsonl --out /data/submission.csv
```

## Honest boundary

Official hidden labels and numeric judging weights are not published. Public-field comparisons are
transparent local measurements over reproducible outputs on development proxies, **not** an official
leaderboard. The defensible claim is **top-cluster development-proxy balance with exact full-pool
release proof** — not guaranteed first place on any official or isolated metric. The
two narrow `frontier-v5` tie-breaks have marginal, within-noise impact; the submission's case rests on
reproducibility, integrity, and validation.
