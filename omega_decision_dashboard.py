"""Redrob V6 Decision Lab — judge-facing evidence and integrity dashboard.

STRICTLY a downstream research/explanation layer. It does NOT import, rerun, or influence the
production ranking path; V6 artifact 8f7f30c68ec30cb6 stays byte-identical. Reads only committed local
artifacts (no network, no model downloads, no production execution).

Run:  streamlit run omega_decision_dashboard.py
(If streamlit is not installed: pip install streamlit pandas)
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from dashboard import charts, components as C, theme
from dashboard.constants import (CONFIG, DISCLAIMER, EXPERIMENTAL_INTEGRITY_NOTE, GATES,
                                 GOLDEN_COMMIT, SHARED_FACTS, VERDICT, VERDICT_DISCLAIMER)
from dashboard.data_loader import load_json_safe
from dashboard.integrity_cards import distribution, load_cards

st.set_page_config(page_title="Omega Decision System", page_icon="🔬",
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown(theme.CSS, unsafe_allow_html=True)  # Command Core design system (dark / indigo)


def _unavailable(art):
    st.warning(f"Artifact unavailable. Expected: `{art.path}`. ({art.message})")


_CC_RANGE = [theme.ACCENT, theme.AMBER, theme.GREEN, theme.BLUE, theme.TEXT_SECONDARY]


def _cc(chart):  # Command Core dark chart styling
    return (chart
            .configure(background=theme.BG_BASE)
            .configure_view(stroke=None)
            .configure_axis(grid=True, gridColor=theme.BORDER, gridOpacity=0.6,
                            domainColor=theme.BORDER, tickColor=theme.BORDER,
                            labelColor=theme.TEXT_SECONDARY, titleColor=theme.TEXT_SECONDARY,
                            labelFont="JetBrains Mono", titleFont="Inter", titleFontWeight=600)
            .configure_legend(labelColor=theme.TEXT_SECONDARY, titleColor=theme.TEXT_MUTED,
                              labelFont="Inter", symbolType="stroke"))


def cc_line(df, xtitle, ytitle, rule_x=None, rule_label=None):
    xcol = df.index.name or "index"
    d = df.reset_index().melt(id_vars=xcol, var_name="ranking", value_name="value")
    line = alt.Chart(d).mark_line(strokeWidth=2).encode(
        x=alt.X(f"{xcol}:Q", title=xtitle),
        y=alt.Y("value:Q", title=ytitle),
        color=alt.Color("ranking:N", scale=alt.Scale(range=_CC_RANGE), title=None))
    layers = [line]
    if rule_x is not None:
        layers.append(alt.Chart(pd.DataFrame({"x": [rule_x]})).mark_rule(
            color=theme.RED, strokeDash=[5, 4], strokeWidth=1.5).encode(x="x:Q"))
        if rule_label:
            layers.append(alt.Chart(pd.DataFrame({"x": [rule_x], "t": [rule_label]})).mark_text(
                color=theme.RED, align="left", dx=5, dy=-6, font="JetBrains Mono", fontSize=10
            ).encode(x="x:Q", text="t:N"))
    st.altair_chart(_cc(alt.layer(*layers).properties(height=300)), use_container_width=True)


def cc_bar(df, value_col, xtitle):
    d = df.reset_index().rename(columns={df.index.name or "index": "label"})
    chart = alt.Chart(d).mark_bar(color=theme.ACCENT, size=22).encode(
        x=alt.X(f"{value_col}:Q", title=xtitle),
        y=alt.Y("label:N", sort="-x", title=None))
    st.altair_chart(_cc(chart.properties(height=max(120, 40 * len(d)))), use_container_width=True)


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Redrob Ranking Decision Lab")
    st.caption("Downstream research & explanation layer — NOT the production ranker.")
    st.markdown(f"**Shipped:** V6 battle-proof `{GOLDEN_COMMIT}`")
    st.markdown("**Ranking core:** `frontier-v5`")
    st.markdown("**Dataset:** 100K candidates (frozen blind arbiter)")
    show_tech = st.toggle("Technical details", value=False)
    show_limits = st.toggle("Show research limitations", value=True)
    st.divider()
    st.markdown("**Reproduce V6 release:**")
    st.code("PYTHONHASHSEED=0 python rank.py --release --workers 2 "
            "--candidates candidates.jsonl --out submission.csv\n"
            "sha256sum submission.csv  # -> 8f7f30c68ec30cb6...", language="bash")
    st.divider()
    st.caption(DISCLAIMER)

reg = load_json_safe(CONFIG["registry"])
dec = load_json_safe(CONFIG["omega_decision"])
fr = load_json_safe(CONFIG["omega_frontier"])
cards = load_cards(CONFIG["integrity_cards"])
mani = load_json_safe(CONFIG["metrics_manifest"])
# Test count is read from the manifest (single source of truth) so it can never drift.
tests_passing = mani.data.get("tests_passing") if mani else None
tests_label = f"{tests_passing} passed" if tests_passing else "see metrics_manifest"

# ----------------------------------------------------------------- 1. verdict
st.markdown(theme.rail("Ω OMEGA DECISION SYSTEM", "REDROB HIREFIT · DECISION INSTRUMENT"),
            unsafe_allow_html=True)
st.markdown(theme.verdict_console(VERDICT, GOLDEN_COMMIT, tests_label, hash_ok=True),
            unsafe_allow_html=True)
n_cards = len(cards)
anomalies = sum(1 for c in cards if c.get("evidence_status") == "PROBABLE_CONTRADICTION")
st.markdown(theme.readout([
    (f"{GOLDEN_COMMIT}", "V6 release"),
    (tests_label.split()[0], "Tests passing"),
    (str(SHARED_FACTS["honeypots_in_top100"]), "Integrity-flagged in top-100"),
    (str(anomalies if n_cards else SHARED_FACTS["anachronism_anomalies_top100"]),
     "Anachronism anomalies"),
    ("AWAITING", "Ψ human panel"),
]), unsafe_allow_html=True)
st.info(VERDICT_DISCLAIMER)
st.caption(
    "Nav:  1·Gates → 2·Regret frontier → 3·Integrity reconciliation → 4·Candidate audit → "
    "5·Fusion autopsy → 6·Ψ panel → 7·Study Φ → 8·Timeline → 9·Why V6"
)

# ----------------------------------------------------------------- 2. gates
st.header("1 · Shipping-gate battery")
gate_cols = st.columns(len(GATES))
for col, (name, status, expl) in zip(gate_cols, GATES):
    col.markdown(theme.gate_html(name, status, expl), unsafe_allow_html=True)
C.note("Four computational gates can be tested automatically. The fifth requires external human "
       "evidence and cannot be simulated honestly. PENDING is not a model-performance failure.")

# ----------------------------------------------------------------- 3. regret frontier
st.header("2 · Minimax-regret frontier (simulated worlds)")
if fr:
    df = charts.frontier_frame(fr.data)
    cc_line(df, "λ — simulated integrity-aversion", "human-aligned utility",
            rule_x=0.10, rule_label="λ=0.10")
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
        cc_bar(charts.regret_frame(dec.data), "max_regret", "max regret across simulated worlds")
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
    width="stretch", hide_index=True)
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
                       "anachronism_severity", "reason"]], width="stretch", hide_index=True)
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
cc_bar(charts.fusion_waterfall_frame(0.0072, 0.0128), "contribution", "share of fusion gain")
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
TL = [("Golden baseline", "frozen reproducible production baseline", "FALLBACK"),
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
      ("Rank-space Condorcet (Copeland)", "beats golden 7/7 on blind arbiter (0.8779)", "RESEARCH ONLY"),
      ("Ship Hedge (severity-gated Copeland)", "historical main artifact; superseded by V6", "SUPERSEDED"),
      ("Dominant V4", "feature-only evidence correction; no component regression vs V3", "ADOPTED"),
      ("Frontier V5", "#1 mean7; #1 strongest union; 30/30 composites over main", "RANKING CORE"),
      ("Battle-proof V6", "hash-pinned, fail-closed, OOM-safe atomic release", "SHIPPED")]
for stage, result, label in TL:
    st.markdown(f"- **{stage}** — {result}  ·  `{label}`")

# ----------------------------------------------------------------- 10. why V6
st.header("9 · Why V6 ships")
st.dataframe({
    "Property": ["Seven-evaluator mean", "Composites vs main", "2 CPU / 16 GiB release",
                 "Failure safety", "Independent human lockbox", "Status"],
    "V6 battle-proof": ["0.906553 · #1/673", "30 wins · 0 losses", "136.0 s pipeline",
                 "Hash-pinned · atomic · OOM-safe", "External recruiter slices; own panel pending", "SHIP · 8f7f30c6"],
    "Historical main hedge": ["0.872686 · #11/673", "Baseline", "Historical runtime",
                 "No V6 release envelope", "External recruiter slices", "SUPERSEDED"],
    "Raw Copeland research": ["Narrow proxy gain", "Not universal", "Not release-qualified",
                 "Anachronism exposure", "Missing", "REJECTED"]},
    width="stretch", hide_index=True)
st.success("V6 ships because it has the strongest broad public-field portfolio we can reproduce, "
           "beats main on all 30 tested composites, and adds an exact-output release gate that "
           "fails closed before a bad or partial shortlist can replace the last good artifact.")
st.markdown("**Docs:** `docs/SHIPPING_DECISION.md` · `docs/OMEGA_DECISION_SUMMARY.md` · "
            "`docs/PSI_INTEGRITY_PANEL.md` · `docs/human_opinion/HUMAN_OPINION_LANDSCAPE.md` · "
            "`docs/REPRODUCTION.md`")
if show_tech and reg:
    st.divider()
    st.subheader("Experiment registry (machine-readable spine)")
    st.json(reg.data)
