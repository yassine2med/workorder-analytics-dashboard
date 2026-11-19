"""Core metrics. All functions take a DataFrame from load_work_orders."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

REQUIRED = ("id", "building", "trade", "priority", "status", "created", "closed")
PRIORITY_ORDER = ["Emergency", "High", "Medium", "Low"]
AGE_BUCKETS = [("0-7", 0, 7), ("8-30", 8, 30), ("31-60", 31, 60), ("61-90", 61, 90), ("90+", 91, None)]


def load_work_orders(path: str | Path) -> pd.DataFrame:
    """Read a work order CSV and parse dates.

    Raises ValueError when a required column is missing or a date cannot be parsed.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")
    for col in ("created", "closed"):
        parsed = pd.to_datetime(df[col].replace("", pd.NA), format="%Y-%m-%d", errors="coerce")
        bad = df[col].ne("") & parsed.isna()
        if bad.any():
            raise ValueError(f"bad date in column '{col}' at row {int(bad.idxmax()) + 2}")
        df[col] = parsed
    if df["created"].isna().any():
        raise ValueError("every work order needs a created date")
    return df


def open_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Rows that have no closed date and a status other than Closed."""
    return df[df["closed"].isna() & df["status"].ne("Closed")].copy()


def bucket_for(age_days: int) -> str:
    """Return the aging bucket label for an age in days."""
    if age_days < 0:
        raise ValueError("age cannot be negative")
    for label, low, high in AGE_BUCKETS:
        if age_days >= low and (high is None or age_days <= high):
            return label
    raise ValueError("unreachable bucket")


def aging_table(df: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """Count open orders by priority (rows) and age bucket (columns)."""
    open_df = open_orders(df)
    labels = [b[0] for b in AGE_BUCKETS]
    if open_df.empty:
        return pd.DataFrame(0, index=PRIORITY_ORDER, columns=labels)
    age = (pd.Timestamp(as_of) - open_df["created"]).dt.days.clip(lower=0)
    open_df["bucket"] = age.map(bucket_for)
    table = pd.crosstab(open_df["priority"], open_df["bucket"])
    return table.reindex(index=PRIORITY_ORDER, columns=labels, fill_value=0)


def backlog_by(df: pd.DataFrame, column: str) -> pd.Series:
    """Open order count grouped by any column such as building or trade."""
    if column not in df.columns:
        raise ValueError(f"unknown column: {column}")
    return open_orders(df).groupby(column).size().sort_values(ascending=False)


def closure_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Median and 90th percentile days to close, by priority."""
    done = df[df["closed"].notna()].copy()
    done["days"] = (done["closed"] - done["created"]).dt.days
    grouped = done.groupby("priority")["days"]
    out = pd.DataFrame({"closed": grouped.size(), "median_days": grouped.median(), "p90_days": grouped.quantile(0.9)})
    return out.reindex(PRIORITY_ORDER).dropna(how="all")


def summary(df: pd.DataFrame, as_of: date) -> dict[str, float | int]:
    """Headline numbers: totals, open count, oldest open age, share older than 30 days."""
    open_df = open_orders(df)
    ages = (pd.Timestamp(as_of) - open_df["created"]).dt.days
    return {
        "total": len(df),
        "open": len(open_df),
        "closed": len(df) - len(open_df),
        "oldest_open_days": int(ages.max()) if len(ages) else 0,
        "pct_open_over_30_days": round(float((ages > 30).mean() * 100), 1) if len(ages) else 0.0,
    }
