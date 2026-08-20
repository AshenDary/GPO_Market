"""How-it-works guide page for first-time dashboard visitors."""

from __future__ import annotations

import streamlit as st


st.markdown("<h2 class='section-title'>How It Works</h2>", unsafe_allow_html=True)

st.markdown(
    """
This tool estimates fair value for a Grand Piece Online trade item, shows a
confidence band around that estimate, adds trend context when enough history
exists, and gives a plain verdict: good deal, fair, or overpriced.

### Data sources

- Primary source: [gpovalues.com](https://gpovalues.com), which publishes solved
  item values from observed Discord trades.
- Method details: [gpovalues methodology](https://gpovalues.com/legal/methodology).
- This project reads their public API and does not scrape Discord directly.
- Secondary source: a curated tier-list JSON used for structural context
  (category, rarity, obtainability). It does not provide market prices.

### Confidence labels

The confidence label comes from gpovalues trade-count bands and is shown as
low, medium, or high. Low-confidence values are still useful, but should be
read as directional rather than exact.

### Trend interpretation

Trend compares item value across dated snapshots. It only appears when there
are multiple snapshot dates, so some items may still show "not enough snapshot
history yet" while data continues to accumulate.

### Coverage limits

Only items that gpovalues has price data for appear in this dashboard. This is
not a full catalog of every item in the game.

### Where to go next

Use Overview for the current catalog, Item lookup to check a specific
item/asking price, and Trend to inspect value history over time.
"""
)
