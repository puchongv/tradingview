#!/usr/bin/env python3
import psycopg2
import pandas as pd
import re
import datetime as dt
from database_connection import DB_CONFIG

SQL_PATH = '/Users/puchong/tradingview/agent-script/strategy_range_scanner_v1_0_0.sql'


def load_sql(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def fill_params(sql: str, *, timeframes_csv: str, start_date: str, end_date: str,
                min_trades: int, payout: float, investment: float,
                quality_mode: str, min_signal_quality: float, min_stability: float) -> str:
    repl = {
        r"\{\{timeframes_csv\}\}": f"'{timeframes_csv}'",
        r"\{\{start_date\}\}": f"'{start_date}'",
        r"\{\{end_date\}\}": f"'{end_date}'",
        r"\{\{min_trades_per_strategy\}\}": f"'{min_trades}'",
        r"\{\{payout_rate\}\}": f"'{payout}'",
        r"\{\{investment_amount\}\}": f"'{investment}'",
        r"\{\{quality_mode\}\}": f"'{quality_mode}'",
        r"\{\{min_signal_quality\}\}": f"'{min_signal_quality}'",
        r"\{\{min_stability\}\}": f"'{min_stability}'",
    }
    for pattern, value in repl.items():
        sql = re.sub(pattern, value, sql)
    return sql


def compute_dates() -> tuple[str, str]:
    today = dt.date.today()
    scan_week_start = today - dt.timedelta(days=7)
    test_end = scan_week_start - dt.timedelta(days=1)
    # Use earliest known date per user note (approx) or 14 days span if earlier not available
    default_start = dt.date(2025, 8, 28)
    start = default_start if default_start < test_end else test_end - dt.timedelta(days=14)
    return start.strftime('%Y-%m-%d'), test_end.strftime('%Y-%m-%d')


def main():
    # Approved playbook buckets (UTC)
    selections = [
        {'timeframe': '10', 'day_of_week': 3, 'hour_of_day': 20, 'strategy_action': 'UT-BOT2-10 | Buy'},
        {'timeframe': '10', 'day_of_week': 3, 'hour_of_day': 16, 'strategy_action': 'UT-BOT2-10 | Sell'},
        {'timeframe': '10', 'day_of_week': 3, 'hour_of_day': 17, 'strategy_action': 'UT-BOT2-10 | Sell'},
        {'timeframe': '30', 'day_of_week': 3, 'hour_of_day': 18, 'strategy_action': 'UT-BOT2-10 | Sell'},
    ]

    start_date, end_date = compute_dates()
    sql_template = load_sql(SQL_PATH)
    sql = fill_params(
        sql_template,
        timeframes_csv='10,30',
        start_date=start_date,
        end_date=end_date,
        min_trades=1,
        payout=0.8,
        investment=250,
        quality_mode='balanced',
        min_signal_quality=0.0,
        min_stability=0.0,
    )

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()

    if df.empty:
        print(f'No rows in test window {start_date} to {end_date}.')
        return

    # Normalize dtypes for matching
    df['timeframe'] = df['timeframe'].astype(str)
    # Filter to selections
    mask = False
    for sel in selections:
        m = (
            (df['timeframe'] == sel['timeframe']) &
            (df['day_of_week'] == sel['day_of_week']) &
            (df['hour_of_day'] == sel['hour_of_day']) &
            (df['strategy_action'] == sel['strategy_action'])
        )
        mask = m if mask is False else (mask | m)
    df_sel = df[mask].copy()

    if df_sel.empty:
        print('No matching rows for the approved playbook in the test window.')
        print(f'Test window: {start_date} to {end_date}')
        print('Available sample (top 20):')
        print(df.head(20).to_string(index=False))
        return

    # Summaries per selection
    group_cols = ['timeframe', 'day_of_week', 'hour_of_day', 'strategy_action']
    agg = df_sel.groupby(group_cols, as_index=False).agg(
        trade=('trade', 'sum'),
        trade_win=('trade_win', 'sum'),
        pnl=('pnl', 'sum'),
    )
    agg['winrate_pct'] = (agg['trade_win'] / agg['trade']).where(agg['trade'] > 0, 0) * 100.0

    # Overall
    total_trades = int(agg['trade'].sum())
    total_wins = int(agg['trade_win'].sum())
    overall_winrate = (total_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    overall_pnl = float(agg['pnl'].sum())

    print(f'Test window: {start_date} to {end_date} (UTC)')
    print('\nPer bucket results:')
    print(agg.to_string(index=False))
    print('\nOverall:')
    print(f'  trades={total_trades}, wins={total_wins}, winrate={overall_winrate:.2f}%, pnl={overall_pnl:.2f}')


if __name__ == '__main__':
    main()


