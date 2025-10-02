#!/usr/bin/env python3
"""
Test: 030 - PNL Leaderboard Selection
Formula: TOP 1 from PNL Performance Leaderboard
Period: 01-30 Sep 2025
Leaderboard: Updated every hour, based on last 3 hours
Filter: winrate>=60%, signals>=3, loss_streak<=3, horizon='10min'
"""
import psycopg2
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

# Constants
WIN_PROFIT = 200
LOSE_LOSS = -250
PAYOUT = 0.8
INVESTMENT = 250
MARTINGALE = 1
MIN_WINRATE = 60
MIN_SIGNALS = 3
MAX_LOSS_STREAK = 3
HORIZON = '10min'
LOOKBACK_HOURS = 3

def calculate_leaderboard(current_time, lookback_hours=3):
    """
    คำนวน leaderboard TOP 5 จากข้อมูล lookback_hours ชั่วโมงย้อนหลัง
    ใช้สูตร PNL Performance (best/worst average)
    """
    conn = psycopg2.connect(**DB_CONFIG)
    
    start_time = current_time - timedelta(hours=lookback_hours)
    
    query = f"""
    WITH params AS (
      SELECT
        {lookback_hours}::int AS hours,
        {PAYOUT}::numeric AS payout,
        {INVESTMENT}::numeric AS investment,
        {MARTINGALE}::numeric AS martingale,
        true::boolean AS enable_filter,
        {MIN_WINRATE}::numeric AS min_winrate,
        {MIN_SIGNALS}::int AS min_signals,
        true::boolean AS enable_loss_cap,
        {MAX_LOSS_STREAK}::int AS max_loss_allowed,
        true::boolean AS enable_horizon_lock,
        '{HORIZON}'::text AS horizon_lock_value
    ),
    raw AS (
      SELECT
        strategy, action, entry_time,
        result_10min, result_30min, result_60min
      FROM tradingviewdata, params
      WHERE entry_time >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
        AND entry_time < '{current_time.strftime('%Y-%m-%d %H:%M:%S')}'
    ),
    long AS (
      SELECT strategy, action, entry_time, '10min' AS horizon, result_10min AS result
      FROM raw WHERE result_10min IN ('WIN','LOSE')
      UNION ALL
      SELECT strategy, action, entry_time, '30min', result_30min
      FROM raw WHERE result_30min IN ('WIN','LOSE')
      UNION ALL
      SELECT strategy, action, entry_time, '60min', result_60min
      FROM raw WHERE result_60min IN ('WIN','LOSE')
    ),
    ordered AS (
      SELECT
        strategy, action, horizon, entry_time, result,
        LAG(result) OVER (PARTITION BY strategy, action, horizon ORDER BY entry_time) AS prev_result
      FROM long
    ),
    islands AS (
      SELECT
        strategy, action, horizon, entry_time, result,
        SUM(CASE WHEN prev_result IS DISTINCT FROM result THEN 1 ELSE 0 END)
          OVER (PARTITION BY strategy, action, horizon ORDER BY entry_time) AS grp_id
      FROM ordered
    ),
    runs AS (
      SELECT
        strategy, action, horizon, entry_time, result, grp_id,
        COUNT(*) OVER (PARTITION BY strategy, action, horizon, grp_id) AS run_len
      FROM islands
    ),
    agg AS (
      SELECT
        strategy, action, horizon,
        COUNT(*) AS total_signals,
        SUM((result='WIN')::int) AS wins,
        ROUND(100.0*SUM((result='WIN')::int)/NULLIF(COUNT(*),0),2) AS winrate_pct,
        COALESCE(MAX(CASE WHEN result='LOSE' THEN run_len END),0) AS max_loss_streak
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
        a.max_loss_streak,
        
        -- FLAT PNL
        (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_flat,
        
        -- BEST-CASE PNL (simplified)
        (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_best,
        
        -- WORST-CASE PNL (simplified)
        (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_worst
        
      FROM agg a
      CROSS JOIN params
      WHERE
        (NOT params.enable_filter)
        OR (
          a.winrate_pct >= params.min_winrate
          AND a.total_signals >= params.min_signals
          AND (NOT params.enable_loss_cap OR a.max_loss_streak <= params.max_loss_allowed)
          AND (NOT params.enable_horizon_lock OR a.horizon = params.horizon_lock_value)
        )
    )
    SELECT
      final.*,
      (final.pnl_best + final.pnl_worst) / 2.0 AS pnl_performance
    FROM final
    ORDER BY pnl_performance DESC
    LIMIT 5;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def fetch_trading_data(start_date, end_date):
    """Fetch trading data for simulation period"""
    conn = psycopg2.connect(**DB_CONFIG)
    query = f"""
    SELECT strategy, action, entry_time, result_10min,
           CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END as pnl_value
    FROM tradingviewdata
    WHERE entry_time >= '{start_date}' AND entry_time < '{end_date}'
      AND result_10min IS NOT NULL
    ORDER BY entry_time;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def run_simulation(start_date, end_date, log_level='debug'):
    """
    Run simulation using PNL Leaderboard
    - Update leaderboard every hour
    - Trade TOP 1 from leaderboard
    """
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Fetch all trading data
    df = fetch_trading_data(start_date, end_date)
    df['hour'] = df['entry_time'].dt.floor('H')
    
    all_hours = pd.date_range(start=start_dt, end=end_dt, freq='H')
    
    current_strategy = None
    total_pnl = 0
    trades = []
    strategy_changes = []
    
    print(f"\n📊 Simulation: {len(all_hours)} hours")
    print(f"🔄 Leaderboard updated every hour (last {LOOKBACK_HOURS}h)")
    print(f"🎯 Trade TOP 1 only\n")
    
    for hour in all_hours:
        hour_str = hour.strftime('%d/%m %H:%M')
        
        # Calculate leaderboard for this hour
        leaderboard = calculate_leaderboard(hour, LOOKBACK_HOURS)
        
        if len(leaderboard) == 0:
            if log_level == 'debug':
                print(f"⏰ {hour_str} - No leaderboard (insufficient data)")
            continue
        
        # Get TOP 1
        top1 = leaderboard.iloc[0]
        best_strategy = f"{top1['strategy']} | {top1['action']}"
        
        # Log leaderboard
        if log_level == 'debug':
            print(f"\n{'='*120}")
            print(f"⏰ {hour_str}         Cumulative PNL = ${total_pnl:.0f}")
            print(f"{'='*120}")
            print(f"🏆 TOP 5 Leaderboard (last {LOOKBACK_HOURS}h):")
            print(f"{'#':<3} {'Strategy':<20} {'Action':<6} {'Signals':>7} {'WR%':>5} {'PNL Perf':>10} {'สถานะ':<8}")
            print(f"{'-'*120}")
            
            for idx, row in leaderboard.iterrows():
                rank = idx + 1
                status = "✅" if rank == 1 else f"#{rank}"
                print(f"{rank:<3} {row['strategy']:<20} {row['action']:<6} {row['total_signals']:>7} "
                      f"{row['winrate_pct']:>5.1f} ${row['pnl_performance']:>9.0f} {status:<8}")
            
            print(f"{'-'*120}")
        
        # Change strategy if needed
        if current_strategy != best_strategy:
            if current_strategy is not None:
                strategy_changes.append({
                    'time': hour,
                    'from': current_strategy,
                    'to': best_strategy
                })
            current_strategy = best_strategy
        
        # Execute trades
        current_trades = df[(df['hour'] == hour) & 
                           (df['strategy'] + ' | ' + df['action'] == best_strategy)]
        
        hour_pnl_change = 0
        for _, trade in current_trades.iterrows():
            pnl_change = WIN_PROFIT if trade['result_10min'] == 'WIN' else LOSE_LOSS
            total_pnl += pnl_change
            hour_pnl_change += pnl_change
            trades.append({
                'time': trade['entry_time'],
                'strategy': best_strategy,
                'result': trade['result_10min'],
                'pnl': pnl_change,
                'total_pnl': total_pnl
            })
            
            if log_level == 'debug':
                trade_time = pd.to_datetime(trade['entry_time']).strftime('%H:%M')
                result_icon = "✅" if trade['result_10min'] == 'WIN' else "❌"
                print(f"  └─ {trade_time}  {result_icon} {trade['result_10min']:<4}  "
                      f"{pnl_change:+.0f}  (Running: ${total_pnl:.0f})")
        
        if log_level == 'debug' and len(current_trades) > 0:
            print(f"\n💰 Hour Change: {hour_pnl_change:+.0f} | Total Trades: {len(current_trades)}")
    
    print(f"\n{'='*120}")
    print(f"💰 FINAL: ${total_pnl:.0f} | Trades: {len(trades)} | Changes: {len(strategy_changes)}")
    print(f"{'='*120}")
    
    return {
        'total_pnl': total_pnl,
        'trades': trades,
        'strategy_changes': strategy_changes
    }

if __name__ == "__main__":
    print("="*120)
    print("🚀 Test 030: PNL Leaderboard Selection")
    print("📅 Period: 01-30 Sep 2025 (30 วัน)")
    print("📊 Formula: PNL Performance (Best+Worst)/2")
    print("🎯 Filter: WR>=60%, Signals>=3, LossStreak<=3, Horizon=10min")
    print("🔄 Leaderboard: Updated every hour (last 3h)")
    print("🏆 Trade: TOP 1 only")
    print("="*120)
    
    results = run_simulation('2025-09-01 00:00:00', '2025-09-30 23:59:59', log_level='debug')
    
    print(f"\n✅ Test 030 Complete!")
    print(f"Formula: PNL Leaderboard (TOP 1)")
    print(f"Final PNL: ${results['total_pnl']:.0f}")


