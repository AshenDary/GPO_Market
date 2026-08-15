import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_signals.ingest.parse_tier_dataset import (
    build_feature_matrix,
    clean_item_name,
    flatten_tier_classified,
)


def test_clean_item_name_with_alias():
    name, alias = clean_item_name("Prestige Candy Cane (+PCC)")
    assert name == "Prestige Candy Cane"
    assert alias == "PCC"


def test_clean_item_name_without_alias():
    name, alias = clean_item_name("Dominus Ultimus")
    assert name == "Dominus Ultimus"
    assert alias is None


def test_flatten_tier_classified_flat_list():
    tier_dict = {"EXCLUSIVE": ["Cool Shades", "Marine Cape"]}
    df = flatten_tier_classified(tier_dict)
    assert len(df) == 2
    assert set(df["tier"]) == {"EXCLUSIVE"}
    assert df["sub_tier"].isna().all()


def test_flatten_tier_classified_nested():
    tier_dict = {
        "SS_TIER": {
            "High_Tier": ["Candy Cane (+CC)"],
            "Mid_Tier": ["Dominus Ultimus"],
        }
    }
    df = flatten_tier_classified(tier_dict)
    assert len(df) == 2
    assert set(df["tier"]) == {"SS"}
    assert set(df["sub_tier"]) == {"High Tier", "Mid Tier"}


@pytest.fixture
def sample_json(tmp_path):
    data = {
        "most_traded_spotlight": [
            {
                "item_id": "candy_cane",
                "item_name": "Candy Cane",
                "alias": "CC",
                "tier": "SS",
                "sub_tier": "High Tier",
                "demand_status": "High Demand",
                "rarity_score": 9,
                "popularity_score": 8,
                "is_unstable": True,
                "obtainability": "UNOB",
                "is_unobtainable": True,
                "category": "Weapon",
                "market_notes": "test",
            }
        ],
        "tier_classified_items": {
            "SS_TIER": {"High_Tier": ["Candy Cane (+CC)"], "Mid_Tier": [], "Low_Tier": []},
            "F_TIER": ["Dark Root"],
        },
    }
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(data))
    return path


def test_build_feature_matrix_joins_spotlight_data(sample_json):
    fm = build_feature_matrix(sample_json)
    candy_cane = fm[fm["item_name"] == "Candy Cane"].iloc[0]

    assert candy_cane["tier_ordinal"] == 8
    assert candy_cane["demand_ordinal"] == 3
    assert candy_cane["has_detailed_record"] == True  # noqa: E712
    assert candy_cane["rarity_score"] == 9

    dark_root = fm[fm["item_name"] == "Dark Root"].iloc[0]
    assert dark_root["tier_ordinal"] == 1
    assert dark_root["has_detailed_record"] == False  # noqa: E712
    assert pd.isna(dark_root["rarity_score"])
