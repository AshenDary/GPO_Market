# Bootstrap prompt

Copy everything below the line into Codex (or any coding agent) when
setting up this repo fresh, or whenever you've dropped new/loose files in
and want them sorted into place. Keep this file up to date if the
architecture changes -- it's meant to replace re-explaining the project
from scratch each session.

---

Read `CONTEXT.md` and `SKILLS.md` in this repo root before doing anything
else. They contain the full architecture, data flow, module
responsibilities, file placement rules, and coding conventions for this
project. Don't ask me to re-explain the project -- everything you need is
in those two files. If they're missing, stop and tell me instead of
guessing at the structure.

**Task 1 -- Arrange loose files.**
Check the repo root and any `_inbox/`-style staging folder for files that
aren't yet in their correct location per CONTEXT.md's architecture and
SKILLS.md's file placement table. For each loose file:
- Read its docstring/imports to identify what it does.
- Match it against SKILLS.md's file placement rules (ingestion -> `src/market_signals/ingest/`, merging -> `features/`, derived signals -> `models/`, CLI tools -> `evaluator/`, tests -> `tests/`, fixtures -> `tests/fixtures/`, thin runners -> `scripts/`, raw data -> `data/raw/`).
- Move it to the correct path, renaming only if the existing file at that
  path has a clearly different (non-conflicting) purpose -- if there's a
  real naming collision, stop and ask rather than overwriting.
- If you can't confidently tell where a file belongs, leave it in place and
  list it as "unresolved" in your final report -- don't guess.

**Task 2 -- Fill structural gaps.**
Create any missing directories or empty `__init__.py` files needed to match
the package structure in CONTEXT.md. Don't overwrite any file that already
matches the described structure and already has content.

**Task 3 -- Environment setup and verification.**
Run these in order. Stop and report immediately if any step fails, rather
than continuing past a failure:

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
python scripts/run_ingest_gpovalues.py
python scripts/run_ingest_tier.py
python scripts/run_feature_build.py
python -m market_signals.evaluator.evaluate "Prestige Candy Cane"
```

Note: `run_ingest_gpovalues.py` needs network access to `gpovalues.com`. If
that's unavailable in your environment, say so explicitly rather than
skipping it silently, and run `pytest` as the fallback verification (it's
fully offline).

**Task 4 -- Report back.**
Summarize: which files you moved and to where, anything left unresolved,
whether `pytest` passed (paste the failure if not), and the final
evaluator command's output.
