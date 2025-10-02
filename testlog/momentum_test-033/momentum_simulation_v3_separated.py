#!/usr/bin/env python3
"""
Test: 033 - Acceleration + Separated Leaderboard + TOP 3 (Score >= 25)
Formula: 5×M₁ + 3×Acceleration (ใช้ P1-P3 เท่านั้น)
Period: 02 Oct 2025, 08:30-12:00 (3.5 ชั่วโมง)
Actions: Buy/Sell ONLY (hard-code)
Lookback: 3 hours (ใช้แค่ P1-P3 ในการคำนวนคะแนน)
Selection: TOP 3 strategies with Score >= 25

🔄 วิธีการ: Separated Leaderboard Approach
  Phase 1: Build Leaderboard (TOP 3)
  Phase 2: Match & Trade (เทียบ raw signals กับ TOP 3)
"""
import psycopg2
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

DB_CONFIG = {'host': '45.77.46.180', 'port': 5432, 'database': 'TradingView', 'user': 'postgres', 'password': 'pwd@root99'}
BET_SIZE, PAYOUT, WIN_PROFIT, LOSE_LOSS = 250, 0.8, 200, -250
TOP_N = 6  # คำนวนคะแนนทั้ง 6 อันดับ
MIN_SCORE = 25  # กรองเฉพาะที่ >= 25
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

def fetch_trading_data_for_scoring(start_date, end_date, lookback_hours=3):
    """
    ✨ Phase 1: ดึงข้อมูลสำหรับคำนวนคะแนน (ย้อนหลัง 3HR)
    """
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
    
    print(f"📊 Scoring data fetched: {lookback_start} to {end_date}")
    print(f"   Total records: {len(df)}")
    
    return df

