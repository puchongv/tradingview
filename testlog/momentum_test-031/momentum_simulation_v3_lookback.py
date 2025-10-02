#!/usr/bin/env python3
"""
Test: 031 - Acceleration (Option D) + 3-Hour Lookback + TOP 3 with Score >= 25
Formula: 5×M₁ + 3×Acceleration
Period: 01-30 Sep 2025 (30 วัน)
Actions: Buy/Sell ONLY (hard-code)
Lookback: ดึงข้อมูลย้อนหลัง 3 ชั่วโมง เพื่อให้ P1-P6 มีค่าจริง
Selection: TOP 3 strategies with Score >= 25 (เพิ่มโอกาสการเทรด)
"""
import psycopg2
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

DB_CONFIG = {'host': '45.77.46.180', 'port': 5432, 'database': 'TradingView', 'user': 'postgres', 'password': 'pwd@root99'}
BET_SIZE, PAYOUT, WIN_PROFIT, LOSE_LOSS = 250, 0.8, 200, -250
TOP_N = 6  # ยังคำนวนคะแนนทั้ง 6 อันดับ
MIN_SCORE = 25  # แต่เลือกเฉพาะที่ >= 25
MAX_SELECT = 3  # เลือกสูงสุด 3 ตัว

def fetch_all_strategies(start_date, end_date):
    """Fetch strategies - Hard-code Buy/Sell only"""
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
    
    # Expand to Buy/Sell
    full_strategies = []
    for s in strategies:
        full_strategies.extend([f"{s} | Buy", f"{s} | Sell"])
    
    return full_strategies

