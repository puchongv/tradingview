#!/usr/bin/env python3
"""
เปรียบเทียบ SQL views กับ Python Test 022
"""
import psycopg2
import pandas as pd
import sys
sys.path.append('/Users/puchong/tradingview/testlog/momentum_test-022')

# Run Python simulation
print("="*100)
print("🐍 รัน Python Test 022...")
print("="*100)

from momentum_simulation_v2_debug import (
    fetch_all_strategies, 
    fetch_trading_data, 
    calculate_hourly_pnl,
    calculate_momentum_score
)
import numpy as np

DB_CONFIG = {'host': '45.77.46.180', 'port': 5432, 'database': 'TradingView', 'user': 'postgres', 'password': 'pwd@root99'}

# Fetch data for current hour
from datetime import datetime, timedelta
now = datetime.now()
current_hour = now.replace(minute=0, second=0, microsecond=0)
start_date = (current_hour - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
end_date = current_hour.strftime('%Y-%m-%d %H:%M:%S')

print(f"\n📅 Period: {start_date} to {end_date}")

# Get Python results
full_strategies = fetch_all_strategies(start_date, end_date)
df = fetch_trading_data(start_date, end_date)
hourly_pnl, all_hours = calculate_hourly_pnl(df, full_strategies)

print(f"📊 Strategies: {len(full_strategies)}")
print(f"📊 Hours: {len(all_hours)}")

# Calculate scores for latest hour
if len(all_hours) == 0:
    print("❌ No data available")
    exit(1)

latest_hour = all_hours[-1]
hour_idx = len(all_hours) - 1

python_results = []
for strategy in full_strategies:
    pnls = []
    for i in range(6):
        lookback_idx = hour_idx - i
        if lookback_idx >= 0:
            pnls.append(hourly_pnl[all_hours[lookback_idx]].get(strategy, 0))
        else:
            pnls.append(0)
    
    recent_raw = calculate_momentum_score(pnls)
    python_results.append({
        'strategy': strategy.split(' | ')[0],
        'action': strategy.split(' | ')[1],
        'p1': pnls[0],
        'p2': pnls[1],
        'p3': pnls[2],
        'raw': recent_raw
    })

df_python = pd.DataFrame(python_results)

# Calculate scores
recent_raws = df_python['raw'].values
recent_kpi = np.mean(recent_raws) + np.std(recent_raws)
df_python['score'] = df_python['raw'].apply(
    lambda x: min((x / recent_kpi) * 30, 30) if recent_kpi > 0 else 0
)

print(f"\n🐍 Python Results (Latest hour: {latest_hour}):")
print(df_python.sort_values('score', ascending=False).head(10).to_string(index=False))

# Get SQL FIXED results
print("\n" + "="*100)
print("🔴 SQL FIXED Results...")
print("="*100)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Deploy FIXED
with open('/Users/puchong/tradingview/database/strategy_acceleration_score_FIXED.sql', 'r') as f:
    cursor.execute(f.read())
    conn.commit()

cursor.execute("""
    SELECT strategy, action, pnl_1h, pnl_2h, pnl_3h, score
    FROM strategy_acceleration_score
    ORDER BY score DESC, pnl_1h DESC
    LIMIT 10;
""")
fixed_results = cursor.fetchall()
df_fixed = pd.DataFrame(fixed_results, columns=['strategy', 'action', 'p1', 'p2', 'p3', 'score'])
print(df_fixed.to_string(index=False))

# Get SQL Aligned results
print("\n" + "="*100)
print("🟢 SQL Aligned Results...")
print("="*100)

with open('/Users/puchong/tradingview/database/strategy_acceleration_score_aligned.sql', 'r') as f:
    cursor.execute(f.read())
    conn.commit()

cursor.execute("""
    SELECT strategy, action, pnl_1h, pnl_2h, pnl_3h, score
    FROM strategy_acceleration_score
    ORDER BY score DESC, pnl_1h DESC
    LIMIT 10;
""")
aligned_results = cursor.fetchall()
df_aligned = pd.DataFrame(aligned_results, columns=['strategy', 'action', 'p1', 'p2', 'p3', 'score'])
print(df_aligned.to_string(index=False))

cursor.close()
conn.close()

# Compare PNL values
print("\n" + "="*100)
print("🔍 เปรียบเทียบ PNL ของ strategies เดียวกัน")
print("="*100)

# Merge all 3
merged = df_python.merge(
    df_fixed, 
    on=['strategy', 'action'], 
    suffixes=('_py', '_fixed')
).merge(
    df_aligned,
    on=['strategy', 'action'],
    suffixes=('', '_aligned')
)

merged.columns = ['strategy', 'action', 'p1_py', 'p2_py', 'p3_py', 'raw_py', 'score_py', 
                  'p1_fixed', 'p2_fixed', 'p3_fixed', 'score_fixed',
                  'p1_aligned', 'p2_aligned', 'p3_aligned', 'score_aligned']

print(f"\n📊 พบ strategies ที่ตรงกัน: {len(merged)}")

# Calculate differences
merged['p1_diff_fixed'] = abs(merged['p1_py'] - merged['p1_fixed'])
merged['p1_diff_aligned'] = abs(merged['p1_py'] - merged['p1_aligned'])

print("\n🎯 สรุป:")
print(f"Average P1 diff (FIXED):   {merged['p1_diff_fixed'].mean():.2f}")
print(f"Average P1 diff (Aligned): {merged['p1_diff_aligned'].mean():.2f}")

# Show examples
print("\n📋 ตัวอย่าง 5 strategies:")
cols = ['strategy', 'action', 'p1_py', 'p1_fixed', 'p1_aligned']
print(merged[cols].head(5).to_string(index=False))

# Find which is closer
if merged['p1_diff_fixed'].mean() < merged['p1_diff_aligned'].mean():
    print("\n🏆 WINNER: SQL FIXED ใกล้เคียง Python มากกว่า!")
else:
    print("\n🏆 WINNER: SQL Aligned ใกล้เคียง Python มากกว่า!")


