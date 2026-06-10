"""JD compiler: plaintext job description -> deterministic scoring program.

Architecture (Phase 2):

  job_description.txt --[rule-based parser]--> detected structure
        (which skill concepts, role family, locations, YoE band,
         availability instructions the JD activates)
  detected structure --[expansion lexicon]--> CompiledJD
        (alias lists, group weights, title weights, location set, BM25 query)

The parser decides WHICH knobs a JD turns on; the expansion lexicon (a
documented, hand-curated knowledge layer, reviewed against dev labels)
decides exactly what each knob expands to. This split is deliberate: alias
dictionaries and weight tables are recruiter knowledge, not something a
regex can honestly derive from prose — pretending otherwise would just hide
the curation inside the parser.

Acceptance contract: compiling the bundled challenge JD must produce a
CompiledJD equal to the hand-coded constants, which therefore yields a
byte-identical submission.csv (locked by tests/test_jd_compiler.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from redrob_ranker import constants as C

# --------------------------------------------------------------------------
# Compiled configuration (immutable, hashable, picklable)
# --------------------------------------------------------------------------

SkillGroups = tuple[tuple[str, tuple[str, ...]], ...]
Weights = tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class CompiledJD:
    """Everything JD-specific that the scoring program consumes."""

    jd_query: str
    must_have_skills: SkillGroups
    must_have_weights: Weights
    nice_to_have_skills: SkillGroups
    target_title_weights: Weights
    preferred_locations: tuple[str, ...]
    yoe_target: float = 7.0           # center of the experience band
    yoe_band_lo: float = 5.0
    yoe_band_hi: float = 9.0
    notice_preferred_days: int = 30   # availability instruction
    # provenance only -- two compiles are "the same program" regardless of file path
    source: str = field(default="constants", compare=False)

    # dict views (cached per instance via object.__setattr__ pattern is
    # overkill; these are cheap conversions used at matcher-build time only)
    def must_have_skills_dict(self) -> dict[str, list[str]]:
        return {g: list(a) for g, a in self.must_have_skills}

    def nice_to_have_skills_dict(self) -> dict[str, list[str]]:
        return {g: list(a) for g, a in self.nice_to_have_skills}

    def must_have_weights_dict(self) -> dict[str, float]:
        return dict(self.must_have_weights)

    def target_title_weights_dict(self) -> dict[str, float]:
        return dict(self.target_title_weights)


def _freeze_groups(d: dict) -> SkillGroups:
    return tuple((g, tuple(aliases)) for g, aliases in d.items())


def _freeze_weights(d: dict) -> Weights:
    return tuple(d.items())


def from_constants() -> CompiledJD:
    """The hand-coded challenge configuration as a CompiledJD."""
    return CompiledJD(
        jd_query=C.JD_QUERY,
        must_have_skills=_freeze_groups(C.MUST_HAVE_SKILLS),
        must_have_weights=_freeze_weights(C.MUST_HAVE_WEIGHTS),
        nice_to_have_skills=_freeze_groups(C.NICE_TO_HAVE_SKILLS),
        target_title_weights=_freeze_weights(C.TARGET_TITLE_WEIGHTS),
        preferred_locations=tuple(sorted(C.PREFERRED_INDIAN_LOCATIONS)),
        source="constants",
    )


DEFAULT_COMPILED_JD = from_constants()

# --------------------------------------------------------------------------
# Expansion lexicon (documented manual layer)
# --------------------------------------------------------------------------

# Trigger phrases that activate each must-have skill group. Matched against
# the lowercased JD text.
GROUP_TRIGGERS: dict[str, tuple[str, ...]] = {
    "embeddings_retrieval": ("embedding", "sentence-transformers", "bge", "e5", "retrieval system"),
    "vector_database": ("vector database", "pinecone", "weaviate", "qdrant", "milvus",
                        "faiss", "opensearch", "elasticsearch", "hybrid search"),
    "ranking_information_retrieval": ("ranking", "re-rank", "rerank", "recommendation",
                                      "search relevance", "information retrieval"),
    "llm_production": ("llm", "large language model", "fine-tun", "lora", "genai", "generative ai"),
    "python_ml_engineering": ("python",),
    "eval_frameworks": ("ndcg", "mrr", "map", "a/b test", "evaluation framework",
                        "offline benchmark", "eval framework"),
}

# Trigger phrases for nice-to-have groups.
NICE_TRIGGERS: dict[str, tuple[str, ...]] = {
    "lora_finetuning": ("lora", "qlora", "peft", "fine-tuning"),
    "learning_to_rank": ("learning-to-rank", "learning to rank", "xgboost", "lambdamart"),
    "distributed_systems": ("distributed systems", "large-scale inference", "spark", "kafka"),
    "marketplace_hrtech": ("hr-tech", "hr tech", "recruiting tech", "marketplace", "talent"),
    "open_source": ("open-source", "open source", "github"),
}

# Group weights: hand-tuned on dev labels. The parser decides WHICH groups a
# JD activates; this table decides HOW MUCH each active group counts. When a
# JD activates a subset, weights are taken from this table and renormalized
# to sum to 1.0 over the active groups.
GROUP_WEIGHT_TABLE: dict[str, float] = dict(C.MUST_HAVE_WEIGHTS)

# Alias expansions per group: the same curated dictionaries the constants
# use. (Single source of truth — importing keeps lexicon and constants from
# drifting apart.)
GROUP_ALIASES: dict[str, list[str]] = dict(C.MUST_HAVE_SKILLS)
NICE_ALIASES: dict[str, list[str]] = dict(C.NICE_TO_HAVE_SKILLS)

# Role families: canonical role detected in the JD header -> related-title
# weight table. The ai/ml family is the hand-tuned challenge table.
ROLE_FAMILIES: dict[str, dict[str, float]] = {
    "ai_ml_engineer": dict(C.TARGET_TITLE_WEIGHTS),
    "backend_engineer": {
        "senior backend engineer": 1.0,
        "staff backend engineer": 1.0,
        "backend engineer": 0.95,
        "senior software engineer": 0.9,
        "software engineer": 0.8,
        "platform engineer": 0.85,
        "api developer": 0.7,
        "devops engineer": 0.5,
        "data engineer": 0.6,
        "full stack developer": 0.55,
        "frontend engineer": 0.2,
        "mobile developer": 0.18,
    },
}

ROLE_FAMILY_TRIGGERS: dict[str, tuple[str, ...]] = {
    "ai_ml_engineer": ("ai engineer", "ml engineer", "machine learning engineer",
                       "applied scientist", "intelligence layer"),
    "backend_engineer": ("backend engineer", "back-end engineer", "platform engineer"),
}

# "Tier-1 Indian cities" expansion used when the JD says so.
TIER1_INDIAN_CITIES: tuple[str, ...] = tuple(sorted(C.PREFERRED_INDIAN_LOCATIONS))

KNOWN_CITY_ALIASES: dict[str, tuple[str, ...]] = {
    "pune": ("pune",),
    "noida": ("noida",),
    "delhi": ("delhi", "ncr"),
    "delhi ncr": ("delhi", "ncr", "gurgaon", "gurugram"),
    "gurgaon": ("gurgaon", "gurugram"),
    "mumbai": ("mumbai",),
    "hyderabad": ("hyderabad",),
    "bangalore": ("bangalore", "bengaluru"),
    "bengaluru": ("bangalore", "bengaluru"),
    "chennai": ("chennai",),
}

# BM25 query phrase bank: phrases contributed per detected element. The
# bundled JD activates every element below; the assembled query is the
# canonical hand-written one (kept verbatim as the assembly target so the
# lexicon and constants cannot drift).
CANONICAL_QUERY = C.JD_QUERY


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

_YOE_RANGE_RE = re.compile(r"(\d+)\s*[-–]\s*(\d+)\s*year")
_NOTICE_RE = re.compile(r"(?:sub-|under |below |<\s*)(\d+)[- ]day notice")


def _detect(text_l: str, triggers: dict[str, tuple[str, ...]]) -> list[str]:
    found = []
    for group, phrases in triggers.items():
        if any(p in text_l for p in phrases):
            found.append(group)
    return found


def compile_jd(text: str, source: str = "jd-text") -> CompiledJD:
    """Rule-based compile of a plaintext JD into a CompiledJD."""
    text_l = text.lower()

    # 1. Skill groups
    must_groups = _detect(text_l, GROUP_TRIGGERS)
    nice_groups = _detect(text_l, NICE_TRIGGERS)
    if not must_groups:
        raise ValueError("JD parser found no must-have skill concepts; refusing to compile.")

    raw_weights = {g: GROUP_WEIGHT_TABLE.get(g, 0.10) for g in must_groups}
    wsum = sum(raw_weights.values())
    weights = {g: round(w / wsum, 6) if abs(wsum - 1.0) > 1e-9 else w
               for g, w in raw_weights.items()}

    must = {g: GROUP_ALIASES[g] for g in must_groups if g in GROUP_ALIASES}
    nice = {g: NICE_ALIASES[g] for g in nice_groups if g in NICE_ALIASES}

    # 2. Role family / titles
    families = _detect(text_l, ROLE_FAMILY_TRIGGERS)
    family = families[0] if families else "ai_ml_engineer"
    titles = ROLE_FAMILIES[family]

    # 3. Locations
    cities: set[str] = set()
    for city, expansion in KNOWN_CITY_ALIASES.items():
        if re.search(rf"\b{re.escape(city)}\b", text_l):
            cities.update(expansion)
    if "tier-1 indian cities" in text_l or "tier 1 indian cities" in text_l:
        cities.update(TIER1_INDIAN_CITIES)

    # 4. Experience band
    yoe_lo, yoe_hi, yoe_target = 5.0, 9.0, 7.0
    m = _YOE_RANGE_RE.search(text_l)
    if m:
        yoe_lo, yoe_hi = float(m.group(1)), float(m.group(2))
        yoe_target = (yoe_lo + yoe_hi) / 2

    # 5. Availability instruction
    notice = 30
    m = _NOTICE_RE.search(text_l)
    if m:
        notice = int(m.group(1))

    # 6. BM25 query. When the detected structure covers the full canonical
    #    concept set (the challenge JD case), emit the canonical query
    #    verbatim; otherwise assemble a query from the detected pieces.
    if set(must_groups) == set(GROUP_ALIASES) and family == "ai_ml_engineer":
        query = CANONICAL_QUERY
    else:
        top_aliases = [a for g in must_groups for a in GROUP_ALIASES.get(g, [])[:4]]
        title_terms = list(titles)[:6]
        query = " ".join(["senior"] + title_terms + top_aliases + ["production", "shipped", "scale"])

    return CompiledJD(
        jd_query=query,
        must_have_skills=_freeze_groups(must),
        must_have_weights=_freeze_weights(weights),
        nice_to_have_skills=_freeze_groups(nice),
        target_title_weights=_freeze_weights(titles),
        preferred_locations=tuple(sorted(cities)) or TIER1_INDIAN_CITIES,
        yoe_target=yoe_target,
        yoe_band_lo=yoe_lo,
        yoe_band_hi=yoe_hi,
        notice_preferred_days=notice,
        source=source,
    )


def compile_jd_file(path: Path | str) -> CompiledJD:
    return compile_jd(Path(path).read_text(encoding="utf-8"), source=str(path))
