"""Candidate text rendering and tokenization."""

from __future__ import annotations

import re
from typing import Iterable

from redrob_ranker.constants import IMPORTANT_PHRASES, SEMANTIC_CONCEPTS

TOKEN_RE = re.compile(r"[a-z0-9_+#.]+")
LOWERED_IMPORTANT_PHRASES = tuple(phrase.lower() for phrase in IMPORTANT_PHRASES)
LOWERED_SEMANTIC_CONCEPTS = {
    concept: tuple(str(alias).lower() for alias in aliases)
    for concept, aliases in SEMANTIC_CONCEPTS.items()
}
# One alternation per concept: search() is true exactly when any alias occurs
# as a plain substring, so each concept needs one pass over the text instead
# of one pass per alias.
_CONCEPT_PATTERNS = {
    concept: re.compile("|".join(re.escape(alias) for alias in aliases))
    for concept, aliases in LOWERED_SEMANTIC_CONCEPTS.items()
}


def norm(value: object) -> str:
    return str(value or "").strip()


def lower(value: object) -> str:
    return norm(value).lower()


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with",
    "i", "you", "they", "we", "this", "or", "but", "not", "what", "all", "were", "when",
    "we", "there", "can", "an", "your", "which", "their", "said", "if", "do", "will",
    "each", "about", "how", "up", "out", "them", "then", "she", "many", "some", "so",
    "these", "would", "other", "into", "has", "more", "her", "two", "like", "him", "see",
    "time", "could", "no", "make", "than", "first", "been", "its", "who", "now", "people",
    "my", "made", "over", "down", "only", "way", "find", "use", "may", "water", "long",
    "little", "very", "after", "words", "called", "just", "where", "most", "know"
}

def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = [t for t in TOKEN_RE.findall(lowered) if t not in STOPWORDS]
    for phrase in LOWERED_IMPORTANT_PHRASES:
        if phrase in lowered:
            tokens.append(phrase.replace("/", "_").replace(" ", "_"))
    return tokens


def join_nonempty(parts: Iterable[object], sep: str = " ") -> str:
    normalized = [norm(part) for part in parts]
    return sep.join(part for part in normalized if part)


def semantic_concept_markers(text: str) -> list[str]:
    lowered = lower(text)
    markers: list[str] = []
    for concept, pattern in _CONCEPT_PATTERNS.items():
        if pattern.search(lowered):
            markers.append(f"concept_{concept}")
    return markers


def candidate_text(candidate: dict) -> str:
    # `or` guards: demo upload paths can carry explicit nulls for these keys
    # (key present, value None); identical output for well-formed records.
    profile = candidate.get("profile") or {}
    career = candidate.get("career_history") or []
    education = candidate.get("education") or []
    skills = candidate.get("skills") or []
    signals = candidate.get("redrob_signals") or {}

    sections: list[str] = []
    sections.append(
        join_nonempty(
            [
                profile.get("current_title"),
                profile.get("headline"),
                profile.get("summary"),
                profile.get("current_industry"),
                profile.get("location"),
                profile.get("country"),
            ]
        )
    )

    for job in career:
        sections.append(
            join_nonempty(
                [
                    job.get("title"),
                    job.get("company"),
                    job.get("industry"),
                    job.get("description"),
                    f"{job.get('duration_months', 0)} months",
                ]
            )
        )

    skill_text = []
    for skill in skills:
        skill_text.append(
            f"{skill.get('name')} {skill.get('proficiency')} "
            f"{skill.get('duration_months', 0)} months endorsements {skill.get('endorsements', 0)}"
        )
    sections.append(" ".join(skill_text))

    for edu in education:
        sections.append(
            join_nonempty(
                [
                    edu.get("degree"),
                    edu.get("field_of_study"),
                    edu.get("institution"),
                    edu.get("tier"),
                ]
            )
        )

    sections.append(
        join_nonempty(
            [
                f"open_to_work {signals.get('open_to_work_flag')}",
                f"response_rate {signals.get('recruiter_response_rate')}",
                f"github_activity {signals.get('github_activity_score')}",
                f"notice_period {signals.get('notice_period_days')}",
                signals.get("preferred_work_mode"),
            ]
        )
    )
    rendered = "\n".join(s for s in sections if s)
    markers = semantic_concept_markers(rendered)
    if markers:
        rendered = f"{rendered}\n{' '.join(markers)}"
    return rendered
