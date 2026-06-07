"""Candidate text rendering and tokenization."""

from __future__ import annotations

import re
from typing import Iterable

from redrob_ranker.constants import IMPORTANT_PHRASES, SEMANTIC_CONCEPTS

TOKEN_RE = re.compile(r"[a-z0-9_+#.]+")


def norm(value: object) -> str:
    return str(value or "").strip()


def lower(value: object) -> str:
    return norm(value).lower()


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = TOKEN_RE.findall(lowered)
    for phrase in IMPORTANT_PHRASES:
        if phrase in lowered:
            tokens.append(phrase.replace("/", "_").replace(" ", "_"))
    return tokens


def join_nonempty(parts: Iterable[object], sep: str = " ") -> str:
    return sep.join(norm(p) for p in parts if norm(p))


def semantic_concept_markers(text: str) -> list[str]:
    lowered = lower(text)
    markers: list[str] = []
    for concept, aliases in SEMANTIC_CONCEPTS.items():
        if any(lower(alias) in lowered for alias in aliases):
            markers.append(f"concept_{concept}")
    return markers


def candidate_text(candidate: dict) -> str:
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

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
