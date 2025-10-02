#!/usr/bin/env python3
"""
Test: เปรียบเทียบ SQL FIXED vs Aligned ด้วยข้อมูลจริง
"""
import psycopg2
import pandas as pd

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

print("="*100)
print("🧪 ทดสอบ SQL FIXED vs Aligned")
print("="*100)

conn = psycopg2.connect(**DB_CONFIG)

# Deploy FIXED
print("\n1️⃣ Deploy SQL FIXED...")
with open('/Users/puchong/tradingview/database/strategy_acceleration_score_FIXED.sql', 'r') as f:
    sql_fixed = f.read()

cursor = conn.cursor()
cursor.execute(sql_fixed)
conn.commit()

# Get results from FIXED
cursor.execute("""
    SELECT strategy, action, pnl_1h, pnl_2h, pnl_3h, score
    FROM strategy_acceleration_score
    ORDER BY strategy, action
    LIMIT 20;
""")
fixed_results = cursor.fetchall()
print(f"✅ FIXED: {len(fixed_results)} rows")

# Deploy Aligned
print("\n2️⃣ Deploy SQL Aligned...")
with open('/Users/puchong/tradingview/database/strategy_acceleration_score_aligned.sql', 'r') as f:
    sql_aligned = f.read()

cursor.execute(sql_aligned)
conn.commit()

# Get results from Aligned
cursor.execute("""
    SELECT strategy, action, pnl_1h, pnl_2h, pnl_3h, score
    FROM strategy_acceleration_score
    ORDER BY strategy, action
    LIMIT 20;
""")
aligned_results = cursor.fetchall()
print(f"✅ Aligned: {len(aligned_results)} rows")

cursor.close()
conn.close()

# Compare
print("\n" + "="*100)
print("📊 เปรียบเทียบผลลัพธ์")
print("="*100)

df_fixed = pd.DataFrame(fixed_results, columns=['strategy', 'action', 'pnl_1h', 'pnl_2h', 'pnl_3h', 'score'])
df_aligned = pd.DataFrame(aligned_results, columns=['strategy', 'action', 'pnl_1h', 'pnl_2h', 'pnl_3h', 'score'])

print("\n🔴 SQL FIXED (TOP 10):")
print(df_fixed.head(10).to_string(index=False))

print("\n🟢 SQL Aligned (TOP 10):")
print(df_aligned.head(10).to_string(index=False))

# Check differences
print("\n" + "="*100)
print("🔍 ตรวจสอบความแตกต่าง")
print("="*100)

merged = df_fixed.merge(
    df_aligned, 
    on=['strategy', 'action'], 
    suffixes=('_fixed', '_aligned'),
    how='outer'
)

print(f"\nจำนวน rows: FIXED={len(df_fixed)}, Aligned={len(df_aligned)}")

# Check PNL differences
pnl_diff = merged[
    (merged['pnl_1h_fixed'] != merged['pnl_1h_aligned']) |
    (merged['pnl_2h_fixed'] != merged['pnl_2h_aligned']) |
    (merged['pnl_3h_fixed'] != merged['pnl_3h_aligned'])
]

if len(pnl_diff) > 0:
    print(f"\n⚠️ พบความแตกต่างของ PNL: {len(pnl_diff)} strategies")
    print("\nตัวอย่าง:")
    print(pnl_diff[['strategy', 'action', 'pnl_1h_fixed', 'pnl_1h_aligned', 'score_fixed', 'score_aligned']].head(5).to_string(index=False))
else:
    print("\n✅ PNL เหมือนกันทุก strategy!")

# Check score differences
score_diff = merged[abs(merged['score_fixed'] - merged['score_aligned']) > 0.01]

if len(score_diff) > 0:
    print(f"\n⚠️ พบความแตกต่างของ Score: {len(score_diff)} strategies")
    print("\nตัวอย่าง:")
    print(score_diff[['strategy', 'action', 'score_fixed', 'score_aligned']].head(5).to_string(index=False))
else:
    print("\n✅ Score เหมือนกันทุก strategy!")

print("\n" + "="*100)
print("🎯 สรุป")
print("="*100)

if len(pnl_diff) == 0 and len(score_diff) == 0:
    print("✅ ผลลัพธ์เหมือนกันทุกอย่าง - ใช้อันไหนก็ได้!")
else:
    print("⚠️ มีความแตกต่าง - ต้องเลือกอันที่ถูกต้องกว่า!")


