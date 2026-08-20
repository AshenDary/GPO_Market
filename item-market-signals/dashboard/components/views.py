"""Streamlit view functions for the market dashboard.

The dashboard is intentionally thin: data joining, trend guards, item
resolution, and price verdicts stay in the existing package modules.
"""

from __future__ import annotations

from html import escape

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from market_signals.evaluator.evaluate import find_item_matches, resolve_item, verdict
from market_signals.models.trend_model import MIN_SNAPSHOTS, compute_trend

PALETTE = {
    "bg": "#0A0A0A",
    "surface": "#161616",
    "border": "#2E2E2E",
    "ink": "#F2F2F0",
    "muted": "#8C8C8C",
}


def _format_value(value: float | int | None) -> str:
    if pd.isna(value):
        return "unknown"
    return f"{value:,.0f}"


def _as_float(value: float | int | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _section_title(label: str) -> None:
    st.markdown(f'<h2 class="section-title">{escape(label)}</h2>', unsafe_allow_html=True)


def _notice(message: str) -> None:
    st.markdown(f'<div class="notice">{escape(message)}</div>', unsafe_allow_html=True)


def _number_span(value: float | int | None) -> str:
    return f'<span class="num">{escape(_format_value(value))}</span>'


def _render_metric_grid(metrics: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="metric-card"><div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div></div>'
        for label, value in metrics
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def _render_price_grid(row: pd.Series) -> None:
    cards = "".join(
        f'<div class="price-card"><div class="price-label">{escape(label)}</div>'
        f'<div class="price-value">{_number_span(value)}</div></div>'
        for label, value in [
            ("Solved value", row["value"]),
            ("Typical low", row["ci_low"]),
            ("Typical high", row["ci_high"]),
        ]
    )
    st.markdown(f'<div class="price-grid">{cards}</div>', unsafe_allow_html=True)


def _position(value: float, low: float, high: float) -> float:
    if high == low:
        return 50.0
    return max(0.0, min(100.0, ((value - low) / (high - low)) * 100))


def _verdict_marker(verdict_text: str) -> str:
    normalized = verdict_text.lower()
    if "good deal" in normalized:
        return "▲"
    if "overpriced" in normalized:
        return "▼"
    return "◆"


def _render_confidence_band(row: pd.Series, asking_price: float = 0.0) -> None:
    low = _as_float(row["ci_low"])
    high = _as_float(row["ci_high"])
    value = _as_float(row["value"])
    asking = _as_float(asking_price) if asking_price > 0 else None

    if low is None or high is None or value is None:
        _notice("Confidence range is unavailable for this item.")
        return

    domain_values = [low, high, value]
    if asking is not None:
        domain_values.append(asking)

    domain_low = min(domain_values)
    domain_high = max(domain_values)
    pad = max((domain_high - domain_low) * 0.08, 1.0)
    domain_low -= pad
    domain_high += pad

    low_pos = _position(low, domain_low, domain_high)
    high_pos = _position(high, domain_low, domain_high)
    value_pos = _position(value, domain_low, domain_high)
    band_left = min(low_pos, high_pos)
    band_width = abs(high_pos - low_pos)

    asking_marker = ""
    asking_label = ""
    verdict_line = ""
    if asking is not None:
        asking_pos = _position(asking, domain_low, domain_high)
        asking_marker = f'<div class="asking-marker" style="left: {asking_pos:.4f}%"></div>'
        asking_label = f"<span>Asking <strong>{escape(_format_value(asking))}</strong></span>"
        verdict_text = verdict(asking, value, low, high)
        verdict_line = (
            f'<p class="verdict-copy"><span class="verdict-mark">{_verdict_marker(verdict_text)}</span>'
            f'<strong>{escape(verdict_text)}</strong></p>'
        )

    st.markdown(
        (
            '<div class="range-panel"><div class="range-label">Confidence band</div>'
            '<div class="range-scale"><div class="range-line"></div>'
            f'<div class="range-band" style="left: {band_left:.4f}%; width: {band_width:.4f}%"></div>'
            f'<div class="range-tick" style="left: {low_pos:.4f}%"></div>'
            f'<div class="range-tick" style="left: {high_pos:.4f}%"></div>'
            f'<div class="range-marker" style="left: {value_pos:.4f}%"></div>{asking_marker}</div>'
            '<div class="range-legend">'
            f'<span>Low <strong>{escape(_format_value(low))}</strong></span>'
            f'<span>Solved <strong>{escape(_format_value(value))}</strong></span>'
            f'<span>High <strong>{escape(_format_value(high))}</strong></span>{asking_label}</div>'
            '<div class="range-caption">Filled diamond marks solved value; '
            'outlined square marks asking price when entered.</div>'
            f'{verdict_line}</div>'
        ),
        unsafe_allow_html=True,
    )


def _style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor(PALETTE["bg"])
    ax.tick_params(colors=PALETTE["muted"])
    ax.xaxis.label.set_color(PALETTE["muted"])
    ax.yaxis.label.set_color(PALETTE["muted"])
    ax.title.set_color(PALETTE["ink"])
    for spine in ax.spines.values():
        spine.set_color(PALETTE["border"])
    ax.grid(True, axis="y", color=PALETTE["border"], linewidth=0.7)


def _render_confidence_bars(confidence_counts: pd.DataFrame) -> None:
    max_items = int(confidence_counts["items"].max())
    rows = []
    for record in confidence_counts.to_dict("records"):
        items = int(record["items"])
        width = (items / max_items) * 100 if max_items else 0
        rows.append(
            f'<div class="bar-row"><div class="bar-label">{escape(str(record["confidence"]))}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width: {width:.4f}%"></div></div>'
            f'<div class="metric-value">{items:,}</div></div>'
        )
    st.markdown(
        f'<div class="chart-panel">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def render_overview(df: pd.DataFrame) -> None:
    _section_title("Market Overview")

    confidence_counts = (
        df["confidence"].fillna("unknown").value_counts().rename_axis("confidence").reset_index(name="items")
    )
    _render_confidence_bars(confidence_counts)

    enriched = int(df["has_tier_enrichment"].fillna(False).sum())
    missing = int((~df["has_tier_enrichment"].fillna(False)).sum())
    _render_metric_grid(
        [
            ("With tier enrichment", f"{enriched:,}"),
            ("Without tier enrichment", f"{missing:,}"),
        ]
    )

    tier_col = "tier_tier" if "tier_tier" in df.columns else "tier"
    chart_df = df.dropna(subset=[tier_col, "value"]).copy()
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=PALETTE["bg"])
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">"]
    for idx, (tier, group) in enumerate(chart_df.groupby(tier_col)):
        ax.scatter(
            group[tier_col],
            group["value"],
            color=PALETTE["ink"],
            edgecolors=PALETTE["border"],
            label=str(tier),
            marker=markers[idx % len(markers)],
            s=32,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Tier")
    ax.set_ylabel("Solved value, log scale")
    ax.set_title("Tier vs solved market value")
    _style_axis(ax)
    legend = ax.legend(
        facecolor=PALETTE["surface"],
        edgecolor=PALETTE["border"],
        labelcolor=PALETTE["muted"],
        fontsize=8,
    )
    for text in legend.get_texts():
        text.set_color(PALETTE["muted"])
    st.pyplot(fig, clear_figure=True)


def render_lookup(df: pd.DataFrame) -> None:
    _section_title("Item Lookup")

    names = sorted(df["name"].dropna().unique())
    query = st.text_input("Search by item name")
    selected = st.selectbox("Or select an item", names, index=0)
    asking_price = st.number_input("Asking price", min_value=0.0, step=1000.0, value=0.0)

    lookup_name = query.strip() or selected
    if query.strip():
        matches = find_item_matches(df, lookup_name)
        if len(matches) > 1:
            _notice(f"Multiple matches for '{lookup_name}'. Be more specific.")
            st.dataframe(matches[["name", "shortcut", "value", "confidence"]], hide_index=True)
            return
        if matches.empty:
            _notice(f"No match found for '{lookup_name}'.")
            return

    row = resolve_item(df, lookup_name)
    if row is None:
        _notice(f"No match found for '{lookup_name}'.")
        return

    shortcut = "" if pd.isna(row.get("shortcut", "")) else row.get("shortcut", "")
    trade_count = int(row["trade_count"]) if not pd.isna(row["trade_count"]) else 0
    st.markdown(
        (
            f'<div class="item-panel"><h3 class="item-title">{escape(str(row["name"]))}</h3>'
            f'<p class="item-meta">{escape(str(shortcut))} / Confidence '
            f'<span class="num">{escape(str(row["confidence"]))}</span> / '
            f'<span class="num">{trade_count:,}</span> trades observed</p>'
            f'<p class="item-meta">Demand: {escape(str(row.get("demand", "unknown")))}</p></div>'
        ),
        unsafe_allow_html=True,
    )

    _render_price_grid(row)
    _render_confidence_band(row, asking_price)
    if row["confidence"] == "low":
        _notice("Low-confidence item: treat this value as directional, not exact.")


def render_trend(df: pd.DataFrame, history: pd.DataFrame | None) -> None:
    _section_title("Trend")

    if history is None or history["snapshot_date"].nunique() < MIN_SNAPSHOTS:
        n_dates = 0 if history is None else history["snapshot_date"].nunique()
        _notice(
            f"Need {MIN_SNAPSHOTS}+ snapshot dates to compute a trend. "
            f"Current snapshot dates: {n_dates}."
        )
        return

    names = sorted(df["name"].dropna().unique())
    selected = st.selectbox("Item", names, key="trend_item")
    row = resolve_item(df, selected)
    if row is None:
        _notice(f"No match found for '{selected}'.")
        return

    trend = compute_trend(row["join_key"])
    item_history = (
        history[history["join_key"] == row["join_key"]]
        .sort_values("snapshot_date")[["snapshot_date", "value"]]
    )
    if trend is None or item_history["snapshot_date"].nunique() < MIN_SNAPSHOTS:
        _notice(f"Not enough snapshot history yet for {row['name']}.")
        return

    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=PALETTE["bg"])
    ax.plot(
        item_history["snapshot_date"],
        item_history["value"],
        color=PALETTE["ink"],
        linewidth=2,
        marker="D",
        markerfacecolor=PALETTE["surface"],
        markeredgecolor=PALETTE["ink"],
    )
    ax.set_xlabel("Snapshot date")
    ax.set_ylabel("Solved value")
    ax.set_title(str(row["name"]))
    _style_axis(ax)
    st.pyplot(fig, clear_figure=True)
    st.markdown(
        (
            '<div class="notice">Trend: '
            f'<strong>{escape(trend["direction"])}</strong> '
            f'<span class="num">{trend["pct_change"]:+.1f}%</span> over '
            f'<span class="num">{trend["n_snapshots"]}</span> snapshots '
            f'<span class="num">({escape(trend["first_date"])} -> {escape(trend["last_date"])})</span>.</div>'
        ),
        unsafe_allow_html=True,
    )
