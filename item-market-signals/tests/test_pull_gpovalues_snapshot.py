import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_signals.ingest.pull_gpovalues_snapshot import flatten_items

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_gpovalues_response.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_flatten_items_row_count():
    df = flatten_items(_load_fixture())
    assert len(df) == 5


def test_flatten_items_has_expected_columns():
    df = flatten_items(_load_fixture())
    for col in ["name", "value", "ci_low", "ci_high", "confidence", "trade_count"]:
        assert col in df.columns


def test_flatten_items_join_key_normalized():
    df = flatten_items(_load_fixture())
    pcc = df[df["slug"] == "prestige-candy-cane"].iloc[0]
    assert pcc["join_key"] == "prestige candy cane"


def test_flatten_items_carries_metadata():
    df = flatten_items(_load_fixture())
    assert (df["n_trades_used"] == 28996).all()
    assert df["generated_at"].iloc[0] == "2026-08-14T22:15:31.532580+00:00"


def test_flatten_items_preserves_low_confidence_flag():
    df = flatten_items(_load_fixture())
    scepter = df[df["slug"] == "snowcap-scepter"].iloc[0]
    assert scepter["confidence"] == "low"
    assert scepter["trade_count"] == 52
