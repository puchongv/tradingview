#!/usr/bin/env python3
"""
Deploy MATERIALIZED VIEW to PostgreSQL Database
"""

import psycopg2
import sys
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

def deploy_materialized_view():
    """
    Deploy mv_strategy_metrics_hourly to database
    """
    print("=" * 100)
    print("🚀 Deploying MATERIALIZED VIEW: mv_strategy_metrics_hourly")
    print("=" * 100)
    print()
    
    try:
        # Connect to database
        print("🔌 Step 1: Connecting to database...")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Database: {DB_CONFIG['database']}")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("   ✅ Connected!")
        print()
        
        # Read SQL file
        print("📄 Step 2: Reading SQL file...")
        with open('agent-script/mv_strategy_metrics_hourly.sql', 'r') as f:
            sql = f.read()
        print("   ✅ SQL file loaded!")
        print()
        
        # Drop existing view if exists
        print("🗑️  Step 3: Dropping existing MATERIALIZED VIEW (if exists)...")
        try:
            cursor.execute("DROP MATERIALIZED VIEW IF EXISTS mv_strategy_metrics_hourly CASCADE;")
            conn.commit()
            print("   ✅ Old view dropped!")
        except Exception as e:
            print(f"   ⚠️  No existing view to drop")
        print()
        
        # Create MATERIALIZED VIEW
        print("🏗️  Step 4: Creating MATERIALIZED VIEW...")
        print("   This may take 10-30 seconds...")
        print()
        
        # Execute entire SQL (includes CREATE MATERIALIZED VIEW and CREATE INDEX)
        print("   → Executing SQL...")
        cursor.execute(sql)
        conn.commit()
        print("   ✅ MATERIALIZED VIEW and indexes created!")
        print()
        
        # Verify creation
        print("✅ Step 5: Verifying MATERIALIZED VIEW...")
        cursor.execute("""
            SELECT COUNT(*) as total_rows
            FROM mv_strategy_metrics_hourly;
        """)
        result = cursor.fetchone()
        total_rows = result[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT strategy || '-' || action) as unique_strategies
            FROM mv_strategy_metrics_hourly;
        """)
        result = cursor.fetchone()
        unique_strategies = result[0]
        
        print(f"   ✅ Total rows: {total_rows}")
        print(f"   ✅ Unique strategies: {unique_strategies}")
        print()
        
        # Show sample data
        print("📊 Step 6: Sample data from MATERIALIZED VIEW:")
        print("-" * 100)
        cursor.execute("""
            SELECT strategy, action, window_hours, total_trades, 
                   winrate_10min, pnl_10min, winrate_30min, pnl_30min
            FROM mv_strategy_metrics_hourly
            ORDER BY strategy, action, window_hours
            LIMIT 5;
        """)
        
        rows = cursor.fetchall()
        print(f"{'Strategy':<15} {'Action':<10} {'Window':<8} {'Trades':<8} {'WR10min':<10} {'PNL10min':<12} {'WR30min':<10} {'PNL30min':<12}")
        print("-" * 100)
        for row in rows:
            strategy, action, window, trades, wr10, pnl10, wr30, pnl30 = row
            print(f"{strategy:<15} {action:<10} {window:>3}h     {trades:>5}    {wr10:>6.2f}%    ${pnl10:>10.2f}    {wr30:>6.2f}%    ${pnl30:>10.2f}")
        print()
        
        # Check last update time
        cursor.execute("""
            SELECT MAX(last_updated) as last_update
            FROM mv_strategy_metrics_hourly;
        """)
        result = cursor.fetchone()
        last_update = result[0]
        print(f"⏰ Last updated: {last_update}")
        print()
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("=" * 100)
        print("✅ DEPLOYMENT SUCCESSFUL!")
        print("=" * 100)
        print()
        
        print("📋 Next Steps:")
        print("-" * 100)
        print("1. ✅ MATERIALIZED VIEW is ready to use")
        print("2. 🔄 Setup auto-refresh (optional but recommended)")
        print("3. 📊 Test V1.8 Custom SQL in Metabase")
        print()
        
        print("🔄 To setup auto-refresh:")
        print("-" * 100)
        print("Option 1: Cron Job")
        print("  crontab -e")
        print("  Add: 0 * * * * psql -h 45.77.46.180 -U postgres -d TradingView \\")
        print("       -c 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;'")
        print()
        print("Option 2: pg_cron Extension")
        print("  SELECT cron.schedule(")
        print("    'refresh-metrics', '0 * * * *',")
        print("    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;$$")
        print("  );")
        print()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        print()
        return False
        
    except FileNotFoundError:
        print("❌ Error: SQL file not found!")
        print("   Expected: agent-script/mv_strategy_metrics_hourly.sql")
        print()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = deploy_materialized_view()
    sys.exit(0 if success else 1)
