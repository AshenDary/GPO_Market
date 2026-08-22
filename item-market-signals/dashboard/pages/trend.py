"""Trend dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import load_feature_matrix, load_history
from dashboard.components.layout import render_refresh_button
from dashboard.components.views import render_trend


render_refresh_button("refresh_trend")

try:
    feature_matrix = load_feature_matrix()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

try:
    snapshot_history = load_history()
except FileNotFoundError:
    snapshot_history = None

render_trend(feature_matrix, snapshot_history)