def fetch_trading_data(start_date, end_date, lookback_hours=3):
    """
    Fetch trading data - Hard-code Buy/Sell only
    ✨ NEW: ดึงข้อมูลย้อนหลัง lookback_hours ชั่วโมง เพื่อให้ cumulative PNL ถูกต้อง
    """
    conn = psycopg2.connect(**DB_CONFIG)
    
    # คำนวน lookback_start_date (ย้อนหลัง 3 ชั่วโมง)
    start_dt = pd.to_datetime(start_date)
    lookback_start = (start_dt - timedelta(hours=lookback_hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    query = f"""
    SELECT strategy, action, entry_time, result_10min,
           CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END as pnl_value
    FROM tradingviewdata
    WHERE entry_time >= '{lookback_start}' AND entry_time < '{end_date}'
      AND action IN ('Buy', 'Sell')
      AND result_10min IS NOT NULL
    ORDER BY entry_time;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"📊 Data fetched: {lookback_start} to {end_date}")
    print(f"   Total records: {len(df)}")
    
    return df

def calculate_hourly_pnl(df, full_strategies):
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    df['hour'] = df['entry_time'].dt.floor('H')
    hourly_pnl = {}
    for strategy in full_strategies:
        df_strat = df[df['strategy_action'] == strategy].copy()
        if len(df_strat) > 0:
            df_strat['cumulative_pnl'] = df_strat['pnl_value'].cumsum()
            for hour, group in df_strat.groupby('hour'):
                if hour not in hourly_pnl: hourly_pnl[hour] = {}
                hourly_pnl[hour][strategy] = group['cumulative_pnl'].iloc[-1]
    all_hours = sorted(hourly_pnl.keys())
    for strategy in full_strategies:
        prev_pnl = 0
        for hour in all_hours:
            if strategy not in hourly_pnl[hour]: hourly_pnl[hour][strategy] = prev_pnl
            else: prev_pnl = hourly_pnl[hour][strategy]
    return hourly_pnl, all_hours

def calculate_momentum_score(pnls):
    """Option D: Acceleration"""
    p1, p2, p3, p4, p5, p6 = pnls
    m1 = p1 - p2
    m2 = p2 - p3
    acceleration = m1 - m2
    return (5 * max(m1, 0) + 3 * max(acceleration, 0))

def run_simulation(start_date, end_date, log_level='info', lookback_hours=3):
    full_strategies = fetch_all_strategies(start_date, end_date)
    
    if log_level in ['info', 'debug']:
        print(f"📊 Found {len(full_strategies)} combinations (Buy/Sell only)\n")
    
    # ✨ ดึงข้อมูลย้อนหลัง 3 ชั่วโมง
    df = fetch_trading_data(start_date, end_date, lookback_hours)
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    df['hour'] = df['entry_time'].dt.floor('H')
    hourly_pnl, all_hours = calculate_hourly_pnl(df, full_strategies)
    
    # ✨ Filter all_hours ให้เอาเฉพาะช่วง simulation period
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    simulation_hours = [h for h in all_hours if start_dt <= h <= end_dt]
    
    print(f"📅 Simulation hours: {len(simulation_hours)} hours (from {simulation_hours[0]} to {simulation_hours[-1]})\n")
    
    current_strategies = []  # เปลี่ยนจาก current_strategy เป็น list
    total_pnl = 0
    trades = []
    strategy_changes = []
    
    for sim_hour_idx, hour in enumerate(simulation_hours):
        # ✨ หา index ของ hour ใน all_hours (เพื่อ lookback ได้ถูกต้อง)
        hour_idx = all_hours.index(hour)
        
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
            
            # Calculate TRADE and WIN counts for debug mode
            hour_data = df[(df['strategy_action'] == strategy) & (df['hour'] == hour)]
            trade_count = len(hour_data)
            win_count = len(hour_data[hour_data['result_10min'] == 'WIN'])
            
            scores[strategy] = {'pnl': pnls[0], 'recent_raw': recent_raw, 'score': 0, 'trades': trade_count, 'wins': win_count}
        
        recent_kpi = np.mean(recent_raws) + np.std(recent_raws) if np.std(recent_raws) > 0 else 1
        
        for strategy in scores:
            raw = scores[strategy]['recent_raw']
            score = min((raw / recent_kpi) * 30, 30) if recent_kpi > 0 else 0
            scores[strategy]['score'] = score
        
        sorted_strategies = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        top6_strategies = [s[0] for s in sorted_strategies[:TOP_N]]
        
        # ✨ NEW: Filter เฉพาะ Score >= 25 และเลือกสูงสุด 3 ตัว
        selected_strategies = [s for s in top6_strategies if scores[s]['score'] >= MIN_SCORE][:MAX_SELECT]
        
        # Log output based on level
        if log_level == 'debug':
            print(f"\n{'='*120}")
            print(f"⏰ {hour_str}         Cumulative PNL = ${total_pnl:.0f}")
            print(f"{'='*120}")
            print(f"🏆 TOP 6 Strategies (Score >= {MIN_SCORE} → Selected TOP {len(selected_strategies)}):")
            print(f"{'Strategy':<30} {'TRADE':>6} {'WIN':>5} {'PNL':>8} {'Score':>7} {'สถานะ':<8}")
            print(f"{'-'*120}")
            
            for idx, strategy in enumerate(top6_strategies, 1):
                trade_count = scores[strategy]['trades']
                win_count = scores[strategy]['wins']
                pnl = scores[strategy]['pnl']
                score = scores[strategy]['score']
                is_selected = strategy in selected_strategies
                
                if is_selected:
                    status = f"✅ #{idx}"
                elif score < MIN_SCORE:
                    status = f"❌ <{MIN_SCORE}"
                else:
                    status = f"#{idx}"
                
                print(f"{strategy:<30} {trade_count:>6} {win_count:>5} ${pnl:>7.0f} {score:>6.1f} {status:<8}")
            
            print(f"{'-'*120}")
        elif log_level == 'info' and sim_hour_idx % 24 == 0:
            selected_names = [s.split('|')[0].strip() for s in selected_strategies]
            print(f"⏰ {hour_str} PNL=${total_pnl:.0f} SELECTED: {len(selected_strategies)} strategies")
        
        # Track strategy changes
        if set(current_strategies) != set(selected_strategies):
            if len(current_strategies) > 0:
                strategy_changes.append({
                    'time': hour,
                    'from': current_strategies.copy(),
                    'to': selected_strategies.copy()
                })
            current_strategies = selected_strategies.copy()
        
        # ✨ Execute trades for ALL selected strategies
        hour_pnl_change = 0
        hour_trade_count = 0
        
        for selected_strategy in selected_strategies:
            current_trades = df[(df['strategy_action'] == selected_strategy) & (df['hour'] == hour)]
            
            for _, trade in current_trades.iterrows():
                pnl_change = WIN_PROFIT if trade['result_10min'] == 'WIN' else LOSE_LOSS
                total_pnl += pnl_change
                hour_pnl_change += pnl_change
                hour_trade_count += 1
                trades.append({
                    'time': trade['entry_time'],
                    'strategy': selected_strategy,
                    'result': trade['result_10min'],
                    'pnl': pnl_change,
                    'total_pnl': total_pnl
                })
                
                # Log each trade in debug mode
                if log_level == 'debug':
                    trade_time = pd.to_datetime(trade['entry_time']).strftime('%H:%M')
                    result_icon = "✅" if trade['result_10min'] == 'WIN' else "❌"
                    print(f"  └─ {trade_time}  {selected_strategy:<30} {result_icon} {trade['result_10min']:<4}  {pnl_change:+.0f}  (Running: ${total_pnl:.0f})")
        
        # Show hour summary in debug mode
        if log_level == 'debug' and hour_trade_count > 0:
            print(f"\n💰 Hour Change: {hour_pnl_change:+.0f} | Total Trades: {hour_trade_count} | Selected: {len(selected_strategies)}")
    
    if log_level in ['info', 'debug']:
        print(f"\n{'='*120}")
        print(f"💰 FINAL: ${total_pnl:.0f} | Trades: {len(trades)} | Strategy Changes: {len(strategy_changes)}")
        print(f"{'='*120}")
    
    return {'total_pnl': total_pnl, 'trades': trades, 'strategy_changes': strategy_changes, 'all_strategies': full_strategies}

if __name__ == "__main__":
    LOG_LEVEL = 'info'  # 'info' or 'debug'
    LOOKBACK_HOURS = 3
    
    print("="*120)
    print("🚀 Test 031: Acceleration + 3-Hour Lookback + TOP 3 (Score >= 25)")
    print("📅 Simulation Period: 01-30 Sep 2025 (30 วัน)")
    print(f"📊 Data Lookback: {LOOKBACK_HOURS} hours")
    print(f"📊 Log Level: {LOG_LEVEL.upper()}")
    print("🎯 Actions: Buy/Sell ONLY (no FlowTrend)")
    print(f"🏆 Selection: TOP {MAX_SELECT} strategies with Score >= {MIN_SCORE}")
    print("="*120)
    results = run_simulation('2025-09-01 00:00:00', '2025-09-30 23:59:59', log_level=LOG_LEVEL, lookback_hours=LOOKBACK_HOURS)
    print(f"\n✅ Test 031 Complete!")
    print(f"Formula: Acceleration (5×M₁ + 3×Acceleration)")
    print(f"Selection: TOP {MAX_SELECT} with Score >= {MIN_SCORE}")
    print(f"Final PNL: ${results['total_pnl']:.0f}")


