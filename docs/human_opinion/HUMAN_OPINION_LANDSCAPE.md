# Human Opinion Landscape — Study Φ (Hacker News pilot)

**Scope & honesty.** This is a **pilot** of Study Φ covering **one stratum only (Hacker
News)** — the ToS-clean public API — coded by a **single coder** (no intercoder reliability),
n = 19 distinct hiring judgments drawn from 95 real retrieved comments. It is **not
representative** of recruiters, of India-specific hiring, or of the field; HN skews toward
engineers and founders. No prevalence claims. Upvotes are excluded by design. The full
multi-stratum, double-coded study is specified and frozen in `protocol.md`.

## Method (traceable)
Real comments retrieved via the HN Algolia public search across four query families
(integrity-focused, quality-first, verification-first, technology-anachronism); full audit
trail in `search_log.csv` (raw text + URLs in `raw_hn_corpus.jsonl`). Inclusion/exclusion per
`protocol.md`; every exclusion logged with a reason (`exclusion_log.csv`, 17 reviewed-excluded:
who's-hiring posts, ATS advice, off-topic tangents, anecdotes without a rule). Codes per
`codebook_v1.md`; per-item codes in `corpus_pilot.csv` (each row carries `coder_2 =
AWAITING_SECOND_CODER`).

## Themes (this stratum)
- **Capability-first is the dominant voice (53% QUALITY_FIRST):** work-samples, week-long
  projects, portfolios, and interviews are repeatedly preferred over résumé claims. Engineers
  trust *demonstrated* ability over *stated* history.
- **Verification-first is the middle path (21% VERIFY_FIRST):** for concerning items
  (employment reality, identity/proxy fraud), the recommended move is a background/reference
  check or a technical probe — **investigate, not auto-reject**.
- **A real integrity-strict minority (21% INTEGRITY_HIGH):** confirmed lying/fabrication
  draws rejection; one outlier rejects résumés over a single typo (logged as a negative case).
- **Post-AI fraud is a live concern (2023+):** fake/ChatGPT applicants and proxy candidates
  appear in the recent items, pushing toward *verification*, not blanket integrity penalties.

## Technology-tenure anomalies (our anachronism analogue)
The three items touching inflated skill-duration / "tech tenure" all resolve **without
rejection**: two say *ignore* ("a good engineer picks up a new stack fast; claimed tenure
isn't the point"), one says *verify in the interview*. In this engineer-heavy stratum, a tech
tenure that looks too long is treated as something the interview filters — **not a decisive
disqualifier.** This is a (capability-leaning) signal, and precisely the place the recruiter
stratum (not yet collected) is most likely to diverge.

## Contrary / minority evidence (preserved)
- `HN_2246385`: rejects on a single typo — a strict-on-minor outlier against the dominant lean.
- `HN_6876400`: asserts fabrication is common in a regional cohort (prejudiced framing; recorded
  as the stated stance, flagged in `notes`).
These are kept, not hidden; they show the distribution has real spread.

## Limits
HN-only; single coder (IRR not established); n = 19 pilot; engineer/founder skew; platform-
and algorithm-shaped; author roles `self_claimed`; short excerpts; no model training on the
corpus. Φ can establish the *structure* of the trade-off, not which Redrob candidates to rank.
