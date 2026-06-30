"""HuggingFace Space demo with glassmorphic dark theme."""

from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from redrob_ranker.pipeline import RankerConfig, run_ranking


def rank_sample(file_obj):
    if file_obj is None:
        return None, "Upload a candidates.jsonl file to begin.", 0, 0, 0, 0.0

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        in_path = base / Path(file_obj.name).name
        out_path = base / "ranked_candidates.csv"
        in_path.write_bytes(Path(file_obj.name).read_bytes())

        result = run_ranking(
            in_path,
            out_path,
            RankerConfig(top_k=100, candidate_pool_size=200, max_candidates=100),
        )

        df = pd.read_csv(out_path)
        features_by_id = {
            candidate.get("candidate_id"): features
            for candidate, features, _ in (result.raw_ranked or [])
        }

        # Enhance dataframe with tier colors
        def get_tier(row):
            rank = int(row.get("rank", 999))
            features = features_by_id.get(str(row.get("candidate_id", "")))
            if features is not None and features.honeypot_multiplier <= 0.0:
                return "Honeypot"
            if rank == 1:
                return "Gold"
            if rank == 2:
                return "Silver"
            if rank == 3:
                return "Bronze"
            return "Standard"

        df["tier"] = df.apply(get_tier, axis=1)

        # Reorder columns for better display
        cols = ["rank", "candidate_id", "score", "tier", "reasoning"]
        df = df[[c for c in cols if c in df.columns]]
        avg_score = df['score'].mean() if len(df) > 0 else 0.0

        status_msg = (
            f"✅ **Ranked {len(df)} candidates** from {result.loaded_count} loaded\n\n"
            f"📊 **Pipeline Stats:**\n"
            f"• Honeypots detected: {result.honeypots_detected}\n"
            f"• Avg score: {avg_score:.4f}\n"
            f"• Processing: Complete"
        )

        return df, status_msg, result.loaded_count, len(df), result.honeypots_detected, avg_score


# ── Custom CSS for glassmorphic dark theme ──
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: #030712 !important;
    color: #f8fafc !important;
}

/* Main background with ambient glows */
.gradio-container::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background: 
        radial-gradient(ellipse 80% 50% at 20% 40%, rgba(6, 182, 212, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse 60% 40% at 80% 60%, rgba(168, 85, 247, 0.06) 0%, transparent 50%);
}

