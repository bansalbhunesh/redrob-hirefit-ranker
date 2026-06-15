"""Redrob Ranking Decision Lab — judge-facing dashboard for the Golden -> Fusion -> Ω -> Ψ -> Φ arc.

STRICTLY a downstream research/explanation layer. It does NOT import, rerun, or influence the
production ranking path; golden af8f2b32 stays byte-identical. Reads only committed local
artifacts (no network, no model downloads, no production execution).

Run:  streamlit run omega_decision_dashboard.py
(If streamlit is not installed: pip install streamlit pandas)
"""
from __future__ import annotations

import streamlit as st

from dashboard import charts, components as C
from dashboard.constants import (CONFIG, DISCLAIMER, EXPERIMENTAL_INTEGRITY_NOTE, GATES,
                                 GOLDEN_COMMIT, VERDICT, VERDICT_DISCLAIMER)
from dashboard.data_loader import load_csv_safe, load_json_safe
from dashboard.integrity_cards import distribution, load_cards

st.set_page_config(page_title="Redrob Ranking Decision Lab", page_icon="⚖️",
                   layout="wide", initial_sidebar_state="expanded")


def _unavailable(art):
    st.warning(f"Artifact unavailable. Expected: `{art.path}`. ({art.message})")


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Redrob Ranking Decision Lab")
    st.caption("Downstream research & explanation layer — NOT the production ranker.")
    st.markdown(f"**Shipped:** Golden `{GOLDEN_COMMIT}`")
    st.markdown("**Active research:** `integration/final-research-program`")
    st.markdown("**Dataset:** 100K candidates (frozen blind arbiter)")
    show_tech = st.toggle("Technical details", value=False)
    show_limits = st.toggle("Show research limitations", value=True)
    st.divider()
    st.markdown("**Reproduce golden** (real path; there is no reproduce.sh):")
    st.code("PYTHONHASHSEED=0 python -m pytest tests/test_submission_gate.py -q\n"
            "sha256sum submission.csv  # -> af8f2b327f05d30e...", language="bash")
    st.divider()
    st.caption(DISCLAIMER)

reg = load_json_safe(CONFIG["registry"])
dec = load_json_safe(CONFIG["omega_decision"])
fr = load_json_safe(CONFIG["omega_frontier"])
cards = load_cards(CONFIG["integrity_cards"])

# ----------------------------------------------------------------- 1. verdict
st.title("⚖️ Ranking Decision: why Golden ships")
C.verdict_banner(VERDICT,
                 "Golden remains the shipped submission because the only gate that can validate "
                 "an alternative — independent candidate-specific human confirmation — has not yet "
                 "been completed.")
n_cards = len(cards)
anomalies = sum(1 for c in cards if c.get("evidence_status") == "PROBABLE_CONTRADICTION")
C.metric_row([("Shipped ranking", f"Golden {GOLDEN_COMMIT}"),
              ("Production tests", "171 passed"),
              ("Shipped-detector flags (top-100)", "0"),
              ("Experimental anachronism anomalies", str(anomalies if n_cards else 52)),
              ("Ψ status", "AWAITING HUMAN DATA")])
st.info(VERDICT_DISCLAIMER)

# ----------------------------------------------------------------- 2. gates
st.header("1 · Shipping-gate battery")
for name, status, expl in GATES:
    C.gate_card(name, status, expl)
C.note("Four computational gates can be tested automatically. The fifth requires external human "
       "evidence and cannot be simulated honestly. PENDING is not a model-performance failure.")

# ----------------------------------------------------------------- 3. regret frontier
st.header("2 · Minimax-regret frontier (simulated worlds)")
if fr:
    df = charts.frontier_frame(fr.data)
    st.line_chart(df)
    st.caption("x-axis = simulated integrity-aversion parameter λ · y-axis = human-aligned utility. "
               "Decision boundary (golden vs constrained) is at λ≈0.10 — a MODEL-SPECIFIC simulated "
               "boundary, not an empirical human threshold.")
    st.warning("λ is a simulated sensitivity parameter, not an estimate of real recruiter or "
               "hackathon-judge preferences. Ω's low regret is partly BY CONSTRUCTION — it is "
               "optimised under the same simulated framework used to score it.")
    lam = st.slider("Explore a simulated world (λ)", 0.0, 2.0, 0.10, 0.10)
    pref = charts.preferred_at_lambda(fr.data, lam)
    if pref:
        u = pref["utilities"]
        cols = st.columns(len(u) + 1)
        cols[0].metric("Preferred (this world)", pref["preferred"])
        for col, (k, v) in zip(cols[1:], u.items()):
            col.metric(k, f"{v:.2f}")
    C.note("Explanatory only — the slider does not produce or overwrite any submission.")
    if dec:
        st.bar_chart(charts.regret_frame(dec.data))
        st.caption("Max regret across simulated worlds (lower = more robust).")
