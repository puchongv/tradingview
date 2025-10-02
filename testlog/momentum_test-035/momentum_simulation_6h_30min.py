#!/usr/bin/env python3
"""
Test: 035 - 6-Hour Lookback + 30-Min Refresh (Match Real Trading Conditions)
Formula: 5×M₁ + 3×Acceleration
Period: 02 Oct 2025, 08:30-11:10 (ตรงกับการเทรดจริง)
Lookback: 6 hours (เหมือน VIEW ที่ deploy อยู่)
Refresh: ทุก 30 นาที (เหมือนที่ผู้ใช้ทำจริง)
Selection: TOP 3 strategies with Score >= 25

🎯 จุดประสงค์: พิสูจน์ว่า 6-hour lookback ทำให้แนะนำผิด
"""
import psycopg2
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

DB_CONFIG = {'host': '45.77.46.180', 'port': 5432, 'database': 'TradingView', 'user': 'postgres', 'password': 'pwd@root99'}
BET_SIZE, PAYOUT, WIN_PROFIT, LOSE_LOSS = 250, 0.8, 200, -250
TOP_N = 6
MIN_SCORE = 25
MAX_SELECT = 3
LOOKBACK_HOURS = 6  # 6 ชั่วโมง (เหมือน VIEW)

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
    
    full_strategies = []
    for s in strategies:
        full_strategies.extend([f"{s} | Buy", f"{s} | Sell"])
    
    return full_strategies

def fetch_trading_data_for_scoring(start_date, end_date, lookback_hours=6):
    """ดึงข้อมูลสำหรับคำนวนคะแนน (ย้อนหลัง 6HR)"""
    conn = psycopg2.connect(**DB_CONFIG)
    
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
    
    print(f"📊 Scoring data: {lookback_start} to {end_date} ({len(df)} records)")
    
    return df

def fetch_signals_for_period(period_start, period_end):
    """ดึง raw signals ที่เกิดขึ้นจริงในช่วงนี้"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = f"""
    SELECT strategy, action, entry_time, result_10min
    FROM tradingviewdata
    WHERE entry_time >= '{period_start}' AND entry_time < '{period_end}'
      AND action IN ('Buy', 'Sell')
      AND result_10min IS NOT NULL
    ORDER BY entry_time;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    return df

def calculate_hourly_pnl(df, full_strategies):
    """คำนวน cumulative PNL"""
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
    """Acceleration (ใช้ P1-P3 เท่านั้น แม้จะ lookback 6h)"""
    p1, p2, p3 = pnls[0], pnls[1], pnls[2]
    m1 = p1 - p2
    m2 = p2 - p3
    acceleration = m1 - m2
    return (5 * max(m1, 0) + 3 * max(acceleration, 0))

def build_leaderboard(hourly_pnl, all_hours, hour_idx, full_strategies):
    """Build Leaderboard และเลือก TOP 3 (Score >= 25)"""
    scores = {}
    recent_raws = []
    
    for strategy in full_strategies:
        pnls = []
        for i in range(3):  # ใช้แค่ P1-P3
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
    
    selected_strategies = [s for s in top6_strategies if scores[s]['score'] >= MIN_SCORE][:MAX_SELECT]
    
    return selected_strategies, scores, top6_strategies

