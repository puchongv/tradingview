#!/usr/bin/env python3
"""
Check existing materialized views in database
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
print("🔍 Checking Existing Materialized Views")
print("=" * 80)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# List all materialized views
print("\n📋 All Materialized Views:")
print("-" * 80)
cursor.execute("""
    SELECT 
        schemaname,
        matviewname,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
    FROM pg_matviews
    WHERE schemaname = 'public'
    ORDER BY matviewname;
""")

views = cursor.fetchall()
for view in views:
    print(f"  - {view[1]:<40} ({view[2]})")

# Check if mv_strategy_metrics_hourly exists
print("\n🔍 Checking mv_strategy_metrics_hourly...")
cursor.execute("""
    SELECT EXISTS (
        SELECT 1 FROM pg_matviews 
        WHERE matviewname = 'mv_strategy_metrics_hourly'
    );
""")
exists = cursor.fetchone()[0]

if exists:
    print("✅ View exists!")
    
    # Get column info
    print("\n📊 Column Structure:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            column_name, 
            data_type
        FROM information_schema.columns
        WHERE table_name = 'mv_strategy_metrics_hourly'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[0]:<30} {col[1]}")
    
    # Sample data
    print("\n📈 Sample Data (TOP 5):")
    print("-" * 80)
    cursor.execute("""
        SELECT * FROM mv_strategy_metrics_hourly 
        ORDER BY hour DESC 
        LIMIT 5;
    """)
    
    rows = cursor.fetchall()
    if rows:
        # Print column names
        colnames = [desc[0] for desc in cursor.description]
        print("  " + " | ".join(f"{col:<15}" for col in colnames))
        print("  " + "-" * (len(colnames) * 17))
        
        # Print data
        for row in rows:
            print("  " + " | ".join(f"{str(val):<15}" for val in row))
else:
    print("❌ View does NOT exist")

cursor.close()
conn.close()

print("\n" + "=" * 80)

