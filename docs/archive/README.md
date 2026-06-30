# Archived R&D notes — historical, not the submission's claims

> **Disclaimer for reviewers.** Everything in this `archive/` folder is a **historical development
> log** from the research process. These notes use **superseded framing, internal codenames (e.g.
> "V6"), and development-proxy comparisons** that are **not** how the final submission is described.
> They are kept only for provenance and auditability.
>
> For the accurate, current description of what ships, read the top-level
> [`README.md`](../../README.md), [`JUDGE_PACKET.md`](../JUDGE_PACKET.md),
> [`EXPLAINABILITY.md`](../EXPLAINABILITY.md), [`REPRODUCTION.md`](../REPRODUCTION.md), and
> [`REGENERATION_PROOF.md`](../REGENERATION_PROOF.md).
>
> Important boundaries that apply to **all** files here:
> - All ranking-quality numbers are **development proxies** (independent heuristic + LLM-judge labels),
>   **not** an official score or leaderboard result.
> - Any "#1", "projected #1", "30/30 wins", or "dominance" wording in these notes is internal
>   proxy-measurement language and is **not** a claim made by the submission.
> - The shipped system is the `main` `--release` build (ranking profile `frontier-v5`); the "V6"
>   codename used throughout these notes refers to that same release engineering, not a separate
>   product.

The shipped artifact is `submission.csv` (SHA-256 `8f7f30c6…`), reproducible with one command — see
[`REGENERATION_PROOF.md`](../REGENERATION_PROOF.md).
