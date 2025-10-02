#!/usr/bin/env python3
"""
Momentum-based Strategy Scoring Simulation
Version: 1.0
Date: 2025-10-01

This script simulates trading strategy selection using a momentum-based
Recent Performance scoring system.

Scoring Formula:
- RecentScore_raw = 5×max(M₁,0) + 4×max(M₂,0) + 3×max(M₃,0) + 2×max(M₄,0) + 1×max(M₅,0)
- Where Mᵢ = PNLᵢ - PNLᵢ₊₁ (momentum/change in PNL)
- Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
- RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)

Trading Rules:
- Investment: $250 per trade
- Payout: 0.8 (WIN: +$200, LOSE: -$250)
- Strategy selection: Choose highest scoring strategy each hour
"""

import psycopg2
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Database Configuration
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

# Trading Parameters
BET_SIZE = 250
PAYOUT = 0.8
WIN_PROFIT = BET_SIZE * PAYOUT  # $200
LOSE_LOSS = -BET_SIZE  # -$250

def fetch_trading_data(start_date, end_date, strategies):
    """Fetch trading data from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    strategy_list = "', '".join(strategies)
    query = f"""
    SELECT strategy, action, entry_time, result_10min,
           CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END as pnl_value
    FROM tradingviewdata
    WHERE entry_time >= '{start_date}' AND entry_time < '{end_date}'
      AND strategy IN ('{strategy_list}')
      AND action IN ('Buy', 'Sell') AND result_10min IS NOT NULL
    ORDER BY entry_time;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def calculate_hourly_pnl(df, strategies):
    """Calculate cumulative PNL for each strategy at each hour"""
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    df['hour'] = df['entry_time'].dt.floor('H')
    
    hourly_pnl = {}
    for strategy in strategies:
        df_strat = df[df['strategy_action'] == strategy].copy()
        if len(df_strat) > 0:
            df_strat['cumulative_pnl'] = df_strat['pnl_value'].cumsum()
            for hour, group in df_strat.groupby('hour'):
                if hour not in hourly_pnl:
                    hourly_pnl[hour] = {}
                hourly_pnl[hour][strategy] = group['cumulative_pnl'].iloc[-1]
    
    # Fill missing PNL values (carry forward last known value)
    all_hours = sorted(hourly_pnl.keys())
    for strategy in strategies:
        prev_pnl = 0
        for hour in all_hours:
            if strategy not in hourly_pnl[hour]:
                hourly_pnl[hour][strategy] = prev_pnl
            else:
                prev_pnl = hourly_pnl[hour][strategy]
    
    return hourly_pnl, all_hours

def calculate_momentum_score(pnls):
    """
    Calculate momentum-based Recent Performance Score
    
    Args:
        pnls: List of [PNL₁, PNL₂, PNL₃, PNL₄, PNL₅, PNL₆]
    
    Returns:
        tuple: (recent_raw, score)
    """
    p1, p2, p3, p4, p5, p6 = pnls
    
    # Calculate momentum (change between consecutive hours)
    m1 = p1 - p2  # Most recent hour change
    m2 = p2 - p3
    m3 = p3 - p4
    m4 = p4 - p5
    m5 = p5 - p6
    
    # Weighted momentum score (only positive momentum counts)
    recent_raw = (5 * max(m1, 0) + 
                  4 * max(m2, 0) + 
                  3 * max(m3, 0) + 
                  2 * max(m4, 0) + 
                  1 * max(m5, 0))
    
    return recent_raw

