"""
Parses a raw tier-list JSON snapshot (see data/raw/) into a flat feature
matrix and writes it to data/snapshots/feature_matrix_{date}.csv.

Every run writes a NEW timestamped file rather than overwriting the last one.
That's deliberate: once you have several snapshots you can concatenate them
(see scripts/run_feature_build.py) into a long-format table and start
tracking how an item's tier or demand status moves over time, which is the
actual "trend" data this project needs.
"""

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

from config.settings import (
    DEMAND_ORDINAL,
    SNAPSHOT_DIR,
    SUB_TIER_ORDINAL,
    TIER_KEY_MAP,
    TIER_ORDINAL,
)

NAME_ALIAS_RE = re.compile(r"^(.*?)\s*\((\+?[^)]+)\)\s*$")


def clean_item_name(raw: str):
    """'Prestige Candy Cane (+PCC)' -> ('Prestige Candy Cane', 'PCC')"""
    m = NAME_ALIAS_RE.match(raw.strip())
    if m:
        return m.group(1).strip(), m.group(2).lstrip("+").strip()
    return raw.strip(), None


def flatten_tier_classified(tier_dict: dict) -> pd.DataFrame:
    rows = []
    for raw_tier_key, contents in tier_dict.items():
        tier_label = TIER_KEY_MAP.get(raw_tier_key, raw_tier_key)

        if isinstance(contents, list):
            for raw_name in contents:
                name, alias = clean_item_name(raw_name)
                rows.append({
                    "item_name": name,
                    "alias_from_tierlist": alias,
                    "tier": tier_label,
                    "sub_tier": None,
                })
        elif isinstance(contents, dict):
            for sub_tier_key, items in contents.items():
                sub_tier_label = sub_tier_key.replace("_", " ")
                for raw_name in items:
                    name, alias = clean_item_name(raw_name)
                    rows.append({
                        "item_name": name,
                        "alias_from_tierlist": alias,
                        "tier": tier_label,
                        "sub_tier": sub_tier_label,
                    })

    df = pd.DataFrame(rows)
    df["join_key"] = df["item_name"].str.lower().str.strip()
    return df


def load_spotlight(spotlight_list: list) -> pd.DataFrame:
    df = pd.DataFrame(spotlight_list)
    df["join_key"] = df["item_name"].str.lower().str.strip()
    return df


def build_feature_matrix(json_path: str | Path) -> pd.DataFrame:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tier_df = flatten_tier_classified(data["tier_classified_items"])
    spotlight_df = load_spotlight(data["most_traded_spotlight"])

    spotlight_cols = [
        c for c in spotlight_df.columns
        if c not in ("tier", "sub_tier", "item_name", "join_key")
    ]
    merged = tier_df.merge(
        spotlight_df[["join_key"] + spotlight_cols], on="join_key", how="left",
    )

    merged["alias"] = merged["alias"].fillna(merged["alias_from_tierlist"])

    merged["tier_ordinal"] = merged["tier"].map(TIER_ORDINAL)
    merged["sub_tier_ordinal"] = merged["sub_tier"].map(SUB_TIER_ORDINAL)
    merged["demand_ordinal"] = merged["demand_status"].map(DEMAND_ORDINAL)

    for col in ("is_unstable", "is_unobtainable"):
        if col in merged.columns:
            merged[col] = merged[col].astype("boolean")

    merged["has_detailed_record"] = merged["rarity_score"].notna()

    # Transparent, hand-weighted placeholder -- used ONLY as a fallback when
    # an item doesn't appear in the gpovalues API snapshot at all (e.g. very
    # obscure items, or exclusives that trade off-channel and are
    # under-sampled per their own methodology page). Never treat this as a
    # substitute for a real solved value when one exists.
    merged["fallback_value_score"] = (
        merged["tier_ordinal"].fillna(0) * 2
        + merged["rarity_score"].fillna(merged["tier_ordinal"].fillna(0) * 1.1)
        + merged["popularity_score"].fillna(0)
        + merged["demand_ordinal"].fillna(0) * 2
    ).round(2)

    feature_cols = [
        "item_name", "alias", "category",
        "tier", "tier_ordinal", "sub_tier", "sub_tier_ordinal",
        "obtainability", "is_unobtainable", "is_unstable",
        "demand_status", "demand_ordinal",
        "rarity_score", "popularity_score",
        "has_detailed_record", "fallback_value_score",
    ]
    feature_cols = [c for c in feature_cols if c in merged.columns]

    feature_matrix = (
        merged[feature_cols]
        .drop_duplicates(subset=["item_name", "tier", "sub_tier"])
        .sort_values(["tier_ordinal", "sub_tier_ordinal"], ascending=[False, False])
        .reset_index(drop=True)
    )
    return feature_matrix


def run(json_path: str | Path, snapshot_dir: Path = SNAPSHOT_DIR) -> Path:
    """Build the tier/rarity reference table and write it as a dated snapshot.

    This is a SECONDARY, structural data source now -- rarity, category,
    obtainability. It does not carry real price data. Real values come from
    ingest/pull_gpovalues_snapshot.py. The two get merged in
    features/build_feature_matrix.py.
    """
    feature_matrix = build_feature_matrix(json_path)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    out_path = snapshot_dir / f"tier_reference_{date.today().isoformat()}.csv"
    feature_matrix.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "data/raw/gpo_market_dataset.json"
    out_path = run(src)
    print(f"Wrote snapshot -> {out_path}")