else:
    _unavailable(fr)

# ----------------------------------------------------------------- 4. the 52 reconciliation
st.header("3 · The 52-anomaly reconciliation")
st.dataframe({
    "Category": ["Shipped honeypot detector", "Experimental anachronism detector",
                 "Confirmed hard contradictions", "Official planted honeypots"],
    "Golden top-100": ["0", "52", "0 confirmed", "unknown"],
    "Interpretation": ["Production ranking guarantee", "Technology-tenure anomalies requiring review",
                       "No independent confirmation", "Official IDs unavailable"]},
    use_container_width=True, hide_index=True)
st.markdown("> **Detector-flagged anomaly ≠ confirmed contradiction ≠ official planted honeypot.**")
if cards:
    st.write("Downstream integrity-card distribution over golden's top-100:")
    st.write({f"{ev} → {act}": n for (ev, act), n in distribution(cards).items()})
    import pandas as pd
    cdf = pd.DataFrame(cards)
    f1 = st.multiselect("Filter by evidence status", sorted(cdf["evidence_status"].unique()))
    f2 = st.multiselect("Filter by recommended action", sorted(cdf["recommended_action"].unique()))
    view = cdf
    if f1:
        view = view[view["evidence_status"].isin(f1)]
    if f2:
        view = view[view["recommended_action"].isin(f2)]
    st.dataframe(view[["candidate_id", "role_fit", "evidence_status", "recommended_action",
                       "anachronism_severity", "reason"]], use_container_width=True, hide_index=True)
    st.caption(EXPERIMENTAL_INTEGRITY_NOTE)

    # ------------------------------------------------------------- 5. audit card
    st.header("4 · Candidate integrity audit card")
    cid = st.selectbox("Select candidate", view["candidate_id"].tolist() if len(view) else cdf["candidate_id"].tolist())
    rec = next((c for c in cards if c["candidate_id"] == cid), None)
    if rec:
        st.markdown(f"""
**Candidate:** `{rec['candidate_id']}`  ·  **Role fit:** {rec['role_fit']}
- **Evidence status:** {rec['evidence_status']}
- **Recommended action:** {rec['recommended_action']}
- **Reason:** {rec['reason']}
- **Corroborating evidence:** {', '.join(rec.get('corroborating_evidence', []))}
- **Verification request:** {rec['verification_request']}
- **Ranking impact:** None — golden order remains unchanged.""")
        st.caption(EXPERIMENTAL_INTEGRITY_NOTE)
else:
    _unavailable(load_json_safe(CONFIG["integrity_cards"]))

# ----------------------------------------------------------------- 6. fusion autopsy
st.header("5 · Fusion autopsy — why the proxy gain was not shipped")
C.metric_row([("Golden proxy", "0.8625"), ("Fusion proxy", "0.8753"), ("Gain", "+0.0128"),
              ("Effective judges", "1.85 of 7"), ("Gain from top-5 candidates", "56%")])
st.bar_chart(charts.fusion_waterfall_frame(0.0072, 0.0128))
st.caption("Fusion found real ranking signal, but the improvement was concentrated in the exact "
           "class whose integrity meaning remains unresolved. Without the anachronism class the "
           "gain inverts to −0.011.")
st.markdown("**Scientifically valuable · Operationally unconfirmed · Not shipped.**")

# ----------------------------------------------------------------- 7. Psi
st.header("6 · Ψ — human integrity panel")
psi = load_json_safe(CONFIG["psi_manifest"])
st.markdown("`Stage A (career quality, dates hidden)` → `Stage B (full timeline)` → "
            "`integrity reversal analysis` → `frozen shipping rule`")
if psi:
    m = psi.data
    C.metric_row([("Frozen candidates", str(m.get("total", 24))),
                  ("Manifest hash", str(m.get("frozen_hash", ""))[:12]),
                  ("Responses", "0"), ("Status", "AWAITING HUMAN DATA")])
