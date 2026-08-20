"""Central dashboard styling so presentation stays out of data modules."""

from __future__ import annotations

from textwrap import dedent

import streamlit as st


def apply_dashboard_style() -> None:
    """Inject the app's fixed monochrome visual system."""
    st.markdown(
        dedent(
            """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

        :root {
            --bg: #0A0A0A;
            --surface: #161616;
            --border: #2E2E2E;
            --ink: #F2F2F0;
            --muted: #8C8C8C;
        }

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"] {
            background: var(--bg);
            color: var(--ink);
            font-family: 'IBM Plex Sans', sans-serif;
        }

        #MainMenu,
        footer {
            display: none;
        }

        [data-testid="stHeader"] {
            background: var(--bg);
            border-bottom: 1px solid var(--border);
        }

        [data-testid="stTopNavSection"] {
            border-bottom: 1px solid var(--border);
        }

        [data-testid="stTopNavLinkContainer"] a {
            color: var(--muted);
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
        }

        [data-testid="stTopNavLinkContainer"] a[aria-current="page"] {
            color: var(--ink);
            text-decoration: underline;
            text-decoration-thickness: 1px;
            text-underline-offset: 0.35rem;
        }

        [data-testid="stAppViewBlockContainer"] {
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }

        * {
            font-family: 'IBM Plex Sans', sans-serif;
            letter-spacing: 0;
        }

        code,
        pre,
        kbd,
        .num,
        [data-testid="stMetricValue"],
        [data-testid="stNumberInput"] input {
            font-family: 'IBM Plex Mono', monospace;
        }

        h1,
        h2,
        h3,
        .app-kicker,
        .section-title,
        .item-title {
            color: var(--ink);
            font-family: 'IBM Plex Sans', sans-serif;
            letter-spacing: 0;
        }

        p,
        label,
        .stMarkdown,
        [data-testid="stWidgetLabel"],
        [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        .app-shell {
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.5rem;
            padding-bottom: 1.25rem;
        }

        .app-kicker {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 600;
            margin-bottom: 0.4rem;
            text-transform: uppercase;
        }

        .app-title {
            color: var(--ink);
            font-size: 2.6rem;
            font-weight: 700;
            line-height: 1;
            margin: 0;
        }

        .app-subtitle {
            color: var(--muted);
            font-size: 1rem;
            margin: 0.75rem 0 0;
            max-width: 760px;
        }

        .section-title {
            border-bottom: 1px solid var(--border);
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0 0 1rem;
            padding-bottom: 0.6rem;
        }

        .metric-grid,
        .price-grid {
            display: grid;
            gap: 1px;
            margin: 1rem 0 1.25rem;
        }

        .metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .price-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .metric-card,
        .price-card,
        .item-panel,
        .range-panel,
        .notice,
        .chart-panel {
            background: var(--surface);
            border: 1px solid var(--border);
        }

        .metric-card,
        .price-card {
            min-height: 92px;
            padding: 1rem;
        }

        .metric-label,
        .price-label,
        .bar-label,
        .range-label,
        .range-caption,
        .history-meta {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 500;
        }

        .metric-value,
        .price-value {
            color: var(--ink);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.55rem;
            font-weight: 600;
            margin-top: 0.45rem;
        }

        .item-panel,
        .range-panel,
        .chart-panel {
            margin-top: 1rem;
            padding: 1rem;
        }

        .item-title {
            font-size: 1.45rem;
            font-weight: 700;
            margin: 0 0 0.35rem;
        }

        .item-meta,
        .verdict-copy {
            color: var(--muted);
            margin: 0.2rem 0;
        }

        .verdict-mark {
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 700;
            margin-right: 0.35rem;
        }

        .verdict-copy strong {
            color: var(--ink);
            font-weight: 700;
        }

        .notice {
            color: var(--muted);
            margin: 1rem 0;
            padding: 0.9rem 1rem;
        }

        .bar-row {
            display: grid;
            grid-template-columns: minmax(96px, 150px) 1fr minmax(54px, auto);
            gap: 1rem;
            margin: 0.7rem 0;
            align-items: center;
        }

        .bar-track {
            background: var(--border);
            height: 1px;
            position: relative;
        }

        .bar-fill {
            background: var(--ink);
            height: 5px;
            left: 0;
            position: absolute;
            top: -2px;
        }

        .range-scale {
            height: 42px;
            margin: 0.35rem 0 0.6rem;
            position: relative;
        }

        .range-line {
            background: var(--border);
            height: 1px;
            left: 0;
            position: absolute;
            right: 0;
            top: 21px;
        }

        .range-band {
            background: var(--muted);
            height: 3px;
            position: absolute;
            top: 20px;
        }

        .range-tick {
            background: var(--ink);
            height: 15px;
            position: absolute;
            top: 14px;
            width: 1px;
        }

        .range-marker {
            background: var(--ink);
            border: 1px solid var(--ink);
            height: 13px;
            position: absolute;
            top: 15px;
            transform: translateX(-50%) rotate(45deg);
            width: 13px;
        }

        .asking-marker {
            background: var(--surface);
            border: 1px solid var(--ink);
            height: 12px;
            position: absolute;
            top: 15px;
            transform: translateX(-50%);
            width: 12px;
        }

        .range-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: space-between;
        }

        .range-legend span {
            color: var(--muted);
            font-size: 0.78rem;
        }

        .range-legend strong {
            color: var(--ink);
            font-family: 'IBM Plex Mono', monospace;
            font-weight: 600;
        }

        .range-caption {
            margin-top: 0.85rem;
        }

        div[data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--border);
            gap: 0.85rem;
        }

        button[data-baseweb="tab"] {
            background: var(--bg);
            border-bottom: 1px solid var(--border);
            color: var(--muted);
            font-weight: 600;
            padding: 0.75rem 0.2rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--ink);
            border-bottom: 1px solid var(--ink);
        }

        .stButton > button,
        [data-testid="stBaseButton-secondary"] {
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--ink);
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
        }

        .stButton > button:hover,
        [data-testid="stBaseButton-secondary"]:hover {
            background: var(--border);
            border: 1px solid var(--ink);
            color: var(--ink);
        }

        input,
        textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] {
            background: var(--surface);
            border-color: var(--border);
            color: var(--ink);
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--border);
        }

        @media (max-width: 760px) {
            [data-testid="stAppViewBlockContainer"] {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .app-title {
                font-size: 2rem;
            }

            .metric-grid,
            .price-grid {
                grid-template-columns: 1fr;
            }

            .bar-row {
                grid-template-columns: 1fr;
                gap: 0.4rem;
            }
        }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )
