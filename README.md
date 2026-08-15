# Item Market Signals

A command-line evaluator for a virtual item trading market. Given an item
name, it pulls together real community price data, tier-list context, demand,
confidence bands, and snapshot history to answer a simple question:

**Is this item fairly priced, undervalued, or overpriced?**

This project is built around the Grand Piece Online secondary market, but the
architecture is meant to demonstrate a broader data workflow: ingest live
market data, enrich it with reference data, build a feature matrix, and expose
the result through a small evaluator.

## What It Shows

- Live market-data ingestion from the public gpovalues.com API
- Offline parsing of a curated tier/rarity JSON dataset
- Snapshot-based data storage for future trend tracking
- Feature merging by exact item name, then shortcut/alias fallback
- Explicit uncertainty handling through confidence labels and value ranges
- A user-facing CLI that returns a practical buy/fair/overpriced signal
- Offline tests using saved fixtures instead of live network calls

## Example

```bash
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

Run tests:

```bash
pytest
```

Tests are fully offline. The live gpovalues ingestion requires network access,
but parser and transformation logic are tested against saved fixtures.

## Project Structure

```text
src/market_signals/
  ingest/       # live API pulls and tier JSON parsing
  features/     # snapshot merging and feature matrix creation
  models/       # derived signals such as trend
  evaluator/    # user-facing CLI

data/
  raw/          # raw source data
  snapshots/    # dated CSV snapshots

outputs/        # generated feature matrices
tests/          # offline unit tests and fixtures
scripts/        # thin pipeline runners
```

## Current Status

The core ingestion, feature-building, and evaluator flow is working. Trend
signals are intentionally guarded until multiple snapshot dates exist, so the
tool avoids pretending that one data point is a real trend.

## Tech Stack

- Python
- pandas
- requests
- Typer
- pytest
- setuptools `src` package layout

