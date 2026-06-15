"""Chart DATA builders (import-light; NO streamlit/plotly). Return pandas frames the app
renders with st.line_chart / st.bar_chart, keeping chart logic testable and dependency-free.
"""
from __future__ import annotations

import pandas as pd


def frontier_frame(frontier_json: dict) -> pd.DataFrame:
    """Regret-frontier long->wide frame: index=lambda, columns=rankings (utility per world)."""
    rows = frontier_json.get("frontier", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "lambda" in df.columns:
        df = df.set_index("lambda")
    return df


def preferred_at_lambda(frontier_json: dict, lam: float) -> dict:
    """Given a simulated λ, return per-ranking utility and the preferred ranking (explanatory)."""
    rows = frontier_json.get("frontier", [])
    if not rows:
        return {}
    nearest = min(rows, key=lambda r: abs(r.get("lambda", 0) - lam))
    rankings = {k: v for k, v in nearest.items() if k != "lambda"}
    pref = max(rankings, key=rankings.get) if rankings else None
    return {"lambda": nearest.get("lambda"), "utilities": rankings, "preferred": pref}


def regret_frame(decision_json: dict) -> pd.DataFrame:
    mr = decision_json.get("max_regret", {})
    if not mr:
        return pd.DataFrame()
    return pd.DataFrame({"max_regret": mr}).sort_values("max_regret")


def fusion_waterfall_frame(top5_influence: float, total_gain: float) -> pd.DataFrame:
    """Contribution of the top-5 influential candidates vs the rest of the fusion gain."""
    top5 = max(0.0, min(top5_influence, total_gain))
    rest = max(0.0, total_gain - top5)
    return pd.DataFrame({"contribution": {"top-5 anachronism candidates": top5,
                                          "all other candidates": rest}})
