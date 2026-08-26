"""Shared Streamlit data loaders that reuse the package pipeline directly."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from market_signals.features.build_feature_matrix import build_feature_matrix
from market_signals.models.trend_model import load_snapshot_history, most_traded

CACHE_TTL_SECONDS = 60 * 60


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_feature_matrix() -> pd.DataFrame:
    """Build the current feature matrix from the latest available snapshots."""
    return build_feature_matrix()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_history() -> pd.DataFrame:
    """Load all gpovalues snapshots for trend views."""
    return load_snapshot_history()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_most_traded(limit: int = 15) -> pd.DataFrame:
    """Load the current most actively traded item ranking."""
    return most_traded(limit=limit)
