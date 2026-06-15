"""Technology-anachronism honeypot detector — hardened, high-precision.

Catches the honeypot class where a profile claims to have used a technology for LONGER
THAN THE TECHNOLOGY HAS EXISTED. Two airtight checks:

  A. SKILL DURATION: a skill's `duration_months` exceeds the technology's maximum
     possible age (now - first_year) + slack.
  B. JOB MENTION: a *completed* job whose end-date year is strictly before the
     technology's first year, yet whose description names the technology.

Design for ZERO false positives:
  - `first_year` is the EARLIEST defensible origin (paper / first public release), so an
    early adopter is never wrongly flagged.
  - SLACK_MONTHS=12 extra grace on top of that.
  - Acronyms matched with word boundaries (no substring hits); multiword matched literally.
  - Only unambiguously-recent technologies are listed (transformers/BERT/GANs etc. are
    deliberately excluded — they are old enough that long tenures are legitimate).

Deterministic, dependency-free, edge-case safe. Experimental module (branch only); does
NOT modify the golden pipeline.
"""
from __future__ import annotations

import datetime as dt
import re

NOW = dt.date(2026, 6, 7)
SLACK_MONTHS = 12

# canonical_name -> (regex pattern, earliest defensible first year)
# years are conservative (paper / first release) to guarantee no false positives.
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
_COMPILED = {name: (re.compile(pat, re.IGNORECASE), yr) for name, (pat, yr) in _TECH.items()}


def _max_months(first_year: int) -> int:
    return (NOW.year - first_year) * 12 + SLACK_MONTHS


def _year(d) -> int | None:
    try:
        return dt.date.fromisoformat(str(d)[:10]).year
    except Exception:
        return None


def violations(candidate: dict) -> list[dict]:
    """Return airtight anachronism violations for a candidate (empty list = clean)."""
    out = []

    # Check A — skill claimed longer than the technology has existed.
    for s in candidate.get("skills", []) or []:
        name = str(s.get("name", "") or "")
        try:
            dur = float(s.get("duration_months", 0) or 0)
        except (TypeError, ValueError):
            dur = 0.0
        for tech, (rx, yr) in _COMPILED.items():
            if rx.search(name):
                cap = _max_months(yr)
                if dur > cap:
                    out.append({"type": "skill_duration", "tech": tech,
                                "claimed_months": dur, "max_months": cap,
                                "severity": round(dur / cap, 2)})
                break  # one tech per skill name

    # Check B — a COMPLETED job that ended before the tech existed yet names it.
    for j in candidate.get("career_history", []) or []:
        if j.get("is_current"):
            continue
        end_y = _year(j.get("end_date"))
        if end_y is None:
            continue
        desc = str(j.get("description", "") or "")
        if not desc:
            continue
        for tech, (rx, yr) in _COMPILED.items():
            if end_y < yr and rx.search(desc):
                out.append({"type": "job_predates_tech", "tech": tech,
                            "job_end_year": end_y, "tech_first_year": yr,
                            "company": j.get("company"), "severity": yr - end_y})
    return out


def is_anachronistic(candidate: dict) -> bool:
    return bool(violations(candidate))


def worst_severity(candidate: dict) -> float:
    """0.0 = clean; for skill_duration this is claimed/max (>1 = impossible)."""
    sev = [v["severity"] for v in violations(candidate) if v["type"] == "skill_duration"]
    return max(sev) if sev else (1.01 if is_anachronistic(candidate) else 0.0)
