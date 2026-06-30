#!/usr/bin/env python3
"""
Generates a zero-dependency, single-file glassmorphic HTML dashboard.
Merges JSONL candidate data with CSV submission results for offline demo.
"""

import argparse
import csv
import json
import os
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a stunning glassmorphic demo.html from candidates and submission."
    )
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--submission", required=True, help="Path to submission CSV")
    parser.add_argument("--out", default="demo.html", help="Output HTML file path")
    parser.add_argument("--title", default="Redrob HireFit Ranker", help="Dashboard title")
    return parser.parse_args()


def extract_candidate_payload(candidate: dict, submission_row: dict) -> dict:
    """Build a rich UI payload from candidate data + submission row."""
    prof = candidate.get("profile", {})
    redrob = candidate.get("redrob_signals", {})
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    career = candidate.get("career_history", [])
    certs = candidate.get("certifications", [])
    langs = candidate.get("languages", [])

    reasoning = submission_row.get("reasoning", "")
    score = float(submission_row.get("score", 0))
    rank = int(submission_row.get("rank", 0))

    # Honeypot detection
    honeypot_flag = "honeypot" in reasoning.lower()
    honeypot_reasons = []
    if honeypot_flag:
        hp_keywords = [
            "impossible timeline", "expert-zero-duration", "multiple current jobs",
            "salary inversion", "education impossibility", "endorsement inflation",
            "title-description contradiction", "skill-duration paradox"
        ]
        for kw in hp_keywords:
            if kw.lower() in reasoning.lower():
                honeypot_reasons.append(kw.replace("-", " ").title())
        if not honeypot_reasons:
            honeypot_reasons.append("Honeypot Detected")

    # Tier
    tier = "standard"
    if rank == 1:
        tier = "gold"
    elif rank == 2:
        tier = "silver"
    elif rank == 3:
        tier = "bronze"
    elif honeypot_flag:
        tier = "honeypot"

    # Behavioral
    behavioral = {
        "profile_completeness": redrob.get("profile_completeness_score", 0),
        "open_to_work": redrob.get("open_to_work_flag", False),
        "response_rate": redrob.get("recruiter_response_rate", 0),
        "avg_response_time": redrob.get("avg_response_time_hours", 0),
        "interview_completion": redrob.get("interview_completion_rate", 0),
        "offer_acceptance": redrob.get("offer_acceptance_rate", 0),
        "github_activity": redrob.get("github_activity_score", 0),
        "saved_by_recruiters": redrob.get("saved_by_recruiters_30d", 0),
        "profile_views": redrob.get("profile_views_received_30d", 0),
        "notice_period": redrob.get("notice_period_days", 0),
        "verified_email": redrob.get("verified_email", False),
        "verified_phone": redrob.get("verified_phone", False),
        "connection_count": redrob.get("connection_count", 0),
        "endorsements": redrob.get("endorsements_received", 0),
        "preferred_work_mode": redrob.get("preferred_work_mode", "unknown"),
        "willing_to_relocate": redrob.get("willing_to_relocate", False),
    }

    # Timeline
    timeline = []
    for job in career:
        timeline.append({
            "company": job.get("company", "Unknown"),
            "title": job.get("title", "Unknown"),
            "start": job.get("start_date", ""),
            "end": job.get("end_date", "Present"),
            "duration_months": job.get("duration_months", 0),
            "is_current": job.get("is_current", False),
            "industry": job.get("industry", "Unknown"),
            "company_size": job.get("company_size", "Unknown"),
        })

    # Skills
    skills_cloud = []
    for sk in skills:
        skills_cloud.append({
            "name": sk.get("name", "Unknown"),
            "proficiency": sk.get("proficiency", "unknown"),
            "endorsements": sk.get("endorsements", 0),
            "duration_months": sk.get("duration_months", 0),
        })

    # Education
    edu_list = []
    for ed in education:
        edu_list.append({
            "institution": ed.get("institution", "Unknown"),
            "degree": ed.get("degree", "Unknown"),
            "field": ed.get("field_of_study", "Unknown"),
            "start": ed.get("start_year", ""),
            "end": ed.get("end_year", ""),
            "grade": ed.get("grade", ""),
            "tier": ed.get("tier", "unknown"),
        })

    return {
        "candidate_id": candidate.get("candidate_id", "Unknown"),
        "rank": rank,
        "score": round(score, 4),
        "tier": tier,
        "honeypot_flag": honeypot_flag,
        "honeypot_reasons": honeypot_reasons,
        "reasoning": reasoning,
        "behavioral": behavioral,
        "profile": {
            "name": prof.get("anonymized_name", "Unknown"),
            "headline": prof.get("headline", ""),
            "summary": prof.get("summary", ""),
            "title": prof.get("current_title", "Unknown"),
            "company": prof.get("current_company", "Unknown"),
            "company_size": prof.get("current_company_size", "Unknown"),
            "industry": prof.get("current_industry", "Unknown"),
            "location": prof.get("location", "Unknown"),
            "country": prof.get("country", "Unknown"),
            "yoe": float(prof.get("years_of_experience", 0.0)),
        },
        "timeline": timeline,
        "skills": skills_cloud,
        "education": edu_list,
        "certifications": [c.get("name", "Unknown") for c in certs],
        "languages": [{"language": l.get("language", ""), "proficiency": l.get("proficiency", "")} for l in langs],
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__</title>
  <style>
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
    :root {
      --bg-deep: #030712;
      --bg-panel: rgba(15, 23, 42, 0.65);
      --bg-card: rgba(30, 41, 59, 0.5);
      --border-glass: rgba(255, 255, 255, 0.08);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-cyan: #06b6d4;
      --accent-purple: #a855f7;
      --accent-gold: #fbbf24;
      --accent-silver: #c0c0c0;
      --accent-bronze: #cd7f32;
      --accent-red: #f87171;
      --accent-green: #4ade80;
      --glow-cyan: rgba(6, 182, 212, 0.3);
      --glow-purple: rgba(168, 85, 247, 0.3);
      --glow-gold: rgba(251, 191, 36, 0.2);
      --radius: 16px;
      --radius-sm: 8px;
      --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-deep);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
      line-height: 1.5;
    }
    .ambient-bg {
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(ellipse 80% 50% at 20% 40%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
        radial-gradient(ellipse 60% 40% at 80% 60%, rgba(168, 85, 247, 0.12) 0%, transparent 50%),
        radial-gradient(ellipse 50% 30% at 50% 100%, rgba(6, 182, 212, 0.08) 0%, transparent 50%);
    }
    .ambient-bg::after {
      content: ''; position: absolute; inset: 0;
      background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
      opacity: 0.3;
    }
    .header {
      position: sticky; top: 0; z-index: 100;
      background: rgba(3, 7, 18, 0.7);
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      border-bottom: 1px solid var(--border-glass);
      padding: 16px 24px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .header-brand { display: flex; align-items: center; gap: 12px; }
    .header-brand .logo {
      width: 40px; height: 40px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      border-radius: 10px; display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 18px;
      box-shadow: 0 0 20px var(--glow-cyan);
    }
    .header-brand h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }
    .header-brand .badge {
      font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px;
      background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan);
      border: 1px solid rgba(6, 182, 212, 0.3);
    }
    .main {
      position: relative; z-index: 1;
      max-width: 1400px; margin: 0 auto; padding: 24px;
      display: grid; grid-template-columns: 1fr 380px; gap: 24px;
    }
    @media (max-width: 1100px) { .main { grid-template-columns: 1fr; } }
    .glass-panel {
      background: var(--bg-panel);
      backdrop-filter: blur(16px) saturate(150%);
      -webkit-backdrop-filter: blur(16px) saturate(150%);
      border: 1px solid var(--border-glass);
      border-radius: var(--radius); padding: 20px;
      transition: var(--transition);
    }
    .glass-panel:hover { border-color: rgba(255, 255, 255, 0.12); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); }
    .panel-title {
      font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;
      color: var(--text-secondary); margin-bottom: 16px;
      display: flex; align-items: center; gap: 8px;
    }
    .metrics-grid {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;
    }
    @media (max-width: 900px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }
    .metric-card {
      background: var(--bg-card); backdrop-filter: blur(12px);
      border: 1px solid var(--border-glass); border-radius: var(--radius);
      padding: 20px; position: relative; overflow: hidden;
      transition: var(--transition); transform: translateZ(0);
    }
    .metric-card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
      opacity: 0.6; transition: var(--transition);
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5); }
    .metric-card:hover::before { opacity: 1; }
    .metric-card .value {
      font-size: 32px; font-weight: 800;
      background: linear-gradient(135deg, var(--text-primary), var(--text-secondary));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      line-height: 1.2;
    }
    .metric-card .label {
      font-size: 12px; font-weight: 500; color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;
    }
    .metric-card .change { font-size: 12px; font-weight: 600; margin-top: 8px; }
    .metric-card .change.positive { color: var(--accent-green); }
    .metric-card .change.negative { color: var(--accent-red); }
    .metric-card.glow-cyan { box-shadow: 0 0 30px var(--glow-cyan); animation: pulseCyan 4s infinite ease-in-out; }
    .metric-card.glow-purple { box-shadow: 0 0 30px var(--glow-purple); animation: pulsePurple 4s infinite ease-in-out reverse; }
    @keyframes pulseCyan { 0%, 100% { box-shadow: 0 0 15px var(--glow-cyan); } 50% { box-shadow: 0 0 35px var(--glow-cyan); } }
    @keyframes pulsePurple { 0%, 100% { box-shadow: 0 0 15px var(--glow-purple); } 50% { box-shadow: 0 0 35px var(--glow-purple); } }

    .pipeline {
      display: flex; align-items: center; gap: 8px; padding: 16px;
      overflow-x: auto; margin-bottom: 24px;
    }
    .pipeline::-webkit-scrollbar { height: 4px; }
    .pipeline::-webkit-scrollbar-track { background: transparent; }
    .pipeline::-webkit-scrollbar-thumb { background: var(--border-glass); border-radius: 2px; }
    .pipeline-node {
      display: flex; flex-direction: column; align-items: center; gap: 6px;
      padding: 10px 16px; border-radius: var(--radius-sm); background: var(--bg-card);
      border: 1px solid var(--border-glass); min-width: 80px; position: relative;
    }
    .pipeline-node .icon { font-size: 20px; }
    .pipeline-node .name { font-size: 11px; font-weight: 600; color: var(--text-secondary); text-align: center; white-space: nowrap; }
    .pipeline-node .count { font-size: 10px; font-weight: 700; color: var(--text-muted); background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; }
    .pipeline-arrow { color: var(--text-muted); font-size: 14px; flex-shrink: 0; }

    .filter-bar {
      display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;
    }
    .filter-btn {
      padding: 8px 16px; border: 1px solid var(--border-glass); border-radius: var(--radius-sm);
      background: var(--bg-card); color: var(--text-secondary);
      font-size: 13px; font-weight: 500; cursor: pointer; transition: var(--transition);
    }
    .filter-btn:hover { border-color: var(--accent-cyan); color: var(--text-primary); }
    .filter-btn.active { background: rgba(6, 182, 212, 0.15); border-color: var(--accent-cyan); color: var(--accent-cyan); }
    .search-box {
      flex: 1; min-width: 200px; padding: 8px 14px;
      border: 1px solid var(--border-glass); border-radius: var(--radius-sm);
      background: var(--bg-card); color: var(--text-primary); font-size: 13px;
      outline: none; transition: var(--transition);
    }
    .search-box:focus { border-color: var(--accent-cyan); box-shadow: 0 0 12px var(--glow-cyan); }
    .search-box::placeholder { color: var(--text-muted); }

    .candidate-list { display: flex; flex-direction: column; gap: 12px; }
    .candidate-card {
      background: var(--bg-card); backdrop-filter: blur(10px);
      border: 1px solid var(--border-glass); border-radius: var(--radius);
      padding: 16px 20px; position: relative; cursor: pointer;
      transition: var(--transition); transform: translateZ(0); overflow: hidden;
    }
    .candidate-card::before {
      content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
      background: var(--accent-cyan); border-radius: var(--radius) 0 0 var(--radius);
      transition: var(--transition);
    }
    .candidate-card:hover { transform: translateX(4px); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4); border-color: rgba(255, 255, 255, 0.15); }
    .candidate-card.tier-gold::before { background: var(--accent-gold); }
    .candidate-card.tier-silver::before { background: var(--accent-silver); }
    .candidate-card.tier-bronze::before { background: var(--accent-bronze); }
    .candidate-card.tier-honeypot::before { background: var(--accent-red); }
    .candidate-card.tier-gold { box-shadow: 0 0 20px var(--glow-gold); }
    .candidate-card.tier-honeypot { border-color: rgba(248, 113, 113, 0.3); }
    .candidate-card .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
    .candidate-card .identity { display: flex; align-items: center; gap: 12px; }
    .candidate-card .rank-badge {
      width: 36px; height: 36px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 14px; background: var(--bg-deep);
      border: 2px solid var(--accent-cyan); color: var(--accent-cyan); flex-shrink: 0;
    }
    .candidate-card.tier-gold .rank-badge { border-color: var(--accent-gold); color: var(--accent-gold); box-shadow: 0 0 12px var(--glow-gold); }
    .candidate-card.tier-silver .rank-badge { border-color: var(--accent-silver); color: var(--accent-silver); }
    .candidate-card.tier-bronze .rank-badge { border-color: var(--accent-bronze); color: var(--accent-bronze); }
    .candidate-card.tier-honeypot .rank-badge { border-color: var(--accent-red); color: var(--accent-red); }
    .candidate-card .name-area h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 2px; }
    .candidate-card .name-area .meta { font-size: 12px; color: var(--text-muted); }
    .candidate-card .score-area { text-align: right; }
    .candidate-card .score-value { font-size: 24px; font-weight: 800; color: var(--accent-cyan); line-height: 1; }
    .candidate-card .score-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
    .candidate-card .reasoning-preview {
      font-size: 13px; color: var(--text-secondary); margin-top: 8px;
      padding-top: 8px; border-top: 1px solid var(--border-glass);
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    }
    .candidate-card .tags { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
    .tag { font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 20px; background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border-glass); }
    .tag-hp { background: rgba(248, 113, 113, 0.1); color: var(--accent-red); border-color: rgba(248, 113, 113, 0.3); }
    .tag-ml { background: rgba(74, 222, 128, 0.1); color: var(--accent-green); border-color: rgba(74, 222, 128, 0.3); }
    .tag-product { background: rgba(6, 182, 212, 0.1); color: var(--accent-cyan); border-color: rgba(6, 182, 212, 0.3); }

    .detail-panel { position: sticky; top: 80px; height: calc(100vh - 100px); overflow-y: auto; }
    .detail-panel::-webkit-scrollbar { width: 6px; }
    .detail-panel::-webkit-scrollbar-track { background: transparent; }
    .detail-panel::-webkit-scrollbar-thumb { background: var(--border-glass); border-radius: 3px; }
    .detail-panel .empty-state { text-align: center; padding: 40px 20px; color: var(--text-muted); }
    .detail-panel .empty-state .icon { font-size: 48px; margin-bottom: 12px; }
    .detail-panel .empty-state h3 { font-size: 16px; font-weight: 600; margin-bottom: 8px; color: var(--text-secondary); }
    .detail-panel .empty-state p { font-size: 13px; }
    .detail-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--border-glass); }
    .detail-header .avatar { width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; flex-shrink: 0; }
    .detail-header .info h3 { font-size: 18px; font-weight: 600; }
    .detail-header .info p { font-size: 13px; color: var(--text-muted); }
    .score-bar-container { margin-bottom: 20px; }
    .score-bar-label { display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .score-bar-track { height: 8px; background: var(--bg-deep); border-radius: 4px; overflow: hidden; position: relative; }
    .score-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple)); transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 0 10px var(--glow-cyan); }
    .score-bar-fill.low { background: linear-gradient(90deg, var(--accent-red), #fb923c); }
    .score-bar-fill.medium { background: linear-gradient(90deg, #fb923c, var(--accent-gold)); }
    .score-bar-fill.high { background: linear-gradient(90deg, var(--accent-gold), var(--accent-green)); }
    .section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin: 20px 0 12px; display: flex; align-items: center; gap: 8px; }
    .section-title::after { content: ''; flex: 1; height: 1px; background: var(--border-glass); }
    .reasoning-box { background: rgba(6, 182, 212, 0.05); border: 1px solid rgba(6, 182, 212, 0.2); border-radius: var(--radius-sm); padding: 12px; font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
    .reasoning-box .highlight { color: var(--accent-cyan); font-weight: 600; }
    .feature-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .feature-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-deep); border-radius: var(--radius-sm); font-size: 12px; }
    .feature-item .name { color: var(--text-muted); }
    .feature-item .value { font-weight: 600; color: var(--text-primary); }
    .feature-item .value.high { color: var(--accent-green); }
    .feature-item .value.medium { color: var(--accent-gold); }
    .feature-item .value.low { color: var(--accent-red); }
    .behavioral-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .behavioral-item { text-align: center; padding: 12px; background: var(--bg-deep); border-radius: var(--radius-sm); border: 1px solid var(--border-glass); }
    .behavioral-item .value { font-size: 20px; font-weight: 700; color: var(--text-primary); }
    .behavioral-item .label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
    .behavioral-item .value.positive { color: var(--accent-green); }
    .behavioral-item .value.negative { color: var(--accent-red); }
    .behavioral-item .value.neutral { color: var(--accent-cyan); }
    .timeline { position: relative; padding-left: 20px; }
    .timeline::before { content: ''; position: absolute; left: 6px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, var(--accent-cyan), var(--accent-purple)); border-radius: 1px; }
    .timeline-item { position: relative; padding-bottom: 16px; }
    .timeline-item::before { content: ''; position: absolute; left: -18px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--bg-deep); border: 2px solid var(--accent-cyan); }
    .timeline-item.current::before { background: var(--accent-cyan); box-shadow: 0 0 8px var(--glow-cyan); }
    .timeline-item .company { font-weight: 600; font-size: 13px; }
    .timeline-item .title { font-size: 12px; color: var(--text-secondary); }
    .timeline-item .duration { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
    .skills-cloud { display: flex; flex-wrap: wrap; gap: 6px; }
    .skill-tag { font-size: 12px; font-weight: 500; padding: 4px 12px; border-radius: 20px; background: var(--bg-deep); border: 1px solid var(--border-glass); color: var(--text-secondary); transition: var(--transition); }
    .skill-tag:hover { border-color: var(--accent-cyan); color: var(--accent-cyan); transform: scale(1.05); }
    .skill-tag.advanced { border-color: rgba(74, 222, 128, 0.3); color: var(--accent-green); }
    .skill-tag.intermediate { border-color: rgba(251, 191, 36, 0.3); color: var(--accent-gold); }
    .skill-tag.beginner { border-color: rgba(148, 163, 184, 0.3); color: var(--text-muted); }
    .edu-item { padding: 10px 12px; background: var(--bg-deep); border-radius: var(--radius-sm); margin-bottom: 8px; border: 1px solid var(--border-glass); }
    .edu-item .institution { font-weight: 600; font-size: 13px; }
    .edu-item .degree { font-size: 12px; color: var(--text-secondary); }
    .edu-item .years { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
    .edu-item .tier-badge { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 10px; margin-top: 4px; }
    .tier-badge.tier-1 { background: rgba(74, 222, 128, 0.15); color: var(--accent-green); }
    .tier-badge.tier-2 { background: rgba(251, 191, 36, 0.15); color: var(--accent-gold); }
    .tier-badge.tier-3 { background: rgba(248, 113, 113, 0.15); color: var(--accent-red); }
    .honeypot-alert { background: rgba(248, 113, 113, 0.08); border: 1px solid rgba(248, 113, 113, 0.3); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 16px; }
    .honeypot-alert .title { font-size: 13px; font-weight: 600; color: var(--accent-red); display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
    .honeypot-alert .reasons { display: flex; flex-wrap: wrap; gap: 6px; }
    .honeypot-alert .reason { font-size: 11px; padding: 3px 10px; border-radius: 20px; background: rgba(248, 113, 113, 0.15); color: var(--accent-red); border: 1px solid rgba(248, 113, 113, 0.2); }
    .honeypot-toggle { display: flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: var(--radius-sm); background: var(--bg-card); border: 1px solid var(--border-glass); color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: var(--transition); margin-bottom: 16px; }
    .honeypot-toggle:hover { border-color: var(--accent-red); color: var(--accent-red); }
    .honeypot-toggle.active { background: rgba(248, 113, 113, 0.1); border-color: var(--accent-red); color: var(--accent-red); }
    @keyframes fadeIn { 0% { opacity: 0; transform: translateY(20px) scale(0.98); } 100% { opacity: 1; transform: translateY(0) scale(1); } }
    .animate-in { animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) both; }
    @media (max-width: 1100px) { .detail-panel { position: fixed; right: -400px; top: 0; bottom: 0; width: 380px; z-index: 200; transition: right 0.3s ease; } .detail-panel.open { right: 0; } .close-btn { display: block; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: 0.001ms !important; } .animate-in { opacity: 1 !important; transform: none !important; } }
    .close-btn { display: none; position: absolute; top: 16px; right: 16px; background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; }
    ::-webkit-scrollbar { width: 8px; } ::-webkit-scrollbar-track { background: var(--bg-deep); } ::-webkit-scrollbar-thumb { background: var(--border-glass); border-radius: 4px; } ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
  </style>
</head>
<body>
  <div class="ambient-bg"></div>
  <header class="header">
    <div class="header-brand">
      <div class="logo">R</div>
      <div><h1>__TITLE__</h1></div>
      <span class="badge">Static Demo</span>
    </div>
    <div style="font-size:13px;color:var(--text-muted);">Generated __TIMESTAMP__</div>
  </header>
  <main class="main">
    <div class="left-col">
      <div class="metrics-grid" id="metricsGrid">
        <div class="metric-card glow-cyan">
          <div class="value" id="metricTotal">—</div>
          <div class="label">Total Candidates</div>
        </div>
        <div class="metric-card">
          <div class="value" id="metricRanked">—</div>
          <div class="label">Ranked Output</div>
        </div>
        <div class="metric-card glow-purple">
          <div class="value" id="metricHoneypots">—</div>
          <div class="label">Honeypots Blocked</div>
        </div>
        <div class="metric-card">
          <div class="value" id="metricAvg">—</div>
          <div class="label">Avg Score</div>
        </div>
      </div>
      <div class="glass-panel">
        <div class="panel-title">🏗️ Pipeline Architecture</div>
        <div class="pipeline" id="pipeline"></div>
      </div>
      <div class="filter-bar">
        <button class="filter-btn active" data-filter="all" onclick="setFilter('all')">All Candidates</button>
        <button class="filter-btn" data-filter="honeypot" onclick="setFilter('honeypot')">🍯 Honeypots</button>
        <button class="filter-btn" data-filter="product" onclick="setFilter('product')">Product Companies</button>
        <button class="filter-btn" data-filter="strong-ml" onclick="setFilter('strong-ml')">Strong ML</button>
        <input type="text" class="search-box" id="searchBox" placeholder="Search by name, title, company..." oninput="handleSearch(event)">
      </div>
      <div class="candidate-list" id="candidateList"></div>
    </div>
    <aside class="detail-panel glass-panel" id="detailPanel">
      <button class="close-btn" onclick="closeDetailPanel()">✕</button>
      <div class="empty-state" id="detailEmpty">
        <div class="icon">👤</div>
        <h3>Select a candidate</h3>
        <p>Click any candidate card to view their full profile, reasoning audit, and feature breakdown.</p>
      </div>
      <div id="detailContent" style="display:none;"></div>
    </aside>
  </main>
  <script>
    const PIPELINE_STAGES = [
      {name:'Load',icon:'📥'},{name:'Text',icon:'📝'},{name:'BM25',icon:'🔍'},
      {name:'33 Features',icon:'🧮'},{name:'Integrity',icon:'🛡️'},{name:'Behavioral',icon:'📊'},
      {name:'Rank',icon:'🏆'},{name:'Reasoning',icon:'💡'}
    ];
    let state = {filter:'all',searchQuery:'',selectedId:null};
    const results = __DATA_JSON__;

    function init() {
      renderMetrics();
      renderPipeline();
      renderCandidates();
    }

    function renderMetrics() {
      const hpCount = results.filter(r => r.honeypot_flag).length;
      const avgScore = results.reduce((s,r) => s + r.score, 0) / results.length;
      document.getElementById('metricTotal').textContent = results.length.toLocaleString();
      document.getElementById('metricRanked').textContent = results.length.toLocaleString();
      document.getElementById('metricHoneypots').textContent = hpCount.toLocaleString();
      document.getElementById('metricAvg').textContent = avgScore.toFixed(3);
    }

    function renderPipeline() {
      const container = document.getElementById('pipeline');
      container.innerHTML = PIPELINE_STAGES.map((s,i) => `
        <div class="pipeline-node">
          <div class="icon">${s.icon}</div>
          <div class="name">${s.name}</div>
          <div class="count">${results.length.toLocaleString()}</div>
        </div>
        ${i < PIPELINE_STAGES.length-1 ? '<div class="pipeline-arrow">→</div>' : ''}
      `).join('');
    }

    function getFiltered() {
      let filtered = [...results];
      if (state.filter === 'honeypot') filtered = filtered.filter(c => c.honeypot_flag);
      else if (state.filter === 'product') filtered = filtered.filter(c => (c.profile?.company||'').toLowerCase().includes('product') || (c.profile?.industry||'').toLowerCase().includes('product'));
      else if (state.filter === 'strong-ml') {
        const mlSkills = ['machine learning','deep learning','nlp','llm','tensorflow','pytorch','transformers'];
        filtered = filtered.filter(c => (c.skills||[]).some(s => mlSkills.some(ml => (s.name||'').toLowerCase().includes(ml))));
      }
      if (state.searchQuery) {
        const q = state.searchQuery.toLowerCase();
        filtered = filtered.filter(c => (c.profile?.name||'').toLowerCase().includes(q) || (c.profile?.title||'').toLowerCase().includes(q) || (c.profile?.company||'').toLowerCase().includes(q) || (c.candidate_id||'').toLowerCase().includes(q));
      }
      return filtered;
    }

    function renderCandidates() {
      const container = document.getElementById('candidateList');
      const filtered = getFiltered();
      if (!filtered.length) {
        container.innerHTML = '<div class="glass-panel" style="text-align:center;padding:40px;"><div style="font-size:48px;margin-bottom:12px;">🔍</div><h3 style="font-size:16px;font-weight:600;color:var(--text-secondary);margin-bottom:8px;">No candidates match</h3><p style="font-size:13px;color:var(--text-muted);">Try adjusting your filters or search query.</p></div>';
        return;
      }
      container.innerHTML = filtered.map((c,i) => `
        <div class="candidate-card tier-${c.tier} animate-in" style="animation-delay:${i*0.03}s" onclick="selectCandidate('${c.candidate_id}')">
          <div class="card-header">
            <div class="identity">
              <div class="rank-badge">${c.rank}</div>
              <div class="name-area">
                <h3>${c.profile?.title||'Unknown'} @ ${c.profile?.company||'Unknown'}</h3>
                <div class="meta">${c.candidate_id} | ${c.profile?.yoe?.toFixed(1)||0} YOE | ${c.profile?.location||'Unknown'}</div>
              </div>
            </div>
            <div class="score-area">
              <div class="score-value">${c.score?.toFixed(4)||'0.0000'}</div>
              <div class="score-label">Score</div>
            </div>
          </div>
          <div class="reasoning-preview">${c.reasoning||'No reasoning available'}</div>
          <div class="tags">
            ${c.honeypot_flag?'<span class="tag tag-hp">🍯 HONEYPOT</span>':''}
            ${c.profile?.yoe>=5?'<span class="tag tag-ml">Experienced</span>':''}
            ${c.behavioral?.open_to_work?'<span class="tag tag-product">Open to Work</span>':''}
          </div>
        </div>
      `).join('');
    }

    function selectCandidate(id) {
      const c = results.find(x => x.candidate_id === id);
      if (!c) return;
      state.selectedId = id;
      document.getElementById('detailEmpty').style.display = 'none';
      document.getElementById('detailContent').style.display = 'block';
      const scorePct = Math.min(c.score*100,100);
      const scoreClass = scorePct>=80?'high':scorePct>=50?'medium':'low';
      const features = c.features||{};
      const featureItems = Object.entries(features).map(([k,v]) => {
        const valClass = v>0.7?'high':v>0.4?'medium':'low';
        return `<div class="feature-item"><span class="name">${k.replace(/_/g,' ')}</span><span class="value ${valClass}">${v.toFixed(3)}</span></div>`;
      }).join('');
      const b = c.behavioral||{};
      const behavioralItems = [
        {label:'Response Rate',value:b.response_rate,fmt:v=>(v*100).toFixed(0)+'%',cls:v=>v>0.5?'positive':v>0.2?'neutral':'negative'},
        {label:'Open to Work',value:b.open_to_work,fmt:v=>v?'✅':'❌',cls:v=>v?'positive':'negative'},
        {label:'Interview Rate',value:b.interview_completion,fmt:v=>(v*100).toFixed(0)+'%',cls:v=>v>0.6?'positive':'neutral'},
        {label:'GitHub Score',value:b.github_activity,fmt:v=>v.toFixed(1),cls:v=>v>7?'positive':v>3?'neutral':'negative'},
        {label:'Profile Views',value:b.profile_views,fmt:v=>v.toString(),cls:()=>'neutral'},
        {label:'Notice Period',value:b.notice_period,fmt:v=>v+'d',cls:v=>v<=30?'positive':v<=60?'neutral':'negative'},
      ].map(item => `<div class="behavioral-item"><div class="value ${item.cls(item.value)}">${item.fmt(item.value)}</div><div class="label">${item.label}</div></div>`).join('');
      const timeline = (c.timeline||[]).map(job => `<div class="timeline-item ${job.is_current?'current':''}"><div class="company">${job.company}</div><div class="title">${job.title}</div><div class="duration">${job.duration_months} months • ${job.industry} • ${job.company_size}</div></div>`).join('');
      const skills = (c.skills||[]).map(s => { const cls=s.proficiency==='advanced'?'advanced':s.proficiency==='intermediate'?'intermediate':'beginner'; return `<span class="skill-tag ${cls}">${s.name} (${s.endorsements})</span>`; }).join('');
      const education = (c.education||[]).map(edu => `<div class="edu-item"><div class="institution">${edu.institution}</div><div class="degree">${edu.degree} — ${edu.field}</div><div class="years">${edu.start}–${edu.end} • ${edu.grade}</div>${edu.tier?`<span class="tier-badge tier-${edu.tier.replace('tier_','')}">${edu.tier.toUpperCase()}</span>`:''}</div>`).join('');
      const honeypotSection = c.honeypot_flag?`<div class="honeypot-alert"><div class="title">🍯 Honeypot Detected</div><div class="reasons">${c.honeypot_reasons?.map(r=>`<span class="reason">${r}</span>`).join('')||'<span class="reason">Flagged by system</span>'}</div></div>`:'';
      document.getElementById('detailContent').innerHTML = `
        ${honeypotSection}
        <div class="detail-header"><div class="avatar">${(c.profile?.name||'U').charAt(0)}</div><div class="info"><h3>${c.profile?.title||'Unknown'} @ ${c.profile?.company||'Unknown'}</h3><p>${c.candidate_id} • ${c.profile?.location||'Unknown'} • ${c.profile?.yoe?.toFixed(1)||0} YOE</p></div></div>
        <div class="score-bar-container"><div class="score-bar-label"><span>Match Score</span><span>${c.score?.toFixed(4)||'0.0000'}</span></div><div class="score-bar-track"><div class="score-bar-fill ${scoreClass}" style="width:${scorePct}%"></div></div></div>
        <div class="section-title">💡 Reasoning Audit</div><div class="reasoning-box">${c.reasoning||'No reasoning available'}</div>
        <div class="section-title">🧮 33-Feature Breakdown</div><div class="feature-grid">${featureItems||'<div style="color:var(--text-muted);font-size:13px;">No feature data</div>'}</div>
        <div class="section-title">📊 Behavioral Signals</div><div class="behavioral-grid">${behavioralItems}</div>
        <div class="section-title">📈 Career Timeline</div><div class="timeline">${timeline||'<div style="color:var(--text-muted);font-size:13px;">No timeline data</div>'}</div>
        <div class="section-title">🎓 Education</div>${education||'<div style="color:var(--text-muted);font-size:13px;">No education data</div>'}
        <div class="section-title">🛠️ Skills</div><div class="skills-cloud">${skills||'<div style="color:var(--text-muted);font-size:13px;">No skills data</div>'}</div>
        ${c.certifications?.length?`<div class="section-title">📜 Certifications</div><div class="skills-cloud">${c.certifications.map(cert=>`<span class="skill-tag">${cert}</span>`).join('')}</div>`:''}
        ${c.languages?.length?`<div class="section-title">🌐 Languages</div><div class="skills-cloud">${c.languages.map(l=>`<span class="skill-tag">${l.language} — ${l.proficiency}</span>`).join('')}</div>`:''}
      `;
      if (window.innerWidth <= 1100) document.getElementById('detailPanel').classList.add('open');
    }

    function closeDetailPanel() { document.getElementById('detailPanel').classList.remove('open'); }
    function setFilter(filter) { state.filter = filter; document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.filter === filter)); renderCandidates(); }
    function handleSearch(e) { state.searchQuery = e.target.value; renderCandidates(); }

    document.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>"""


def main():
    args = parse_args()

    print(f"Loading candidates from {args.candidates}...")
    candidates_by_id = {}
    with open(args.candidates, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            c = json.loads(line)
            candidates_by_id[c["candidate_id"]] = c

    print(f"Loading submission from {args.submission}...")
    results = []
    with open(args.submission, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["candidate_id"]
            cand = candidates_by_id.get(cid, {})
            payload = extract_candidate_payload(cand, row)
            results.append(payload)

    results.sort(key=lambda x: x["rank"])

    print(f"Generating {args.out} with {len(results)} candidates...")
    json_data = json.dumps(results, indent=2)

    html_out = HTML_TEMPLATE.replace("__DATA_JSON__", json_data)
    html_out = html_out.replace("__TITLE__", args.title)
    html_out = html_out.replace("__TIMESTAMP__", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_out)

    file_size = os.path.getsize(args.out)
    print(f"Done! {args.out} ({file_size:,} bytes)")
    print(f"   Open {args.out} in your browser. Zero dependencies, fully offline.")


if __name__ == "__main__":
    main()
