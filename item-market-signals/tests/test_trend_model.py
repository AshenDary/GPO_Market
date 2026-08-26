from pathlib import Path

import pandas as pd

from market_signals.models.trend_model import compute_trend, most_traded


def _write_gpovalues_snapshot(snapshot_dir: Path, date: str, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(snapshot_dir / f"gpovalues_{date}.csv", index=False)


def test_compute_trend_accepts_metric_column(tmp_path: Path) -> None:
    _write_gpovalues_snapshot(
        tmp_path,
        "2026-08-25",
        [
            {"name": "Item A", "tier": "A", "value": 100, "trade_count": 10, "join_key": "item a"},
        ],
    )
    assert compute_trend("item a", tmp_path, value_column="trade_count") is None

    _write_gpovalues_snapshot(
        tmp_path,
        "2026-08-26",
        [
            {"name": "Item A", "tier": "A", "value": 150, "trade_count": 15, "join_key": "item a"},
        ],
    )

    trend = compute_trend("item a", tmp_path, value_column="trade_count")

    assert trend is not None
    assert trend["metric"] == "trade_count"
    assert trend["first_value"] == 10
    assert trend["last_value"] == 15
    assert trend["pct_change"] == 50
    assert trend["direction"] == "up"


def test_most_traded_reads_latest_snapshot_only(tmp_path: Path) -> None:
    _write_gpovalues_snapshot(
        tmp_path,
        "2026-08-25",
        [
            {"name": "Old Leader", "tier": "S", "value": 1, "trade_count": 9999, "join_key": "old leader"},
        ],
    )
    _write_gpovalues_snapshot(
        tmp_path,
        "2026-08-26",
        [
            {"name": "Latest Second", "tier": "A", "value": 200, "trade_count": 20, "join_key": "latest second"},
            {"name": "Latest First", "tier": "B", "value": 100, "trade_count": 30, "join_key": "latest first"},
        ],
    )

    ranking = most_traded(tmp_path, limit=1)

    assert ranking["name"].tolist() == ["Latest First"]
    assert ranking["trade_count"].tolist() == [30]
