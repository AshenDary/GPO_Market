"""
build_feature_matrix.py

Parses the virtual-item market reference dataset (gpo_market_dataset.json)
and produces a flat, model-ready feature matrix.

Two source structures are combined:
  1. most_traded_spotlight   -> rich per-item records (scores, demand, notes)
  2. tier_classified_items   -> broad tier/sub-tier placement for 80+ items,
                                 with no numeric scores

Output: feature_matrix.csv (one row per unique item x tier placement)

Usage:
    python build_feature_matrix.py [path_to_json] [output_csv]
"""

import json
import re
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Ordinal encodings (mirrors dataset_metadata, kept explicit here so the
# script is self-contained even if metadata keys drift)
# ---------------------------------------------------------------------------
TIER_ORDINAL = {
    "EXCLUSIVE": 9, "SS": 8, "A+": 7, "A": 6, "A-": 5,
    "B+": 4, "B": 3, "B-": 2, "F": 1,
}

DEMAND_ORDINAL = {"High Demand": 3, "Stable Demand": 2, "Low Demand": 1}

SUB_TIER_ORDINAL = {"High Tier": 3, "Mid Tier": 2, "Low Tier": 1}

# raw JSON key -> canonical tier label used in TIER_ORDINAL / tier_mapping
TIER_KEY_MAP = {
    "EXCLUSIVE": "EXCLUSIVE",
    "SS_TIER": "SS",
    "A_PLUS_TIER": "A+",
    "A_TIER": "A",
    "A_MINUS_TIER": "A-",
    "B_PLUS_TIER": "B+",
    "B_TIER": "B",
    "B_MINUS_TIER": "B-",
    "F_TIER": "F",
}

NAME_ALIAS_RE = re.compile(r"^(.*?)\s*\((\+?[^)]+)\)\s*$")


def clean_item_name(raw: str):
    """'Prestige Candy Cane (+PCC)' -> ('Prestige Candy Cane', 'PCC')"""
    m = NAME_ALIAS_RE.match(raw.strip())
    if m:
        name = m.group(1).strip()
        alias = m.group(2).lstrip("+").strip()
        return name, alias
    return raw.strip(), None


def flatten_tier_classified(tier_dict: dict) -> pd.DataFrame:
    """Flatten the nested tier_classified_items block into one row per item."""
    rows = []
    for raw_tier_key, contents in tier_dict.items():
        tier_label = TIER_KEY_MAP.get(raw_tier_key, raw_tier_key)

        if isinstance(contents, list):
            # EXCLUSIVE and F_TIER: flat lists, no sub-tier split
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


def build_feature_matrix(json_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tier_df = flatten_tier_classified(data["tier_classified_items"])
    spotlight_df = load_spotlight(data["most_traded_spotlight"])

    # left join: every item in the tier list gets enriched with spotlight
    # detail when available. Items only in the tier list keep NaNs for the
    # spotlight-only columns.
    spotlight_cols_to_bring = [
        c for c in spotlight_df.columns
        if c not in ("tier", "sub_tier", "item_name", "join_key")
    ]
    merged = tier_df.merge(
        spotlight_df[["join_key"] + spotlight_cols_to_bring],
        on="join_key",
        how="left",
    )

    # consolidate alias: prefer the spotlight's curated alias, fall back to
    # the one parsed out of the tier-list string
    merged["alias"] = merged["alias"].fillna(merged["alias_from_tierlist"])

    # ---- ordinal / numeric encodings -------------------------------------
    merged["tier_ordinal"] = merged["tier"].map(TIER_ORDINAL)
    merged["sub_tier_ordinal"] = merged["sub_tier"].map(SUB_TIER_ORDINAL)
    merged["demand_ordinal"] = merged["demand_status"].map(DEMAND_ORDINAL)

    for col in ("is_unstable", "is_unobtainable"):
        if col in merged.columns:
            merged[col] = merged[col].astype("boolean")

    merged["has_detailed_record"] = merged["rarity_score"].notna()

    # proxy_value_score: a transparent, hand-weighted placeholder so the
    # feature matrix isn't empty of a "value-like" column before you have
    # real trade-price data. This is NOT a market value estimate -- it's a
    # starting heuristic to sanity-check feature relationships. Swap it out
    # once you have your own logged trade prices as the real target.
    merged["proxy_value_score"] = (
        merged["tier_ordinal"].fillna(0) * 2
        + merged["rarity_score"].fillna(merged["tier_ordinal"].fillna(0) * 1.1)
        + merged["popularity_score"].fillna(0)
        + merged["demand_ordinal"].fillna(0) * 2
    ).round(2)

    # ---- final feature matrix ---------------------------------------------
    feature_cols = [
        "item_name", "alias", "category",
        "tier", "tier_ordinal", "sub_tier", "sub_tier_ordinal",
        "obtainability", "is_unobtainable", "is_unstable",
        "demand_status", "demand_ordinal",
        "rarity_score", "popularity_score",
        "has_detailed_record", "proxy_value_score",
    ]
    feature_cols = [c for c in feature_cols if c in merged.columns]

    feature_matrix = (
        merged[feature_cols]
        .drop_duplicates(subset=["item_name", "tier", "sub_tier"])
        .sort_values(["tier_ordinal", "sub_tier_ordinal"], ascending=[False, False])
        .reset_index(drop=True)
    )

    return feature_matrix, merged


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else "gpo_market_dataset.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "feature_matrix.csv"

    if not Path(json_path).exists():
        raise FileNotFoundError(f"Could not find {json_path}")

    feature_matrix, _ = build_feature_matrix(json_path)
    feature_matrix.to_csv(out_path, index=False)

    print(f"Wrote {len(feature_matrix)} rows -> {out_path}\n")
    print(feature_matrix.head(15).to_string(index=False))
    print(f"\nTotal unique item-placements : {len(feature_matrix)}")
    print(f"With detailed spotlight data  : {int(feature_matrix['has_detailed_record'].sum())}")
    print(f"Tier-list only (no scores)    : {int((~feature_matrix['has_detailed_record']).sum())}")
    print("\nColumn dtypes:")
    print(feature_matrix.dtypes)


if __name__ == "__main__":
    main()
