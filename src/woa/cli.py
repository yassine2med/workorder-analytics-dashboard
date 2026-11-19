"""Command line report: python -m woa <csv> --as-of YYYY-MM-DD"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from .metrics import aging_table, backlog_by, closure_stats, load_work_orders, summary


def build_report(path: str, as_of: date) -> str:
    """Return the text report for one CSV file."""
    df = load_work_orders(path)
    s = summary(df, as_of)
    lines = [
        f"Work orders as of {as_of.isoformat()}",
        f"total {s['total']}  open {s['open']}  closed {s['closed']}",
        f"oldest open: {s['oldest_open_days']} days  open over 30 days: {s['pct_open_over_30_days']}%",
        "",
        "Open orders by priority and age (days)",
        aging_table(df, as_of).to_string(),
        "",
        "Open orders by building",
        backlog_by(df, "building").to_string(),
        "",
        "Days to close by priority",
        closure_stats(df).round(1).to_string(),
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="woa", description="Work order aging and backlog report")
    parser.add_argument("csv", help="work order CSV")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(), help="report date, YYYY-MM-DD")
    args = parser.parse_args(argv)
    try:
        print(build_report(args.csv, args.as_of))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
