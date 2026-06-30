# Pre-Submission Checklist — Redrob HireFit Ranker

Everything controllable in the repository is verified here. “Owner action” means it depends on the challenge portal or an account outside this repository.

## Verified in the repository

- **Release locked:** V6 battle-proof release, frontier-v5 ranking core, SHA-256 prefix `8f7f30c6`.
- **One release path:** `PYTHONHASHSEED=0 python rank.py --release ...` forces the champion and fails closed on input, model, configuration, count, numeric, or output drift.
- **Reproducible:** `./reproduce.sh` is green; the full 100K Docker release is byte-identical and atomic; a forced OOM preserves the previous output.
- **Resource fit:** CPU-only and offline; 136.0 s pipeline / 149.1 s wall at 2 CPU / 16 GiB; sampled peak 4.13 GiB.
- **Ranking evidence:** 30/30 composite wins over main; #1/673 mean7; #1/100 mean15; #3/322 balance4; 883 safety fusions; 100 repeated half-splits; external reviewer and blind slices.
- **Integrity:** 0 detected honeypots in the top 100, with 53 detected in the pool.
- **Supply chain:** digest-pinned base image, hash-pinned wheels, `pip --require-hashes`, and no known production dependency vulnerabilities in the dated audit.
- **Judge path:** 60-second judge packet, evidence-first README, public-field scorecard, methodology, deployment guide, pitch deck (PPTX + PDF), and screenshots are linked from the repository front page.
- **Fresh visual proof:** desktop and 390-pixel mobile screenshots were rendered from the current V6 API on 2026-06-30; the responsive pipeline and detail drawer were tightened after inspection.
- **Deployment:** the Hugging Face Space is the primary live sandbox and returns HTTP 200. The repository includes a schema-validated Render Blueprint and documented health/readiness gates.
- **Honest live-status disclosure:** the historical Render mirror is externally suspended and is not advertised as live proof.
- **Repository access check:** GitHub reported the repository as **private** on 2026-06-30. This is the only P0 publication blocker and requires an explicit owner visibility decision.

## Optional presentation enhancement

- A two-minute narrated walkthrough could help a time-limited judge, but it is not presented as an existing artifact and is not required to reproduce or evaluate the ranker.

## Owner action outside this repository

1. Make the GitHub repository public when authorized, then verify it in a logged-out browser.
2. Confirm the challenge portal entry points to that public repository and the exact `8f7f30c6…` submission artifact.
3. If the historical Render account is reactivated, run every acceptance check in [DEPLOYMENT.md](DEPLOYMENT.md) before advertising that mirror as live.
4. Rotate any credential that may have appeared outside version control; no credential is required by the ranker or committed here.

## Claim boundary

Official hidden labels and numeric judging weights are unpublished. The mission-derived positioning score and public-field rank estimates are transparent estimates, not official results. The measured claim is narrower and stronger: V6 is the best balanced artifact tested in this repository, wins every measured composite against main, remains inside the challenge resource envelope, and preserves deterministic fail-closed delivery.
