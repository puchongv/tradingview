"""Execute the Strategy Evaluation SQL with default parameters.

This helper reads the Metabase query, replaces the Liquid-style template
placeholders with the defaults used in dashboards, and runs the result against
the configured database so data can be checked outside Metabase.

Environment variables (override defaults):
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence


# Location of the maintained SQL file.
DEFAULT_SQL_PATH = Path(__file__).resolve().parent.parent / (
    "metabase/Strategy Evalucation Score V1.0.2.sql"
)

# Default values that Metabase would normally inject via templating.
PARAM_DEFAULTS = {
    "horizon_list": "'10min'",
    "max_loss_streak_cap": "4",
    "payout": "0.8",
    "investment": "250",
    "reverse_enable": "false",
    "abs_pnl": "false",
    "prime_list": "10",
    "pnl_kpi": "1000",
    "pnl_score_72h": "5",
    "pnl_score_48h": "10",
    "pnl_score_24h": "15",
    "pnl_score_12h": "10",
    "winrate_score_72h": "8",
    "winrate_score_48h": "8",
    "winrate_score_24h": "8",
    "winrate_consistency_score": "6",
    "recent_performance_max_score": "30",
}


def load_query(sql_path: Path) -> str:
    sql = sql_path.read_text()
    for key, value in PARAM_DEFAULTS.items():
        sql = sql.replace(f"{{{{{key}}}}}", value)
    return sql


def connect(**kwargs):  # type: ignore[override]
    """Return a DB connection using psycopg (v3) or psycopg2."""

    try:
        import psycopg  # type: ignore

        return psycopg.connect(**kwargs)
    except ModuleNotFoundError:
        try:
            import psycopg2  # type: ignore

            return psycopg2.connect(**kwargs)
        except ModuleNotFoundError as exc:  # pragma: no cover - env specific
            raise SystemExit(
                "Install `psycopg` or `psycopg2` to run the SQL (e.g. pip install psycopg)."
            ) from exc


def print_rows(columns: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
    if not rows:
        print("No rows returned.")
        return

    widths = [len(col) for col in columns]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))

    def fmt_line(values: Iterable[object]) -> str:
        return " | ".join(str(val).ljust(widths[idx]) for idx, val in enumerate(values))

    divider = "-+-".join("-" * width for width in widths)
    print(fmt_line(columns))
    print(divider)
    for row in rows:
        print(fmt_line(row))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sql-file",
        default=str(DEFAULT_SQL_PATH),
        help="Path to the SQL file (defaults to Strategy Evalucation Score V1.0.2).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional LIMIT override appended to the query.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sql_path = Path(args.sql_file)
    if not sql_path.exists():
        print(f"SQL file not found: {sql_path}", file=sys.stderr)
        return 1

    query = load_query(sql_path)
    if args.limit is not None:
        query = f"SELECT * FROM ({query}) as subquery LIMIT {args.limit}"

    conn_kwargs = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "dbname": os.getenv("DB_NAME", "postgres"),
    }

    with connect(**conn_kwargs) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

    print_rows(columns, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