/* Glass panels */
.glass-panel {
    background: rgba(15, 23, 42, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 20px !important;
}

/* Header styling */
.header-glass {
    background: rgba(3, 7, 18, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding: 20px !important;
    margin-bottom: 24px !important;
}

/* Metric cards */
.metric-card {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}
.metric-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}
.metric-card .value {
    font-size: 28px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #f8fafc, #94a3b8) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}
.metric-card .label {
    font-size: 11px !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    margin-top: 4px !important;
}

/* Tier badges in dataframe */
.tier-gold { color: #fbbf24 !important; font-weight: 700 !important; }
.tier-silver { color: #c0c0c0 !important; font-weight: 700 !important; }
.tier-bronze { color: #cd7f32 !important; font-weight: 700 !important; }
.tier-honeypot { color: #f87171 !important; font-weight: 700 !important; }

/* Buttons */
button.primary {
    background: linear-gradient(135deg, #06b6d4, #a855f7) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    border-radius: 10px !important;
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.3) !important;
    transition: all 0.3s ease !important;
}
button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 0 30px rgba(6, 182, 212, 0.5) !important;
}

/* Dataframe styling */
.table-wrap {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    overflow: hidden !important;
}
.table-wrap th {
    background: rgba(15, 23, 42, 0.9) !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
}
.table-wrap td {
    background: rgba(30, 41, 59, 0.3) !important;
    color: #e2e8f0 !important;
    font-size: 13px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
}
.table-wrap tr:hover td {
    background: rgba(6, 182, 212, 0.05) !important;
}

/* Accordion */
.accordion {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
}
.accordion-header {
    background: rgba(30, 41, 59, 0.5) !important;
    color: #f8fafc !important;
    font-weight: 600 !important;
}

/* Textbox */
input, textarea {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #f8fafc !important;
    border-radius: 10px !important;
}
input:focus, textarea:focus {
    border-color: #06b6d4 !important;
    box-shadow: 0 0 12px rgba(6, 182, 212, 0.2) !important;
}

/* File upload zone */
.upload-zone {
    border: 2px dashed rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    background: rgba(30, 41, 59, 0.3) !important;
    padding: 40px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}
.upload-zone:hover {
    border-color: #06b6d4 !important;
    background: rgba(6, 182, 212, 0.05) !important;
    box-shadow: 0 0 30px rgba(6, 182, 212, 0.1) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #030712; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }
"""


with gr.Blocks(
    title="Redrob HireFit Ranker",
    css=CUSTOM_CSS,
    theme=gr.themes.Base(
        primary_hue="cyan",
        secondary_hue="purple",
        neutral_hue="slate",
    ).set(
        body_background_fill="*neutral_950",
        body_text_color="*neutral_100",
        background_fill_primary="*neutral_900",
        background_fill_secondary="*neutral_800",
        border_color_primary="*neutral_700",
        button_primary_background_fill="*primary_500",
        button_primary_text_color="white",
    )
) as demo:

    # Header
    with gr.Row(elem_classes=["header-glass"]):
        with gr.Column():
            gr.Markdown("""
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:40px;height:40px;background:linear-gradient(135deg,#06b6d4,#a855f7);border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:white;box-shadow:0 0 20px rgba(6,182,212,0.3);">R</div>
                <div>
                    <h1 style="margin:0;font-size:22px;font-weight:700;color:#f8fafc;">Redrob HireFit Ranker</h1>
                    <p style="margin:0;font-size:13px;color:#94a3b8;">CPU-only • offline • 100K candidates • 33 features</p>
                </div>
            </div>
            """)

    # Metrics row
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Column(elem_classes=["metric-card"]):
                metric_total = gr.Markdown("<div class='value'>—</div><div class='label'>Candidates</div>")
        with gr.Column(scale=1):
            with gr.Column(elem_classes=["metric-card"]):
                metric_ranked = gr.Markdown("<div class='value'>—</div><div class='label'>Ranked</div>")
        with gr.Column(scale=1):
            with gr.Column(elem_classes=["metric-card"]):
                metric_honeypots = gr.Markdown("<div class='value'>—</div><div class='label'>Honeypots</div>")
        with gr.Column(scale=1):
            with gr.Column(elem_classes=["metric-card"]):
                metric_avg = gr.Markdown("<div class='value'>—</div><div class='label'>Avg Score</div>")

    # Pipeline visualization
    with gr.Row(elem_classes=["glass-panel"]):
        gr.Markdown("""
        <div style="display:flex;align-items:center;gap:8px;overflow-x:auto;padding:8px 0;">
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">📥</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">Load</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">📝</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">Text</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">🔍</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">BM25</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">🧮</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">33 Features</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">🍯</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">Honeypot</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">📊</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">Behavior</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">🏆</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">Rank</div></div>
            <div style="color:#64748b;">→</div>
            <div style="padding:8px 12px;background:rgba(30,41,59,0.5);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;min-width:70px;"><div style="font-size:18px;margin-bottom:4px;">💡</div><div style="font-size:11px;font-weight:600;color:#94a3b8;">Reason</div></div>
        </div>
        """)

    # Upload and results
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📤 Upload Candidates")
            upload = gr.File(
                label="",
                file_types=[".json", ".jsonl", ".csv"],
                elem_classes=["upload-zone"]
            )
            run_btn = gr.Button("🔥 Rank Candidates", variant="primary", elem_classes=["primary"])

            gr.Markdown("""
            <div style="margin-top:16px;padding:12px;background:rgba(6,182,212,0.05);border:1px solid rgba(6,182,212,0.2);border-radius:10px;">
                <p style="margin:0;font-size:12px;color:#94a3b8;">
                    <strong style="color:#06b6d4;">💡 Pro tip:</strong> Upload a small sample (≤100 candidates) for instant results. 
                    The full 100K run is done via CLI: <code>python rank.py</code>
                </p>
            </div>
            """)

        with gr.Column(scale=2):
            gr.Markdown("### 📊 Results")
            table = gr.Dataframe(
                label="",
                wrap=True,
                elem_classes=["table-wrap"]
            )
            status = gr.Markdown(label="Status")

    # Candidate detail accordion
    with gr.Accordion("🔍 Candidate Detail View", open=False, elem_classes=["accordion"]):
        with gr.Row():
            with gr.Column(scale=1):
                detail_id = gr.Textbox(label="Candidate ID", interactive=False)
                detail_score = gr.Textbox(label="Score", interactive=False)
                detail_tier = gr.Textbox(label="Tier", interactive=False)
            with gr.Column(scale=2):
                detail_reasoning = gr.Textbox(
                    label="Reasoning Audit",
                    lines=5,
                    interactive=False
                )

    # Honeypot explorer
    with gr.Accordion("🍯 Honeypot Explorer", open=False, elem_classes=["accordion"]):
        gr.Markdown("""
        <div style="padding:12px;background:rgba(248,113,113,0.05);border:1px solid rgba(248,113,113,0.2);border-radius:10px;">
            <p style="margin:0;font-size:13px;color:#f87171;">
                Honeypot candidates are flagged by 8 aggressive heuristics including impossible timelines, 
                salary inversion, education impossibility, and title-description contradictions.
            </p>
        </div>
        """)
        honeypot_table = gr.Dataframe(label="Flagged Candidates")

    # Event handlers
    def process_and_detail(file_obj):
        df, status_msg, loaded, ranked, hps, avg = rank_sample(file_obj)

        # Extract honeypot rows for the explorer
        if df is not None and "tier" in df.columns:
            hp_df = df[df["tier"].str.contains("Honeypot", na=False)]
        else:
            hp_df = pd.DataFrame()

        # Get top candidate details
        if df is not None and len(df) > 0:
            top = df.iloc[0]
            detail = (
                top.get("candidate_id", "N/A"),
                f"{top.get('score', 0):.4f}",
                top.get("tier", "Standard"),
                top.get("reasoning", "No reasoning available")
            )
        else:
            detail = ("N/A", "0.0000", "N/A", "Upload a file to see details")
            
        m_total = f"<div class='value'>{loaded:,}</div><div class='label'>Candidates</div>"
        m_ranked = f"<div class='value'>{ranked:,}</div><div class='label'>Ranked</div>"
        m_hps = f"<div class='value'>{hps:,}</div><div class='label'>Honeypots</div>"
        m_avg = f"<div class='value'>{avg:.3f}</div><div class='label'>Avg Score</div>"

        return df, status_msg, hp_df, detail[0], detail[1], detail[2], detail[3], m_total, m_ranked, m_hps, m_avg

    run_btn.click(
        process_and_detail,
        inputs=upload,
        outputs=[table, status, honeypot_table, detail_id, detail_score, detail_tier, detail_reasoning, metric_total, metric_ranked, metric_honeypots, metric_avg]
    )


if __name__ == "__main__":
    demo.launch()
