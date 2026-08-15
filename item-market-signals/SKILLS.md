# SKILLS.md

Conventions and recipes for working on this codebase. Read CONTEXT.md first
for what the project is; this file is about how to work in it.

## Command reference

```bash
# one-time setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# verify everything works (offline, no network needed)
pytest

# pull real data (network required)
python scripts/run_ingest_gpovalues.py     # primary: live values from gpovalues.com
python scripts/run_ingest_tier.py          # secondary: parse data/raw/*.json

# merge into one feature matrix
python scripts/run_feature_build.py

# use it
python -m market_signals.evaluator.evaluate "Item Name"
python -m market_signals.evaluator.evaluate "Item Name" --asking-price 300000

# trend across accumulated snapshots (needs 2+ snapshot dates)
python -m market_signals.models.trend_model
```

## File placement rules

| Kind of file | Goes in |
|---|---|
| New data source ingestion (fetch + parse) | `src/market_signals/ingest/` |
| Logic that merges/joins snapshot types | `src/market_signals/features/` |
| Anything computing a derived signal (trend, score, prediction) | `src/market_signals/models/` |
| User-facing CLI tools | `src/market_signals/evaluator/` |
| Path constants, encodings, shared config | `src/config/settings.py` (don't create a second config file) |
| Thin script wrapper for a pipeline stage | `scripts/`, name `run_<stage>.py` |
| Tests | `tests/`, filename `test_<module_under_test>.py` |
| Offline test fixtures (saved API responses, sample JSON) | `tests/fixtures/` |
| Raw external data dumps (tier lists, etc.) | `data/raw/` |
| Generated/dated snapshots | `data/snapshots/`, never committed (gitignored) |
| Generated merged/final tables | `outputs/`, never committed (gitignored) |

## Adding a new data source

Follow the pattern in `ingest/pull_gpovalues_snapshot.py`:

1. Write a `fetch_x(...)` function that does the network call and nothing
   else -- raise on failure, don't swallow errors.
2. Write a `flatten_x(payload: dict) -> pd.DataFrame` function that's pure
   (no network, no filesystem) so it can be unit tested against a fixture.
3. Write a `run(...)` function that calls both and writes a dated snapshot
   to `data/snapshots/{source}_{date}.csv`.
4. Save a trimmed real sample of the actual response to
   `tests/fixtures/sample_{source}_response.json` and write tests against
   `flatten_x()` only -- never call the live network in a test.
5. Add a thin `scripts/run_ingest_{source}.py` wrapper.
6. Wire it into `features/build_feature_matrix.py` if it should be merged
   with the rest, following the existing "exact match, then fallback match,
   then flag unmatched" pattern -- don't drop unmatched rows.

## Adding a new evaluator check or model

If it's a new derived signal (not just a lookup), it needs:
- A minimum-data guard constant at module level (see `MIN_SNAPSHOTS` in
  `trend_model.py`), named `MIN_*`.
- A clear, printed/returned message when the guard isn't met -- never
  silently return `None` or a zero without explanation.
- A docstring explaining *why* the threshold is what it is, not just what
  the threshold is.

## Testing conventions

- Tests run fully offline. If a module hits the network, it must have a
  pure function separated out (see "Adding a new data source" above) that
  the tests actually exercise.
- One test file per module under test: `tests/test_<module>.py`.
- Fixtures are real (possibly trimmed) samples of actual data, not
  hand-invented dicts that might not match the real shape -- when adding a
  fixture, get it from an actual API response or actual source file first.
- `conftest.py` at repo root handles `sys.path` so tests can `import
  market_signals...` and `import config...` without needing `pip install -e .`
  first -- don't remove it or duplicate its logic inside individual test files.

## Style notes

- Every module-level docstring explains *why* the module exists and how it
  relates to the others, not just what functions are in it -- match the
  existing files' tone, don't drop to bare one-liners.
- Prefer `pathlib.Path` over string paths throughout; all real paths come
  from `config/settings.py`.
- Don't add fuzzy/heuristic matching (string similarity, guessed
  normalization) for item names without flagging it clearly in output --
  see the "Known gotchas" section of CONTEXT.md for why.



