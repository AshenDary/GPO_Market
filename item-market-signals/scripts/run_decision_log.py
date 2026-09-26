"""
Entry point: python scripts/run_decision_log.py ...

Records and inspects the private local decision log. The real log CSV is
ignored by Git because it contains personal trading decisions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_signals.decisions.cli import app

if __name__ == "__main__":
    app()
