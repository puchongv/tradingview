-- ============================================================================
-- pg_cron Setup for MATERIALIZED VIEW Auto-Refresh
-- ============================================================================
-- Purpose: Setup automatic refresh for mv_strategy_metrics_hourly
-- Refresh: Every 1 hour at minute 0
-- ============================================================================

-- 1. Check if pg_cron extension exists
SELECT * FROM pg_extension WHERE extname = 'pg_cron';

-- 2. Install pg_cron extension (if not exists)
-- Note: Requires superuser privileges
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 3. Create unique index for CONCURRENTLY refresh (if not exists)
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique 
ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);

-- 4. Schedule refresh job (every 1 hour)
SELECT cron.schedule(
    'refresh-strategy-metrics-hourly',     -- job name
    '0 * * * *',                           -- every hour at minute 0
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
);

-- 5. Verify job was created
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

-- ============================================================================
-- Useful Queries for Monitoring
-- ============================================================================

-- View all cron jobs
SELECT * FROM cron.job;

-- View recent job runs
SELECT 
    jobid,
    runid,
    job_pid,
    database,
    username,
    command,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 20;

-- Check last refresh time of MATERIALIZED VIEW
SELECT 
    schemaname,
    matviewname,
    last_refresh,
    now() - last_refresh AS time_since_refresh
FROM pg_matviews
WHERE matviewname = 'mv_strategy_metrics_hourly';

-- ============================================================================
-- Management Commands
-- ============================================================================

-- Unschedule job (if needed)
-- SELECT cron.unschedule('refresh-strategy-metrics-hourly');

-- Change schedule to every 2 hours
-- SELECT cron.unschedule('refresh-strategy-metrics-hourly');
-- SELECT cron.schedule(
--     'refresh-strategy-metrics-hourly',
--     '0 */2 * * *',  -- every 2 hours
--     $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
-- );

-- Change schedule to every 3 hours
-- SELECT cron.unschedule('refresh-strategy-metrics-hourly');
-- SELECT cron.schedule(
--     'refresh-strategy-metrics-hourly',
--     '0 */3 * * *',  -- every 3 hours
--     $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
-- );

-- Manual refresh (for testing)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;
