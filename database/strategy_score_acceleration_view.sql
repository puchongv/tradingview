-- ========================================================================================================
-- Strategy Score View - Acceleration Formula (Option D)
-- Formula: 5×M₁ + 3×Acceleration
-- Description: Real-time strategy scoring based on momentum acceleration
-- Author: AI Assistant
-- Created: 2025-10-02
-- ========================================================================================================

-- Drop existing view if exists
DROP MATERIALIZED VIEW IF EXISTS strategy_score_acceleration CASCADE;

-- Create materialized view for better performance
CREATE MATERIALIZED VIEW strategy_score_acceleration AS

WITH 
-- Step 1: Get hourly PNL for each strategy-action combination
hourly_trades AS (
    SELECT 
        strategy,
        action,
        strategy || ' | ' || action as strategy_action,
        DATE_TRUNC('hour', entry_time) as hour,
        CASE 
            WHEN result_10min = 'WIN' THEN 50 
            ELSE -50 
        END as pnl_value,
        entry_time
    FROM tradingviewdata
    WHERE 
        action IN ('Buy', 'Sell')  -- Hard-code Buy/Sell only
        AND result_10min IS NOT NULL
        AND entry_time >= NOW() - INTERVAL '30 days'  -- Keep last 30 days
),

-- Step 2: Calculate cumulative PNL for each strategy at each hour
cumulative_pnl AS (
    SELECT 
        strategy_action,
        hour,
        SUM(pnl_value) OVER (
            PARTITION BY strategy_action 
            ORDER BY hour 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as cumulative_pnl,
        COUNT(*) OVER (
            PARTITION BY strategy_action, hour
        ) as trade_count,
        SUM(CASE WHEN pnl_value > 0 THEN 1 ELSE 0 END) OVER (
            PARTITION BY strategy_action, hour
        ) as win_count
    FROM hourly_trades
),

-- Step 3: Get latest cumulative PNL for each hour
hourly_pnl_latest AS (
    SELECT DISTINCT ON (strategy_action, hour)
        strategy_action,
        hour,
        cumulative_pnl,
        trade_count,
        win_count
    FROM cumulative_pnl
    ORDER BY strategy_action, hour, cumulative_pnl DESC
),

-- Step 4: Calculate PNL windows (P1-P6) for each strategy at current time
pnl_windows AS (
    SELECT 
        a.strategy_action,
        a.hour as current_hour,
        
        -- Current cumulative PNL (P1)
        COALESCE(a.cumulative_pnl, 0) as p1,
        
        -- Previous hours (P2-P6)
        COALESCE(LAG(a.cumulative_pnl, 1) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p2,
        COALESCE(LAG(a.cumulative_pnl, 2) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p3,
        COALESCE(LAG(a.cumulative_pnl, 3) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p4,
        COALESCE(LAG(a.cumulative_pnl, 4) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p5,
        COALESCE(LAG(a.cumulative_pnl, 5) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p6,
        
        -- Trade stats
        a.trade_count,
        a.win_count
    FROM hourly_pnl_latest a
),

-- Step 5: Calculate Momentum and Acceleration
momentum_calc AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, p2, p3, p4, p5, p6,
        trade_count,
        win_count,
        
        -- Momentum calculations
        (p1 - p2) as m1,
        (p2 - p3) as m2,
        
        -- Acceleration (momentum of momentum)
        ((p1 - p2) - (p2 - p3)) as acceleration
    FROM pnl_windows
),

-- Step 6: Calculate raw score using Acceleration formula
raw_scores AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, m1, acceleration,
        trade_count,
        win_count,
        
        -- Acceleration Formula: 5×M₁ + 3×Acceleration
        (5.0 * GREATEST(m1, 0) + 3.0 * GREATEST(acceleration, 0)) as recent_raw
    FROM momentum_calc
),

-- Step 7: Calculate KPI and normalized score (per hour)
score_normalization AS (
    SELECT 
        strategy_action,
        current_hour,
        p1,
        m1,
        acceleration,
        recent_raw,
        trade_count,
        win_count,
        
        -- KPI = mean + stddev (per hour)
        AVG(recent_raw) OVER (PARTITION BY current_hour) + 
        STDDEV(recent_raw) OVER (PARTITION BY current_hour) as recent_kpi
    FROM raw_scores
)

-- Final: Calculate normalized score (0-30)
SELECT 
    strategy_action,
    SPLIT_PART(strategy_action, ' | ', 1) as strategy,
    SPLIT_PART(strategy_action, ' | ', 2) as action,
    current_hour,
    p1 as current_pnl,
    m1 as momentum,
    acceleration,
    recent_raw,
    recent_kpi,
    
    -- Normalized score (0-30)
    CASE 
        WHEN recent_kpi > 0 THEN 
            LEAST((recent_raw / recent_kpi) * 30, 30)
        ELSE 0 
    END as score,
    
    -- Trade stats
    trade_count,
    win_count,
    CASE 
        WHEN trade_count > 0 THEN 
            ROUND((win_count::numeric / trade_count) * 100, 2)
        ELSE 0 
    END as win_rate,
    
    -- Metadata
    NOW() as updated_at
FROM score_normalization
WHERE current_hour >= NOW() - INTERVAL '24 hours'  -- Keep last 24 hours
ORDER BY current_hour DESC, score DESC;

-- Create indexes for better performance
CREATE INDEX idx_strategy_score_hour ON strategy_score_acceleration(current_hour DESC);
CREATE INDEX idx_strategy_score_score ON strategy_score_acceleration(score DESC);
CREATE INDEX idx_strategy_score_strategy ON strategy_score_acceleration(strategy_action);

-- Add comment
COMMENT ON MATERIALIZED VIEW strategy_score_acceleration IS 
'Real-time strategy scoring using Acceleration formula (5×M₁ + 3×Acceleration). 
Updated every hour via cron job. Shows scores for last 24 hours.';

-- Initial refresh
REFRESH MATERIALIZED VIEW strategy_score_acceleration;

