"""Private decision log built from snapshot-time market signals.

The log records what the tool knew when a buy/no-buy decision was made. It
stores gpovalues' published market value and range separately from personal
asking, purchase, and resale fields so later analysis does not mix observed
market estimates with actual completed transactions.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from config.settings import DECISION_LOG_PATH, SNAPSHOT_DIR
from market_signals.evaluator.evaluate import find_item_matches, verdict

DECISION_COLUMNS = [
    "decision_id",
    "decision_timestamp",
    "snapshot_date",
    "snapshot_file",
    "snapshot_generated_at",
    "item_slug",
    "item_name",
    "item_shortcut",
    "join_key",
    "asking_price",
    "published_value",
    "ci_low",
    "ci_high",
    "confidence",
    "demand",
    "demand_ratio",
    "trade_count",
    "n_trades_used",
    "verdict",
    "bought",
    "purchase_price",
    "resale_date",
    "resale_price",
    "resale_notes",
    "marked_value_date",
    "marked_value",
    "marked_value_source",
    "notes",
]


class DecisionLogError(ValueError):
    """Base class for decision-log validation errors."""


class ItemNotFoundError(DecisionLogError):
    """Raised when a requested item is absent from the selected snapshot."""


class AmbiguousItemMatchError(DecisionLogError):
    """Raised when a lookup matches multiple snapshot rows."""


class MissingItemPriceError(DecisionLogError):
    """Raised when a snapshot row lacks the fields needed for a verdict."""


class DecisionNotFoundError(DecisionLogError):
    """Raised when an update targets a decision id that is not logged."""


class ResaleAlreadyRecordedError(DecisionLogError):
    """Raised when a resale update would overwrite an existing actual sale."""


class ResaleWithoutPurchaseError(DecisionLogError):
    """Raised when a resale update targets a no-buy decision."""


def latest_gpovalues_snapshot(snapshot_dir: Path = SNAPSHOT_DIR) -> Path:
    """Return the latest dated gpovalues snapshot by filename date."""
    matches = sorted(snapshot_dir.glob("gpovalues_*.csv"))
    if not matches:
        raise FileNotFoundError(f"No gpovalues snapshots found in {snapshot_dir}.")
    return matches[-1]


def snapshot_date_from_path(snapshot_path: Path) -> str:
    """Extract the ISO date from a gpovalues snapshot filename."""
    name = snapshot_path.stem
    prefix = "gpovalues_"
    if not name.startswith(prefix):
        raise ValueError(f"Snapshot file must be named like gpovalues_YYYY-MM-DD.csv: {snapshot_path}")
    return name.removeprefix(prefix)


def load_snapshot(snapshot_path: Path | None = None, snapshot_dir: Path = SNAPSHOT_DIR) -> pd.DataFrame:
    """Load the selected gpovalues snapshot, defaulting to the latest one."""
    selected_path = snapshot_path or latest_gpovalues_snapshot(snapshot_dir)
    snapshot = pd.read_csv(selected_path)
    snapshot["snapshot_date"] = snapshot_date_from_path(selected_path)
    snapshot["snapshot_file"] = selected_path.name
    return snapshot


def resolve_snapshot_item(snapshot: pd.DataFrame, item_name: str) -> pd.Series:
    """Resolve one item in a snapshot using the evaluator's matching rules."""
    matches = find_item_matches(snapshot, item_name)
    if len(matches) == 1:
        return matches.iloc[0]
    if len(matches) > 1:
        names = ", ".join(str(name) for name in matches["name"].dropna().head(8))
        raise AmbiguousItemMatchError(
            f"Multiple matches for '{item_name}': {names}. Use an exact item name."
        )
    raise ItemNotFoundError(f"No match found for '{item_name}' in the selected snapshot.")


def recompute_saved_verdict(entry: pd.Series | dict[str, object]) -> str:
    """Recompute a verdict only from fields saved in the decision log."""
    return verdict(
        _required_float(entry, "asking_price"),
        _required_float(entry, "published_value"),
        _required_float(entry, "ci_low"),
        _required_float(entry, "ci_high"),
    )


