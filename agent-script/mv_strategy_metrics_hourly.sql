-- ============================================================================
-- MATERIALIZED VIEW: mv_strategy_metrics_hourly
-- ============================================================================
-- Purpose: Pre-compute general trading metrics (Total Trade, Win, Winrate, PNL)
--          for different time windows to improve performance and reusability
--
-- Refresh: Every 1-3 hours (via cron job or pg_cron)
-- Usage:   Used by Metabase Custom SQL for scoring, dashboards, charts
-- ============================================================================

-- Drop if exists
DROP MATERIALIZED VIEW IF EXISTS mv_strategy_metrics_hourly CASCADE;

-- Create Materialized View
CREATE MATERIALIZED VIEW mv_strategy_metrics_hourly AS
WITH config AS (
    -- Default investment and payout values
    SELECT 
        250.0 AS default_investment,
        0.8 AS default_payout
),
time_windows AS (
    -- Define all time windows we want to calculate
    SELECT unnest(ARRAY[1, 2, 3, 4, 5, 6, 12, 24, 48, 72]) AS window_hours
),
strategy_list AS (
    -- Get all unique strategy combinations
    SELECT DISTINCT
        strategy,
        action,
        symbol
    FROM tradingviewdata
    WHERE entry_time >= NOW() - INTERVAL '72 hours'
      AND (result_10min IN ('WIN', 'LOSE') 
           OR result_30min IN ('WIN', 'LOSE')
           OR result_60min IN ('WIN', 'LOSE'))
)
SELECT
    sl.strategy,
    sl.action,
    sl.symbol,
    tw.window_hours,
    
    -- Total trades (using 10min as baseline)
    COUNT(*) FILTER (WHERE t.result_10min IN ('WIN', 'LOSE')) AS total_trades,
    
    -- 10min metrics
    COUNT(*) FILTER (WHERE t.result_10min = 'WIN') AS wins_10min,
    COUNT(*) FILTER (WHERE t.result_10min = 'LOSE') AS losses_10min,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE t.result_10min = 'WIN')::numeric
        / NULLIF(COUNT(*) FILTER (WHERE t.result_10min IN ('WIN', 'LOSE')), 0),
        2
    ) AS winrate_10min,
    (
        (COUNT(*) FILTER (WHERE t.result_10min = 'WIN')::numeric * c.default_investment * c.default_payout)
        -
        (COUNT(*) FILTER (WHERE t.result_10min = 'LOSE')::numeric * c.default_investment)
    ) AS pnl_10min,
    
    -- 30min metrics
    COUNT(*) FILTER (WHERE t.result_30min = 'WIN') AS wins_30min,
    COUNT(*) FILTER (WHERE t.result_30min = 'LOSE') AS losses_30min,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE t.result_30min = 'WIN')::numeric
        / NULLIF(COUNT(*) FILTER (WHERE t.result_30min IN ('WIN', 'LOSE')), 0),
        2
    ) AS winrate_30min,
    (
        (COUNT(*) FILTER (WHERE t.result_30min = 'WIN')::numeric * c.default_investment * c.default_payout)
        -
        (COUNT(*) FILTER (WHERE t.result_30min = 'LOSE')::numeric * c.default_investment)
    ) AS pnl_30min,
    
    -- 60min metrics
    COUNT(*) FILTER (WHERE t.result_60min = 'WIN') AS wins_60min,
    COUNT(*) FILTER (WHERE t.result_60min = 'LOSE') AS losses_60min,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE t.result_60min = 'WIN')::numeric
        / NULLIF(COUNT(*) FILTER (WHERE t.result_60min IN ('WIN', 'LOSE')), 0),
        2
    ) AS winrate_60min,
    (
        (COUNT(*) FILTER (WHERE t.result_60min = 'WIN')::numeric * c.default_investment * c.default_payout)
        -
        (COUNT(*) FILTER (WHERE t.result_60min = 'LOSE')::numeric * c.default_investment)
    ) AS pnl_60min,
    
    NOW() AS last_updated
    
