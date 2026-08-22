"""Overview dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import load_feature_matrix
from dashboard.components.layout import render_refresh_button
from dashboard.components.views import render_overview


render_refresh_button("refresh_overview")

try:
    feature_matrix = load_feature_matrix()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

render_overview(feature_matrix)
