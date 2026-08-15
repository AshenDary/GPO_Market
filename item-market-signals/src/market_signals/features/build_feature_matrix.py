"""
Merges the latest gpovalues.com price snapshot (real values, confidence,
demand) with the latest tier reference snapshot (structural features:
rarity, category, obtainability) into one feature matrix.

Join strategy, in order:
  1. exact normalized name match
  2. shortcut/alias match (gpovalues "shortcut" vs tier list alias, e.g. PCC)
  3. leave unmatched -- flagged, not guessed at

Run ingest/pull_gpovalues_snapshot.py and ingest/parse_tier_dataset.py
first so both snapshot types exist.
"""

from pathlib import Path

import pandas as pd

from config.settings import SNAPSHOT_DIR


def _latest(pattern: str, snapshot_dir: Path = SNAPSHOT_DIR) -> Path:
    matches = sorted(snapshot_dir.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No files matching '{pattern}' in {snapshot_dir}. "
            "Run the relevant ingestion script first."
        )
    return matches[-1]


def build_feature_matrix(snapshot_dir: Path = SNAPSHOT_DIR) -> pd.DataFrame:
    gpovalues = pd.read_csv(_latest("gpovalues_*.csv", snapshot_dir))
    tier_ref = pd.read_csv(_latest("tier_reference_*.csv", snapshot_dir))

    tier_ref = tier_ref.rename(columns={"item_name": "tier_item_name"})
    tier_ref["join_key"] = tier_ref["tier_item_name"].str.lower().str.strip()

    # Pass 1: exact normalized name match
    merged = gpovalues.merge(
        tier_ref, on="join_key", how="left", suffixes=("", "_tier")
    )

    # Pass 2: for anything still unmatched, try shortcut <-> alias
    unmatched_mask = merged["tier_item_name"].isna()
    if unmatched_mask.any() and "alias" in tier_ref.columns:
        alias_lookup = (
            tier_ref.dropna(subset=["alias"])
            .assign(alias_key=lambda d: d["alias"].str.lower().str.strip())
            .set_index("alias_key")
        )
        for idx in merged[unmatched_mask].index:
            shortcut = merged.at[idx, "shortcut"]
            if pd.isna(shortcut):
                continue
            key = str(shortcut).lower().strip()
            if key in alias_lookup.index:
                row = alias_lookup.loc[key]
                for col in tier_ref.columns:
                    if col in merged.columns:
                        merged.at[idx, col] = row[col] if not isinstance(row, pd.DataFrame) else row[col].iloc[0]

    merged["has_tier_enrichment"] = merged["tier_item_name"].notna()

    unmatched_count = (~merged["has_tier_enrichment"]).sum()
    if unmatched_count:
        print(
            f"Note: {unmatched_count} gpovalues item(s) had no tier-list "
            "match (name/shortcut). They still have real price data from "
            "gpovalues -- they just won't have tier/category enrichment."
        )

    return merged


def run(snapshot_dir: Path = SNAPSHOT_DIR, out_path: Path | None = None) -> Path:
    from config.settings import OUTPUT_DIR

    feature_matrix = build_feature_matrix(snapshot_dir)
    out_path = out_path or (OUTPUT_DIR / "feature_matrix_master.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    feature_matrix.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    out_path = run()
    print(f"Wrote merged feature matrix -> {out_path}")
