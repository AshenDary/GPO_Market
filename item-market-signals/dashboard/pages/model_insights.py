"""Structural value model diagnostics page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import (
    load_feature_matrix,
    load_tier_reference,
    load_value_regression_model,
)
from dashboard.components.layout import render_refresh_button
from dashboard.components.views import render_model_insights
from market_signals.models.value_regression import InsufficientTrainingDataError


render_refresh_button("refresh_model_insights")

try:
    feature_matrix = load_feature_matrix()
    tier_reference = load_tier_reference()
    value_model = load_value_regression_model()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
except InsufficientTrainingDataError as exc:
    st.warning(str(exc))
    st.stop()

render_model_insights(feature_matrix, value_model, tier_reference)
