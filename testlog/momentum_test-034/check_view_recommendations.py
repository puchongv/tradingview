#!/usr/bin/env python3
"""
Test 034: ตรวจสอบว่า VIEW แนะนำอะไรในแต่ละชั่วโมงที่คุณเทรดจริง
เปรียบเทียบกับ Real Trades และ Simulation
"""
import psycopg2
import pandas as pd
from datetime import datetime

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

# ดึง Real Trades
def get_real_trades():
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
    SELECT 
        strategy,
        action,
        entry_time,
        result_10min
    FROM tradingviewdata
    WHERE session IN (SELECT session_id FROM workflow_sessions)
    AND entry_time >= '2025-10-02 08:30:00' 
    AND entry_time <= '2025-10-02 11:10:00'
    AND action IN ('Buy', 'Sell')
    ORDER BY entry_time ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# คำนวน VIEW recommendations (ใช้ logic เดียวกับ VIEW)
def calculate_view_recommendations_at_time(target_time):
    """
    คำนวน TOP 3 ที่ VIEW ควรแนะนำ ณ เวลานั้น
    (ใช้ logic จาก strategy_acceleration_score_FIXED.sql)
    """
    conn = psycopg2.connect(**DB_CONFIG)
    
    # ดึงข้อมูล 6 ชั่วโมงย้อนหลัง (ตาม VIEW)
    query = f"""
    WITH raw_trades AS (
        SELECT 
            strategy || ' | ' || action as strategy_action,
            DATE_TRUNC('hour', entry_time) as hour,
            CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END as pnl_change
        FROM tradingviewdata
        WHERE entry_time >= '{target_time}'::timestamp - INTERVAL '6 hours'
          AND entry_time < '{target_time}'::timestamp
          AND action IN ('Buy', 'Sell')
          AND result_10min IS NOT NULL
    ),
    hourly_changes AS (
        SELECT 
            strategy_action,
            hour,
            SUM(pnl_change) as hourly_change
        FROM raw_trades
        GROUP BY strategy_action, hour
    ),
    cumulative AS (
        SELECT 
            strategy_action,
            hour,
            SUM(hourly_change) OVER (
                PARTITION BY strategy_action 
                ORDER BY hour
            ) as cumulative_pnl
        FROM hourly_changes
    ),
    latest_pnls AS (
        SELECT DISTINCT ON (strategy_action)
            strategy_action,
            cumulative_pnl as p1
        FROM cumulative
        ORDER BY strategy_action, hour DESC
    ),
    with_lags AS (
        SELECT 
            c.strategy_action,
            MAX(CASE WHEN c.hour = (SELECT MAX(hour) FROM cumulative) THEN c.cumulative_pnl ELSE 0 END) as p1,
            MAX(CASE WHEN c.hour = (SELECT MAX(hour) FROM cumulative) - INTERVAL '1 hour' THEN c.cumulative_pnl ELSE 0 END) as p2,
            MAX(CASE WHEN c.hour = (SELECT MAX(hour) FROM cumulative) - INTERVAL '2 hours' THEN c.cumulative_pnl ELSE 0 END) as p3
        FROM cumulative c
        GROUP BY c.strategy_action
    ),
    scores AS (
        SELECT 
            strategy_action,
            p1,
            p1 - p2 as m1,
            p2 - p3 as m2,
            (p1 - p2) - (p2 - p3) as accel,
            (5 * GREATEST(p1 - p2, 0) + 3 * GREATEST((p1 - p2) - (p2 - p3), 0)) as raw_score
        FROM with_lags
    ),
    normalized AS (
        SELECT 
            strategy_action,
            p1,
            raw_score,
            CASE 
                WHEN (AVG(raw_score) OVER () + STDDEV(raw_score) OVER ()) > 0
                THEN LEAST((raw_score / NULLIF((AVG(raw_score) OVER () + STDDEV(raw_score) OVER ()), 0)) * 30, 30)
                ELSE 0
            END as score
        FROM scores
    )
    SELECT 
        strategy_action,
        score,
        p1 as pnl
    FROM normalized
    WHERE score >= 25
    ORDER BY score DESC, p1 DESC
    LIMIT 3;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

print("="*120)
print("🔍 Test 034: วิเคราะห์ว่า VIEW แนะนำอะไร vs Real Trades vs Simulation")
print("="*120)

# ดึง Real Trades
real_trades = get_real_trades()
print(f"\n📊 Real Trades: {len(real_trades)} trades")
print(real_trades.to_string(index=False))

# คำนวน Real PNL
win_count = len(real_trades[real_trades['result_10min'] == 'WIN'])
lose_count = len(real_trades[real_trades['result_10min'] == 'LOSE'])
real_pnl = (win_count * 200) - (lose_count * 250)
print(f"\n💔 Real Result: WIN={win_count}, LOSE={lose_count}, PNL={real_pnl:+.0f}")

# เช็ค VIEW recommendations ณ แต่ละชั่วโมง
test_times = [
    '2025-10-02 09:00:00',
    '2025-10-02 10:00:00', 
    '2025-10-02 11:00:00'
]

print("\n" + "="*120)
print("🏆 VIEW Recommendations ณ แต่ละชั่วโมง:")
print("="*120)

for time_str in test_times:
    print(f"\n⏰ {time_str}")
    print("-" * 120)
    recs = calculate_view_recommendations_at_time(time_str)
    if len(recs) > 0:
        print(recs.to_string(index=False))
    else:
        print("❌ ไม่มี strategies ที่ Score >= 25")

print("\n" + "="*120)
print("📝 สรุป:")
print("="*120)
print(f"Real Trades: {len(real_trades)} trades, PNL: ${real_pnl:+.0f}")
print("Simulation (Test 033): 7 trades, PNL: $+1,400")
print("\n→ ต้องเทียบว่า VIEW แนะนำตรงกับ Real Trades ที่คุณเทรดหรือไม่")
print("→ และเทียบกับ Simulation ที่ชนะ $1,400")

