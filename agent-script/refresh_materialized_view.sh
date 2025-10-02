#!/bin/bash
# ============================================================================
# MATERIALIZED VIEW Refresh Script (System Cron)
# ============================================================================
# Purpose: Refresh mv_strategy_metrics_hourly using system cron
# Usage: ./refresh_materialized_view.sh
# Cron: 0 * * * * /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh
# ============================================================================

# Database connection settings
PGHOST="45.77.44.36"
PGPORT="5432"
PGDATABASE="tradingpatterns"
PGUSER="postgres"
PGPASSWORD="Baanpuchong2004"

# Log file
LOG_DIR="/Users/puchong/tradingview/logs"
LOG_FILE="$LOG_DIR/mv_refresh.log"

# Create log directory if not exists
mkdir -p "$LOG_DIR"

# Export password for psql
export PGPASSWORD

# Log start
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting MATERIALIZED VIEW refresh..." >> "$LOG_FILE"

# Execute refresh
if psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;" >> "$LOG_FILE" 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ MATERIALIZED VIEW refreshed successfully!" >> "$LOG_FILE"
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ Error refreshing MATERIALIZED VIEW" >> "$LOG_FILE"
    exit 1
fi
