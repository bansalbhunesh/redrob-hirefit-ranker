# Adversarial Integrity Audit

Branch: `codex/100-score-gap-lab`  
Status: experimental branch evidence, not part of submitted `main`.

This audit adds deterministic detection for adversarial resume text patterns
without changing the official ranking path.

## What Is Detected

- Hidden Unicode/control characters often used for invisible keyword stuffing.
- Prompt-injection text such as "ignore previous instructions" or "rank me first".
- Extreme repeated keyword blocks.

The detector lives in `src/redrob_ranker/integrity.py`. It is used by
`scripts/adversarial_integrity_audit.py` for audit/manual-review evidence.

## Tests

```bash
python -m pytest tests/test_integrity.py -q
```

Result:

```text
3 passed
```

The tests prove:

- Prompt-injection and hidden-control text are detected.
- Repeated keyword blocks are detected.
- Integrity flags have manual-review penalty semantics available through the
  existing disqualifier multiplier.

## Full Pool Scan

Command:

```bash
python scripts/adversarial_integrity_audit.py --candidates candidates.jsonl --out artifacts/adversarial_integrity_100k_v2.csv --max-candidates 100000
```

Result:

```text
Scanned 100000 candidates; flagged 0 profiles; counts={}
Runtime: 60.4s
```

## Interpretation

This closes a real review attack without polluting the submitted ranking:

- The branch can show prompt-injection/hidden-text defenses in fixtures.
- The full pool has no detected adversarial text under the tuned threshold.
- Strong synthetic AI profiles are not falsely punished merely for containing
  many legitimate retrieval/ranking terms.

Do not claim this is a fraud-proof parser. It is a deterministic integrity
screen that can feed manual review or demo badges.

