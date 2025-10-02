#!/usr/bin/env python3
"""
============================================================================
MATERIALIZED VIEW Refresh Script (Python + Cron)
============================================================================
Purpose: Refresh mv_strategy_metrics_hourly with error handling and logging
Usage: python3 refresh_mv.py
Cron: 0 * * * * cd /Users/puchong/tradingview && python3 agent-script/refresh_mv.py
============================================================================
"""

import psycopg2
from datetime import datetime
import logging
import sys
import os

# Setup logging
log_dir = '/Users/puchong/tradingview/logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=f'{log_dir}/mv_refresh.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database connection settings
DB_CONFIG = {
    'host': '45.77.44.36',
    'port': 5432,
    'database': 'tradingpatterns',
    'user': 'postgres',
    'password': 'Baanpuchong2004'
}

def refresh_materialized_view():
    """Refresh the MATERIALIZED VIEW with error handling"""
    conn = None
    cursor = None
    
    try:
        logging.info("=" * 80)
        logging.info("Starting MATERIALIZED VIEW refresh...")
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get start time
        start_time = datetime.now()
        
        # Execute refresh
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;")
        conn.commit()
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Get view info
        cursor.execute("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS size,
                (SELECT COUNT(*) FROM mv_strategy_metrics_hourly) AS row_count
        """)
        size, row_count = cursor.fetchone()
        
        logging.info(f"✅ MATERIALIZED VIEW refreshed successfully!")
        logging.info(f"   Duration: {duration:.2f} seconds")
        logging.info(f"   Size: {size}")
        logging.info(f"   Rows: {row_count:,}")
        
        return True
        
    except psycopg2.Error as e:
        logging.error(f"❌ Database error: {e}")
        logging.error(f"   Error code: {e.pgcode}")
        logging.error(f"   Error message: {e.pgerror}")
        return False
        
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_view_status():
    """Check the last refresh time of MATERIALIZED VIEW"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                last_refresh,
                EXTRACT(EPOCH FROM (NOW() - last_refresh)) / 3600 AS hours_since_refresh
            FROM pg_matviews
            WHERE matviewname = 'mv_strategy_metrics_hourly'
        """)
        
        result = cursor.fetchone()
        if result:
            last_refresh, hours_ago = result
            logging.info(f"Last refresh: {last_refresh} ({hours_ago:.1f} hours ago)")
        else:
            logging.warning("MATERIALIZED VIEW not found!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Error checking view status: {e}")

if __name__ == "__main__":
    # Check status before refresh
    check_view_status()
    
    # Perform refresh
    success = refresh_materialized_view()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
