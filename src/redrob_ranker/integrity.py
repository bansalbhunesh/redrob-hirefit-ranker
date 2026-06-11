"""Adversarial resume integrity checks.

These checks are intentionally lightweight and deterministic. They do not try to
prove fraud; they surface text patterns that should require manual review in a
hiring workflow.
"""

from __future__ import annotations

import re


INVISIBLE_CONTROL_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
PROMPT_INJECTION_RE = re.compile(
    r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+"
    r"(instructions|prompts|rules)|"
    r"system\s+prompt|developer\s+message|you\s+are\s+chatgpt|"
    r"rank\s+me\s+(first|top)|give\s+me\s+(rank|score)\s*(1|one|100)",
    re.IGNORECASE,
)
KEYWORD_BLOCK_RE = re.compile(
    r"\b(python|rag|llm|embedding|embeddings|vector|search|ranking|ranker|"
    r"faiss|milvus|qdrant|langchain|retrieval)\b",
    re.IGNORECASE,
)
PROMPT_PREFILTER = (
    "ignore", "disregard", "forget", "system prompt", "developer message",
    "chatgpt", "rank me", "score 100", "score one", "give me score",
)
KEYWORD_MARKERS = (
    "python", "rag", "llm", "embedding", "embeddings", "vector", "search",
    "ranking", "ranker", "faiss", "milvus", "qdrant", "langchain", "retrieval",
)


def integrity_flags(text: str) -> list[str]:
    raw = str(text or "")
    lowered = raw.lower()
    flags: list[str] = []

    if INVISIBLE_CONTROL_RE.search(raw):
        flags.append("hidden_text_control_chars")
    if any(marker in lowered for marker in PROMPT_PREFILTER) and PROMPT_INJECTION_RE.search(lowered):
        flags.append("prompt_injection_text")

    keyword_counts = []
    total_keyword_hits = 0
    for marker in KEYWORD_MARKERS:
        count = lowered.count(marker)
        if count:
            keyword_counts.append(count)
            total_keyword_hits += count
    if total_keyword_hits >= 60:
        unique_ratio = len(keyword_counts) / max(1, total_keyword_hits)
        if unique_ratio <= 0.35:
            flags.append("repeated_keyword_block")

    return flags
