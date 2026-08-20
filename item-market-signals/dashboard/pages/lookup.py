"""Item lookup dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import load_feature_matrix
from dashboard.components.views import render_lookup


try:
    feature_matrix = load_feature_matrix()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

render_lookup(feature_matrix)
