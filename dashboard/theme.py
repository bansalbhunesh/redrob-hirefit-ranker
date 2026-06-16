"""Command Core design system — tokens, global CSS, and HTML builders for the judge-facing
dashboard. Import-light (NO streamlit, NO production imports) so it is testable and reusable
across surfaces. Aesthetic: mission-control instrument — sharp edges, hairline borders, no
shadows, monospace numerals. Indigo accent (no teal).
"""
from __future__ import annotations

# ── tokens (Flight Deck: bright 400-level accents + visible borders on slate, for contrast) ──
BG_VOID = "#020617"; BG_BASE = "#0F172A"; BG_SURFACE = "#1E293B"
BG_ELEVATED = "#334155"; BG_INPUT = "#0B1221"
BORDER = "#475569"; BORDER_ACTIVE = "#64748B"          # borders are VISIBLE, not near-black
TEXT_PRIMARY = "#F1F5F9"; TEXT_SECONDARY = "#CBD5E1"; TEXT_MUTED = "#94A3B8"; TEXT_MONO = "#E2E8F0"
ACCENT = "#38BDF8"; AMBER = "#FBBF24"; RED = "#FB7185"; GREEN = "#4ADE80"; BLUE = "#38BDF8"
FONT_UI = "'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
FONT_MONO = "'JetBrains Mono','SF Mono',Consolas,ui-monospace,monospace"

# status -> (color, marker)
_STATUS = {
    "PASS": (GREEN, "●"), "PENDING": (AMBER, "◐"), "FAIL": (RED, "✕"), "INFO": (BLUE, "●"),
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

.stApp {{ background:{BG_BASE}; color:{TEXT_PRIMARY}; font-family:{FONT_UI}; }}
section.main, .block-container {{ background:{BG_BASE}; }}
.block-container {{ padding-top:2.2rem; max-width:1280px; }}

/* headings */
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
  font-family:{FONT_UI}; color:{TEXT_PRIMARY}; letter-spacing:-0.01em; font-weight:600;
}}
.stApp h2 {{ font-size:1.05rem; text-transform:uppercase; letter-spacing:0.08em;
  color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER}; padding-bottom:.5rem; margin-top:1.6rem; }}
.stApp p, .stApp li, .stApp label, .stMarkdown {{ color:{TEXT_SECONDARY}; }}

/* sharp edges everywhere */
.stApp [data-testid="stVerticalBlock"] > div, .stApp .element-container,
.stButton > button, .stDataFrame, [data-testid="stMetric"] {{ border-radius:0 !important; }}

