#!/usr/bin/env python3
"""
Test V1.9 scoring directly on database with hardcoded default parameters
"""

import psycopg2
from decimal import Decimal

# Database connection
conn = psycopg2.connect(
    host="45.77.46.180",
    port=5432,
    database="TradingView",
    user="postgres",
    password="pwd@root99"
)

cur = conn.cursor()

# Read and execute the SQL file
with open('agent-script/test_v19_with_defaults.sql', 'r') as f:
    sql = f.read()

print("🔍 Testing V1.9 with default parameters...")
print("="*100)

try:
    cur.execute(sql)
    results = cur.fetchall()
    
    # Get column names
    colnames = [desc[0] for desc in cur.description]
    
    print(f"\n✅ Query executed successfully!")
    print(f"📊 Found {len(results)} strategies\n")
    print("="*100)
    
    for idx, row in enumerate(results, 1):
        print(f"\n🎯 Strategy #{idx}: {row[colnames.index('strategy')]} - {row[colnames.index('action')]}")
        print("-"*100)
        
        # Input data
        print("\n📥 Input Data:")
        print(f"   72h_pnl:     {row[colnames.index('72h_pnl')]}")
        print(f"   48h_pnl:     {row[colnames.index('48h_pnl')]}")
        print(f"   24h_pnl:     {row[colnames.index('24h_pnl')]}")
        print(f"   12h_pnl:     {row[colnames.index('12h_pnl')]}")
        print(f"   6h_pnl:      {row[colnames.index('6h_pnl')]}")
        print(f"   3h_pnl:      {row[colnames.index('3h_pnl')]}")
        print(f"   72h_winrate: {row[colnames.index('72h_winrate')]}%")
        print(f"   48h_winrate: {row[colnames.index('48h_winrate')]}%")
        print(f"   24h_winrate: {row[colnames.index('24h_winrate')]}%")
        
        # Individual PNL scores
        print("\n💰 PNL Scores (breakdown):")
        print(f"   72h: {row[colnames.index('pnl_score_72h')]}")
        print(f"   48h: {row[colnames.index('pnl_score_48h')]}")
        print(f"   24h: {row[colnames.index('pnl_score_24h')]}")
        print(f"   12h: {row[colnames.index('pnl_score_12h')]}")
        
        # Output scores
        print("\n📊 Output Scores:")
        print(f"   PNL Score (40):         {row[colnames.index('pnl_score40')]}")
        print(f"   Winrate Score (30):     {row[colnames.index('winrate_score30')]}")
        print(f"   Performance Score (30): {row[colnames.index('performance_score30')]}")
        print(f"   🏆 TOTAL SCORE:         {row[colnames.index('total_score')]}")
        
        # Manual calculation for verification
        print("\n🧮 Manual Verification (PNL Score):")
        pnl_72h = float(row[colnames.index('72h_pnl')] or 0)
        pnl_48h = float(row[colnames.index('48h_pnl')] or 0)
        pnl_24h = float(row[colnames.index('24h_pnl')] or 0)
        pnl_12h = float(row[colnames.index('12h_pnl')] or 0)
        
        score_72h = min(max((pnl_72h / (1000 * 2.5)) * 5, 0), 5)
        score_48h = min(max((pnl_48h / (1000 * 2.0)) * 10, 0), 10)
        score_24h = min(max((pnl_24h / (1000 * 1.0)) * 15, 0), 15)
        score_12h = min(max((pnl_12h / (1000 * 0.7)) * 10, 0), 10)
        total_pnl = score_72h + score_48h + score_24h + score_12h
        
        print(f"   Expected 72h: {score_72h:.2f} | Actual: {row[colnames.index('pnl_score_72h')]}")
        print(f"   Expected 48h: {score_48h:.2f} | Actual: {row[colnames.index('pnl_score_48h')]}")
        print(f"   Expected 24h: {score_24h:.2f} | Actual: {row[colnames.index('pnl_score_24h')]}")
        print(f"   Expected 12h: {score_12h:.2f} | Actual: {row[colnames.index('pnl_score_12h')]}")
        print(f"   Expected Total: {total_pnl:.2f} | Actual: {row[colnames.index('pnl_score40')]}")
        
        # Check if match
        if abs(total_pnl - float(row[colnames.index('pnl_score40')])) < 0.01:
            print("   ✅ PNL Score matches!")
        else:
            print("   ❌ PNL Score MISMATCH!")
        
        print("="*100)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    cur.close()
    conn.close()

print("\n✅ Test completed!")




