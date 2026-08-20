"""Streamlit dashboard for exploring the current item market snapshots."""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from dashboard.components.data import load_feature_matrix, load_history
from dashboard.components.styling import apply_dashboard_style
from dashboard.components.views import render_lookup, render_overview, render_trend


st.set_page_config(page_title="Item Market Signals", layout="wide")
apply_dashboard_style()

if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

st.markdown(
    dedent(
        """
    <div class="app-shell">
        <div class="app-kicker">Grand Piece Online market intelligence</div>
        <h1 class="app-title">Item Market Signals</h1>
        <p class="app-subtitle">
            Fair values, confidence bands, tier context, and snapshot trends
            from the latest tracked market data.
        </p>
    </div>
    """,
    ).strip(),
    unsafe_allow_html=True,
)

try:
    feature_matrix = load_feature_matrix()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

try:
    snapshot_history = load_history()
except FileNotFoundError:
    snapshot_history = None

overview_tab, lookup_tab, trend_tab = st.tabs(["Overview", "Item lookup", "Trend"])

with overview_tab:
    render_overview(feature_matrix)

with lookup_tab:
    render_lookup(feature_matrix)

with trend_tab:
    render_trend(feature_matrix, snapshot_history)
