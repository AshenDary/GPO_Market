# Contributing

Thanks for helping improve Item Market Signals. Contributions should preserve
the project's main contract: market-derived estimates must be transparent
about uncertainty, and missing or ambiguous item matches must remain visible.

## Development setup

From the `item-market-signals/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run the offline test suite before opening a pull request:

```bash
pytest
```

Tests must not call the live gpovalues API. Keep network requests in a fetch
function and test the pure parsing or transformation function with a saved
fixture instead.

## Making changes

- Keep ingestion, feature-building, model, evaluator, dashboard, and script
  responsibilities in their existing directories. See `SKILLS.md`.
- Add or update a focused test for behavior changes.
- Preserve minimum-data guards and explain uncertainty in user-facing output.
- Do not replace dated snapshots with one mutable "latest" file.
- Do not add fuzzy item-name matching without clearly flagging possible false
  matches.
- Keep generated snapshots and feature outputs separate from raw source data.

For dashboard changes, run:

```bash
streamlit run dashboard/app.py
```

Confirm that the affected page works with the committed snapshot data and
that the sidebar refresh still makes newly generated data visible.

## Data refreshes

Live ingestion requires network access and is not part of the test suite:

```bash
python scripts/run_ingest_gpovalues.py
python scripts/run_ingest_tier.py
python scripts/run_feature_build.py
```

Only run these commands when intentionally refreshing market data. Review
the resulting dated snapshots and generated outputs before committing them.
Raw API pulls under `data/raw/` remain ignored; the curated tier input is the
tracked exception.

## Pull requests

Describe the user-facing or analytical change, the tests you ran, and any
data refreshes included in the pull request. Call out changes to confidence,
trend, matching, or model behavior explicitly because they affect how users
interpret the signals.