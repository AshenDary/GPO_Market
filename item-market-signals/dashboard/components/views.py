"""Streamlit view functions for the market dashboard.

The dashboard is intentionally thin: data joining, trend guards, item
resolution, and price verdicts stay in the existing package modules.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from market_signals.evaluator.evaluate import find_item_matches, resolve_item, verdict
from market_signals.models.trend_model import MIN_SNAPSHOTS, compute_trend


def _format_value(value: float | int | None) -> str:
    if pd.isna(value):
        return "unknown"
    return f"{value:,.0f}"


def render_overview(df: pd.DataFrame) -> None:
    st.subheader("Market Overview")

    confidence_counts = (
        df["confidence"].fillna("unknown").value_counts().rename_axis("confidence").reset_index(name="items")
    )
    st.bar_chart(confidence_counts, x="confidence", y="items")

    enriched = int(df["has_tier_enrichment"].fillna(False).sum())
    missing = int((~df["has_tier_enrichment"].fillna(False)).sum())
    col_a, col_b = st.columns(2)
    col_a.metric("With tier enrichment", f"{enriched:,}")
    col_b.metric("Without tier enrichment", f"{missing:,}")

    tier_col = "tier_tier" if "tier_tier" in df.columns else "tier"
    chart_df = df.dropna(subset=[tier_col, "value"]).copy()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for tier, group in chart_df.groupby(tier_col):
        ax.scatter(group[tier_col], group["value"], alpha=0.6, label=str(tier), s=28)
    ax.set_yscale("log")
    ax.set_xlabel("Tier")
    ax.set_ylabel("Solved value, log scale")
    ax.set_title("Tier vs solved market value")
    ax.grid(True, which="both", axis="y", alpha=0.25)
    st.pyplot(fig, clear_figure=True)


def render_lookup(df: pd.DataFrame) -> None:
    st.subheader("Item Lookup")

    names = sorted(df["name"].dropna().unique())
    query = st.text_input("Search by item name")
    selected = st.selectbox("Or select an item", names, index=0)
    asking_price = st.number_input("Asking price", min_value=0.0, step=1000.0, value=0.0)

    lookup_name = query.strip() or selected
    if query.strip():
        matches = find_item_matches(df, lookup_name)
        if len(matches) > 1:
            st.warning(f"Multiple matches for '{lookup_name}'. Be more specific.")
            st.dataframe(matches[["name", "shortcut", "value", "confidence"]], hide_index=True)
            return
        if matches.empty:
            st.error(f"No match found for '{lookup_name}'.")
            return

    row = resolve_item(df, lookup_name)
    if row is None:
        st.error(f"No match found for '{lookup_name}'.")
        return

    st.markdown(f"### {row['name']} ({row.get('shortcut', '')})")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Fair value", _format_value(row["value"]))
    col_b.metric("Typical low", _format_value(row["ci_low"]))
    col_c.metric("Typical high", _format_value(row["ci_high"]))

    st.write(f"**Confidence:** {row['confidence']} ({int(row['trade_count'])} trades observed)")
    st.write(f"**Demand:** {row.get('demand', 'unknown')}")
    if row["confidence"] == "low":
        st.info("Low-confidence item: treat this value as directional, not exact.")

    if asking_price > 0:
        st.write(
            f"**Asking price {_format_value(asking_price)}:** "
            f"{verdict(asking_price, row['value'], row['ci_low'], row['ci_high'])}"
        )


def render_trend(df: pd.DataFrame, history: pd.DataFrame | None) -> None:
    st.subheader("Trend")

    if history is None or history["snapshot_date"].nunique() < MIN_SNAPSHOTS:
        n_dates = 0 if history is None else history["snapshot_date"].nunique()
        st.info(
            f"Need {MIN_SNAPSHOTS}+ snapshot dates to compute a trend. "
            f"Current snapshot dates: {n_dates}."
        )
        return

    names = sorted(df["name"].dropna().unique())
    selected = st.selectbox("Item", names, key="trend_item")
    row = resolve_item(df, selected)
    if row is None:
        st.error(f"No match found for '{selected}'.")
        return

    trend = compute_trend(row["join_key"])
    item_history = (
        history[history["join_key"] == row["join_key"]]
        .sort_values("snapshot_date")[["snapshot_date", "value"]]
    )
    if trend is None or item_history["snapshot_date"].nunique() < MIN_SNAPSHOTS:
        st.info(f"Not enough snapshot history yet for {row['name']}.")
        return

    st.line_chart(item_history, x="snapshot_date", y="value")
    st.write(
        f"Trend: **{trend['direction']} {trend['pct_change']:+.1f}%** over "
        f"{trend['n_snapshots']} snapshots ({trend['first_date']} -> {trend['last_date']})."
    )

