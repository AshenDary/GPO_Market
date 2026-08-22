"""Streamlit view functions for the market dashboard.

The dashboard is intentionally thin: data joining, trend guards, item
resolution, and price verdicts stay in the existing package modules.
"""

from __future__ import annotations

from html import escape

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.layout import render_metric_cards
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


def _image_html(image_url: object) -> str:
    if isinstance(image_url, str) and image_url.startswith(("http://", "https://")):
        return f'<img src="{escape(image_url, quote=True)}" alt="">'
    return '<span class="item-image-placeholder">NO IMAGE</span>'


def _render_verdict_panel(row: pd.Series, asking_price: float) -> None:
    low = _as_float(row["ci_low"])
    high = _as_float(row["ci_high"])
    value = _as_float(row["value"])

    if asking_price <= 0 or low is None or high is None or value is None:
        title = "Enter an asking price for a buy/fair/overpriced verdict"
        kicker = "Verdict"
    else:
        verdict_text = verdict(asking_price, value, low, high)
        title = verdict_text
        kicker = f"Asking {_format_value(asking_price)}"

    st.markdown(
        (
            '<div class="verdict-panel">'
            f'<div class="verdict-kicker">{escape(kicker)}</div>'
            f'<div class="verdict-title">{escape(title)}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


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
    render_metric_cards(
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

    quick_picks = (
        df.dropna(subset=["trade_count"])
        .sort_values("trade_count", ascending=False)
        .head(5)["name"]
        .tolist()
    )
    st.markdown('<div class="quick-picks">', unsafe_allow_html=True)
    quick_cols = st.columns(len(quick_picks)) if quick_picks else []
    for idx, item_name in enumerate(quick_picks):
        with quick_cols[idx]:
            if st.button(str(item_name), key=f"quick_pick_{idx}"):
                st.session_state["lookup_item"] = item_name
    st.markdown("</div>", unsafe_allow_html=True)

    if "lookup_item" not in st.session_state and names:
        st.session_state["lookup_item"] = names[0]

    selected = st.selectbox("Item", names, key="lookup_item")
    asking_price = st.number_input("Asking price", min_value=0.0, step=1000.0, value=0.0)

    row = resolve_item(df, selected)
    if row is None:
        _notice(f"No match found for '{selected}'.")
        return

    shortcut = "" if pd.isna(row.get("shortcut", "")) else row.get("shortcut", "")
    trade_count = int(row["trade_count"]) if not pd.isna(row["trade_count"]) else 0
    st.markdown(
        (
            '<div class="lookup-hero">'
            f'<div class="item-image-frame">{_image_html(row.get("image_url"))}</div>'
            '<div>'
            f'<h3 class="item-title">{escape(str(row["name"]))}</h3>'
            f'<p class="item-meta">{escape(str(shortcut))}</p>'
            f'<p class="item-meta">Confidence <span class="num">{escape(str(row["confidence"]))}</span> / '
            f'<span class="num">{trade_count:,}</span> trades observed</p>'
            f'<p class="item-meta">Demand: {escape(str(row.get("demand", "unknown")))}</p>'
            '</div></div>'
        ),
        unsafe_allow_html=True,
    )

    _render_verdict_panel(row, asking_price)
    render_metric_cards(
        [
            ("Solved value", _format_value(row["value"])),
            ("Typical low", _format_value(row["ci_low"])),
            ("Typical high", _format_value(row["ci_high"])),
            ("Confidence", str(row["confidence"])),
            ("Demand", str(row.get("demand", "unknown"))),
            ("Trades observed", f"{trade_count:,}"),
        ],
        class_name="metric-grid--three",
    )
    _render_confidence_band(row, asking_price)
    if row["confidence"] == "low":
        _notice("Low-confidence item: treat this value as directional, not exact.")


def _badge_style(_: object) -> str:
    return (
        "background-color: #161616; "
        "border: 1px solid #8C8C8C; "
        "border-radius: 999px; "
        "color: #F2F2F0; "
        "font-weight: 600; "
        "text-align: center;"
    )


def render_value_list(df: pd.DataFrame) -> None:
    _section_title("Value List")

    tier_col = "tier_tier" if "tier_tier" in df.columns else "tier"
    table_cols = ["image_url", "name", tier_col, "value", "confidence", "demand", "trade_count"]
    table_df = df[table_cols].copy()
    table_df = table_df.rename(columns={tier_col: "tier"})
    table_df["value"] = pd.to_numeric(table_df["value"], errors="coerce").round().astype("Int64")
    table_df["trade_count"] = pd.to_numeric(table_df["trade_count"], errors="coerce").astype("Int64")

    query = st.text_input("Search by item name", key="value_list_search")
    if query.strip():
        table_df = table_df[
            table_df["name"].fillna("").str.contains(query.strip(), case=False, regex=False)
        ]

    table_df = table_df.sort_values("value", ascending=False, na_position="last")
    styled_table = table_df.style.map(_badge_style, subset=["tier", "confidence", "demand"])
    st.dataframe(
        styled_table,
        hide_index=True,
        use_container_width=True,
        height=620,
        row_height=72,
        column_order=["image_url", "name", "tier", "value", "confidence", "demand", "trade_count"],
        column_config={
            "image_url": st.column_config.ImageColumn("Item", width="medium"),
            "name": st.column_config.TextColumn("Name", width="large"),
            "tier": st.column_config.TextColumn("Tier"),
            "value": st.column_config.NumberColumn("Value", format="localized"),
            "confidence": st.column_config.TextColumn("Confidence"),
            "demand": st.column_config.TextColumn("Demand"),
            "trade_count": st.column_config.NumberColumn("Trade count", format="localized"),
        },
    )


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

    item_history = item_history.assign(snapshot_date=pd.to_datetime(item_history["snapshot_date"]))
    fig = go.Figure(
        data=[
            go.Scatter(
                x=item_history["snapshot_date"],
                y=item_history["value"],
                mode="lines+markers",
                line={"color": PALETTE["ink"], "width": 2},
                marker={
                    "symbol": "diamond",
                    "size": 9,
                    "color": PALETTE["surface"],
                    "line": {"color": PALETTE["ink"], "width": 1},
                },
                customdata=item_history["snapshot_date"].dt.strftime("%Y-%m-%d"),
                hovertemplate="Date: %{customdata}<br>Value: %{y:,.0f}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=str(row["name"]),
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["bg"],
        font={"color": PALETTE["muted"], "family": "IBM Plex Sans"},
        hoverlabel={
            "bgcolor": PALETTE["surface"],
            "bordercolor": PALETTE["border"],
            "font_color": PALETTE["ink"],
        },
        margin={"l": 20, "r": 20, "t": 48, "b": 20},
        xaxis={
            "title": {"text": "Snapshot date", "font": {"color": PALETTE["muted"]}},
            "gridcolor": PALETTE["border"],
            "linecolor": PALETTE["border"],
            "tickfont": {"color": PALETTE["muted"]},
        },
        yaxis={
            "title": {"text": "Solved value", "font": {"color": PALETTE["muted"]}},
            "gridcolor": PALETTE["border"],
            "linecolor": PALETTE["border"],
            "tickfont": {"color": PALETTE["muted"]},
            "tickformat": ",.0f",
        },
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
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
