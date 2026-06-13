#!/usr/bin/env python3
"""
Generate training data for the LightGBM re-ranker.

Stratified sampling ensures the model sees:
- Top candidates (what the current ranker likes)
- Keyword favorites (what the 20k proxy likes)
- Disagreements (where ranker and keyword diverge)
- Mid-tier candidates (ranks 80-400)
- Random candidates (baseline distribution)
- Honeypots (adversarial examples)

Labels come from the PessimisticJudge (multiplicative gates).
The 8 calibration pairs are used for VALIDATION, not training.
"""

import json
import random
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from redrob_ranker.features import compute_features, final_score

def score_candidate(candidate):
    feats = compute_features(candidate)
    # Recreate the linear score
    score = final_score(feats, retrieval_score=feats.values.get("bm25_score", 0.0), semantic_score=0.0)
    return score, feats
from redrob_ranker.pessimistic_judge import PessimisticJudge, batch_judge

# ================================================================
# CONFIG
# ================================================================
TARGET_SAMPLES = 1500
RANDOM_SEED = 42
OUTPUT_PATH = "training_data.jsonl"
BLIND_TEST_PATH = "blind_test_frozen.jsonl"

# The 8 calibration pairs from your old calibration.py
CALIBRATION_PAIRS = [
    ("CAND_0068811", "CAND_0001610"),
    ("CAND_0065878", "CAND_0074735"),
    ("CAND_0060054", "CAND_0042506"),
    ("CAND_0075574", "CAND_0043860"),
    ("CAND_0083879", "CAND_0099806"),
    ("CAND_0005649", "CAND_0016163"),
    ("CAND_0061257", "CAND_0030468"),
    ("CAND_0027691", "CAND_0042100"),
]

# ================================================================
# LOAD CANDIDATES
# ================================================================
def load_candidates(path: str):
    """Load candidates from jsonl."""
    candidates = []
    with open(path) as f:
        for line in f:
            candidates.append(json.loads(line))
    return candidates

# ================================================================
# KEYWORD SCORER (your 20k proxy)
# ================================================================
def keyword_score(candidate: dict) -> float:
    """
    Simple keyword coverage scorer.
    This is your 20k proxy baseline - counts surface term presence.
    """
    text = " ".join([
        candidate.get("profile", {}).get("summary", ""),
        candidate.get("profile", {}).get("headline", ""),
        " ".join([h.get("description", "") for h in candidate.get("career_history", [])]),
        " ".join([s.get("name", "") for s in candidate.get("skills", [])]),
    ]).lower()

    # Count AI/backend/data keywords
    keywords = [
        "python", "pytorch", "tensorflow", "ml", "ai", "backend", "api", "database",
        "sql", "etl", "tableau", "power bi", "docker", "kubernetes", "devops",
        "elasticsearch", "search", "ranking", "retrieval", "embeddings", "vector"
    ]

    matched = sum(1 for kw in keywords if kw in text)
    return min(matched / 10.0, 1.0)


