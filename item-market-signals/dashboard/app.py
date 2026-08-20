"""Streamlit dashboard router with shared frame and top navigation."""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from dashboard.components.styling import apply_dashboard_style


NAV_PAGES = [
    st.Page("pages/overview.py", title="Overview", icon=":material/dashboard:", default=True),
    st.Page("pages/lookup.py", title="Item lookup", icon=":material/search:"),
    st.Page("pages/trend.py", title="Trend", icon=":material/show_chart:"),
    st.Page("pages/guide.py", title="How it works", icon=":material/info:"),
]


st.set_page_config(page_title="Item Market Signals", layout="wide")
apply_dashboard_style()

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

refresh_col, _ = st.columns([0.25, 0.75])
with refresh_col:
    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

page = st.navigation(NAV_PAGES, position="top")
page.run()
