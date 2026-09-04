# Item Market Signals

Item Market Signals is a market intelligence dashboard for the Grand Piece
Online trading economy. It combines continuously updated community values
from gpovalues.com with tier, rarity, and obtainability context, then turns
that data into practical buy, fair, and overpriced signals for item decisions.

The project includes a Streamlit dashboard for exploring the market and a CLI
evaluator for quick item checks. Dated snapshots preserve market history so
trend signals can be measured as more observations accumulate.

The active project code lives in the `item-market-signals/` folder.

## What It Shows

- Live market-data ingestion from the public gpovalues.com API
- Offline parsing of a curated tier/rarity JSON dataset
- Snapshot-based data storage for trend tracking over time
- Feature merging by exact item name, then shortcut/alias fallback
- Explicit uncertainty handling through confidence labels and value ranges
- A user-facing CLI that returns a practical buy/fair/overpriced signal
- A Streamlit dashboard with Overview, Item lookup, Trade Simulator, Trend,
  Value List, and How it works views
- Offline tests using saved fixtures instead of live network calls

## Example

```bash
cd item-market-signals
python -m market_signals.evaluator.evaluate "Prestige Candy Cane"
```

Example output:

```text
Prestige Candy Cane (PCC)
  Fair value      : 3,000,000
  Typical range   : 2,700,000 - 3,300,000
  Confidence      : medium (454 trades observed)
  Demand          : Low
  Trend           : not enough snapshot history yet
```

You can also include a seller's asking price:

```bash
python -m market_signals.evaluator.evaluate "Candy Cane" --asking-price 300000
```

## How It Works

The project combines two data sources:

1. **gpovalues.com API**  
   Primary source for solved item values, confidence intervals, demand, and
   observed trade counts.

2. **Tier reference JSON**  
   Secondary source for structural context such as tier, category, rarity, and
   obtainability.

Each data pull is saved as a dated snapshot. Those snapshots are merged into a
single feature matrix, which the evaluator reads when answering item queries.
Trend analysis becomes more useful as more snapshots accumulate over time.

## Quick Start

```bash
cd item-market-signals
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run the full local pipeline:

```bash
python scripts/run_ingest_gpovalues.py
python scripts/run_ingest_tier.py
python scripts/run_feature_build.py
python -m market_signals.evaluator.evaluate "Prestige Candy Cane"
```

Run the dashboard:

```bash
streamlit run dashboard/app.py
```

Use the sidebar `Refresh data` button after running ingestion scripts so
cached data is reloaded immediately.

Run tests:

```bash
pytest
```

Tests are fully offline. The live gpovalues ingestion requires network access,
but parser and transformation logic are tested against saved fixtures.

## Project Structure

```text
item-market-signals/
  dashboard/    # Streamlit app + dashboard components
  src/          # package code (ingest, features, models, evaluator)
  data/
    raw/        # curated tier source + temporary raw pulls
    snapshots/  # dated gpovalues and tier CSV snapshots
  outputs/      # generated merged feature matrix files
  scripts/      # thin pipeline runners
  tests/        # offline unit tests and fixtures
```

## Current Status

The ingestion, feature-building, evaluator, and dashboard flows are all
working on `main`. Trend signals remain guarded by a minimum snapshot count,
and this repository currently has multiple snapshot dates, so trend output is
available for items with sufficient history.

## Tech Stack

- Python
- pandas
- requests
- Typer
- pytest
- setuptools `src` package layout

