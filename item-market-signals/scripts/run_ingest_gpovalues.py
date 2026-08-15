"""
Entry point: python scripts/run_ingest_gpovalues.py

Pulls the current community-solved item values from gpovalues.com and
writes a dated snapshot. This is the PRIMARY data source for the project.

Run this on a schedule (daily is enough -- see a cron example in README.md)
to accumulate the snapshot history that models/trend_model.py needs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_signals.ingest.pull_gpovalues_snapshot import run

if __name__ == "__main__":
    out_path = run()
    print(f"Wrote snapshot -> {out_path}")
