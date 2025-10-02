#!/usr/bin/env python3
"""
Deploy Simple Strategy Score View to Database
"""
import psycopg2

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

print("=" * 80)
print("🚀 Deploying Simple Strategy Score View (UTC+7)")
print("=" * 80)

# Read SQL file
print("\n📄 Reading SQL file...")
with open('database/strategy_score_simple_view.sql', 'r') as f:
    sql = f.read()

# Connect to database
print("🔌 Connecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Connected successfully")
    
    # Execute SQL
    print("\n⚙️  Creating materialized view...")
    cursor.execute(sql)
    conn.commit()
    print("✅ View created successfully")
    
    # Check view
    print("\n🔍 Verifying view...")
    cursor.execute("SELECT COUNT(*) FROM strategy_score_simple;")
    count = cursor.fetchone()[0]
    print(f"✅ View verified: {count} records")
    
    # Get TOP 5
    print("\n🏆 TOP 5 Strategies:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            strategy, 
            action, 
            pnl_1h, 
            pnl_2h, 
            pnl_3h, 
            score,
            last_update
        FROM strategy_score_simple
        LIMIT 5;
    """)
    
    rows = cursor.fetchall()
    print(f"{'Rank':<5} {'Strategy':<20} {'Action':<6} {'PNL-1H':>8} {'PNL-2H':>8} {'PNL-3H':>8} {'Score':>7} {'Updated':<20}")
    print("-" * 80)
    for idx, row in enumerate(rows, 1):
        print(f"{idx:<5} {row[0]:<20} {row[1]:<6} {row[2]:>8.0f} {row[3]:>8.0f} {row[4]:>8.0f} {row[5]:>7.2f} {row[6]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ Deployment Complete!")
    print("=" * 80)
    print("\n💡 Query: SELECT * FROM strategy_score_simple LIMIT 10;")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

