from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from market_signals.decisions.log import (
    AmbiguousItemMatchError,
    MissingItemPriceError,
    ResaleAlreadyRecordedError,
    ResaleWithoutPurchaseError,
    build_decision_entry,
    load_decision_log,
    log_decision,
    record_resale_outcome,
    recompute_saved_verdict,
)


FIXED_TIME = datetime(2026, 9, 26, 12, 30, tzinfo=timezone.utc)


def _write_snapshot(snapshot_dir: Path, snapshot_date: str, rows: list[dict[str, object]]) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"gpovalues_{snapshot_date}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _row(name: str, **overrides: object) -> dict[str, object]:
    base = {
        "slug": name.lower().replace(" ", "-"),
        "name": name,
        "shortcut": "",
        "value": 100.0,
        "ci_low": 90.0,
        "ci_high": 110.0,
        "confidence": "medium",
        "rarity": "Legendary",
        "tier": "A",
        "demand": "Stable Demand",
        "demand_ratio": 1.2,
        "trade_count": 250,
        "derivation": "test",
        "share_url": "https://example.test/item",
        "image_url": "https://example.test/item.png",
        "generated_at": "2026-09-26T01:00:00+00:00",
        "n_trades_used": 12345,
        "join_key": name.lower().strip(),
    }
    return {**base, **overrides}


def test_logs_buy_entry_with_snapshot_provenance(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    log_path = tmp_path / "decision_log.csv"
    _write_snapshot(snapshot_dir, "2026-09-26", [_row("Prestige Candy Cane", shortcut="PCC")])

    entry = log_decision(
        "Prestige Candy Cane",
        80.0,
        True,
        purchase_price=78.0,
        snapshot_dir=snapshot_dir,
        log_path=log_path,
        decision_timestamp=FIXED_TIME,
    )
    saved = load_decision_log(log_path).iloc[0]

    assert entry["verdict"] == "GOOD DEAL -- asking price is below the typical trade range"
    assert saved["snapshot_date"] == "2026-09-26"
    assert saved["snapshot_file"] == "gpovalues_2026-09-26.csv"
    assert saved["snapshot_generated_at"] == "2026-09-26T01:00:00+00:00"
    assert saved["item_slug"] == "prestige-candy-cane"
    assert bool(saved["bought"]) is True
    assert saved["purchase_price"] == pytest.approx(78.0)


def test_logs_no_buy_entry_without_purchase_price(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    log_path = tmp_path / "decision_log.csv"
    _write_snapshot(snapshot_dir, "2026-09-26", [_row("Candy Cane")])

    log_decision(
        "Candy Cane",
        125.0,
        False,
        snapshot_dir=snapshot_dir,
        log_path=log_path,
        decision_timestamp=FIXED_TIME,
    )
    saved = load_decision_log(log_path).iloc[0]

    assert saved["verdict"] == "OVERPRICED -- asking price is above the typical trade range"
    assert bool(saved["bought"]) is False
    assert pd.isna(saved["purchase_price"])
    assert pd.isna(saved["resale_price"])


def test_ambiguous_item_matches_are_rejected(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    _write_snapshot(
        snapshot_dir,
        "2026-09-26",
        [_row("Candy Cane"), _row("Prestige Candy Cane", shortcut="PCC")],
    )

    with pytest.raises(AmbiguousItemMatchError, match="Multiple matches"):
        build_decision_entry("cane", 100.0, False, snapshot_dir=snapshot_dir)


def test_missing_price_fields_are_rejected(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    _write_snapshot(snapshot_dir, "2026-09-26", [_row("Mystery Item", value=None)])

    with pytest.raises(MissingItemPriceError, match="value"):
        build_decision_entry("Mystery Item", 100.0, False, snapshot_dir=snapshot_dir)


def test_saved_verdict_reproduces_without_newer_snapshots(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    old_snapshot = _write_snapshot(snapshot_dir, "2026-09-10", [_row("Candy Cane", value=100, ci_low=90, ci_high=110)])
    _write_snapshot(snapshot_dir, "2026-09-26", [_row("Candy Cane", value=1000, ci_low=900, ci_high=1100)])

    entry = build_decision_entry(
        "Candy Cane",
        95.0,
        False,
        snapshot_path=old_snapshot,
        snapshot_dir=snapshot_dir,
        decision_timestamp=FIXED_TIME,
    )

    assert entry["snapshot_file"] == "gpovalues_2026-09-10.csv"
    assert entry["verdict"] == "FAIR -- asking price is at or below the solved fair value"
    assert recompute_saved_verdict(entry) == entry["verdict"]


def test_records_actual_resale_without_marked_value_fields(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    log_path = tmp_path / "decision_log.csv"
    _write_snapshot(snapshot_dir, "2026-09-26", [_row("Candy Cane")])
    entry = log_decision(
        "Candy Cane",
        80.0,
        True,
        purchase_price=80.0,
        snapshot_dir=snapshot_dir,
        log_path=log_path,
        decision_timestamp=FIXED_TIME,
    )

    updated = record_resale_outcome(
        str(entry["decision_id"]),
        120.0,
        resale_date="2026-10-10",
        log_path=log_path,
    )

    assert updated["resale_date"] == "2026-10-10"
    assert updated["resale_price"] == pytest.approx(120.0)
    assert pd.isna(updated["marked_value"])
    assert pd.isna(updated["marked_value_source"])
    with pytest.raises(ResaleAlreadyRecordedError):
        record_resale_outcome(str(entry["decision_id"]), 130.0, log_path=log_path)


def test_rejects_resale_for_no_buy_decision(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    log_path = tmp_path / "decision_log.csv"
    _write_snapshot(snapshot_dir, "2026-09-26", [_row("Candy Cane")])
    entry = log_decision(
        "Candy Cane",
        125.0,
        False,
        snapshot_dir=snapshot_dir,
        log_path=log_path,
        decision_timestamp=FIXED_TIME,
    )

    with pytest.raises(ResaleWithoutPurchaseError):
        record_resale_outcome(str(entry["decision_id"]), 120.0, log_path=log_path)
