"""Shared dashboard layout fragments that do not touch market data logic."""

from __future__ import annotations

from html import escape
from textwrap import dedent

import streamlit as st


FOOTER_LINKS: tuple[tuple[str, str], ...] = (
    (
        "Grand Piece Online Wiki",
        "https://grand-piece-online.fandom.com/wiki/Grand_Piece_Online_Wiki",
    ),
    (
        "Game Content",
        "https://grand-piece-online.fandom.com/wiki/Game_Content",
    ),
    (
        "Devil Fruits",
        "https://grand-piece-online.fandom.com/wiki/Devil_Fruits",
    ),
    (
        "Updates",
        "https://grand-piece-online.fandom.com/wiki/Updates",
    ),
    ("gpovalues.com", "https://gpovalues.com"),
)


def render_refresh_button(key: str) -> None:
    """Clear Streamlit's cached data loaders for pages backed by snapshots."""
    refresh_col, _ = st.columns([0.25, 0.75])
    with refresh_col:
        if st.button("Refresh data", key=key):
            st.cache_data.clear()
            st.rerun()


def render_footer(repo_url: str) -> None:
    """Render muted project/resource credits below each routed page."""
    links = " / ".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noreferrer">{escape(label)}</a>'
        for label, url in (*FOOTER_LINKS, ("GitHub repo", repo_url))
    )
    st.markdown(
        dedent(
            f"""
        <div class="app-footer">
            <span>Sources and references:</span> {links}
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )
