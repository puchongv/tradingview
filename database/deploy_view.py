#!/usr/bin/env python3
"""
Deploy Strategy Score View to Database
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
print("🚀 Deploying Strategy Score View")
print("=" * 80)

# Read SQL file
print("\n📄 Reading SQL file...")
with open('database/strategy_score_acceleration_view.sql', 'r') as f:
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
    cursor.execute("SELECT COUNT(*) FROM strategy_score_acceleration;")
    count = cursor.fetchone()[0]
    print(f"✅ View verified: {count} records")
    
    # Get latest hour
    cursor.execute("SELECT MAX(current_hour) FROM strategy_score_acceleration;")
    latest_hour = cursor.fetchone()[0]
    print(f"📅 Latest hour: {latest_hour}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ Deployment Complete!")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