FROM strategy_list sl
CROSS JOIN time_windows tw
CROSS JOIN config c
LEFT JOIN tradingviewdata t
    ON t.strategy = sl.strategy
   AND t.action = sl.action
   AND t.symbol = sl.symbol
   AND t.entry_time >= NOW() - (tw.window_hours || ' hours')::INTERVAL
   AND (t.result_10min IN ('WIN', 'LOSE') 
        OR t.result_30min IN ('WIN', 'LOSE')
        OR t.result_60min IN ('WIN', 'LOSE'))
GROUP BY
    sl.strategy,
    sl.action,
    sl.symbol,
    tw.window_hours,
    c.default_investment,
    c.default_payout
HAVING COUNT(*) FILTER (WHERE t.result_10min IN ('WIN', 'LOSE')) > 0  -- Only strategies with trades
ORDER BY strategy, action, window_hours;

-- Create indexes for fast lookup
CREATE INDEX idx_mv_metrics_strategy_action 
    ON mv_strategy_metrics_hourly(strategy, action);

CREATE INDEX idx_mv_metrics_window 
    ON mv_strategy_metrics_hourly(window_hours);

CREATE INDEX idx_mv_metrics_composite 
    ON mv_strategy_metrics_hourly(strategy, action, window_hours);

-- ============================================================================
-- REFRESH COMMANDS
-- ============================================================================

-- Manual refresh (for testing)
-- REFRESH MATERIALIZED VIEW mv_strategy_metrics_hourly;

-- Concurrent refresh (doesn't block reads)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;

-- ============================================================================
-- SETUP CRON JOB (Option 1 - Linux Cron)
-- ============================================================================
-- Run: crontab -e
-- Add this line:
-- 0 * * * * psql -U your_user -d your_database -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;"
--
-- This will refresh every hour at minute 0

-- ============================================================================
-- SETUP pg_cron (Option 2 - PostgreSQL Extension)
-- ============================================================================
-- 1. Install pg_cron extension:
--    CREATE EXTENSION IF NOT EXISTS pg_cron;
--
-- 2. Schedule the refresh:
--    SELECT cron.schedule(
--        'refresh-strategy-metrics',
--        '0 * * * *',  -- Every hour
--        $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;$$
--    );
--
-- 3. Check scheduled jobs:
--    SELECT * FROM cron.job;
--
-- 4. Unschedule (if needed):
--    SELECT cron.unschedule('refresh-strategy-metrics');

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Get PNL for different windows
-- SELECT strategy, action, window_hours, pnl
-- FROM mv_strategy_metrics_hourly
-- WHERE strategy = 'MWP10-1m'
--   AND action = 'FlowTrend Bullish + Buy+'
--   AND window_hours IN (72, 48, 24, 12)
-- ORDER BY window_hours DESC;

-- Example 2: Get Winrate for consistency check
-- SELECT strategy, action, window_hours, winrate
-- FROM mv_strategy_metrics_hourly
-- WHERE strategy = 'MWP10-1m'
--   AND action = 'FlowTrend Bullish + Buy+'
--   AND window_hours IN (72, 48, 24)
-- ORDER BY window_hours DESC;

-- Example 3: Get Recent Performance data (1-6 hours)
-- SELECT strategy, action, window_hours, pnl
-- FROM mv_strategy_metrics_hourly
-- WHERE strategy = 'MWP10-1m'
--   AND action = 'FlowTrend Bullish + Buy+'
--   AND window_hours IN (1, 2, 3, 4, 5, 6)
-- ORDER BY window_hours;

-- Example 4: Get all metrics for a strategy
-- SELECT *
-- FROM mv_strategy_metrics_hourly
-- WHERE strategy = 'MWP10-1m'
--   AND action = 'FlowTrend Bullish + Buy+'
-- ORDER BY window_hours;

-- ============================================================================
-- MONITORING & MAINTENANCE
-- ============================================================================

-- Check last update time
-- SELECT MAX(last_updated) AS last_refresh
-- FROM mv_strategy_metrics_hourly;

-- Check view size
-- SELECT pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS view_size;

-- Check number of rows
-- SELECT COUNT(*) AS total_rows FROM mv_strategy_metrics_hourly;

-- Check data distribution
-- SELECT window_hours, COUNT(*) AS strategies_count
-- FROM mv_strategy_metrics_hourly
-- GROUP BY window_hours
-- ORDER BY window_hours;