/* metrics -> terminal readout */
[data-testid="stMetricValue"] {{
  font-family:{FONT_MONO} !important; font-size:30px !important; font-weight:300 !important;
  color:{TEXT_PRIMARY} !important; font-variant-numeric:tabular-nums; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{
  font-family:{FONT_UI} !important; font-size:11px !important; font-weight:600 !important;
  letter-spacing:0.06em !important; text-transform:uppercase !important; color:{TEXT_MUTED} !important; }}

/* dataframes -> blotter */
.stDataFrame, [data-testid="stDataFrame"] {{ border:1px solid {BORDER} !important; font-family:{FONT_MONO} !important; }}
[data-testid="stDataFrame"] thead th, .stDataFrame thead th {{
  background:{BG_SURFACE} !important; color:{TEXT_SECONDARY} !important; text-transform:uppercase !important;
  font-size:11px !important; letter-spacing:0.05em !important; font-weight:600 !important; }}
[data-testid="stDataFrame"] td {{ color:{TEXT_MONO} !important; border-bottom:1px solid {BORDER} !important; }}

/* buttons / inputs */
.stButton > button {{
  background:{BG_SURFACE} !important; color:{TEXT_PRIMARY} !important; border:1px solid {BORDER} !important;
  text-transform:uppercase !important; letter-spacing:0.05em !important; font-size:11px !important;
  font-weight:500 !important; }}
.stButton > button:hover {{ border-color:{ACCENT} !important; background:{BG_ELEVATED} !important; }}
.stTextInput input, .stNumberInput input, [data-baseweb="select"] > div {{
  background:{BG_INPUT} !important; color:{TEXT_PRIMARY} !important; border:1px solid {BORDER} !important;
  border-radius:2px !important; }}
.stSlider [data-baseweb="slider"] {{ color:{ACCENT}; }}

/* code / hashes */
.stApp code, .stCode, pre {{ font-family:{FONT_MONO} !important; color:{TEXT_MONO} !important;
  background:{BG_INPUT} !important; border:1px solid {BORDER} !important; border-radius:2px !important; }}

/* alerts: muted, hairline, sharp (no candy colors) */
[data-testid="stAlert"] {{ border-radius:0 !important; background:{BG_SURFACE} !important;
  border:1px solid {BORDER} !important; border-left:2px solid {BORDER_ACTIVE} !important; color:{TEXT_SECONDARY} !important; }}

/* sidebar */
[data-testid="stSidebar"] {{ background:{BG_VOID}; border-right:1px solid {BORDER}; }}
[data-testid="stSidebar"] * {{ color:{TEXT_SECONDARY}; }}

/* chrome off */
#MainMenu, footer, header [data-testid="stToolbar"] {{ visibility:hidden; }}
[data-testid="stHeader"], header {{ background:{BG_BASE} !important; }}

/* ── command-core HTML blocks ── */
.cc-rail {{ font-family:{FONT_MONO}; font-size:.72rem; letter-spacing:.18em; text-transform:uppercase;
  color:{TEXT_MUTED}; display:flex; justify-content:space-between; align-items:center;
  border-bottom:1px solid {BORDER}; padding-bottom:.5rem; margin:.2rem 0 1rem; }}
.cc-verdict {{ background:linear-gradient(90deg,rgba(217,119,6,.10),rgba(180,83,9,.04));
  border:1px solid {AMBER}; padding:22px 24px; margin:.2rem 0 1.2rem; }}
.cc-verdict .vk {{ font-family:{FONT_MONO}; font-size:.72rem; letter-spacing:.16em; color:{AMBER};
  text-transform:uppercase; }}
.cc-verdict .vv {{ font-family:{FONT_MONO}; font-size:1.7rem; font-weight:400; color:{AMBER};
  letter-spacing:.01em; margin:.25rem 0 .1rem; }}
.cc-verdict .vmeta {{ font-family:{FONT_MONO}; font-size:.8rem; color:{TEXT_MONO}; margin-top:.6rem; }}
.cc-verdict .vmeta b {{ color:{GREEN}; font-weight:500; }}
.cc-gate {{ background:{BG_SURFACE}; border:1px solid {BORDER}; border-left:2px solid var(--gc);
  padding:12px 14px; height:100%; }}
.cc-gate .gm {{ font-family:{FONT_MONO}; color:var(--gc); font-size:.8rem; }}
.cc-gate .gn {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; color:{TEXT_SECONDARY};
  font-weight:600; margin:.35rem 0; line-height:1.35; }}
.cc-gate .gs {{ font-family:{FONT_MONO}; font-size:.72rem; color:var(--gc); letter-spacing:.06em; }}
.cc-gate .gx {{ font-size:.7rem; color:{TEXT_MUTED}; line-height:1.45; margin-top:.4rem; }}
.cc-pill {{ display:inline-block; font-family:{FONT_MONO}; font-size:.66rem; letter-spacing:.08em;
  padding:2px 8px; border-radius:2px; background:{BG_ELEVATED}; border:1px solid var(--gc); color:var(--gc); }}
.cc-readout {{ display:grid; gap:1px; background:{BORDER}; border:1px solid {BORDER};
  grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); margin:.2rem 0 1rem; }}
.cc-readout .cell {{ background:{BG_BASE}; padding:14px 16px; }}
.cc-readout .rv {{ font-family:{FONT_MONO}; font-size:1.5rem; font-weight:300; color:{TEXT_PRIMARY};
  font-variant-numeric:tabular-nums; line-height:1.05; }}
.cc-readout .rl {{ font-size:10.5px; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
  color:{TEXT_MUTED}; margin-top:6px; }}
</style>
"""


def rail(left: str, right: str = "") -> str:
    return f"<div class='cc-rail'><span>{left}</span><span>{right}</span></div>"


def verdict_console(verdict: str, golden: str, tests_label: str, hash_ok: bool = True) -> str:
    chk = f"<b>✓</b>" if hash_ok else "—"
    return (
        f"<div class='cc-verdict'>"
        f"<div class='vk'>⚠ Automatic decision</div>"
        f"<div class='vv'>{verdict}</div>"
        f"<div class='vmeta'>Golden: {golden} &nbsp;|&nbsp; Tests: {tests_label} &nbsp;|&nbsp; "
        f"Hash: {chk}</div></div>"
    )


def readout(cells: list[tuple[str, str]]) -> str:
    inner = "".join(
        f"<div class='cell'><div class='rv'>{v}</div><div class='rl'>{l}</div></div>" for v, l in cells
    )
    return f"<div class='cc-readout'>{inner}</div>"


def gate_html(name: str, status: str, explanation: str) -> str:
    color, marker = _STATUS.get(status, (TEXT_MUTED, "○"))
    return (
        f"<div class='cc-gate' style='--gc:{color}'>"
        f"<span class='gm'>{marker}</span> <span class='gs'>{status}</span>"
        f"<div class='gn'>{name}</div>"
        f"<div class='gx'>{explanation}</div></div>"
    )
