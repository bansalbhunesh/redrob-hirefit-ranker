"""Streamlit render helpers (imports streamlit; UI only — never imported by production or tests)."""
from __future__ import annotations

import streamlit as st

from dashboard.constants import STATUS_COLORS


def verdict_banner(verdict, subtitle):
    st.markdown(
        f"<div style='padding:1.2rem;border:2px solid #1b8a5a;border-radius:10px;background:#f3faf6'>"
        f"<div style='font-size:2.2rem;font-weight:800;color:#14532d'>{verdict}</div>"
        f"<div style='font-size:1rem;color:#333;margin-top:.4rem'>{subtitle}</div></div>",
        unsafe_allow_html=True)


def metric_row(metrics: list[tuple[str, str]]):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def gate_card(name, status, explanation):
    color = STATUS_COLORS.get(status, "#444")
    st.markdown(
        f"<div style='padding:.7rem;border-left:6px solid {color};background:#fafafa;margin:.3rem 0'>"
        f"<b>{name}</b> &nbsp;<span style='color:{color};font-weight:700'>[{status}]</span><br>"
        f"<span style='color:#444;font-size:.9rem'>{explanation}</span></div>",
        unsafe_allow_html=True)


def note(text):
    st.caption("ℹ️ " + text)
