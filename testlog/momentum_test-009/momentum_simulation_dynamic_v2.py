#!/usr/bin/env python3
"""
Momentum-based Strategy Scoring Simulation with Dynamic Strategy & Action Detection
Version: 2.0 (Option B - Linear Momentum)
Test: 009
Date: 2025-10-01

✅ UPDATED: Dynamic Strategy & Action Detection (no hard-code)
✅ Test Period: 1-30 September 2025

Scoring Formula:
- RecentScore_raw = 5×max(M₁,0) + 4×max(M₂,0) + 3×max(M₃,0) + 2×max(M₄,0) + 1×max(M₅,0)
- Where Mᵢ = PNLᵢ - PNLᵢ₊₁ (momentum/change in PNL)
"""

import psycopg2
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

BET_SIZE = 250
PAYOUT = 0.8
WIN_PROFIT = BET_SIZE * PAYOUT
LOSE_LOSS = -BET_SIZE
TOP_N = 6

def fetch_all_strategy_actions(start_date, end_date):
    """✅ UPDATED: Fetch all strategy-action combinations dynamically"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = f"""
    SELECT DISTINCT 
        strategy,
        action,
        strategy || ' | ' || action as full_name
    FROM tradingviewdata
    WHERE entry_time >= '{start_date}' AND entry_time < '{end_date}'
      AND result_10min IS NOT NULL
    ORDER BY strategy, action;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df['full_name'].tolist(), df['strategy'].unique(), df['action'].unique()

def fetch_trading_data(start_date, end_date):
    """✅ UPDATED: Fetch ALL trading data (all actions)"""
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

def calculate_hourly_pnl(df, full_strategies):
    """Calculate cumulative PNL for each strategy at each hour"""
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    df['hour'] = df['entry_time'].dt.floor('H')
    
    hourly_pnl = {}
    for strategy in full_strategies:
        df_strat = df[df['strategy_action'] == strategy].copy()
        if len(df_strat) > 0:
            df_strat['cumulative_pnl'] = df_strat['pnl_value'].cumsum()
            for hour, group in df_strat.groupby('hour'):
                if hour not in hourly_pnl:
                    hourly_pnl[hour] = {}
                hourly_pnl[hour][strategy] = group['cumulative_pnl'].iloc[-1]
    
    all_hours = sorted(hourly_pnl.keys())
    for strategy in full_strategies:
        prev_pnl = 0
        for hour in all_hours:
            if strategy not in hourly_pnl[hour]:
                hourly_pnl[hour][strategy] = prev_pnl
            else:
                prev_pnl = hourly_pnl[hour][strategy]
    
    return hourly_pnl, all_hours

def calculate_momentum_score(pnls):
    """Option B: Linear Momentum"""
    p1, p2, p3, p4, p5, p6 = pnls
    
    m1 = p1 - p2
    m2 = p2 - p3
    m3 = p3 - p4
    m4 = p4 - p5
    m5 = p5 - p6
    
    recent_raw = (5 * max(m1, 0) + 
                  4 * max(m2, 0) + 
                  3 * max(m3, 0) + 
                  2 * max(m4, 0) + 
                  1 * max(m5, 0))
    
    return recent_raw

def run_simulation(start_date, end_date, verbose=True):
    """Run simulation with dynamic strategy-action detection"""
    
    full_strategies, base_strategies, actions = fetch_all_strategy_actions(start_date, end_date)
    
    if verbose:
        print(f"📊 Found {len(base_strategies)} strategies, {len(actions)} actions")
        print(f"📋 Total combinations: {len(full_strategies)}")
        print(f"🎯 Actions: {', '.join(actions)}\n")
    
    df = fetch_trading_data(start_date, end_date)
    hourly_pnl, all_hours = calculate_hourly_pnl(df, full_strategies)
    
    current_strategy = None
    total_pnl = 0
    trades = []
    strategy_changes = []
    
    for hour_idx, hour in enumerate(all_hours):
        hour_str = hour.strftime('%d/%m %H:%M')
        
        scores = {}
        recent_raws = []
        
        for strategy in full_strategies:
            pnls = []
            for i in range(6):
                lookback_idx = hour_idx - i
                if lookback_idx >= 0:
                    pnls.append(hourly_pnl[all_hours[lookback_idx]].get(strategy, 0))
                else:
                    pnls.append(0)
            
            recent_raw = calculate_momentum_score(pnls)
            recent_raws.append(recent_raw)
            scores[strategy] = {'pnl': pnls[0], 'recent_raw': recent_raw, 'score': 0}
        
        recent_kpi = np.mean(recent_raws) + np.std(recent_raws) if np.std(recent_raws) > 0 else 1
        
        for strategy in scores:
            raw = scores[strategy]['recent_raw']
            score = min((raw / recent_kpi) * 30, 30) if recent_kpi > 0 else 0
            scores[strategy]['score'] = score
        
        sorted_strategies = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        top6_strategies = [s[0] for s in sorted_strategies[:TOP_N]]
        best_strategy = top6_strategies[0]
        
        if verbose and hour_idx % 24 == 0:
            print(f"\n{'='*120}")
            print(f"⏰ {hour_str}         Cumulative PNL = ${total_pnl:.0f}")
            print(f"🏆 TOP 6: {', '.join([s.split('|')[0].strip() for s in top6_strategies[:3]])}...")
        
        if current_strategy != best_strategy:
            if current_strategy is not None:
                strategy_changes.append({'time': hour, 'from': current_strategy, 'to': best_strategy})
            current_strategy = best_strategy
        
        current_trades = df[(df['strategy_action'] == best_strategy) & (df['hour'] == hour)]
        for _, trade in current_trades.iterrows():
            pnl_change = WIN_PROFIT if trade['result_10min'] == 'WIN' else LOSE_LOSS
            total_pnl += pnl_change
            trades.append({'time': trade['entry_time'], 'strategy': best_strategy, 'result': trade['result_10min'], 'pnl': pnl_change, 'total_pnl': total_pnl})
    
    if verbose:
        print(f"\n{'='*120}")
        print(f"💰 FINAL Total PNL: ${total_pnl:.0f}")
        print(f"📊 Total Trades: {len(trades)}")
        print(f"🔄 Strategy Changes: {len(strategy_changes)}")
        print(f"{'='*120}")
    
    return {'total_pnl': total_pnl, 'trades': trades, 'strategy_changes': strategy_changes, 'all_strategies': full_strategies}

if __name__ == "__main__":
    START_DATE = '2025-09-01 00:00:00'
    END_DATE = '2025-09-30 23:59:59'
    
    print("="*120)
    print("🚀 Test 009: Linear Momentum (Option B) - Dynamic Strategy & Action")
    print(f"📅 Period: {START_DATE} to {END_DATE}")
    print(f"💰 Investment: ${BET_SIZE}/trade, Payout: {PAYOUT}")
    print("="*120)
    
    results = run_simulation(START_DATE, END_DATE, verbose=True)
    
    print(f"\n✅ Test 009 Complete!")
    print(f"Formula: Linear (5,4,3,2,1)")
    print(f"Final PNL: ${results['total_pnl']:.0f}")

