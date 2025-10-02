-- ============================================================================
-- Direct pg_cron Setup for VPS
-- ============================================================================
-- Purpose: Setup auto-refresh for mv_strategy_metrics_hourly
-- Database: TradingView on 45.77.46.180
-- ============================================================================

-- 1. Install pg_cron extension
\echo '============================================================================'
\echo '1️⃣ Installing pg_cron extension'
\echo '============================================================================'
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Verify installation
SELECT 
    extname, 
    extversion,
    'Extension installed successfully' AS status
FROM pg_extension 
WHERE extname = 'pg_cron';

\echo ''
\echo '============================================================================'
\echo '2️⃣ Creating unique index for CONCURRENTLY refresh'
\echo '============================================================================'

-- Create unique index if not exists
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique 
ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);

-- Verify index
SELECT 
    indexname, 
    tablename,
    'Index created successfully' AS status
FROM pg_indexes 
WHERE tablename = 'mv_strategy_metrics_hourly'
  AND indexname = 'idx_mv_strategy_metrics_unique';

\echo ''
\echo '============================================================================'
\echo '3️⃣ Removing old cron job (if exists)'
\echo '============================================================================'

-- Remove old job if exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'refresh-strategy-metrics-hourly') THEN
        PERFORM cron.unschedule('refresh-strategy-metrics-hourly');
        RAISE NOTICE 'Old job removed';
    ELSE
        RAISE NOTICE 'No old job found';
    END IF;
END $$;

\echo ''
\echo '============================================================================'
\echo '4️⃣ Scheduling auto-refresh job (every 1 hour)'
\echo '============================================================================'

-- Schedule new job
SELECT cron.schedule(
    'refresh-strategy-metrics-hourly',     -- job name
    '0 * * * *',                           -- every hour at minute 0
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
    active,
    'Job scheduled successfully' AS status
FROM cron.job
WHERE jobname = 'refresh-strategy-metrics-hourly';

\echo ''
\echo '============================================================================'
\echo '5️⃣ Performing initial manual refresh'
\echo '============================================================================'

-- Manual refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;

\echo ''
\echo '============================================================================'
\echo '6️⃣ Checking MATERIALIZED VIEW status'
\echo '============================================================================'

-- Show status
SELECT 
    matviewname,
    last_refresh,
    NOW() - last_refresh AS time_since_refresh,
    pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS size,
    'Refresh completed successfully' AS status
FROM pg_matviews
WHERE matviewname = 'mv_strategy_metrics_hourly';

-- Show row count
SELECT 
    COUNT(*) AS total_rows,
    'Total strategies in view' AS description
FROM mv_strategy_metrics_hourly;

\echo ''
\echo '============================================================================'
\echo '✅ Setup Complete!'
\echo '============================================================================'
\echo ''
\echo '📊 Next Steps:'
\echo '   1. Monitor cron jobs:'
\echo '      SELECT * FROM cron.job;'
\echo ''
\echo '   2. Check recent job runs:'
\echo '      SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;'
\echo ''
\echo '   3. View MATERIALIZED VIEW status:'
\echo '      SELECT matviewname, last_refresh FROM pg_matviews WHERE matviewname = ''mv_strategy_metrics_hourly'';'
\echo ''
\echo '============================================================================'