def run_simulation(start_date, end_date):
    """
    Simulation with 6-hour lookback + 30-min refresh
    """
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    full_strategies = fetch_all_strategies(start_date, end_date)
    print(f"📊 Found {len(full_strategies)} combinations\n")
    
    # ดึงข้อมูลสำหรับคำนวนคะแนน (ย้อนหลัง 6HR)
    scoring_df = fetch_trading_data_for_scoring(start_date, end_date, LOOKBACK_HOURS)
    hourly_pnl, all_hours = calculate_hourly_pnl(scoring_df, full_strategies)
    
    # สร้าง 30-min periods
    current_time = start_dt
    periods = []
    while current_time < end_dt:
        period_end = current_time + timedelta(minutes=30)
        if period_end > end_dt:
            period_end = end_dt
        periods.append((current_time, period_end))
        current_time = period_end
    
    print(f"📅 Simulation: {len(periods)} periods (30-min each)\n")
    
    current_strategies = []
    total_pnl = 0
    trades = []
    
    print("="*120)
    print("🔄 Test 035: 6-Hour Lookback + 30-Min Refresh")
    print("="*120)
    
    for period_idx, (period_start, period_end) in enumerate(periods):
        period_str = period_start.strftime('%d/%m %H:%M')
        
        # หา hour_idx สำหรับคำนวนคะแนน
        current_hour = period_start.floor('H')
        if current_hour in all_hours:
            hour_idx = all_hours.index(current_hour)
        else:
            continue
        
        # PHASE 1: Build Leaderboard
        selected_strategies, scores, top6_strategies = build_leaderboard(
            hourly_pnl, all_hours, hour_idx, full_strategies
        )
        
        # Log
        print(f"\n{'='*120}")
        print(f"⏰ {period_str}-{period_end.strftime('%H:%M')}     Cumulative PNL = ${total_pnl:.0f}")
        print(f"{'='*120}")
        print(f"🏆 LEADERBOARD (Score >= {MIN_SCORE} → Selected {len(selected_strategies)}):")
        print(f"{'Strategy':<30} {'PNL':>8} {'Score':>7} {'สถานะ':<12}")
        print(f"{'-'*120}")
        
        for idx, strategy in enumerate(top6_strategies, 1):
            pnl = scores[strategy]['pnl']
            score = scores[strategy]['score']
            is_selected = strategy in selected_strategies
            
            if is_selected:
                rank = selected_strategies.index(strategy) + 1
                status = f"✅ TOP {rank}"
            elif score < MIN_SCORE:
                status = f"❌ <{MIN_SCORE}"
            else:
                status = f"#{idx}"
            
            print(f"{strategy:<30} ${pnl:>7.0f} {score:>6.1f} {status:<12}")
        
        print(f"{'-'*120}")
        
        # Track changes
        if set(current_strategies) != set(selected_strategies):
            current_strategies = selected_strategies.copy()
        
        # PHASE 2: Match & Trade
        signals_df = fetch_signals_for_period(
            period_start.strftime('%Y-%m-%d %H:%M:%S'),
            period_end.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        print(f"\n💰 TRADING ({len(signals_df)} signals):")
        
        period_pnl = 0
        matched = 0
        
        for _, signal in signals_df.iterrows():
            strategy_action = signal['strategy_action']
            
            if strategy_action in selected_strategies:
                matched += 1
                pnl_change = WIN_PROFIT if signal['result_10min'] == 'WIN' else LOSE_LOSS
                total_pnl += pnl_change
                period_pnl += pnl_change
                
                trades.append({
                    'time': signal['entry_time'],
                    'strategy': strategy_action,
                    'result': signal['result_10min'],
                    'pnl': pnl_change,
                    'total_pnl': total_pnl
                })
                
                trade_time = pd.to_datetime(signal['entry_time']).strftime('%H:%M')
                result_icon = "✅" if signal['result_10min'] == 'WIN' else "❌"
                rank = selected_strategies.index(strategy_action) + 1
                print(f"  ✅ {trade_time}  {strategy_action:<30} TOP{rank} {result_icon} {signal['result_10min']:<4}  {pnl_change:+.0f}  (Total: ${total_pnl:.0f})")
        
        if matched == 0:
            print(f"  ⏭️  No matched signals")
        
        print(f"\n📊 Period: Matched={matched}/{len(signals_df)}, PNL Change={period_pnl:+.0f}")
    
    print(f"\n{'='*120}")
    print(f"💰 FINAL: ${total_pnl:.0f} | Trades: {len(trades)}")
    print(f"{'='*120}")
    
    return {'total_pnl': total_pnl, 'trades': trades, 'periods': len(periods)}

if __name__ == "__main__":
    print("="*120)
    print("🚀 Test 035: 6-Hour Lookback + 30-Min Refresh (Real Trading Conditions)")
    print("📅 Period: 02 Oct 2025, 08:30-11:10")
    print(f"📊 Lookback: {LOOKBACK_HOURS} hours (เหมือน VIEW ปัจจุบัน)")
    print("🔄 Refresh: ทุก 30 นาที (เหมือนที่ผู้ใช้ทำจริง)")
    print(f"🏆 Selection: TOP {MAX_SELECT} with Score >= {MIN_SCORE}")
    print("="*120)
    
    results = run_simulation('2025-10-02 08:30:00', '2025-10-02 11:10:00')
    
    print(f"\n✅ Test 035 Complete!")
    print(f"6-Hour Lookback + 30-Min Refresh")
    print(f"Final PNL: ${results['total_pnl']:.0f}")
    print(f"\n📊 Compare:")
    print(f"  Real Trading (VIEW 6h): -$600")
    print(f"  Test 035 (6h lookback): ${results['total_pnl']:.0f}")
    print(f"  Test 033 (3h lookback): $+1,400")

