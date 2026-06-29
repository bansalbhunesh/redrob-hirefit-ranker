"""High-precision technology-anachronism checks used by dominant-v4.

The detector is deliberately conservative: only clearly recent technologies
are listed, origin years use the earliest defensible public date, and claimed
skill duration receives a full year of grace.  It contains no candidate IDs or
dataset-specific text fingerprints.
"""

from __future__ import annotations

import datetime as dt
import re

NOW = dt.date(2026, 6, 7)
SLACK_MONTHS = 12

_TECH = {
    "RAG": (r"\brag\b|retrieval[- ]augmented", 2020),
    "LangChain": (r"\blangchain\b", 2022),
    "LlamaIndex": (r"\bllama[- ]?index\b|\bgpt[- ]?index\b", 2022),
    "LangGraph": (r"\blanggraph\b", 2024),
    "ChatGPT": (r"\bchatgpt\b", 2022),
    "GPT-4": (r"\bgpt[- ]?4\b", 2023),
    "GPT-3": (r"\bgpt[- ]?3\b", 2020),
    "GPT-3.5": (r"\bgpt[- ]?3\.5\b", 2022),
    "DALL-E": (r"\bdall[- ]?e\b", 2021),
    "Stable Diffusion": (r"stable diffusion", 2022),
    "Midjourney": (r"\bmidjourney\b", 2022),
    "Whisper": (r"\bwhisper\b", 2022),
    "LoRA": (r"\blora\b", 2021),
    "QLoRA": (r"\bqlora\b", 2023),
    "PEFT": (r"\bpeft\b", 2022),
    "vLLM": (r"\bvllm\b", 2023),
    "Ollama": (r"\bollama\b", 2023),
    "DSPy": (r"\bdspy\b", 2023),
    "AutoGen": (r"\bautogen\b", 2023),
    "CrewAI": (r"\bcrewai\b", 2023),
    "Claude (LLM)": (r"\bclaude\b", 2023),
    "Gemini (LLM)": (r"\bgemini\b", 2023),
    "LLaMA": (r"\bllama\b(?![- ]?index)", 2023),
    "Mistral": (r"\bmistral\b|\bmixtral\b", 2023),
    "Pinecone": (r"\bpinecone\b", 2019),
    "Weaviate": (r"\bweaviate\b", 2019),
    "Qdrant": (r"\bqdrant\b", 2021),
    "Chroma DB": (r"\bchroma\s?db\b|\bchromadb\b", 2022),
    "Milvus": (r"\bmilvus\b", 2019),
    "vector database": (r"vector (database|db|search|store)", 2019),
    "Sentence Transformers": (r"sentence[- ]?transformers?\b|\bsbert\b", 2019),
    "Prompt Engineering": (r"prompt engineering", 2021),
    "InstructGPT": (r"\binstructgpt\b", 2022),
}
_COMPILED = {
    name: (re.compile(pattern, re.IGNORECASE), year)
    for name, (pattern, year) in _TECH.items()
}


def _max_months(first_year: int) -> int:
    return (NOW.year - first_year) * 12 + SLACK_MONTHS


def _year(value: object) -> int | None:
    try:
        return dt.date.fromisoformat(str(value)[:10]).year
    except (TypeError, ValueError):
        return None


def violations(candidate: dict) -> list[dict]:
    """Return conservative temporal violations (empty means no violation)."""

    found: list[dict] = []
    for skill in candidate.get("skills", []) or []:
        name = str(skill.get("name", "") or "")
        try:
            duration = float(skill.get("duration_months", 0) or 0)
        except (TypeError, ValueError):
            duration = 0.0
        for technology, (pattern, first_year) in _COMPILED.items():
            if pattern.search(name):
                maximum = _max_months(first_year)
                if duration > maximum:
                    found.append(
                        {
                            "type": "skill_duration",
                            "tech": technology,
                            "claimed_months": duration,
                            "max_months": maximum,
                            "severity": round(duration / maximum, 2),
                        }
                    )
                break

    for job in candidate.get("career_history", []) or []:
        if job.get("is_current"):
            continue
        end_year = _year(job.get("end_date"))
        if end_year is None:
            continue
        description = str(job.get("description", "") or "")
        if not description:
            continue
        for technology, (pattern, first_year) in _COMPILED.items():
            if end_year < first_year and pattern.search(description):
                found.append(
                    {
                        "type": "job_predates_tech",
                        "tech": technology,
                        "job_end_year": end_year,
                        "tech_first_year": first_year,
                        "company": job.get("company"),
                        "severity": first_year - end_year,
                    }
                )
    return found


def worst_severity(candidate: dict) -> float:
    """Return 0 for clean profiles and >1 for a temporal contradiction."""

    found = violations(candidate)
    skill_severity = [
        item["severity"] for item in found if item["type"] == "skill_duration"
    ]
    return max(skill_severity) if skill_severity else (1.01 if found else 0.0)