def build_decision_entry(
    item_name: str,
    asking_price: float,
    bought: bool,
    *,
    purchase_price: float | None = None,
    notes: str = "",
    snapshot_path: Path | None = None,
    snapshot_dir: Path = SNAPSHOT_DIR,
    decision_timestamp: datetime | None = None,
) -> dict[str, object]:
    """Build one log row from the snapshot available at decision time."""
    if asking_price <= 0:
        raise ValueError("asking_price must be greater than zero.")
    if purchase_price is not None and purchase_price <= 0:
        raise ValueError("purchase_price must be greater than zero when provided.")

    selected_snapshot_path = snapshot_path or latest_gpovalues_snapshot(snapshot_dir)
    snapshot = load_snapshot(selected_snapshot_path, snapshot_dir)
    row = resolve_snapshot_item(snapshot, item_name)

    value = _required_float(row, "value")
    ci_low = _required_float(row, "ci_low")
    ci_high = _required_float(row, "ci_high")
    decision_time = decision_timestamp or datetime.now(timezone.utc)
    saved_verdict = verdict(asking_price, value, ci_low, ci_high)

    return {
        "decision_id": uuid4().hex,
        "decision_timestamp": decision_time.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_date": str(row["snapshot_date"]),
        "snapshot_file": str(row["snapshot_file"]),
        "snapshot_generated_at": _string_or_blank(row.get("generated_at")),
        "item_slug": _string_or_blank(row.get("slug")),
        "item_name": _string_or_blank(row.get("name")),
        "item_shortcut": _string_or_blank(row.get("shortcut")),
        "join_key": _string_or_blank(row.get("join_key")),
        "asking_price": float(asking_price),
        "published_value": value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence": _string_or_blank(row.get("confidence")),
        "demand": _string_or_blank(row.get("demand")),
        "demand_ratio": _optional_float(row.get("demand_ratio")),
        "trade_count": _optional_float(row.get("trade_count")),
        "n_trades_used": _optional_float(row.get("n_trades_used")),
        "verdict": saved_verdict,
        "bought": bool(bought),
        "purchase_price": "" if purchase_price is None else float(purchase_price),
        "resale_date": "",
        "resale_price": "",
        "resale_notes": "",
        "marked_value_date": "",
        "marked_value": "",
        "marked_value_source": "",
        "notes": notes,
    }


def append_decision(entry: dict[str, object], log_path: Path = DECISION_LOG_PATH) -> dict[str, object]:
    """Append one decision entry to the private CSV log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_decision_log(log_path)
    new_row = pd.DataFrame([entry], columns=DECISION_COLUMNS)
    updated = new_row if existing.empty else pd.concat([existing, new_row], ignore_index=True)
    updated.to_csv(log_path, index=False)
    return entry


def log_decision(
    item_name: str,
    asking_price: float,
    bought: bool,
    *,
    purchase_price: float | None = None,
    notes: str = "",
    snapshot_path: Path | None = None,
    snapshot_dir: Path = SNAPSHOT_DIR,
    log_path: Path = DECISION_LOG_PATH,
    decision_timestamp: datetime | None = None,
) -> dict[str, object]:
    """Build and append one private decision-log row."""
    entry = build_decision_entry(
        item_name,
        asking_price,
        bought,
        purchase_price=purchase_price,
        notes=notes,
        snapshot_path=snapshot_path,
        snapshot_dir=snapshot_dir,
        decision_timestamp=decision_timestamp,
    )
    return append_decision(entry, log_path)


def load_decision_log(log_path: Path = DECISION_LOG_PATH) -> pd.DataFrame:
    """Load the private decision log, returning an empty schema if absent."""
    if not log_path.exists():
        return pd.DataFrame(columns=DECISION_COLUMNS)
    df = pd.read_csv(log_path, dtype={"decision_id": str})
    for column in DECISION_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[DECISION_COLUMNS]


def get_decision(decision_id: str, log_path: Path = DECISION_LOG_PATH) -> pd.Series:
    """Return one logged decision by id."""
    log = load_decision_log(log_path)
    matches = log[log["decision_id"] == decision_id]
    if len(matches) != 1:
        raise DecisionNotFoundError(f"No decision found with id '{decision_id}'.")
    return matches.iloc[0]


def record_resale_outcome(
    decision_id: str,
    resale_price: float,
    *,
    resale_date: date | str | None = None,
    resale_notes: str = "",
    log_path: Path = DECISION_LOG_PATH,
    force: bool = False,
) -> pd.Series:
    """Record an actual resale outcome without touching marked-value fields."""
    if resale_price <= 0:
        raise ValueError("resale_price must be greater than zero.")

    log = load_decision_log(log_path)
    matches = log.index[log["decision_id"] == decision_id].tolist()
    if len(matches) != 1:
        raise DecisionNotFoundError(f"No decision found with id '{decision_id}'.")

    idx = matches[0]
    if not _as_bool(log.at[idx, "bought"]):
        raise ResaleWithoutPurchaseError(
            f"Decision '{decision_id}' was logged as no-buy, so it cannot receive an actual resale outcome."
        )

    existing_price = log.at[idx, "resale_price"]
    if not force and not _is_blank(existing_price):
        raise ResaleAlreadyRecordedError(
            f"Decision '{decision_id}' already has a resale price. Use force=True to overwrite."
        )

    for column in ("resale_date", "resale_notes"):
        log[column] = log[column].astype("object")
    actual_date = resale_date or date.today()
    log.at[idx, "resale_date"] = actual_date.isoformat() if isinstance(actual_date, date) else str(actual_date)
    log.at[idx, "resale_price"] = float(resale_price)
    log.at[idx, "resale_notes"] = resale_notes
    log.to_csv(log_path, index=False)
    return log.iloc[idx]


def _required_float(row: pd.Series | dict[str, object], field: str) -> float:
    value = row[field] if isinstance(row, dict) else row.get(field)
    parsed = _optional_float(value)
    if parsed is None:
        raise MissingItemPriceError(f"Selected item is missing required price field '{field}'.")
    return parsed


def _optional_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed)


def _string_or_blank(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _is_blank(value: object) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "buy", "bought"}
