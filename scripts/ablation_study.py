#!/usr/bin/env python3
"""ConFit v2: Ablation Studies + Statistical Rigor
Generates the final performance table with bootstrap CIs for all ranking layers.
"""

import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def dcg_at_k(r, k):
    r = np.asarray(r, dtype=float)[:k]
    if r.size:
        return np.sum((2**r - 1) / np.log2(np.arange(2, r.size + 2)))
    return 0.

def ndcg_at_k(r, k, ground_truth):
    dcg_max = dcg_at_k(sorted(ground_truth, reverse=True), k)
    if not dcg_max:
        return 0.
    return dcg_at_k(r, k) / dcg_max

def bootstrap_ci(pred_scores, true_scores, k=10, n_resamples=1000, ci=95):
    """Computes bootstrap confidence interval for NDCG@10."""
    n = len(true_scores)
    metrics = []
    
    indices = np.arange(n)
    for _ in range(n_resamples):
        sample_idx = np.random.choice(indices, size=n, replace=True)
        samp_preds = [pred_scores[i] for i in sample_idx]
        samp_true = [true_scores[i] for i in sample_idx]
        
        # Sort sample
        combined = list(zip(samp_preds, samp_true))
        combined.sort(key=lambda x: x[0], reverse=True)
        r = [x[1] for x in combined]
        
        val = ndcg_at_k(r, k, samp_true)
        metrics.append(val)
        
    lower = np.percentile(metrics, (100 - ci) / 2)
    upper = np.percentile(metrics, 100 - (100 - ci) / 2)
    return np.mean(metrics), lower, upper

def main():
    frozen_path = ROOT / "blind_labels_frozen.jsonl"
    if not frozen_path.exists():
        print(f"Error: {frozen_path} missing.")
        sys.exit(1)
        
    labels = {}
    with open(frozen_path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            labels[d["candidate_id"]] = d["consensus_label"]
            
    sys.path.insert(0, str(ROOT / "src"))
    from redrob_ranker.features import compute_features
    from redrob_ranker.io import iter_candidates
    from redrob_ranker.moe_scorer import get_moe_scorer
    
    moe = get_moe_scorer()
    cands_path = ROOT / "candidates.jsonl"
    
    # Evaluate over blind labels
    blind_cands = []
    for c in iter_candidates(cands_path):
        if c["candidate_id"] in labels:
            blind_cands.append(c)
            
    # We will compute 5 sets of scores
    scores_bm25 = []
    scores_hand = []
    scores_depth = []
    scores_hyre = []
    scores_mmoe = []
    ground_truth = []
    
    # A mock JD text for the MoE routing
    jd_text = "Backend Engineer python django postgres"
    
    for c in blind_cands:
        cid = c["candidate_id"]
        true_score = labels[cid]
        ground_truth.append(true_score)
        
        feats = compute_features(c)
        v = feats.values
        
        # 1. BM25 Only (using mock or generic baseline)
        s1 = v.get("core_skill_match", 0.0)
        scores_bm25.append(s1)
        
        # 2. +Hand-tuned
        s2 = s1 + v.get("nice_skill_match", 0.0) * 0.5 + v.get("production_evidence", 0.0) * 1.5
        scores_hand.append(s2)
        
        # 3. +Depth scoring
        s3 = s2 + v.get("skill_depth_score", 0.0) * 2.0
        scores_depth.append(s3)
        
        # 4. +HyRE
        s4 = s3 + v.get("hyre_similarity", 0.0) * 1.0
        scores_hyre.append(s4)
        
    # 5. +MMoE
    # Construct feature matrix for MMoE
    features_list = []
    for c in blind_cands:
        feats = compute_features(c)
        v = feats.values
        
        # Hardcode order matching the 29 INPUT_DIM
        fnames = [
            "core_skill_match", "jd_keyword_coverage_score", "nice_skill_match",
            "skill_depth_score", "endorsement_trust", "assessment_score_avg",
            "disqualifier_skill_flag", "keyword_stuffer_flag", "github_signal",
            "product_company_ratio", "consulting_only_flag", "ir_ranking_experience",
            "production_evidence", "title_match_score", "senior_title_held",
            "career_trajectory_score", "scale_signal", "code_writing_recent",
            "yoe_fit_score", "education_score", "ml_ai_tenure_score",
            "open_source_signal", "availability_score", "engagement_score",
            "responsiveness_score", "interview_reliability", "profile_quality",
            "notice_period_score", "location_score", "relocation_willing",
            "backend_depth_score", "data_bi_depth_score", "hyre_similarity"
        ][:29] # Cap at 29
        
        vec = [v.get(fn, 0.0) for fn in fnames]
        features_list.append(vec)
        
    X_mmoe = np.array(features_list)
    scores_mmoe = moe.score_candidates(jd_text, X_mmoe)
    
    # Calculate Base Metrics
    ablations = [
        ("BM25 only", scores_bm25),
        ("+Hand-tuned", scores_hand),
        ("+Depth scoring", scores_depth),
        ("+HyRE", scores_hyre),
        ("+MMoE", scores_mmoe)
    ]
    
    print("Ablation Study Results (1000 resamples, 95% CI)\n")
    print("| Model | NDCG@10 | Pearson | Delta | 95% CI |")
    print("|-------|---------|---------|-------|--------|")
    
    baseline_ndcg = 0.0
    for i, (name, preds) in enumerate(ablations):
        # Sort and NDCG
        comb = list(zip(preds, ground_truth))
        comb.sort(key=lambda x: x[0], reverse=True)
        r = [x[1] for x in comb]
        
        ndcg = ndcg_at_k(r, 10, ground_truth)
        pearson = np.corrcoef(preds, ground_truth)[0, 1]
        
        mean_ndcg, ci_lower, ci_upper = bootstrap_ci(preds, ground_truth)
        
        if i == 0:
            delta_str = "—"
            baseline_ndcg = ndcg
        else:
            delta = ndcg - baseline_ndcg
            delta_str = f"+{delta:.4f}"
            baseline_ndcg = ndcg # update baseline to previous
            
        print(f"| {name} | {ndcg:.4f} | {pearson:.4f} | {delta_str} | [{ci_lower:.4f}, {ci_upper:.4f}] |")

if __name__ == "__main__":
    main()