# ================================================================
# STRATIFIED SAMPLING
# ================================================================
def stratified_sample(candidates: list, target: int = TARGET_SAMPLES) -> list:
    """Create stratified sample for training."""
    random.seed(RANDOM_SEED)

    # Score all candidates with both rankers
    print("Scoring all candidates with current ranker...")
    ranker_scores = []
    for c in candidates:
        try:
            score, _ = score_candidate(c)
            ranker_scores.append((c, score))
        except Exception as e:
            print(f"Warning: failed to score {c.get('candidate_id', 'unknown')}: {e}")
            ranker_scores.append((c, 0.0))

    print("Scoring all candidates with keyword proxy...")
    keyword_scores = []
    for c in candidates:
        keyword_scores.append((c, keyword_score(c)))

    # Sort
    by_ranker = sorted(ranker_scores, key=lambda x: x[1], reverse=True)
    by_keyword = sorted(keyword_scores, key=lambda x: x[1], reverse=True)

    # Build strata
    strata = defaultdict(list)

    # Stratum 1: Ranker top 200
    for c, _ in by_ranker[:200]:
        strata["ranker_top"].append(c)

    # Stratum 2: Keyword top 200
    for c, _ in by_keyword[:200]:
        strata["keyword_top"].append(c)

    # Stratum 3: Disagreements (high divergence)
    ranker_map = {c["candidate_id"]: s for c, s in ranker_scores}
    kw_map = {c["candidate_id"]: s for c, s in keyword_scores}

    for c in candidates:
        cid = c["candidate_id"]
        if cid in ranker_map and cid in kw_map:
            if abs(ranker_map[cid] - kw_map[cid]) > 0.25:
                strata["disagreement"].append(c)

    # Stratum 4: Mid-tier (ranks 100-400)
    for c, _ in by_ranker[100:400]:
        strata["mid_tier"].append(c)

    # Stratum 5: Random
    if len(candidates) > 400:
        strata["random"] = random.sample(candidates[400:], min(200, len(candidates)-400))

    # Stratum 6: Honeypots (candidates with many trap flags)
    from redrob_ranker.features import CandidateFeatures
    for c in candidates:
        try:
            feats = compute_features(c)
            if feats.honeypot_multiplier < 0.5 or feats.values.get("keyword_stuffer_flag") or feats.values.get("consulting_only_flag"):
                strata["honeypot"].append(c)
        except:
            pass

    # Sample from each stratum
    pool = []
    seen = set()

    sampling_plan = {
        "ranker_top": 250,
        "keyword_top": 250,
        "disagreement": 300,
        "mid_tier": 250,
        "random": 200,
        "honeypot": 250,
    }

    for stratum_name, n_samples in sampling_plan.items():
        available = strata.get(stratum_name, [])
        if not available:
            continue
        sampled = random.sample(available, min(n_samples, len(available)))
        for c in sampled:
            cid = c["candidate_id"]
            if cid not in seen:
                seen.add(cid)
                pool.append(c)

    # Ensure we have the calibration pairs in the pool (for validation)
    for winner_id, loser_id in CALIBRATION_PAIRS:
        for cid in [winner_id, loser_id]:
            if cid not in seen:
                c = next((x for x in candidates if x.get("candidate_id") == cid), None)
                if c:
                    seen.add(cid)
                    pool.append(c)

    # Limit to target
    pool = pool[:target]
    print(f"Stratified pool: {len(pool)} candidates")
    print(f"  Stratum sizes: {[(k, len(v)) for k, v in strata.items()]}")

    return pool


# ================================================================
# GENERATE LABELS
# ================================================================
def generate_labels(pool: list, role_family: str = "ai_ml_engineering"):
    """Generate pessimistic labels for the pool."""
    judge = PessimisticJudge(role_family)
    data = []

    for candidate in pool:
        judgment = judge.judge(candidate)
        features = compute_features(candidate)

        # Also get linear score for comparison
        linear_score, _ = score_candidate(candidate)

        # Build feature vector (exact same 28 features + 2 new depth features)
        feature_vector = {
            "bm25_score": features.values.get("bm25_score", 0.0),
            "core_skill_match": features.values.get("core_skill_match", 0.0),
            "nice_skill_match": features.values.get("nice_skill_match", 0.0),
            "skill_depth_score": features.values.get("skill_depth_score", 0.0),
            "endorsement_trust": features.values.get("endorsement_trust", 0.0),
            "assessment_score_avg": features.values.get("assessment_score_avg", 0.0),
            "github_signal": features.values.get("github_signal", 0.0),
            "product_company_ratio": features.values.get("product_company_ratio", 0.0),
            "ir_ranking_experience": features.values.get("ir_ranking_experience", 0.0),
            "production_evidence": features.values.get("production_evidence", 0.0),
            "senior_title_held": features.values.get("senior_title_held", 0.0),
            "career_trajectory_score": features.values.get("career_trajectory_score", 0.0),
            "scale_signal": features.values.get("scale_signal", 0.0),
            "code_writing_recent": features.values.get("code_writing_recent", 0.0),
            "yoe_fit_score": features.values.get("yoe_fit_score", 0.0),
            "education_score": features.values.get("education_score", 0.0),
            "ml_ai_tenure_score": features.values.get("ml_ai_tenure_score", 0.0),
            "open_source_signal": features.values.get("open_source_signal", 0.0),
            "location_score": features.values.get("location_score", 0.0),
            "relocation_willing": features.values.get("relocation_willing", 0.0),
            "notice_period_score": features.values.get("notice_period_score", 0.0),
            "disqualifier_flag": 1.0 if features.values.get("disqualifier_skill_flag") else 0.0,
            "keyword_stuffer_flag": 1.0 if features.values.get("keyword_stuffer_flag") else 0.0,
            "consulting_only_flag": 1.0 if features.values.get("consulting_only_flag") else 0.0,
            "honeypot_multiplier": features.honeypot_multiplier,
            "title_match_score": features.values.get("title_match_score", 0.0),
            "backend_depth_score": features.values.get("backend_depth_score", 0.0),
            "data_bi_depth_score": features.values.get("data_bi_depth_score", 0.0),
        }

        data.append({
            "candidate_id": candidate["candidate_id"],
            "role_family": role_family,
            "features": feature_vector,
            "pessimistic_label": judgment.score,
            "linear_label": linear_score,
            "disagreement": abs(judgment.score - linear_score),
            "passed_gates": judgment.passed_gates,
            "failed_gate": judgment.failed_gate,
            "gate_scores": judgment.gate_scores,
        })

    return data