def run_simulation(start_date, end_date, strategies, verbose=True):
    """
    Run trading simulation with momentum-based scoring
    
    Args:
        start_date: Start date string (YYYY-MM-DD HH:MM:SS)
        end_date: End date string (YYYY-MM-DD HH:MM:SS)
        strategies: List of strategy names (will be expanded to Buy/Sell actions)
        verbose: If True, print hourly logs
    
    Returns:
        dict: Simulation results including total_pnl, trades, strategy_changes
    """
    # Fetch data
    df = fetch_trading_data(start_date, end_date, strategies)
    
    # Expand strategies to include actions
    full_strategies = []
    for strat in strategies:
        full_strategies.extend([f"{strat} | Buy", f"{strat} | Sell"])
    
    # Calculate hourly PNL
    hourly_pnl, all_hours = calculate_hourly_pnl(df, full_strategies)
    
    # Run simulation
    current_strategy = None
    total_pnl = 0
    trades = []
    strategy_changes = []
    
    for hour_idx, hour in enumerate(all_hours):
        hour_str = hour.strftime('%d/%m %H:%M')
        
        # Calculate scores for all strategies
        scores = {}
        recent_raws = []
        
        for strategy in full_strategies:
            # Get last 6 hours of PNL
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
        
        # Calculate KPI and normalize scores
        recent_kpi = np.mean(recent_raws) + np.std(recent_raws) if np.std(recent_raws) > 0 else 1
        
        for strategy in scores:
            raw = scores[strategy]['recent_raw']
            score = min((raw / recent_kpi) * 30, 30) if recent_kpi > 0 else 0
            scores[strategy]['score'] = score
        
        # Select best strategy
        best_strategy = max(scores, key=lambda s: scores[s]['score'])
        
        # Print hourly log
        if verbose:
            print(f"\n{'='*120}")
            print(f"⏰ {hour_str}         Cumulative PNL = ${total_pnl:.0f}")
            print(f"{'='*120}")
            print(f"{'Strategy':<30} {'PNL':>8} {'Score':>7} {'สถานะ':<8}")
            print(f"{'-'*120}")
            
            for strategy in sorted(scores.keys()):
                pnl = scores[strategy]['pnl']
                score = scores[strategy]['score']
                is_selected = strategy == best_strategy
                status = "✅" if is_selected else "❌"
                print(f"{strategy:<30} ${pnl:>7.0f} {score:>6.1f} {status:<8}")
            
            print(f"{'-'*120}")
        
        # Track strategy changes
        if current_strategy != best_strategy:
            if current_strategy is not None:
                strategy_changes.append({
                    'time': hour,
                    'from': current_strategy,
                    'to': best_strategy
                })
            current_strategy = best_strategy
        
        # Calculate realized PNL from trades
        current_trades = df[(df['strategy_action'] == best_strategy) & (df['hour'] == hour)]
        for _, trade in current_trades.iterrows():
            if trade['result_10min'] == 'WIN':
                pnl_change = WIN_PROFIT
                total_pnl += pnl_change
            else:
                pnl_change = LOSE_LOSS
                total_pnl += pnl_change
            
            trades.append({
                'time': trade['entry_time'],
                'strategy': best_strategy,
                'result': trade['result_10min'],
                'pnl': pnl_change,
                'total_pnl': total_pnl
            })
    
    # Print final summary
    if verbose:
        print(f"\n{'='*120}")
        print(f"💰 FINAL Total PNL: ${total_pnl:.0f}")
        print(f"📊 Total Trades: {len(trades)}")
        print(f"🔄 Strategy Changes: {len(strategy_changes)}")
        print(f"{'='*120}")
    
    return {
        'total_pnl': total_pnl,
        'trades': trades,
        'strategy_changes': strategy_changes,
        'scores_history': scores
    }

if __name__ == "__main__":
    # Simulation parameters
    START_DATE = '2025-09-29 00:00:00'
    END_DATE = '2025-10-01 00:00:00'
    STRATEGIES = ['MWP10-1m', 'MWP20-3m', 'MWP-27', 'MWP-31', 'SuperTrend10']
    
    print("="*120)
    print("🚀 Starting Momentum-based Strategy Scoring Simulation")
    print(f"📅 Period: {START_DATE} to {END_DATE}")
    print(f"💰 Investment: ${BET_SIZE}/trade, Payout: {PAYOUT}")
    print(f"📈 Strategies: {', '.join(STRATEGIES)}")
    print("="*120)
    
    # Run simulation
    results = run_simulation(START_DATE, END_DATE, STRATEGIES, verbose=True)
    
    print(f"\n✅ Simulation complete!")
    print(f"Final PNL: ${results['total_pnl']:.0f}")

