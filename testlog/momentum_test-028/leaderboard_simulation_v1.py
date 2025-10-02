#!/usr/bin/env python3
"""
Leaderboard-based Simulation
Version: 1.0
Date: 2025-10-02

This script replays trades by using a "leaderboard" that mirrors the
PNL-fomula.sql view. Every hour we:
  1) Rebuild the leaderboard from the last 3 hours of data (top 5 rows).
  2) Execute only those trades whose strategy|action pair appears on the leaderboard.
  3) Record realized PNL using flat stakes ($250 per trade, 0.8 payout).

Use this script to validate that the SQL leaderboard behaves as intended
when plugged into a backtest flow.
"""

from __future__ import annotations

import psycopg2
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import warnings
warnings.filterwarnings("ignore")

# Database configuration (same as other simulations)
DB_CONFIG = {
    "host": "45.77.46.180",
    "port": 5432,
    "database": "TradingView",
    "user": "postgres",
    "password": "pwd@root99",
}

# Trading parameters (flat staking)
BET_SIZE = 250
PAYOUT = 0.8
WIN_PROFIT = BET_SIZE * PAYOUT  # +200
LOSE_LOSS = -BET_SIZE           # -250

# Leaderboard parameters (mirrors PNL-fomula.sql defaults)
LOOKBACK_HOURS = 3
PAYOUT_RATIO = 0.80
MARTINGALE = 1
MIN_WINRATE = 60
MIN_SIGNALS = 3
MAX_LOSS_ALLOWED = 3
HORIZON_LOCK = "10min"
RANK_LIMIT = 5

LEADERBOARD_SQL = """
WITH params AS (
    SELECT
        %(lookback_hours)s::int AS hours,
        %(payout)s::numeric AS payout,
        %(investment)s::numeric AS investment,
        %(martingale)s::numeric AS martingale,
        %(enable_filter)s::boolean AS enable_filter,
        %(min_winrate)s::numeric AS min_winrate,
        %(min_signals)s::int AS min_signals,
        %(enable_loss_cap)s::boolean AS enable_loss_cap,
        %(max_loss_allowed)s::int AS max_loss_allowed,
        %(enable_horizon_lock)s::boolean AS enable_horizon_lock,
        %(horizon_lock_value)s::text AS horizon_lock_value
),
raw AS (
    SELECT
        t.strategy,
        t.action,
        t.entry_time,
        t.result_10min,
        t.result_30min,
        t.result_60min
    FROM tradingviewdata t
    CROSS JOIN params
    WHERE t.entry_time >= %(end_time)s::timestamp - (params.hours || ' hours')::interval
      AND t.entry_time < %(end_time)s::timestamp
      AND t.action IN ('Buy','Sell')
),
long AS (
    SELECT strategy, action, entry_time, '10min'::text AS horizon, result_10min AS result
    FROM raw WHERE result_10min IN ('WIN','LOSE')
    UNION ALL
    SELECT strategy, action, entry_time, '30min', result_30min
    FROM raw WHERE result_30min IN ('WIN','LOSE')
    UNION ALL
    SELECT strategy, action, entry_time, '60min', result_60min
    FROM raw WHERE result_60min IN ('WIN','LOSE')
),
filtered_horizon AS (
    SELECT *
    FROM long, params
    WHERE NOT params.enable_horizon_lock OR horizon = params.horizon_lock_value
),
ordered AS (
    SELECT
        strategy,
        action,
        horizon,
        entry_time,
        result,
        LAG(result) OVER (PARTITION BY strategy, action, horizon ORDER BY entry_time) AS prev_result
    FROM filtered_horizon
),
islands AS (
    SELECT
        strategy,
        action,
        horizon,
        entry_time,
        result,
        SUM(CASE WHEN prev_result IS DISTINCT FROM result THEN 1 ELSE 0 END)
            OVER (PARTITION BY strategy, action, horizon ORDER BY entry_time) AS grp_id
    FROM ordered
),
runs AS (
    SELECT
        strategy,
        action,
        horizon,
        entry_time,
        result,
        grp_id,
        COUNT(*) OVER (PARTITION BY strategy, action, horizon, grp_id) AS run_len
    FROM islands
),
latest AS (
    SELECT DISTINCT ON (strategy, action, horizon)
        strategy,
        action,
        horizon,
        entry_time,
        result,
        grp_id,
        run_len
    FROM runs
    ORDER BY strategy, action, horizon, entry_time DESC
),
agg AS (
    SELECT
        strategy,
        action,
        horizon,
        COUNT(*) AS total_signals,
        SUM((result = 'WIN')::int) AS wins,
        ROUND(100.0 * SUM((result = 'WIN')::int) / NULLIF(COUNT(*), 0), 2) AS winrate_pct,
        COALESCE(MAX(CASE WHEN result = 'WIN' THEN run_len END), 0) AS max_win_streak,
        COALESCE(MAX(CASE WHEN result = 'LOSE' THEN run_len END), 0) AS max_loss_streak
    FROM runs
    GROUP BY strategy, action, horizon
),
final AS (
    SELECT
        a.strategy,
        a.action,
        a.horizon,
        a.total_signals,
        a.wins,
        (a.total_signals - a.wins) AS losses,
        a.winrate_pct,
        a.max_win_streak,
        a.max_loss_streak,
        l.result AS current_result,
        l.run_len AS current_streak_len,
        (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_flat,
        (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_best,
        (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_worst
    FROM agg a
    LEFT JOIN latest l
        ON l.strategy = a.strategy
       AND l.action = a.action
       AND l.horizon = a.horizon
    CROSS JOIN params
    WHERE
        (NOT params.enable_filter)
        OR (
            a.winrate_pct >= params.min_winrate
            AND a.total_signals >= params.min_signals
            AND (NOT params.enable_loss_cap OR a.max_loss_streak <= params.max_loss_allowed)
        )
)
SELECT
    final.*,
    (final.pnl_best + final.pnl_worst) / 2.0 AS pnl_performance
FROM final
ORDER BY pnl_performance DESC, final.winrate_pct DESC
LIMIT %(rank_limit)s;
"""

