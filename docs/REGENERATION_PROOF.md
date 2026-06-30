# Full-pool regeneration proof

This records a from-scratch regeneration of the committed `submission.csv` from the full 100,000-row
private challenge pool, to prove the shipped artifact is reproducible (not hand-edited). No private
data is committed — only this log.

## Command (canonical, as documented)

```bash
PYTHONHASHSEED=0 python rank.py --release \
  --candidates candidates.jsonl --out submission.csv --workers 2
```

## Environment

- Date (UTC): 2026-06-30T20:12:15Z
- Repo state: `main` @ `d69d874` (ranking code unchanged from the committed artifact)
- Python: 3.14.3 (compatible with 3.11+; CI runs 3.11)
- OS: Windows; CPU-only; offline (no network during ranking)
- Pool: full private `candidates.jsonl` (100,000 candidates) — not redistributed
- BM25 backend: `bm25s`

## Result

```
Release verified: frontier-v5, SHA-256 8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062
Pipeline completed in 76.2s
Loaded 100000 candidates; ranked pool 100000; honeypots detected 53; honeypots in output 0
```

- **Regenerated SHA-256:** `8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`
- **Golden SHA-256 (committed):** `8f7f30c68ec30cb66ad7d9c2f7103e7fbb6b20f639fdace8961f395c30ab6062`
- **Match:** ✅ byte-identical to the committed `submission.csv`
- **Validation:** `scripts/validate_submission.py` → `Submission is valid.`
- **Pipeline exit code:** 0

The full pool is excluded from the repository (`.gitignore`), so a third party reproduces this by
placing the official `candidates.jsonl` at the repo root and running the command above; the gate
`tests/test_submission_gate.py` additionally pins the committed bytes and a fixed-slice behavior hash.
