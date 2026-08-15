"""
Central path configuration. Every module imports paths from here instead of
hardcoding strings, so moving the project or renaming a folder is a one-line
change.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SNAPSHOT_DIR = DATA_DIR / "snapshots"

OUTPUT_DIR = ROOT_DIR / "outputs"

# Public, documented API for community-solved GPO item values. No auth
# required. See https://gpovalues.com/legal/methodology for how they derive
# these numbers (Dijkstra ratio-chains over ~29K observed Discord trades,
# anchored to Mythical Fruit Chest = 10,000). Poll politely -- once a day is
# plenty; their own solve pipeline runs on 12h/30-day decay windows.
GPOVALUES_API_URL = "https://gpovalues.com/api/v1/items.json"
GPOVALUES_USER_AGENT = "item-market-signals/0.1 (personal portfolio project)"

# Ordinal encodings shared across ingestion and feature building.
# Kept here (not duplicated per-module) so tier/demand weighting only ever
# changes in one place.
TIER_ORDINAL = {
    "EXCLUSIVE": 9, "SS": 8, "A+": 7, "A": 6, "A-": 5,
    "B+": 4, "B": 3, "B-": 2, "F": 1,
}

DEMAND_ORDINAL = {"High Demand": 3, "Stable Demand": 2, "Low Demand": 1}

SUB_TIER_ORDINAL = {"High Tier": 3, "Mid Tier": 2, "Low Tier": 1}

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
