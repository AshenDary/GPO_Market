"""Trade simulator dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import load_feature_matrix, load_value_regression_model
from dashboard.components.layout import render_refresh_button
from dashboard.components.views import render_trade_simulator
from market_signals.models.value_regression import InsufficientTrainingDataError


render_refresh_button("refresh_simulator")

try:
    feature_matrix = load_feature_matrix()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

try:
    value_model = load_value_regression_model()
except (FileNotFoundError, InsufficientTrainingDataError):
    value_model = None

render_trade_simulator(feature_matrix, value_model)
