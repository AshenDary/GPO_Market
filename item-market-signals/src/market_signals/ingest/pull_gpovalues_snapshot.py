"""
Pulls community-solved item values from gpovalues.com's public API and
writes a dated snapshot. This is the PRIMARY value data source for the
project -- real, at-scale (28,000+ observed Discord trades as of writing),
continuously updated, with built-in confidence bands.

See https://gpovalues.com/legal/methodology for how they derive values:
Dijkstra ratio-chains anchored to Mythical Fruit Chest = 10,000, decayed on
12-hour/30-day windows, confidence purely trade-count driven (<200 = low,
200-999 = medium, 1000+ = high).

Run this on a schedule (daily is plenty -- see run() docstring for why).
Each run writes data/snapshots/gpovalues_{date}.csv AND caches the raw JSON
response under data/raw/ for reproducibility.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from config.settings import GPOVALUES_API_URL, GPOVALUES_USER_AGENT, RAW_DIR, SNAPSHOT_DIR

ITEM_COLUMNS = [
    "slug", "name", "shortcut", "value", "ci_low", "ci_high",
    "confidence", "rarity", "tier", "demand", "demand_ratio",
    "trade_count", "derivation", "share_url", "image_url",
]


def fetch_items_json(url: str = GPOVALUES_API_URL, timeout: int = 15) -> dict:
    """Hit the live API. Raises on any non-200 or network error -- callers
    should not silently proceed with stale/partial data."""
    headers = {"User-Agent": GPOVALUES_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def flatten_items(payload: dict) -> pd.DataFrame:
    """Turn the API's {"items": [...]} payload into a flat dataframe.

    Kept separate from fetch_items_json() specifically so this can be unit
    tested against a saved fixture without hitting the network -- see
    tests/test_pull_gpovalues_snapshot.py.
    """
    items = payload.get("items", [])
    df = pd.DataFrame(items)

    cols = [c for c in ITEM_COLUMNS if c in df.columns]
    df = df[cols].copy()

    df["generated_at"] = payload.get("generated_at")
    df["n_trades_used"] = payload.get("n_trades_used")
    df["join_key"] = df["name"].str.lower().str.strip()

    return df


def run(
    snapshot_dir: Path = SNAPSHOT_DIR,
    raw_dir: Path = RAW_DIR,
    snapshot_date: date | None = None,
) -> Path:
    payload = fetch_items_json()
    df = flatten_items(payload)

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    d = (snapshot_date or date.today()).isoformat()

    raw_path = raw_dir / f"gpovalues_raw_{d}.json"
    raw_path.write_text(json.dumps(payload, indent=2))

    out_path = snapshot_dir / f"gpovalues_{d}.csv"
    df.to_csv(out_path, index=False)

    return out_path


if __name__ == "__main__":
    out_path = run()
    print(f"Wrote snapshot -> {out_path}")
