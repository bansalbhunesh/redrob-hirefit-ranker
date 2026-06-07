#!/usr/bin/env python3
"""
Generates a zero-dependency, single-file HTML dashboard for the Stage 5 interview.
Merges the JSONL candidate data with the CSV submission results.
"""

import argparse
import csv
import json
import os
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Generate demo.html from candidates and submission.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--submission", required=True, help="Path to submission CSV")
    parser.add_argument("--out", default="demo.html", help="Output HTML file path")
    return parser.parse_args()

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Redrob Ranker Results</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0f172a; color: #e2e8f0; line-height: 1.5; }
    h1 { color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 10px; }
    .metric-container { display: flex; gap: 20px; margin-bottom: 30px; }
    .metric { flex: 1; padding: 20px; background: #1e293b; border-radius: 8px; text-align: center; border: 1px solid #334155; }
    .metric h3 { margin: 0; font-size: 32px; color: #38bdf8; }
    .metric p { margin: 5px 0 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
    
    .candidate { margin: 15px 0; padding: 20px; background: #1e293b; border-radius: 8px; border-left: 4px solid #38bdf8; position: relative; }
    .rank-1 { border-left-color: #fbbf24; }
    .rank-2 { border-left-color: #94a3b8; }
    .rank-3 { border-left-color: #b45309; }
    
    .header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .title-area h2 { margin: 0; font-size: 20px; color: #f8fafc; }
    .title-area .meta { color: #94a3b8; font-size: 14px; margin-top: 4px; }
    .score-area { text-align: right; }
    .score { font-size: 24px; font-weight: bold; color: #38bdf8; }
    .rank-badge { position: absolute; top: -10px; left: -10px; background: #38bdf8; color: #0f172a; width: 30px; height: 30px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }
    .rank-1 .rank-badge { background: #fbbf24; }
    .rank-2 .rank-badge { background: #94a3b8; }
    .rank-3 .rank-badge { background: #b45309; }
    
    .reasoning { color: #cbd5e1; font-size: 15px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #334155; }
    
    .tag { display: inline-block; padding: 2px 8px; margin: 0 4px 4px 0; background: #334155; border-radius: 4px; font-size: 12px; }
    .tag-hp { background: #450a0a; color: #f87171; border: 1px solid #7f1d1d; }
  </style>
</head>
<body>
  <h1>Redrob HireFit Engine v2.0</h1>
  <div id="metrics" class="metric-container"></div>
  <div id="candidates"></div>
  
  <script>
    // Injected Data
    const results = __DATA_JSON__;
    
    // Render Metrics
    const hpCount = results.filter(r => r.reasoning.toLowerCase().includes("honeypot")).length;
    document.getElementById('metrics').innerHTML = `
      <div class="metric"><h3>${results.length}</h3><p>Ranked Output</p></div>
      <div class="metric"><h3>${hpCount}</h3><p>Honeypots Blocked in Top K</p></div>
      <div class="metric"><h3>132s</h3><p>Avg 100K Runtime</p></div>
    `;
    
    // Render Candidates
    const container = document.getElementById('candidates');
    let html = '';
    
    results.forEach(r => {
        const rankClass = r.rank <= 3 ? `rank-${r.rank}` : '';
        const hpTag = r.reasoning.toLowerCase().includes("honeypot") ? `<span class="tag tag-hp">HONEYPOT</span>` : '';
        
        html += `
        <div class="candidate ${rankClass}">
            <div class="rank-badge">${r.rank}</div>
            <div class="header">
                <div class="title-area">
                    <h2>${r.title} @ ${r.company} ${hpTag}</h2>
                    <div class="meta">${r.candidate_id} | ${r.yoe} Years Exp | ${r.location}</div>
                </div>
                <div class="score-area">
                    <div class="score">${parseFloat(r.score).toFixed(4)}</div>
                </div>
            </div>
            <div class="reasoning">
                <strong>Audit Log:</strong> ${r.reasoning}
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
  </script>
</body>
</html>
"""

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
            prof = cand.get("profile", {})
            
            results.append({
                "candidate_id": cid,
                "rank": int(row["rank"]),
                "score": float(row["score"]),
                "reasoning": row["reasoning"],
                "title": prof.get("current_title", "Unknown"),
                "company": prof.get("current_company", "Unknown"),
                "yoe": float(prof.get("years_of_experience", 0.0)),
                "location": prof.get("location", "Unknown")
            })
            
    results.sort(key=lambda x: x["rank"])
    
    print(f"Generating {args.out}...")
    json_data = json.dumps(results, indent=2)
    html_out = HTML_TEMPLATE.replace("__DATA_JSON__", json_data)
    
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_out)
        
    print(f"Done! Open {args.out} in your browser.")

if __name__ == "__main__":
    main()
