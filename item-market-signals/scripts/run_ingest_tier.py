"""
Entry point: python scripts/run_ingest_tier.py [path/to/raw.json]

Parses a raw tier-list JSON into a dated tier_reference snapshot under
data/snapshots/. This is the SECONDARY, structural data source (rarity,
category, obtainability) -- run scripts/run_ingest_gpovalues.py for the
primary real-price data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_signals.ingest.parse_tier_dataset import run

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/raw/gpo_market_dataset.json"
    out_path = run(src)
    print(f"Wrote snapshot -> {out_path}")
