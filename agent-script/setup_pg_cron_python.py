#!/usr/bin/env python3
"""
============================================================================
pg_cron Setup Script (Python)
============================================================================
Purpose: Install and configure pg_cron for MATERIALIZED VIEW auto-refresh
Database: TradingView on 45.77.46.180
============================================================================
"""

import psycopg2
from psycopg2 import sql
import sys

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

def print_header(text):
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)

def execute_sql(cursor, sql_text, description):
    try:
        cursor.execute(sql_text)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

def main():
    print_header("🚀 VPS MATERIALIZED VIEW Auto-Refresh Setup")
    
    try:
        # Connect to database
        print("\n📡 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        # 1. Install pg_cron extension
        print_header("1️⃣ Installing pg_cron extension")
        execute_sql(cursor, 
                   "CREATE EXTENSION IF NOT EXISTS pg_cron;",
                   "pg_cron extension installed")
        
        # Verify installation
        cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_cron';")
        result = cursor.fetchone()
        if result:
            print(f"   Extension: {result[0]}, Version: {result[1]}")
        else:
            print("⚠️  pg_cron extension not found. May need manual installation.")
            print("   Try: sudo apt-get install postgresql-XX-cron")
            sys.exit(1)
        
        # 2. Create unique index
        print_header("2️⃣ Creating unique index for CONCURRENTLY refresh")
        execute_sql(cursor,
                   """CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique 
                      ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);""",
                   "Unique index created")
        
        # Verify index
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE tablename = 'mv_strategy_metrics_hourly'
              AND indexname = 'idx_mv_strategy_metrics_unique';
        """)
        result = cursor.fetchone()
        if result:
            print(f"   Index: {result[0]} on {result[1]}")
        
        # 3. Remove old cron job
        print_header("3️⃣ Removing old cron job (if exists)")
        cursor.execute("SELECT COUNT(*) FROM cron.job WHERE jobname = 'refresh-strategy-metrics-hourly';")
        job_count = cursor.fetchone()[0]
        
        if job_count > 0:
            cursor.execute("SELECT cron.unschedule('refresh-strategy-metrics-hourly');")
            print("✅ Old job removed")
        else:
            print("ℹ️  No old job found")
        
        # 4. Schedule new job
        print_header("4️⃣ Scheduling auto-refresh job (every 1 hour)")
        cursor.execute("""
            SELECT cron.schedule(
                'refresh-strategy-metrics-hourly',
                '0 * * * *',
                $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
            );
        """)
        print("✅ Cron job scheduled successfully")
        
        # Show created job
        cursor.execute("""
            SELECT jobid, schedule, command, database, username, active
            FROM cron.job
            WHERE jobname = 'refresh-strategy-metrics-hourly';
        """)
        job = cursor.fetchone()
        if job:
            print(f"\n   Job ID: {job[0]}")
            print(f"   Schedule: {job[1]}")
            print(f"   Command: {job[2][:50]}...")
            print(f"   Database: {job[3]}")
            print(f"   User: {job[4]}")
            print(f"   Active: {job[5]}")
        
        # 5. Manual refresh
        print_header("5️⃣ Performing initial manual refresh")
        print("⏳ Refreshing... (this may take a moment)")
        
        execute_sql(cursor,
                   "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;",
                   "MATERIALIZED VIEW refreshed")
        
        # 6. Check status
        print_header("6️⃣ Checking MATERIALIZED VIEW status")
        
        cursor.execute("""
            SELECT 
                matviewname,
                last_refresh,
                NOW() - last_refresh AS time_since_refresh,
                pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS size
            FROM pg_matviews
            WHERE matviewname = 'mv_strategy_metrics_hourly';
        """)
        status = cursor.fetchone()
        if status:
            print(f"\n   View: {status[0]}")
            print(f"   Last Refresh: {status[1]}")
            print(f"   Time Since: {status[2]}")
            print(f"   Size: {status[3]}")
        
        cursor.execute("SELECT COUNT(*) FROM mv_strategy_metrics_hourly;")
        row_count = cursor.fetchone()[0]
        print(f"   Total Rows: {row_count:,}")
        
        # Success!
        print_header("✅ Setup Complete!")
        print("\n📊 Summary:")
        print("   • pg_cron extension installed")
        print("   • Unique index created")
        print("   • Auto-refresh scheduled (every 1 hour)")
        print("   • Initial refresh completed")
        print("\n🔍 Monitor with:")
        print("   SELECT * FROM cron.job;")
        print("   SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;")
        print("\n" + "=" * 80 + "\n")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
