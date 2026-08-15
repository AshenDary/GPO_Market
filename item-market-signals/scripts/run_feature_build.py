"""
Entry point: python scripts/run_feature_build.py

Merges the latest gpovalues price snapshot with the latest tier reference
snapshot into outputs/feature_matrix_master.csv. Run both ingestion scripts
first.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_signals.features.build_feature_matrix import run

if __name__ == "__main__":
    out_path = run()
    print(f"Wrote merged feature matrix -> {out_path}")

