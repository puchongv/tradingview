#!/bin/bash
# ============================================================================
# MATERIALIZED VIEW Refresh Script for VPS
# ============================================================================
# Purpose: Refresh mv_strategy_metrics_hourly on VPS
# VPS: 45.77.46.180
# Database: TradingView
# ============================================================================

# Database connection
PGHOST="45.77.46.180"
PGPORT="5432"
PGDATABASE="TradingView"
PGUSER="postgres"
PGPASSWORD="pwd@root99"

# Log file
LOG_DIR="/opt/tradingview/logs"
LOG_FILE="$LOG_DIR/mv_refresh.log"

# Create log directory if not exists
mkdir -p "$LOG_DIR"

# Export password
export PGPASSWORD

# Log start
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting MATERIALIZED VIEW refresh..." >> "$LOG_FILE"

# Execute refresh
if psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;" >> "$LOG_FILE" 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Success! MATERIALIZED VIEW refreshed" >> "$LOG_FILE"
    
    # Log view statistics
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -tAc "
        SELECT 
            '$(date '+%Y-%m-%d %H:%M:%S') - Stats: ' || 
            COUNT(*) || ' rows, ' || 
            pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) || ' size'
        FROM mv_strategy_metrics_hourly;
    " >> "$LOG_FILE" 2>&1
    
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ Error: Failed to refresh MATERIALIZED VIEW" >> "$LOG_FILE"
    exit 1
fi
