from pathlib import Path

import pandas as pd
import pytest

from market_signals.models.value_regression import (
    InsufficientTrainingDataError,
    encode_feature_frame,
    predict_value,
    prepare_feature_frame,
    train_value_regression,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "value_regression_items.csv"


def _fixture() -> pd.DataFrame:
    return pd.read_csv(FIXTURE_PATH)


def test_min_training_samples_guard_triggers_below_threshold() -> None:
    df = _fixture().head(2)

    with pytest.raises(InsufficientTrainingDataError, match="Need at least 3"):
        train_value_regression(df, min_training_samples=3)


def test_encoding_produces_sane_output() -> None:
    df = _fixture()
    model = train_value_regression(df, min_training_samples=5)

    prepared = prepare_feature_frame(df)
    encoded = encode_feature_frame(model, prepared)

    assert not encoded.empty
    assert not encoded.isna().any().any()
    assert any("tier_ordinal" in column for column in encoded.columns)
    assert any("is_unstable" in column for column in encoded.columns)


def test_higher_tier_predicts_higher_value_all_else_equal() -> None:
    df = _fixture()
    model = train_value_regression(df, min_training_samples=5)
    low_tier = {
        "tier_ordinal": 2,
        "sub_tier_ordinal": 2,
        "demand_ordinal": 2,
        "demand_ratio": 1.0,
        "category": "Weapon",
        "obtainability": "DROP",
        "is_unstable": False,
        "is_unobtainable": False,
    }
    high_tier = {**low_tier, "tier_ordinal": 8}

    assert predict_value(model, high_tier) > predict_value(model, low_tier)
