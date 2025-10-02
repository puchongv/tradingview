#!/usr/bin/env python3
"""
Deploy Strategy Acceleration Score View
"""
import psycopg2

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

print("=" * 100)
print("🚀 Deploying Strategy Acceleration Score")
print("=" * 100)

# Read SQL file
print("\n📄 Reading SQL file...")
import os
sql_path = os.path.join(os.path.dirname(__file__), 'strategy_acceleration_score_FIXED.sql')
with open(sql_path, 'r') as f:
    sql = f.read()

# Connect to database
print("🔌 Connecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Connected successfully")
    
    # Execute SQL
    print("\n⚙️  Creating materialized view: strategy_acceleration_score")
    cursor.execute(sql)
    conn.commit()
    print("✅ View created successfully")
    
    # Check view
    print("\n🔍 Verifying view...")
    cursor.execute("SELECT COUNT(*) FROM strategy_acceleration_score;")
    count = cursor.fetchone()[0]
    print(f"✅ View verified: {count} records")
    
    # Get TOP 10
    print("\n" + "=" * 100)
    print("🏆 TOP 10 Strategy Acceleration Scores")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            ROW_NUMBER() OVER () as rank,
            strategy, 
            action, 
            pnl_1h, 
            pnl_2h, 
            pnl_3h, 
            score,
            TO_CHAR(last_update, 'YYYY-MM-DD HH24:MI:SS') as updated
        FROM strategy_acceleration_score
        LIMIT 10;
    """)
    
    rows = cursor.fetchall()
    print(f"{'#':<3} {'Strategy':<20} {'Action':<6} {'PNL-1H':>8} {'PNL-2H':>8} {'PNL-3H':>8} {'Score':>7} {'Updated':<20}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<3} {row[1]:<20} {row[2]:<6} {row[3]:>8.0f} {row[4]:>8.0f} {row[5]:>8.0f} {row[6]:>7.2f} {row[7]:<20}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 100)
    print("✅ Deployment Complete!")
    print("=" * 100)
    print("\n💡 Usage:")
    print("  SELECT * FROM strategy_acceleration_score LIMIT 10;")
    print("  SELECT * FROM strategy_acceleration_score WHERE action = 'Buy' LIMIT 5;")
    print("\n🔄 Refresh:")
    print("  REFRESH MATERIALIZED VIEW strategy_acceleration_score;")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