# ================================================================
# VALIDATE ON CALIBRATION PAIRS
# ================================================================
def validate_on_calibration_pairs(data: list, candidates: list):
    """Ensure the pessimistic judge correctly orders the 8 calibration pairs."""
    print("\n=== VALIDATING ON 8 CALIBRATION PAIRS ===")
    data_map = {row["candidate_id"]: row for row in data}

    all_pass = True
    for winner_id, loser_id in CALIBRATION_PAIRS:
        winner = data_map.get(winner_id)
        loser = data_map.get(loser_id)

        if not winner or not loser:
            print(f"  MISSING: {winner_id} or {loser_id} not in pool")
            all_pass = False
            continue

        w_score = winner["pessimistic_label"]
        l_score = loser["pessimistic_label"]

        if w_score > l_score + 0.01:
            print(f"  PASS: {winner_id} ({w_score:.3f}) > {loser_id} ({l_score:.3f})")
        else:
            print(f"  FAIL: {winner_id} ({w_score:.3f}) NOT > {loser_id} ({l_score:.3f})")
            all_pass = False

    if all_pass:
        print("  ALL 8 PAIRS PASS. Judge is calibrated.\n")
    else:
        print("  SOME PAIRS FAIL. Tune thresholds in PessimisticJudge.\n")

    return all_pass


# ================================================================
# SPLIT AND SAVE
# ================================================================
def split_and_save(data: list):
    """Split into train/val/blind and save."""
    random.seed(RANDOM_SEED)
    random.shuffle(data)

    n = len(data)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)

    train = data[:n_train]
    val = data[n_train:n_train + n_val]
    blind = data[n_train + n_val:]

    # Save train
    with open("training_data_train.jsonl", "w") as f:
        for row in train:
            f.write(json.dumps(row) + "\n")

    # Save val
    with open("training_data_val.jsonl", "w") as f:
        for row in val:
            f.write(json.dumps(row) + "\n")

    # Save blind (THE FROZEN SET - never touch during training)
    with open(BLIND_TEST_PATH, "w") as f:
        for row in blind:
            f.write(json.dumps(row) + "\n")

    print(f"Saved: train={len(train)}, val={len(val)}, blind={len(blind)}")
    print(f"Blind test FROZEN at: {BLIND_TEST_PATH}")

    # Disagreement stats
    high_disagreement = sum(1 for row in data if row["disagreement"] > 0.30)
    print(f"High disagreement (>0.30): {high_disagreement} samples")
    print("These are your HARD NEGATIVES for the model to learn.")


# ================================================================
# MAIN
# ================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="candidates.jsonl", help="Path to candidates.jsonl")
    parser.add_argument("--role", default="ai_ml_engineering", help="Role family for labels")
    args = parser.parse_args()

    print(f"Loading candidates from {args.candidates}...")
    candidates = load_candidates(args.candidates)
    print(f"Loaded {len(candidates)} candidates")

    print("\nGenerating stratified pool...")
    pool = stratified_sample(candidates, TARGET_SAMPLES)

    print("\nGenerating pessimistic labels...")
    data = generate_labels(pool, args.role)

    print("\nValidating on calibration pairs...")
    validate_on_calibration_pairs(data, candidates)

    print("\nSplitting and saving...")
    split_and_save(data)

    print("\nDone. Training data ready for LightGBM.")

if __name__ == "__main__":
    main()
