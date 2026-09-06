"""Item lookup dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import load_feature_matrix, load_tier_reference, load_value_regression_model
from dashboard.components.layout import render_refresh_button
from dashboard.components.views import render_lookup
from market_signals.models.value_regression import InsufficientTrainingDataError


render_refresh_button("refresh_lookup")

try:
    feature_matrix = load_feature_matrix()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

try:
    value_model = load_value_regression_model()
    tier_reference = load_tier_reference()
except (FileNotFoundError, InsufficientTrainingDataError):
    value_model = None
    tier_reference = None

render_lookup(feature_matrix, value_model, tier_reference)