# NOTE: For simplicity the pnl_best/pnl_worst columns mirror pnl_flat because
# martingale is fixed at 1. If you enable martingale logic, port the detailed
# formulas from SQL as needed.

@dataclass
class TradeRecord:
    time: datetime
    strategy_action: str
    result: str
    pnl_change: float
    total_pnl: float

@dataclass
class HourSnapshot:
    hour: datetime
    leaderboard: List[Tuple[str, str, str, float]]  # (strategy, action, horizon, score)


def fetch_trading_data(conn, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch raw trades with a buffer for lookback."""
    lookback_start = start_date - timedelta(hours=LOOKBACK_HOURS)
    query = """
        SELECT strategy, action, entry_time, result_10min
        FROM tradingviewdata
        WHERE entry_time >= %s
          AND entry_time < %s
          AND action IN ('Buy','Sell')
          AND result_10min IS NOT NULL
        ORDER BY entry_time
    """
    df = pd.read_sql_query(query, conn, params=(lookback_start, end_date))
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["hour"] = df["entry_time"].dt.floor("H")
    df["strategy_action"] = df["strategy"] + " | " + df["action"]
    return df


def load_leaderboard(conn, end_time: datetime) -> pd.DataFrame:
    """Run the SQL leaderboard query for a given timestamp."""
    params = {
        "lookback_hours": LOOKBACK_HOURS,
        "payout": PAYOUT_RATIO,
        "investment": BET_SIZE,
        "martingale": MARTINGALE,
        "enable_filter": True,
        "min_winrate": MIN_WINRATE,
        "min_signals": MIN_SIGNALS,
        "enable_loss_cap": True,
        "max_loss_allowed": MAX_LOSS_ALLOWED,
        "enable_horizon_lock": True,
        "horizon_lock_value": HORIZON_LOCK,
        "end_time": end_time,
        "rank_limit": RANK_LIMIT,
    }

    df = pd.read_sql_query(LEADERBOARD_SQL, conn, params=params)
    return df


def run_simulation(start_date: str, end_date: str, verbose: bool = True) -> Dict[str, object]:
    """Replay trades using the leaderboard filter."""
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        trades_df = fetch_trading_data(conn, start_dt, end_dt)

        hours = pd.date_range(start_dt, end_dt, freq="H", inclusive="left")
        total_pnl = 0.0
        trade_log: List[TradeRecord] = []
        snapshots: List[HourSnapshot] = []

        for hour in hours:
            leaderboard_df = load_leaderboard(conn, hour)
            allowed = set(
                leaderboard_df["strategy"] + " | " + leaderboard_df["action"]
            )
            leaderboard_preview = [
                (
                    row["strategy"],
                    row["action"],
                    row["horizon"],
                    float(row["pnl_performance"]),
                )
                for _, row in leaderboard_df.iterrows()
            ]
            snapshots.append(HourSnapshot(hour=hour.to_pydatetime(), leaderboard=leaderboard_preview))

            hour_trades = trades_df[trades_df["hour"] == hour]
            if verbose:
                print("\n" + "=" * 100)
                print(f"⏰ {hour.strftime('%d/%m %H:%M')}  | Leaderboard entries: {len(leaderboard_preview)} | Cumulative PNL = ${total_pnl:.0f}")
                for idx, item in enumerate(leaderboard_preview, 1):
                    strat, act, horizon, score = item
                    print(f"  #{idx} {strat} | {act:<4} ({horizon})  Score≈{score:.2f}")

            for _, trade in hour_trades.iterrows():
                if trade["strategy_action"] in allowed:
                    pnl_change = WIN_PROFIT if trade["result_10min"] == "WIN" else LOSE_LOSS
                    total_pnl += pnl_change
                    record = TradeRecord(
                        time=trade["entry_time"].to_pydatetime(),
                        strategy_action=trade["strategy_action"],
                        result=trade["result_10min"],
                        pnl_change=pnl_change,
                        total_pnl=total_pnl,
                    )
                    trade_log.append(record)
                    if verbose:
                        print(f"    └─ {record.time.strftime('%H:%M')}  {record.strategy_action:<25} {record.result:<4} {record.pnl_change:+.0f}  (Total ${record.total_pnl:.0f})")

        if verbose:
            print("\n" + "=" * 100)
            print(f"💰 FINAL Total PNL: ${total_pnl:.0f}")
            print(f"📊 Executed Trades: {len(trade_log)}")
            print(f"🕑 Hours Simulated: {len(hours)}")
            print("=" * 100)

        return {
            "total_pnl": total_pnl,
            "trades": trade_log,
            "snapshots": snapshots,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    START_DATE = "2025-09-01 00:00:00"
    END_DATE = "2025-09-30 23:59:59"

    print("=" * 120)
    print("🚀 Leaderboard Simulation (3h lookback, Top 5)")
    print(f"📅 Period: {START_DATE} to {END_DATE}")
    print(f"🎯 Filters: winrate ≥ {MIN_WINRATE}%, signals ≥ {MIN_SIGNALS}, loss streak ≤ {MAX_LOSS_ALLOWED}")
    print("=" * 120)

    results = run_simulation(START_DATE, END_DATE, verbose=True)

    print("\n✅ Simulation complete!")
    print(f"Final PNL: ${results['total_pnl']:.0f}")
