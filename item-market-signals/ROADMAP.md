# Roadmap

Revised after dropping the personal trade log: real price data now comes
from gpovalues.com (28,000+ observed trades, continuously updated), so
Phases 0-2 are mostly data-plumbing, not data-collection-by-hand. The
constraint that actually gates progress now is snapshot history over time,
not trade count -- move to the next phase when the exit criteria are met.

| Phase | Goal | Key tasks | Exit criteria | Est. duration |
|---|---|---|---|---|
| **0. Setup** | Working repo, environment | `pip install -r requirements.txt && pip install -e .`, confirm `pytest` passes | `pytest` green (offline, no network needed) | 1 day |
| **1. First real pull** | Confirm the primary data source works | Run `run_ingest_gpovalues.py` against the live API, run `run_ingest_tier.py` against the tier JSON, run `run_feature_build.py`, spot-check 5-10 items against `gpovalues.com` directly | Merged feature matrix exists, values match the live site for items you check by hand | 1 day |
| **2. Snapshot accumulation** | Build real trend data | Schedule `run_ingest_gpovalues.py` daily (cron or manual), let it run | 7-14+ distinct snapshot dates in `data/snapshots/` | 1-2 weeks, passive |
| **3. Dashboard + deployment** | Make the evaluator visible and keep data fresh | Add Streamlit dashboard, local launchers, and GitHub Actions daily ingest around 9am Manila time | Dashboard runs locally; scheduled workflow commits fresh snapshots and outputs when connected to GitHub | 1-2 days |
| **4. Evaluator in daily use** | Actually use it before buying | Run `evaluator/evaluate.py` or the Streamlit lookup against real listings you come across (Discord, marketplace sites, wherever you're buying from) -- no logging required, just query it live | You've used it on 10+ real decisions and can point to at least one where it changed what you did | Ongoing from week 2 |
| **5. Trend quality pass** | Move past first-vs-last delta | Once you have 10+ snapshot dates, upgrade `trend_model.py` from a simple delta to a proper slope (linear regression over snapshot index, or `statsmodels` if you want seasonality awareness) | Trend numbers you'd defend in an interview, not just a two-point delta | 3-5 days once Phase 2 exit criteria hit |
| **6. Low-confidence backfill** | Handle the items gpovalues is thin on | Train a small regression (`scikit-learn`) on high/medium-confidence items: structural features (tier, rarity, category) -> value. Use it to sanity-check low-confidence items, not replace their number | A documented estimate for every low-confidence item, clearly labeled as model-derived vs. observed | 1 week |
| **7. Portfolio packaging** | Resume-ready case study | Write up the methodology (be specific: what gpovalues does, what you added on top and why), include dashboard screenshots and an honest "what this doesn't do" section | Case study + repo both presentable without extra verbal explanation | 3-5 days |

## What changed from the original plan, and why

The original design needed you to log completed trades to have any labeled
data at all. You don't trade item-for-item and don't have that log, so it
was a dead end. gpovalues.com already does what a trade log would have
given you, at a scale (29K trades) no amount of personal logging would
reach. The project is now "build a better evaluator on top of real market
data" instead of "predict my own trades" -- a stronger and more honest fit
for how you actually use the market.

## What's intentionally deferred

- **Personal price-check logging.** You opted to skip this for now and rely
  on the API. Nothing stops you from adding a lightweight log later if you
  want a personal "did the evaluator actually help me" record for the
  portfolio write-up -- it's a small addition, not a redesign, if you
  change your mind in Phase 3+.
- **Wiki scraping for content features** (PvP relevance, drop mechanics
  beyond what's already in the tier JSON). Worth doing eventually for
  richer "worth it" reasoning, not needed for the core evaluator to work.
- **Discord bot wrapper.** Nice for later daily-use ergonomics, but the
  Streamlit dashboard now covers the portfolio-facing interface.
