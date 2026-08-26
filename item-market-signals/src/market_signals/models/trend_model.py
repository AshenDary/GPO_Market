"""
Computes per-item metric trends across accumulated gpovalues snapshots.

MIN_SNAPSHOTS exists for the same reason the old baseline.py had a row
guard: one data point isn't a trend, and pretending otherwise produces a
confident-looking number that means nothing. Run
ingest/pull_gpovalues_snapshot.py on a schedule (daily/every few days) to
build up history -- this module gets more useful the longer you let it run,
not through any extra modeling effort.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import SNAPSHOT_DIR

MIN_SNAPSHOTS = 2


def load_snapshot_history(snapshot_dir: Path = SNAPSHOT_DIR) -> pd.DataFrame:
    """Concatenate every gpovalues_*.csv snapshot into one long dataframe."""
    files = sorted(snapshot_dir.glob("gpovalues_*.csv"))
    if not files:
        raise FileNotFoundError(f"No gpovalues snapshots found in {snapshot_dir}.")

    frames = []
    for f in files:
        df = pd.read_csv(f)
        # filename is gpovalues_{date}.csv -- pull the date back out
        df["snapshot_date"] = f.stem.replace("gpovalues_", "")
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


def _latest_snapshot_file(snapshot_dir: Path = SNAPSHOT_DIR) -> Path:
    files = sorted(snapshot_dir.glob("gpovalues_*.csv"))
    if not files:
        raise FileNotFoundError(f"No gpovalues snapshots found in {snapshot_dir}.")
    return files[-1]


def compute_trend(
    item_join_key: str,
    snapshot_dir: Path = SNAPSHOT_DIR,
    value_column: str = "value",
) -> dict | None:
    """Returns trend info for one item metric, or None without enough history."""
    history = load_snapshot_history(snapshot_dir)
    if value_column not in history.columns:
        raise KeyError(f"Column '{value_column}' not found in gpovalues snapshots.")

    item_history = (
        history[history["join_key"] == item_join_key]
        .sort_values("snapshot_date")
    )

    n_snapshots = item_history["snapshot_date"].nunique()
    if n_snapshots < MIN_SNAPSHOTS:
        return None

    first = item_history.iloc[0]
    last = item_history.iloc[-1]

    pct_change = ((last[value_column] - first[value_column]) / first[value_column]) * 100

    return {
        "metric": value_column,
        "n_snapshots": n_snapshots,
        "first_date": first["snapshot_date"],
        "first_value": first[value_column],
        "last_date": last["snapshot_date"],
        "last_value": last[value_column],
        "pct_change": round(pct_change, 2),
        "direction": "up" if pct_change > 0 else ("down" if pct_change < 0 else "flat"),
    }


def most_traded(snapshot_dir: Path = SNAPSHOT_DIR, limit: int = 15) -> pd.DataFrame:
    """Rank current activity from the latest gpovalues snapshot only."""
    latest_snapshot = _latest_snapshot_file(snapshot_dir)
    snapshot = pd.read_csv(latest_snapshot)
    required_columns = ["name", "tier", "trade_count", "value", "join_key"]
    missing_columns = [col for col in required_columns if col not in snapshot.columns]
    if missing_columns:
        raise KeyError(
            f"Latest gpovalues snapshot is missing columns: {', '.join(missing_columns)}"
        )

    ranking = snapshot[required_columns].copy()
    ranking["trade_count"] = pd.to_numeric(ranking["trade_count"], errors="coerce")
    ranking["value"] = pd.to_numeric(ranking["value"], errors="coerce")
    return (
        ranking.dropna(subset=["trade_count"])
        .sort_values("trade_count", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    import sys

    history = load_snapshot_history()
    n_dates = history["snapshot_date"].nunique()
    print(f"{n_dates} snapshot date(s) found.")

    if n_dates < MIN_SNAPSHOTS:
        print(
            f"Need {MIN_SNAPSHOTS}+ snapshot dates to compute any trend. "
            "Keep running pull_gpovalues_snapshot.py on a schedule."
        )
        sys.exit(0)

    print("\nBiggest movers (first snapshot -> latest):")
    results = []
    for key in history["join_key"].dropna().unique():
        trend = compute_trend(key, SNAPSHOT_DIR)
        if trend:
            name = history[history["join_key"] == key]["name"].iloc[0]
            results.append({"name": name, **trend})

    movers = pd.DataFrame(results).sort_values("pct_change", ascending=False)
    print(movers[["name", "pct_change", "direction", "n_snapshots"]].to_string(index=False))
