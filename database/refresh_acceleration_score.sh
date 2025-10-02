#!/bin/bash
# ========================================================================================================
# Refresh Strategy Acceleration Score
# Description: Refresh materialized view every hour
# ========================================================================================================

# Database configuration
DB_HOST="45.77.46.180"
DB_PORT="5432"
DB_NAME="TradingView"
DB_USER="postgres"
DB_PASS="pwd@root99"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log file
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"
LOG_FILE="$LOG_DIR/acceleration_score_refresh.log"

# Create log directory if not exists
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Start refresh
log_message "======================================"
log_message "Refreshing Strategy Acceleration Score..."

# Execute refresh
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -c "REFRESH MATERIALIZED VIEW strategy_acceleration_score;" \
    >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    log_message "✅ View refreshed successfully"
    
    # Get row count
    ROW_COUNT=$(PGPASSWORD="$DB_PASS" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM strategy_acceleration_score;")
    
    log_message "📊 Total records: $(echo $ROW_COUNT | tr -d ' ')"
else
    log_message "❌ Error refreshing view"
    exit 1
fi

log_message "======================================"