def fetch_signals_for_hour(hour_start, hour_end):
    """
    ✨ Phase 2: ดึง raw signals ที่เกิดขึ้นจริงในชั่วโมงนี้
    (แยกจาก scoring data)
    """
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = f"""
    SELECT strategy, action, entry_time, result_10min
    FROM tradingviewdata
    WHERE entry_time >= '{hour_start}' AND entry_time < '{hour_end}'
      AND action IN ('Buy', 'Sell')
      AND result_10min IS NOT NULL
    ORDER BY entry_time;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df['strategy_action'] = df['strategy'] + ' | ' + df['action']
    return df

def calculate_hourly_pnl(df, full_strategies):
    """คำนวน cumulative PNL ของแต่ละ strategy ทุกชั่วโมง"""
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
    """
    ✨ Acceleration (ใช้ P1-P3 เท่านั้น)
    P1 = PNL ปัจจุบัน
    P2 = PNL ย้อนหลัง 1HR
    P3 = PNL ย้อนหลัง 2HR
    """
    p1, p2, p3 = pnls[0], pnls[1], pnls[2]
    m1 = p1 - p2
    m2 = p2 - p3
    acceleration = m1 - m2
    return (5 * max(m1, 0) + 3 * max(acceleration, 0))

def build_leaderboard(hourly_pnl, all_hours, hour_idx, full_strategies, log_level='info'):
    """
    ✨ PHASE 1: Build Leaderboard
    คำนวนคะแนนและเลือก TOP 3 (Score >= 25)
    """
    scores = {}
    recent_raws = []
    
    # คำนวนคะแนนของทุก strategy
    for strategy in full_strategies:
        pnls = []
        # ใช้แค่ P1-P3
        for i in range(3):
            lookback_idx = hour_idx - i
            if lookback_idx >= 0:
                pnls.append(hourly_pnl[all_hours[lookback_idx]].get(strategy, 0))
            else:
                pnls.append(0)
        
        recent_raw = calculate_momentum_score(pnls)
        recent_raws.append(recent_raw)
        scores[strategy] = {'pnl': pnls[0], 'recent_raw': recent_raw, 'score': 0}
    
    # Normalize scores
    recent_kpi = np.mean(recent_raws) + np.std(recent_raws) if np.std(recent_raws) > 0 else 1
    
    for strategy in scores:
        raw = scores[strategy]['recent_raw']
        score = min((raw / recent_kpi) * 30, 30) if recent_kpi > 0 else 0
        scores[strategy]['score'] = score
    
    # เรียงลำดับและเลือก TOP 6
    sorted_strategies = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    top6_strategies = [s[0] for s in sorted_strategies[:TOP_N]]
    
    # กรอง Score >= 25 และเลือกสูงสุด 3 ตัว
    selected_strategies = [s for s in top6_strategies if scores[s]['score'] >= MIN_SCORE][:MAX_SELECT]
    
    return selected_strategies, scores, top6_strategies

def run_simulation(start_date, end_date, log_level='info', lookback_hours=3):
    """
    ✨ Main Simulation with Separated Leaderboard Approach
    """
    full_strategies = fetch_all_strategies(start_date, end_date)
    
    if log_level in ['info', 'debug']:
        print(f"📊 Found {len(full_strategies)} combinations (Buy/Sell only)\n")
    
    # ดึงข้อมูลสำหรับคำนวนคะแนน (ย้อนหลัง 3HR)
    scoring_df = fetch_trading_data_for_scoring(start_date, end_date, lookback_hours)
    hourly_pnl, all_hours = calculate_hourly_pnl(scoring_df, full_strategies)
    
    # Filter simulation hours
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    simulation_hours = [h for h in all_hours if start_dt <= h <= end_dt]
    
    print(f"📅 Simulation hours: {len(simulation_hours)} hours\n")
    
    current_strategies = []
    total_pnl = 0
    trades = []
    strategy_changes = []
    
    for sim_hour_idx, hour in enumerate(simulation_hours):
        hour_idx = all_hours.index(hour)
        hour_str = hour.strftime('%d/%m %H:%M')
        
        # ═══════════════════════════════════════════════════════
        # PHASE 1: BUILD LEADERBOARD
        # ═══════════════════════════════════════════════════════
        selected_strategies, scores, top6_strategies = build_leaderboard(
            hourly_pnl, all_hours, hour_idx, full_strategies, log_level
        )
        
        # Log leaderboard
        if log_level == 'debug':
            print(f"\n{'='*120}")
            print(f"⏰ {hour_str}         Cumulative PNL = ${total_pnl:.0f}")
            print(f"{'='*120}")
            print(f"🏆 PHASE 1: LEADERBOARD (Score >= {MIN_SCORE} → Selected TOP {len(selected_strategies)}):")
            print(f"{'Strategy':<30} {'PNL':>8} {'Score':>7} {'สถานะ':<12}")
            print(f"{'-'*120}")
            
            for idx, strategy in enumerate(top6_strategies, 1):
                pnl = scores[strategy]['pnl']
                score = scores[strategy]['score']
                is_selected = strategy in selected_strategies
                
                if is_selected:
                    status = f"✅ TOP {selected_strategies.index(strategy)+1}"
                elif score < MIN_SCORE:
                    status = f"❌ <{MIN_SCORE}"
                else:
                    status = f"#{idx}"
                
                print(f"{strategy:<30} ${pnl:>7.0f} {score:>6.1f} {status:<12}")
            
            print(f"{'-'*120}")
        
        elif log_level == 'info' and sim_hour_idx % 24 == 0:
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
        
        # ═══════════════════════════════════════════════════════
        # PHASE 2: MATCH & TRADE
        # ═══════════════════════════════════════════════════════
        hour_end = hour + timedelta(hours=1)
        signals_df = fetch_signals_for_hour(hour.strftime('%Y-%m-%d %H:%M:%S'), 
                                           hour_end.strftime('%Y-%m-%d %H:%M:%S'))
        
        if log_level == 'debug':
            print(f"\n💰 PHASE 2: MATCH & TRADE ({len(signals_df)} raw signals):")
        
        hour_pnl_change = 0
        hour_trade_count = 0
        matched_count = 0
        skipped_count = 0
        
        for _, signal in signals_df.iterrows():
            strategy_action = signal['strategy_action']
            
            # เทียบกับ TOP 3 leaderboard
            if strategy_action in selected_strategies:
                # ✅ Match → เทรด
                matched_count += 1
                pnl_change = WIN_PROFIT if signal['result_10min'] == 'WIN' else LOSE_LOSS
                total_pnl += pnl_change
                hour_pnl_change += pnl_change
                hour_trade_count += 1
                
                trades.append({
                    'time': signal['entry_time'],
                    'strategy': strategy_action,
                    'result': signal['result_10min'],
                    'pnl': pnl_change,
                    'total_pnl': total_pnl
                })
                
                if log_level == 'debug':
                    trade_time = pd.to_datetime(signal['entry_time']).strftime('%H:%M')
                    result_icon = "✅" if signal['result_10min'] == 'WIN' else "❌"
                    rank = selected_strategies.index(strategy_action) + 1
                    print(f"  ✅ {trade_time}  {strategy_action:<30} TOP{rank} {result_icon} {signal['result_10min']:<4}  {pnl_change:+.0f}  (Total: ${total_pnl:.0f})")
            else:
                # ❌ Not in TOP 3 → ข้าม
                skipped_count += 1
                if log_level == 'debug' and skipped_count <= 3:  # แสดงแค่ 3 ตัวแรก
                    trade_time = pd.to_datetime(signal['entry_time']).strftime('%H:%M')
                    print(f"  ⏭️  {trade_time}  {strategy_action:<30} [SKIP - Not in TOP3]")
        
        # Hour summary
        if log_level == 'debug':
            if skipped_count > 3:
                print(f"  ⏭️  ... และอีก {skipped_count - 3} signals ที่ถูกข้าม")
            print(f"\n📊 Hour Summary: Matched={matched_count}, Skipped={skipped_count}, PNL Change={hour_pnl_change:+.0f}")
    
    if log_level in ['info', 'debug']:
        print(f"\n{'='*120}")
        print(f"💰 FINAL: ${total_pnl:.0f} | Trades: {len(trades)} | Strategy Changes: {len(strategy_changes)}")
        print(f"{'='*120}")
    
    return {
        'total_pnl': total_pnl,
        'trades': trades,
        'strategy_changes': strategy_changes,
        'all_strategies': full_strategies
    }

if __name__ == "__main__":
    LOG_LEVEL = 'debug'  # 'info' or 'debug'
    LOOKBACK_HOURS = 3
    
    print("="*120)
    print("🚀 Test 033: Acceleration + Separated Leaderboard + TOP 3 (Score >= 25)")
    print("📅 Simulation Period: 02 Oct 2025, 08:30-12:00 (3.5 ชั่วโมง)")
    print(f"📊 Data Lookback: {LOOKBACK_HOURS} hours (ใช้ P1-P3 เท่านั้น)")
    print(f"📊 Log Level: {LOG_LEVEL.upper()}")
    print("🎯 Actions: Buy/Sell ONLY (no FlowTrend)")
    print(f"🏆 Selection: TOP {MAX_SELECT} strategies with Score >= {MIN_SCORE}")
    print("\n✨ Separated Leaderboard Approach")
    print("   Phase 1: Build Leaderboard (คำนวนคะแนน, เลือก TOP 3)")
    print("   Phase 2: Match & Trade (เทียบ raw signals กับ TOP 3)")
    print("="*120)
    
    results = run_simulation('2025-10-02 08:30:00', '2025-10-02 12:00:00', log_level=LOG_LEVEL, lookback_hours=LOOKBACK_HOURS)
    
    print(f"\n✅ Test 033 Complete!")
    print(f"Formula: Acceleration (5×M₁ + 3×Acceleration, P1-P3 only)")
    print(f"Selection: Separated Leaderboard → TOP {MAX_SELECT} with Score >= {MIN_SCORE}")
    print(f"Final PNL: ${results['total_pnl']:.0f}")

