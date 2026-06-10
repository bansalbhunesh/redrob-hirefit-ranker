#!/usr/bin/env python3
"""Generate a size-faithful synthetic 100K candidate pool for runtime benchmarking.

NOT competition data — a deterministic lookalike matching the released pool's
schema and per-candidate byte budget (~4.9 KB avg, 100K records ~490 MB), so a
clean cloud machine can measure worst-case runtime without the private dataset
ever leaving the dev machine. Scores/rankings on this pool are meaningless;
only wall time and byte-determinism are.

Usage: python scripts/generate_loadtest_pool.py --n 100000 --out pool.jsonl
"""

from __future__ import annotations

import argparse
import json
import random

TITLES = ["Software Engineer", "Machine Learning Engineer", "Data Scientist",
          "Senior AI Engineer", "Backend Engineer", "Data Engineer", "Business Analyst",
          "DevOps Engineer", "Product Manager", "Marketing Manager"]
COMPANIES = ["Hooli", "Globex Inc", "Initech", "Acme Corp", "Pied Piper", "TCS",
             "Infosys", "Flipkart", "Swiggy", "Razorpay", "Stark Industries", "Netflix"]
SKILLS = ["Python", "SQL", "Spark", "TensorFlow", "PyTorch", "Docker", "Kubernetes",
          "AWS", "Airflow", "Kafka", "Elasticsearch", "BM25", "Faiss", "LangChain",
          "Java", "Go", "React", "Pandas", "Scikit-learn", "MLOps", "Redis", "GCP"]
CITIES = ["Bengaluru", "Mumbai", "Hyderabad", "Pune", "Delhi", "Chennai", "Noida"]
WORDS = ("built deployed scaled production retrieval ranking recommendation search "
         "pipeline latency throughput embedding vector model feature evaluation "
         "system data platform service api batch realtime experiment metrics ndcg "
         "personalization relevance machine learning engineer team product users "
         "millions requests architecture microservices optimization infrastructure").split()


def sentence(rng: random.Random, n: int) -> str:
    return " ".join(rng.choice(WORDS) for _ in range(n)).capitalize() + "."


def candidate(rng: random.Random, i: int) -> dict:
    yoe = round(rng.uniform(1, 16), 1)
    n_jobs = rng.randint(2, 6)
    n_skills = rng.randint(8, 20)
    title = rng.choice(TITLES)
    summary = (f"{title} with {yoe} years of experience. " +
               " ".join(sentence(rng, rng.randint(14, 24)) for _ in range(rng.randint(3, 6))))
    career = [{
        "title": rng.choice(TITLES),
        "company": rng.choice(COMPANIES),
        "industry": rng.choice(["Software", "E-commerce", "Fintech", "Consulting"]),
        "duration_months": rng.randint(6, 60),
        "is_current": j == 0,
        "start_date": f"{rng.randint(2012, 2024)}-{rng.randint(1, 12):02d}-01",
        "end_date": None if j == 0 else f"{rng.randint(2015, 2026)}-{rng.randint(1, 12):02d}-01",
        "description": " ".join(sentence(rng, rng.randint(16, 28)) for _ in range(rng.randint(2, 4))),
    } for j in range(n_jobs)]
    skills = [{
        "name": rng.choice(SKILLS),
        "proficiency": rng.choice(["beginner", "intermediate", "advanced", "expert"]),
        "duration_months": rng.randint(0, 72),
        "endorsements": rng.randint(0, 60),
    } for _ in range(n_skills)]
    return {
        # CAND_9xxxxxx: validator-format-compliant, disjoint from the real
        # pool's CAND_0000001..0100000 range.
        "candidate_id": f"CAND_{9000000 + i:07d}",
        "profile": {
            "anonymized_name": f"Candidate {i}",
            "current_title": title,
            "current_company": rng.choice(COMPANIES),
            "headline": f"{title} | " + ", ".join(rng.sample(SKILLS, 3)),
            "summary": summary,
            "years_of_experience": yoe,
            "location": rng.choice(CITIES),
            "country": "India",
            "current_industry": "Software",
        },
        "career_history": career,
        "skills": skills,
        "education": [{
            "degree": rng.choice(["B.Tech", "M.Tech", "M.Sc", "Ph.D"]),
            "field_of_study": rng.choice(["Computer Science", "Machine Learning", "Statistics"]),
            "institution": f"Institute {rng.randint(1, 400)}",
            "tier": rng.choice(["tier_1", "tier_2", "tier_3"]),
            "start_year": 2008, "end_year": 2012,
        }],
        "certifications": [], "languages": ["English"],
        "redrob_signals": {
            "open_to_work_flag": rng.random() < 0.5,
            "recruiter_response_rate": round(rng.random(), 2),
            "avg_response_time_hours": rng.randint(1, 200),
            "interview_completion_rate": round(rng.random(), 2),
            "offer_acceptance_rate": round(rng.random(), 2),
            "profile_completeness_score": rng.randint(20, 100),
            "last_active_date": f"2026-{rng.randint(1, 6):02d}-{rng.randint(1, 28):02d}",
            "notice_period_days": rng.choice([15, 30, 60, 90, 120]),
            "github_activity_score": rng.randint(0, 100),
            "profile_views_received_30d": rng.randint(0, 200),
            "applications_submitted_30d": rng.randint(0, 30),
            "saved_by_recruiters_30d": rng.randint(0, 25),
            "search_appearance_30d": rng.randint(0, 500),
            "endorsements_received": rng.randint(0, 80),
            "verified_email": True, "verified_phone": rng.random() < 0.7,
            "linkedin_connected": rng.random() < 0.8,
            "willing_to_relocate": rng.random() < 0.4,
            "preferred_work_mode": rng.choice(["remote", "hybrid", "onsite"]),
            "skill_assessment_scores": {},
            "expected_salary_range_inr_lpa": {"min": 20, "max": 45},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--out", default="pool.jsonl")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    total = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for i in range(args.n):
            line = json.dumps(candidate(rng, i), ensure_ascii=False)
            fh.write(line + "\n")
            total += len(line) + 1
    print(f"wrote {args.n} candidates, {total / 1e6:.0f} MB -> {args.out}")


if __name__ == "__main__":
    main()