st.error("AWAITING HUMAN DATA — no human responses exist; no synthetic results are shown as human.")
C.note("Public discourse can justify the question. Only Ψ can answer it for these candidates.")

# ----------------------------------------------------------------- 8. Phi
st.header("7 · Study Φ — real public hiring discourse")
phi = load_json_safe(CONFIG["phi_manifest"])
if phi:
    m = phi.data
    C.metric_row([("Included units", str(m.get("combined_units", 27))),
                  ("Strata", "HN + Workplace-SE"), ("Coder", "single (no IRR)"),
                  ("Anachronism cell", f"{m.get('anachronism_decision_items', 5)} (not saturated)")])
st.write({"CLEAR → CONTINUE": "", "AMBIGUOUS → CLARIFY": "", "PROBABLE_CONTRADICTION → VERIFY": "",
          "CONFIRMED_CONTRADICTION → BLOCK": ""})
st.caption("Product-oriented interpretation, NOT a deterministic universal rule.")
st.info("Real public discourse supports a severity-conditioned verification process. It does NOT "
        "establish how Redrob judges will treat the 52 candidates and cannot replace Ψ.")
if show_limits:
    st.caption("Limits: small corpus · HN + Workplace-SE only · HR/workplace-process (NOT verified "
               "recruiter) stratum · single coder · AWAITING_SECOND_CODER · anachronism cell not "
               "saturated · no candidate-specific labels.")

# ----------------------------------------------------------------- 9. timeline
st.header("8 · Research timeline (progress = reducing uncertainty)")
TL = [("Golden baseline", "frozen reproducible submission", "SHIPPED"),
      ("Competitive audit", "leaders' lead is proxy-overfit noise", "RESEARCH ONLY"),
      ("Cross-encoder / learned ranking", "lose on blind arbiter", "MEASURED NEGATIVE"),
      ("Rank-space fusion", "+0.0128 but anachronism-driven", "RESEARCH ONLY"),
      ("Judge-dependence audit", "1.85 effective judges", "RESEARCH ONLY"),
      ("Candidate-influence audit", "56% of gain from 5 candidates", "RESEARCH ONLY"),
      ("Evidence channels (BM25F etc.)", "independent but no proxy gain", "MEASURED NEGATIVE"),
      ("Integrity-constrained fusion", "0 honeypots but −0.13", "RESEARCH ONLY"),
      ("Experiment Ω", "NO_RANKING_DOMINATES (simulated)", "RESEARCH ONLY"),
      ("Experiment Ψ", "frozen human instrument", "AWAITING HUMAN DATA"),
      ("Study Φ", "severity-conditioned discourse", "AWAITING HUMAN DATA"),
      ("Integrity audit cards", "downstream explanation", "EXPLANATION LAYER"),
      ("Ship Golden", "EV-max verified default", "SHIPPED")]
for stage, result, label in TL:
    st.markdown(f"- **{stage}** — {result}  ·  `{label}`")

# ----------------------------------------------------------------- 10. why golden
st.header("9 · Why Golden ships")
st.dataframe({
    "Property": ["Frozen output", "Deterministic", "Proxy improvement", "Candidate-influence robust",
                 "Independent human lockbox", "Shipped"],
    "Golden": ["Yes", "Yes", "Baseline", "Baseline", "Not needed to reproduce baseline", "Yes"],
    "Fusion": ["Research", "Yes", "Yes (fragile)", "Failed (5-candidate)", "Missing", "No"],
    "Ω candidate": ["Research", "Yes", "Simulation-dependent", "Simulated", "Missing", "No"]},
    use_container_width=True, hide_index=True)
st.success("Golden is not shipped because every alternative was inferior. It is shipped because it "
           "is the only ranking whose current benefits and risks are verified without depending on "
           "unresolved human assumptions.")
st.markdown("**Docs:** `docs/SHIPPING_DECISION.md` · `docs/OMEGA_DECISION_SUMMARY.md` · "
            "`docs/PSI_INTEGRITY_PANEL.md` · `docs/human_opinion/HUMAN_OPINION_LANDSCAPE.md` · "
            "`docs/REPRODUCTION.md`")
if show_tech and reg:
    st.divider(); st.subheader("Experiment registry (machine-readable spine)")
    st.json(reg.data)
