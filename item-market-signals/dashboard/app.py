"""Streamlit dashboard for exploring the current item market snapshots."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from dashboard.components.data import load_feature_matrix, load_history
from dashboard.components.views import render_lookup, render_overview, render_trend


st.set_page_config(page_title="Item Market Signals", layout="wide")
st.title("Item Market Signals")
st.caption("Live evaluator for fair values, confidence, tier context, and snapshot trends.")

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
