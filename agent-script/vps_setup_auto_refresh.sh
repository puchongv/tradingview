#!/bin/bash
# ============================================================================
# VPS Auto-Refresh Setup Script
# ============================================================================
# Purpose: Complete setup for MATERIALIZED VIEW auto-refresh on VPS
# VPS: 45.77.46.180
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "🚀 VPS MATERIALIZED VIEW Auto-Refresh Setup"
echo "============================================================================"
echo ""

VPS_HOST="45.77.46.180"
VPS_USER="root"
DB_HOST="45.77.46.180"
DB_PORT="5432"
DB_NAME="TradingView"
DB_USER="postgres"
DB_PASS="pwd@root99"

echo "📡 Connecting to VPS: $VPS_HOST"
echo ""

# Create setup script to run on VPS
cat > /tmp/vps_setup_commands.sh << 'EOFVPS'
#!/bin/bash
set -e

echo "============================================================================"
echo "1️⃣ Checking PostgreSQL and pg_cron"
echo "============================================================================"

# Check PostgreSQL version
psql -U postgres -d TradingView -c "SELECT version();" || {
    echo "❌ Cannot connect to PostgreSQL"
    exit 1
}

echo "✅ PostgreSQL connected"
echo ""

# Check if pg_cron is available
echo "🔍 Checking pg_cron extension..."
PGCRON_AVAILABLE=$(psql -U postgres -d TradingView -tAc "SELECT COUNT(*) FROM pg_available_extensions WHERE name='pg_cron';")

if [ "$PGCRON_AVAILABLE" = "0" ]; then
    echo "⚠️  pg_cron extension not available, installing..."
    
    # Install pg_cron (Ubuntu/Debian)
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y postgresql-contrib
        
        # Try to install pg_cron from repository
        PG_VERSION=$(psql -U postgres -d TradingView -tAc "SHOW server_version;" | cut -d'.' -f1)
        apt-get install -y postgresql-${PG_VERSION}-cron || {
            echo "⚠️  pg_cron package not found in repository"
            echo "📝 Manual installation may be required"
        }
    fi
else
    echo "✅ pg_cron extension available"
fi

echo ""
echo "============================================================================"
echo "2️⃣ Installing pg_cron extension in database"
echo "============================================================================"

psql -U postgres -d TradingView << 'EOFSQL'
-- Install pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Check if extension is installed
SELECT * FROM pg_extension WHERE extname = 'pg_cron';
EOFSQL

echo "✅ pg_cron extension installed"
echo ""

echo "============================================================================"
echo "3️⃣ Creating unique index for CONCURRENTLY refresh"
echo "============================================================================"

psql -U postgres -d TradingView << 'EOFSQL'
-- Create unique index if not exists
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique 
ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);

-- Verify index
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename = 'mv_strategy_metrics_hourly';
EOFSQL

echo "✅ Unique index created"
echo ""

echo "============================================================================"
echo "4️⃣ Scheduling auto-refresh job (every 1 hour)"
echo "============================================================================"

psql -U postgres -d TradingView << 'EOFSQL'
-- Remove old job if exists
SELECT cron.unschedule('refresh-strategy-metrics-hourly') 
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'refresh-strategy-metrics-hourly');

-- Schedule new job (every hour at minute 0)
SELECT cron.schedule(
    'refresh-strategy-metrics-hourly',
    '0 * * * *',
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
);

-- Show created job
SELECT 
    jobid,
    schedule,
    command,
    nodename,
    nodeport,
    database,
    username,
    active
FROM cron.job
WHERE jobname = 'refresh-strategy-metrics-hourly';
EOFSQL

echo "✅ Cron job scheduled"
echo ""

echo "============================================================================"
echo "5️⃣ Performing initial manual refresh"
echo "============================================================================"

psql -U postgres -d TradingView << 'EOFSQL'
-- Manual refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;

-- Show status
SELECT 
    matviewname,
    last_refresh,
    NOW() - last_refresh AS time_since_refresh,
    pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS size
FROM pg_matviews
WHERE matviewname = 'mv_strategy_metrics_hourly';

-- Show row count
SELECT COUNT(*) AS total_rows FROM mv_strategy_metrics_hourly;
EOFSQL

echo "✅ Initial refresh completed"
echo ""

echo "============================================================================"
echo "✅ Setup Complete!"
echo "============================================================================"
echo ""
echo "📊 Summary:"
echo "   • pg_cron extension installed"
echo "   • Unique index created"
echo "   • Auto-refresh scheduled (every 1 hour)"
echo "   • Initial refresh completed"
echo ""
echo "🔍 Monitor with:"
echo "   psql -U postgres -d TradingView -c \"SELECT * FROM cron.job;\""
echo "   psql -U postgres -d TradingView -c \"SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;\""
echo ""
EOFVPS

# Upload and execute on VPS
echo "📤 Uploading setup script to VPS..."
scp /tmp/vps_setup_commands.sh ${VPS_USER}@${VPS_HOST}:/tmp/

echo "🔧 Executing setup on VPS..."
ssh ${VPS_USER}@${VPS_HOST} "bash /tmp/vps_setup_commands.sh"

echo ""
echo "============================================================================"
echo "✅ All Done!"
echo "============================================================================"
echo ""
echo "🎯 Next Steps:"
echo "   1. Check if cron job is running:"
echo "      ssh ${VPS_USER}@${VPS_HOST} \"psql -U postgres -d TradingView -c 'SELECT * FROM cron.job;'\""
echo ""
echo "   2. Monitor job runs:"
echo "      ssh ${VPS_USER}@${VPS_HOST} \"psql -U postgres -d TradingView -c 'SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 5;'\""
echo ""
echo "   3. Check MATERIALIZED VIEW status:"
echo "      ssh ${VPS_USER}@${VPS_HOST} \"psql -U postgres -d TradingView -c 'SELECT matviewname, last_refresh FROM pg_matviews WHERE matviewname = \\\"mv_strategy_metrics_hourly\\\";'\""
echo ""
