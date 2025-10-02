#!/usr/bin/env python3
"""
🎯 Momentum-based Strategy Scoring Simulation - Template
Features:
- Dynamic strategy selection (scan ALL strategies)
- Hard-code Actions: Buy/Sell only
- Log levels: info (summary) / debug (detailed)
"""
import psycopg2
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Database configuration
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

# Trading parameters
BET_SIZE = 250
PAYOUT = 0.8
WIN_PROFIT = BET_SIZE * PAYOUT
LOSE_LOSS = -BET_SIZE
TOP_N = 6

def fetch_all_strategies(start_date, end_date):
    """Fetch all unique strategies from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    query = f"""
    SELECT DISTINCT strategy
    FROM tradingviewdata
    WHERE entry_time >= '{start_date}' AND entry_time < '{end_date}'
      AND action IN ('Buy', 'Sell')
      AND result_10min IS NOT NULL
    ORDER BY strategy;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    strategies = df['strategy'].tolist()
    full_strategies = []
    for strat in strategies:
        full_strategies.extend([f"{strat} | Buy", f"{strat} | Sell"])
    
    return full_strategies

def fetch_trading_data(start_date, end_date):
    """Fetch trading data"""
    conn = psycopg2.connect(**DB_CONFIG)
    query = f"""
    SELECT strategy, action, entry_time, result_10min,
           CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END as pnl_value
    FROM tradingviewdata
    WHERE entry_time >= '{start_date}' AND entry_time < '{end_date}'
      AND action IN ('Buy', 'Sell')
      AND result_10min IS NOT NULL
    ORDER BY entry_time;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    df['hour'] = pd.to_datetime(df['entry_time']).dt.floor('H')
    return df

def calculate_hourly_pnl(df, full_strategies):
    """Calculate hourly PNL for each strategy"""
    all_hours = sorted(df['hour'].unique())
    hourly_pnl = {}
    
    for hour in all_hours:
        hourly_pnl[hour] = {}
        hour_data = df[df['hour'] == hour]
        for strategy in full_strategies:
            strategy_trades = hour_data[hour_data['strategy_action'] == strategy]
            pnl = strategy_trades['pnl_value'].sum() if len(strategy_trades) > 0 else 0
            hourly_pnl[hour][strategy] = pnl
    
    return hourly_pnl, all_hours

def calculate_momentum_score(pnls):
    """
    Calculate momentum-based Recent Performance Score
    Formula: Acceleration (Option D)
    
    Args:
        pnls: List of [PNL₁, PNL₂, PNL₃, PNL₄, PNL₅, PNL₆]
    
    Returns:
        float: recent_raw score
    """
    p1, p2, p3, p4, p5, p6 = pnls
    
    # Calculate momentum
    m1 = p1 - p2  # Most recent momentum
    m2 = p2 - p3  # Previous momentum
    
    # Acceleration (momentum of momentum)
    acceleration = m1 - m2
    
    # Score: 5×M₁ + 3×Acceleration
    recent_raw = (5 * max(m1, 0) + 3 * max(acceleration, 0))
    
    return recent_raw

def run_simulation(start_date, end_date, log_level='info'):
    """
    Run trading simulation with DYNAMIC Top 6 strategy selection
    
    Args:
        start_date: Start date string (YYYY-MM-DD HH:MM:SS)
        end_date: End date string (YYYY-MM-DD HH:MM:SS)
        log_level: 'info' (summary) or 'debug' (detailed)
    
    Returns:
        dict: Simulation results including total_pnl, trades, strategy_changes
    """
    # Fetch strategies
    full_strategies = fetch_all_strategies(start_date, end_date)
    
    if log_level in ['info', 'debug']:
        print(f"📊 Found {len(full_strategies)} combinations (Buy/Sell only)\n")
    
    # Fetch data
    df = fetch_trading_data(start_date, end_date)
    hourly_pnl, all_hours = calculate_hourly_pnl(df, full_strategies)
    
    # Initialize simulation
    current_strategy = None
    total_pnl = 0
    trades = []
    strategy_changes = []
    
    # Run simulation
    for hour_idx, hour in enumerate(all_hours):
        hour_str = hour.strftime('%d/%m %H:%M')
        scores = {}
        recent_raws = []
        
        # Calculate scores for ALL strategies
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
            
            # Calculate TRADE and WIN counts for current hour
            hour_data = df[(df['strategy_action'] == strategy) & (df['hour'] == hour)]
            trade_count = len(hour_data)
            win_count = len(hour_data[hour_data['result_10min'] == 'WIN'])
            
            scores[strategy] = {
                'pnl': pnls[0], 
                'recent_raw': recent_raw, 
                'score': 0,
                'trades': trade_count,
                'wins': win_count
            }
        
        # Normalize scores
        recent_kpi = np.mean(recent_raws) + np.std(recent_raws) if np.std(recent_raws) > 0 else 1
        
        for strategy in scores:
            raw = scores[strategy]['recent_raw']
            score = min((raw / recent_kpi) * 30, 30) if recent_kpi > 0 else 0
            scores[strategy]['score'] = score
        
        # Select TOP 6
        sorted_strategies = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        top6_strategies = [s[0] for s in sorted_strategies[:TOP_N]]
        best_strategy = top6_strategies[0]
        
        # ========== LOG OUTPUT ==========
        if log_level == 'debug':
            # Detailed log (like V008) - every hour with table
            print(f"\n{'='*120}")
            print(f"⏰ {hour_str}         Cumulative PNL = ${total_pnl:.0f}")
            print(f"{'='*120}")
            print(f"🏆 TOP 6 Strategies (out of {len(full_strategies)} total):")
            print(f"{'Strategy':<30} {'TRADE':>6} {'WIN':>5} {'PNL':>8} {'Score':>7} {'สถานะ':<8}")
            print(f"{'-'*120}")
            
            for idx, strategy in enumerate(top6_strategies, 1):
                trade_count = scores[strategy]['trades']
                win_count = scores[strategy]['wins']
                pnl = scores[strategy]['pnl']
                score = scores[strategy]['score']
                is_selected = strategy == best_strategy
                status = "✅" if is_selected else f"#{idx}"
                print(f"{strategy:<30} {trade_count:>6} {win_count:>5} ${pnl:>7.0f} {score:>6.1f} {status:<8}")
            
            print(f"{'-'*120}")
        
        elif log_level == 'info' and hour_idx % 24 == 0:
            # Summary log (like V016/017) - daily summary
            print(f"⏰ {hour_str} PNL=${total_pnl:.0f} TOP: {best_strategy.split('|')[0].strip()}")
        
        # Track strategy changes
        if current_strategy != best_strategy:
            if current_strategy is not None:
                strategy_changes.append({
                    'time': hour,
                    'from': current_strategy,
                    'to': best_strategy
                })
            current_strategy = best_strategy
        
        # Execute trades
        current_trades = df[(df['strategy_action'] == best_strategy) & (df['hour'] == hour)]
        for _, trade in current_trades.iterrows():
            pnl_change = WIN_PROFIT if trade['result_10min'] == 'WIN' else LOSE_LOSS
            total_pnl += pnl_change
            trades.append({
                'time': trade['entry_time'],
                'strategy': best_strategy,
                'result': trade['result_10min'],
                'pnl': pnl_change,
                'total_pnl': total_pnl
            })
    
    # Print final summary
    if log_level in ['info', 'debug']:
        print(f"\n{'='*120}")
        print(f"💰 FINAL: ${total_pnl:.0f} | Trades: {len(trades)} | Changes: {len(strategy_changes)}")
        print(f"{'='*120}")
    
    return {
        'total_pnl': total_pnl,
        'trades': trades,
        'strategy_changes': strategy_changes,
        'all_strategies': full_strategies
    }

if __name__ == "__main__":
    # Configuration
    START_DATE = '2025-09-22 00:00:00'
    END_DATE = '2025-09-30 23:59:59'
    LOG_LEVEL = 'debug'  # 'info' or 'debug'
    
    print("="*120)
    print("🚀 Momentum Simulation - Acceleration Formula")
    print(f"📅 Period: {START_DATE} to {END_DATE}")
    print(f"📊 Log Level: {LOG_LEVEL.upper()}")
    print(f"🎯 Actions: Buy/Sell ONLY (hard-code)")
    print(f"💰 Investment: ${BET_SIZE}/trade, Payout: {PAYOUT}")
    print("="*120)
    
    results = run_simulation(START_DATE, END_DATE, log_level=LOG_LEVEL)
    
    print(f"\n✅ Simulation Complete!")
    print(f"Formula: Acceleration (5×M₁ + 3×Acceleration)")
    print(f"Final PNL: ${results['total_pnl']:.0f}")

