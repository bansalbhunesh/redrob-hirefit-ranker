"""Precision/recall tests for the anachronism detector. Run: python experiments/test_anachronism.py
Proves it flags real impossibilities and does NOT false-positive on legit profiles."""
import sys
from pathlib import Path

sys.path.insert(0, "experiments")
from anachronism import is_anachronistic, violations


def sk(name, months):
    return {"name": name, "duration_months": months, "proficiency": "expert"}


def cand(skills=None, jobs=None):
    return {"skills": skills or [], "career_history": jobs or []}


POSITIVE = [  # must flag
    ("RAG 94mo (tech ~2020)", cand([sk("RAG", 94)])),
    ("LangChain 63mo (2022)", cand([sk("LangChain", 63)])),
    ("LlamaIndex 96mo (2022)", cand([sk("LlamaIndex", 96)])),
    ("Prompt Engineering 94mo (2021)", cand([sk("Prompt Engineering", 94)])),
    ("vLLM 60mo (2023, cap 48)", cand([sk("vLLM", 60)])),
    ("LangGraph 40mo (2024, cap 36)", cand([sk("LangGraph", 40)])),
    ("job ended 2017 mentions RAG", cand(jobs=[{"end_date": "2017-06-01", "is_current": False,
                                                "description": "Built a RAG pipeline for search", "company": "X"}])),
]

NEGATIVE = [  # must NOT flag (full-proof / no false positives)
    ("Python 240mo", cand([sk("Python", 240)])),
    ("SQL 180mo", cand([sk("SQL", 180)])),
    ("Transformers 90mo (excluded/old)", cand([sk("Transformers", 90)])),
    ("BERT 80mo (excluded/old)", cand([sk("BERT", 80)])),
    ("RAG 40mo (under cap)", cand([sk("RAG", 40)])),
    ("LangChain 50mo (under cap)", cand([sk("LangChain", 50)])),
    ("drag-and-drop UI 120mo (substring 'rag')", cand([sk("Drag-and-drop UI", 120)])),
    ("LoRaWAN 150mo (substring 'lora')", cand([sk("LoRaWAN", 150)])),
    ("current job since 2015 mentions RAG", cand(jobs=[{"end_date": None, "is_current": True,
                                                        "description": "We adopted RAG in 2023", "company": "Y"}])),
    ("completed job ended 2024 mentions RAG", cand(jobs=[{"end_date": "2024-01-01", "is_current": False,
                                                          "description": "Built RAG systems", "company": "Z"}])),
    ("empty candidate", cand()),
    ("malformed skill duration", cand([{"name": "RAG", "duration_months": None}])),
]


def main():
    fails = 0
    for name, c in POSITIVE:
        if not is_anachronistic(c):
            print(f"FAIL (missed)     : {name}"); fails += 1
        else:
            print(f"ok   flag         : {name}  -> {violations(c)[0]['type']}/{violations(c)[0]['tech']}")
    for name, c in NEGATIVE:
        if is_anachronistic(c):
            print(f"FAIL (false-pos)  : {name}  -> {violations(c)}"); fails += 1
        else:
            print(f"ok   clean        : {name}")
    print(f"\n{'ALL TESTS PASSED' if fails == 0 else str(fails)+' TEST(S) FAILED'} "
          f"({len(POSITIVE)} positive, {len(NEGATIVE)} negative controls)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
