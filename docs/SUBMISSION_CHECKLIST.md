# Pre-Submission Checklist — Redrob HireFit Ranker

Everything controllable in the repository is verified here. “Owner action” means it depends on the challenge portal or an account outside this repository.

## Verified in the repository

- **Release locked:** fail-closed release, frontier-v5 ranking core, SHA-256 prefix `8f7f30c6`.
- **One release path:** `PYTHONHASHSEED=0 python rank.py --release ...` forces the champion and fails closed on input, model, configuration, count, numeric, or output drift.
- **Reproducible:** `./reproduce.sh` is green; the full 100K Docker release is byte-identical and atomic; a forced OOM preserves the previous output.
- **Resource fit:** CPU-only and offline; 136.0 s pipeline / 149.1 s wall at 2 CPU / 16 GiB; sampled peak 4.13 GiB.
- **Ranking evidence:** improves every measured composite versus the repository's default profile and sits in the top cluster on development proxies (broad / strongest-union / four-axis means); external reviewer and blind cross-checks. Dev proxies, not an official score.
- **Integrity:** 0 detected honeypots in the top 100, with 53 detected in the pool.
- **Supply chain:** digest-pinned base image, hash-pinned wheels, `pip --require-hashes`, and no known production dependency vulnerabilities in the dated audit.
- **Judge path:** the judge-proof package, 60-second judge packet, evidence-first README, methodology, deployment guide, current pitch deck, and screenshots are linked from the repository front page. Historical R&D notes remain under `docs/archive/` and are not submission claims.
- **Fresh visual proof:** desktop and 390-pixel mobile screenshots were regenerated from the live Render and Hugging Face surfaces on 2026-07-01.
- **Deployment:** both the Hugging Face Space and Render decision room returned HTTP 200 on 2026-07-02; the repository also includes a schema-validated Render Blueprint and documented health/readiness gates.
- **Public access:** verified through the live GitHub repository, Hugging Face Space, and Render app on 2026-07-02.

## Optional presentation enhancement

- A two-minute narrated walkthrough could help a time-limited judge, but it is not presented as an existing artifact and is not required to reproduce or evaluate the ranker.

## Owner action outside this repository

1. Confirm the challenge portal entry points to the public repository and the exact `8f7f30c6…` submission artifact.
2. Record and attach the optional two-minute walkthrough if the challenge portal provides a video field; the verified flow is in [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
3. Rotate any credential that may have appeared outside version control; no credential is required by the ranker or committed here.

## Claim boundary

Official hidden labels and numeric judging weights are unpublished. The mission-derived positioning score and public-field rank estimates are transparent estimates, not official results. The measured claim is narrower and honest: the release is the best balanced artifact tested in this repository, wins every measured composite against main, remains inside the challenge resource envelope, and preserves deterministic fail-closed delivery.
