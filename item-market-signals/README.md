# item-market-signals

An evaluator for a virtual item secondary market: pulls real, continuously
updated community-solved item values from a public API, enriches them with
structural tier/rarity data, tracks value trend over time, and tells you
whether a given asking price is a good deal.

See `ROADMAP.md` for the phase-by-phase plan this repo is built around.

## Data sources

1. **[gpovalues.com](https://gpovalues.com)** (primary, real prices) --
   a fan-built API solving item values from ~29,000 observed Discord
   trades, with confidence intervals and trade-count-driven confidence
   labels. See their
   [methodology](https://gpovalues.com/legal/methodology) for exactly how.
   No personal trade log needed -- this is real market data, not self-reported.
2. **Tier/rarity reference JSON** (secondary, structural) -- category,
   obtainability, rarity used to enrich items and cross-check the tier list
   against what the market actually pays.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .        # makes `config` and `market_signals` importable anywhere
```

Pull the current market values:

```bash
python scripts/run_ingest_gpovalues.py
```

Parse the structural reference data (drop a raw tier-list JSON into
`data/raw/` first):

```bash
python scripts/run_ingest_tier.py
```

Merge them into one feature matrix:

```bash
python scripts/run_feature_build.py
```

Check an item:

```bash
python -m market_signals.evaluator.evaluate "Prestige Candy Cane"
python -m market_signals.evaluator.evaluate "Candy Cane" --asking-price 300000
```

Run tests (fully offline -- gpovalues ingestion is tested against a saved
fixture, not the live network):

```bash
pytest
```

### Building snapshot history

The trend feature needs multiple dated snapshots. Run
`run_ingest_gpovalues.py` daily -- a simple cron entry works fine:

```
0 9 * * * cd /path/to/item-market-signals && .venv/bin/python scripts/run_ingest_gpovalues.py
```

## File structure

```
item-market-signals/
├── README.md
├── ROADMAP.md                       # phase-by-phase project plan
├── requirements.txt
├── .gitignore, .env.example, pyproject.toml, conftest.py
├── data/
│   ├── raw/                         # cached raw JSON pulls (gitignored)
│   └── snapshots/                    # dated gpovalues_*.csv + tier_reference_*.csv (gitignored)
├── src/
│   ├── config/
│   │   └── settings.py              # paths, ordinal encodings, API url -- single source of truth
│   └── market_signals/
│       ├── ingest/
│       │   ├── pull_gpovalues_snapshot.py   # PRIMARY: live API -> dated snapshot
│       │   └── parse_tier_dataset.py        # SECONDARY: raw JSON -> tier_reference snapshot
│       ├── features/
│       │   └── build_feature_matrix.py      # merges the two into one table
│       ├── models/
│       │   └── trend_model.py               # value trend across snapshot history
│       └── evaluator/
│           └── evaluate.py                  # the actual buy/pass CLI tool
├── scripts/
│   ├── run_ingest_gpovalues.py
│   ├── run_ingest_tier.py
│   └── run_feature_build.py
├── notebooks/
│   └── 01_eda_baseline.ipynb
├── tests/
│   ├── fixtures/sample_gpovalues_response.json   # real (trimmed) API sample, offline testing
│   ├── test_pull_gpovalues_snapshot.py
│   └── test_parse_tier_dataset.py
└── outputs/                          # feature_matrix_master.csv, gitignored
```

## Architecture

Two data sources merge into one evaluator:

1. **gpovalues.com API** (`ingest/pull_gpovalues_snapshot.py`) -- real
   solved values, confidence bands, demand, trade counts. Snapshotted daily
   so `models/trend_model.py` can compute real trend once enough dates
   accumulate (needs 2+ snapshot dates minimum, and honestly says so if you
   don't have them yet).
2. **Tier/rarity reference** (`ingest/parse_tier_dataset.py`) -- structural
   enrichment only. Matched to gpovalues items by name, then by
   shortcut/alias as a fallback. Unmatched items keep their real gpovalues
   price and are just flagged as missing enrichment, not dropped.

`features/build_feature_matrix.py` merges the two.
`evaluator/evaluate.py` is the actual user-facing tool: look up an item,
optionally pass an asking price, get a fair value + confidence band + trend
+ a plain verdict (good deal / fair / overpriced).

## Renaming

`item-market-signals` is a placeholder name -- swap it for whatever fits
your portfolio, then also swap the `market_signals` import path if you
change the package name (search-and-replace across `src/`, `scripts/`,
`tests/`, and `notebooks/`).