#!/usr/bin/env python3
"""
Verify Strategy Acceleration Score - No Duplicates Check
"""
import psycopg2

DB_CONFIG = {
    'host': '45.77.46.180',
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

def verify_no_duplicates():
    """Check for duplicate strategy-action combinations"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("🔍 Checking for Duplicate Strategy-Action Combinations")
    print("="*80 + "\n")
    
    # Check for duplicates
    cur.execute("""
        SELECT strategy, action, COUNT(*) as count 
        FROM strategy_acceleration_score 
        GROUP BY strategy, action 
        HAVING COUNT(*) > 1
        ORDER BY count DESC;
    """)
    
    duplicates = cur.fetchall()
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate combinations:\n")
        for row in duplicates:
            print(f"  {row[0]} | {row[1]} - {row[2]} occurrences")
    else:
        print("✅ No duplicates found! Each strategy-action combination appears exactly once.\n")
    
    # Show total unique strategies
    cur.execute("SELECT COUNT(DISTINCT strategy || ' | ' || action) FROM strategy_acceleration_score;")
    total = cur.fetchone()[0]
    print(f"📊 Total unique strategy-action combinations: {total}")
    
    # Show sample
    print("\n" + "-"*80)
    print("📋 Sample (First 5 records):")
    print("-"*80)
    cur.execute("""
        SELECT strategy, action, pnl_1h, pnl_2h, pnl_3h, score 
        FROM strategy_acceleration_score 
        ORDER BY score DESC, pnl_1h DESC 
        LIMIT 5;
    """)
    
    for row in cur.fetchall():
        print(f"  {row[0]:<25} {row[1]:<10} {row[2]:>7} {row[3]:>7} {row[4]:>7} {row[5]:>7.2f}")
    
    print("\n" + "="*80)
    print("✅ Verification Complete!")
    print("="*80 + "\n")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_no_duplicates()

