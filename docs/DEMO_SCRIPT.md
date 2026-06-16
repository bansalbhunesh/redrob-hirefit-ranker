# Demo Script — Redrob HireFit Ranker (≈2 min, hackathon-winning)

Goal: in 2 minutes show **product thinking + scientific honesty**, not just "we got a score."
Format: voiceover + on-screen cues. Record at a calm, confident pace. Lead with the product, prove
it live, then land the one thing no other team has.

---

## The 2-minute script

**[0:00 — HOOK]**  *(show: a keyword-stuffed "Marketing Manager — 9 AI keywords" profile next to a real engineer)*
> "Keyword filters hire the wrong people. The dataset is *built* to punish them — stuffers, wrong-role
> profiles, and impossible 'honeypots'. So we didn't build a keyword matcher. We built a ranker that
> reads **careers and evidence**, the way a great recruiter does."

**[0:18 — IT WORKS, LIVE]**  *(show: HuggingFace Space — upload candidates, the top-100 appears)*
> "This is live, not precomputed. Upload 100,000 candidates and in about 80 seconds, on CPU, fully
> offline, you get an explainable top-100. Number one: a Senior ML Engineer at Zomato who *shipped*
> hybrid retrieval and ranking at 50-million-query scale — and every rank traces back to named
> features, not a black box."  *(click a row → show the feature breakdown + grounded reason)*

**[0:42 — WHY YOU CAN TRUST IT]**  *(show: the integrity checklist / 0 honeypots)*
> "It blocks the traps: 53 honeypots detected, **zero** in the shortlist. And it's honest about
> uncertainty — a flagged profile is marked **'verify with a human'**, never auto-rejected. The
> whole output is **byte-reproducible** and locked by 198 tests."

**[1:05 — THE DIFFERENTIATOR]**  *(show: the measured-negatives table)*
> "Here's what makes this different. We didn't *guess* this was the best approach — we **proved** it.
> We built ten stronger-sounding alternatives: a cross-encoder, the ACL-2026 DART reranker,
> LightGBM, learned weights, embeddings — and **measured every one losing** on a blind set we froze
> before tuning. The fancy lever is empty; the evidence is the win."

**[1:28 — THE SHIP + VALIDATION]**  *(show: the decision flow diagram)*
> "What we ship is a careful upgrade: golden's high-confidence top-30, with the tail re-ordered by
> consensus. It beats the baseline on **7 of 7** label sets — and we confirmed it with **two
> independent LLM judges, from different labs, that the model was never tuned against.** Both agreed."

**[1:48 — THE HONEST FLEX]**  *(show: the stress-test result)*
> "We even built the *higher-scoring* alternative — and then **rejected it**, because a blinded
> integrity judge found its extra picks weren't actually better hires. We ship the option we can
> defend, with the safer ranking one command away as a fallback."

**[2:05 — PRODUCT THINKING / CLOSE]**  *(show: the Render audit payload + 'drop-in for Redrob')*
> "It's a drop-in scoring layer for Redrob's stack: per-candidate JSON — features, multipliers,
> flags — that a recruiter can defend in a meeting. We don't rank resumes. **We rank hireability —
> and we can prove every decision.**"

---

## 30-second lightning version (if a slot is tight)

> "Keyword filters hire the wrong people. We built a deterministic, CPU-only ranker that reads
> careers, not keywords — live top-100 of 100K in 80 seconds, every rank explainable, zero honeypots.
> The flex isn't the score; it's the *receipts*: ten modern alternatives built and measured losing,
> the shipped ranking confirmed by two independent LLM judges, and even the higher-scoring option
> rejected on integrity. We don't rank resumes — we rank hireability, and we prove it."

---

## Delivery tips

- **Show, don't tell:** every claim has an on-screen artifact (live ranking, feature breakdown,
  measured-negatives table, two-judge result). Judges believe what they see run.
- **Lead with product, close with science.** The hook and the live demo earn the right to the rigor.
- **Own the honest limit once, with confidence:** "these are dev-proxy labels, not the official
  score — our edge is rigor and reproducibility." Stating it first makes you *more* credible, not less.
- **End on the one line:** "We rank hireability — and we can prove every decision."
- Keep it ~2:00–2:30. Record the screen captures *after* the live sites finish rebuilding so the
  contrast/labels look crisp.
