-- ========================================================================================================
-- Strategy Acceleration Score V2
-- Formula: 5×M₁ + 3×Acceleration (M₁=P1-P2, Acceleration=M₁-M₂)
-- Description: Latest hour only, no timezone conversion
-- Created: 2025-10-02
-- ========================================================================================================

-- Drop existing view if exists
DROP MATERIALIZED VIEW IF EXISTS strategy_acceleration_score CASCADE;

-- Create materialized view
CREATE MATERIALIZED VIEW strategy_acceleration_score AS

WITH 
-- Step 1: Get hourly trades (NO timezone conversion)
hourly_trades AS (
    SELECT 
        strategy,
        action,
        strategy || ' | ' || action as strategy_action,
        DATE_TRUNC('hour', entry_time) as hour,
        CASE 
            WHEN result_10min = 'WIN' THEN 50 
            ELSE -50 
        END as pnl_value
    FROM tradingviewdata
    WHERE 
        action IN ('Buy', 'Sell')
        AND result_10min IS NOT NULL
        AND entry_time >= NOW() - INTERVAL '30 days'
),

-- Step 2: Calculate cumulative PNL for each strategy
cumulative_pnl AS (
    SELECT 
        strategy_action,
        hour,
        SUM(pnl_value) OVER (
            PARTITION BY strategy_action 
            ORDER BY hour 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as cumulative_pnl
    FROM hourly_trades
),

-- Step 3: Get latest cumulative PNL for each hour
hourly_pnl_latest AS (
    SELECT DISTINCT ON (strategy_action, hour)
        strategy_action,
        hour,
        cumulative_pnl
    FROM cumulative_pnl
    ORDER BY strategy_action, hour, cumulative_pnl DESC
),

-- Step 4: Calculate PNL windows (P1-P6)
pnl_windows AS (
    SELECT 
        a.strategy_action,
        a.hour as current_hour,
        COALESCE(a.cumulative_pnl, 0) as p1,
        COALESCE(LAG(a.cumulative_pnl, 1) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p2,
        COALESCE(LAG(a.cumulative_pnl, 2) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p3,
        COALESCE(LAG(a.cumulative_pnl, 3) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p4,
        COALESCE(LAG(a.cumulative_pnl, 4) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p5,
        COALESCE(LAG(a.cumulative_pnl, 5) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p6
    FROM hourly_pnl_latest a
),

-- Step 5: Calculate Momentum and Acceleration
momentum_calc AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, p2, p3,
        (p1 - p2) as m1,
        (p2 - p3) as m2,
        ((p1 - p2) - (p2 - p3)) as acceleration
    FROM pnl_windows
),

-- Step 6: Calculate raw score using Acceleration formula
raw_scores AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, p2, p3,
        -- Formula: 5×M₁ + 3×Acceleration
        (5.0 * GREATEST(m1, 0) + 3.0 * GREATEST(acceleration, 0)) as recent_raw
    FROM momentum_calc
),

-- Step 7: Calculate KPI and normalized score (LATEST HOUR ONLY)
score_normalization AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, p2, p3,
        recent_raw,
        AVG(recent_raw) OVER (PARTITION BY current_hour) + 
        STDDEV(recent_raw) OVER (PARTITION BY current_hour) as recent_kpi
    FROM raw_scores
    WHERE current_hour = (SELECT MAX(current_hour) FROM raw_scores)  -- ✅ LATEST HOUR ONLY
)

-- Final: Clean output (NO timezone conversion)
SELECT 
    SPLIT_PART(strategy_action, ' | ', 1) as strategy,
    SPLIT_PART(strategy_action, ' | ', 2) as action,
    ROUND(p1::numeric, 0) as "pnl_1h",
    ROUND(p2::numeric, 0) as "pnl_2h",
    ROUND(p3::numeric, 0) as "pnl_3h",
    ROUND(
        CASE 
            WHEN recent_kpi > 0 THEN 
                LEAST((recent_raw / recent_kpi) * 30, 30)
            ELSE 0 
        END::numeric, 
        2
    ) as score,
    NOW()::timestamp as last_update
FROM score_normalization
ORDER BY 
    score DESC, 
    "pnl_1h" DESC, 
    "pnl_2h" DESC, 
    "pnl_3h" DESC;

-- Create indexes for performance
CREATE INDEX idx_strategy_acceleration_score_score 
    ON strategy_acceleration_score(score DESC);
    
CREATE INDEX idx_strategy_acceleration_score_strategy 
    ON strategy_acceleration_score(strategy, action);

-- Add documentation
COMMENT ON MATERIALIZED VIEW strategy_acceleration_score IS 
'Strategy Acceleration Score V2 - Latest hour only, no timezone conversion
Formula: 5×M₁ + 3×Acceleration
Columns: strategy, action, pnl_1h, pnl_2h, pnl_3h, score, last_update
Order: score DESC, pnl_1h DESC, pnl_2h DESC, pnl_3h DESC
Returns: LATEST HOUR ONLY (no duplicates)
Updated: Every hour via cron';

-- Initial refresh
REFRESH MATERIALIZED VIEW strategy_acceleration_score;

