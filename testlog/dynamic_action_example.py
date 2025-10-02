#!/usr/bin/env python3
"""
Example: Dynamic Action Detection
แก้ไขให้ scan ทุก action อัตโนมัติ ไม่ hard-code
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

def fetch_all_strategy_actions_dynamic(start_date, end_date, verbose=True):
    """
    ✅ แก้ไขแล้ว: Fetch ทุก strategy-action combinations โดยอัตโนมัติ
    ไม่ hard-code action ใดๆ
    """
    conn = psycopg2.connect(**DB_CONFIG)
    
    # ไม่มี AND action IN ('Buy', 'Sell') แล้ว!
    query = f"""
    SELECT DISTINCT 
        strategy,
        action,
        strategy || ' | ' || action as full_name
    FROM tradingviewdata
    WHERE entry_time >= '{start_date}' 
      AND entry_time < '{end_date}'
      AND result_10min IS NOT NULL
    ORDER BY strategy, action;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # สรุปข้อมูล
    unique_strategies = df['strategy'].unique()
    unique_actions = df['action'].unique()
    full_strategies = df['full_name'].tolist()
    
    if verbose:
        print("=" * 80)
        print("📊 Dynamic Strategy-Action Detection")
        print("=" * 80)
        print(f"\n✅ Found {len(unique_strategies)} unique strategies:")
        for s in unique_strategies:
            print(f"   - {s}")
        
        print(f"\n✅ Found {len(unique_actions)} unique actions:")
        for a in unique_actions:
            count = len(df[df['action'] == a])
            print(f"   - {a:<30} ({count} combinations)")
        
        print(f"\n✅ Total combinations: {len(full_strategies)}")
        print("\n📋 All Strategy-Action Combinations:")
        for idx, full in enumerate(full_strategies[:20], 1):
            print(f"   {idx:2}. {full}")
        if len(full_strategies) > 20:
            print(f"   ... and {len(full_strategies) - 20} more")
        print("=" * 80)
    
    return full_strategies, unique_strategies, unique_actions

# ทดสอบ
if __name__ == "__main__":
    START_DATE = '2025-09-29 00:00:00'
    END_DATE = '2025-10-01 00:00:00'
    
    full_strategies, strategies, actions = fetch_all_strategy_actions_dynamic(
        START_DATE, END_DATE, verbose=True
    )
    
    print(f"\n🎯 Summary:")
    print(f"   Old method (hard-code):  22 combinations (Buy + Sell only)")
    print(f"   New method (dynamic):    {len(full_strategies)} combinations")
    print(f"   Improvement:             +{len(full_strategies) - 22} combinations (+{((len(full_strategies) - 22) / 22 * 100):.0f}%)")

