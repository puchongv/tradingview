-- ========================================================================================================
-- Strategy Acceleration Score (100% Same Logic as Python Test 022)
-- Formula: 5×M₁ + 3×Acceleration (M₁=P1-P2, Acceleration=M₁-M₂)
-- ========================================================================================================

DROP MATERIALIZED VIEW IF EXISTS strategy_acceleration_score CASCADE;

CREATE MATERIALIZED VIEW strategy_acceleration_score AS

WITH 
-- Step 1: Get hourly trades (EXACTLY like Python fetch_trading_data)
hourly_trades AS (
    SELECT 
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
        AND entry_time >= NOW() - INTERVAL '6 hours'  -- 6 hour lookback (2× safety margin)
),

-- Step 2: Calculate cumulative PNL (EXACTLY like Python: cumsum())
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

-- Step 3: Get latest PNL for each hour (EXACTLY like Python: iloc[-1])
hourly_pnl AS (
    SELECT DISTINCT ON (strategy_action, hour)
        strategy_action,
        hour,
        cumulative_pnl
    FROM cumulative_pnl
    ORDER BY strategy_action, hour, cumulative_pnl DESC
),

-- Step 4: Forward fill missing hours (EXACTLY like Python: prev_pnl logic)
filled_data AS (
    SELECT 
        strategy_action,
        hour,
        cumulative_pnl,
        COALESCE(
            cumulative_pnl,
            LAST_VALUE(cumulative_pnl) OVER (
                PARTITION BY strategy_action 
                ORDER BY hour 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ),
            0
        ) as filled_pnl
    FROM (
        SELECT 
            s.strategy_action,
            h.hour,
            hp.cumulative_pnl
        FROM (SELECT DISTINCT strategy_action FROM hourly_pnl) s
        CROSS JOIN (SELECT DISTINCT hour FROM hourly_pnl) h
        LEFT JOIN hourly_pnl hp 
            ON s.strategy_action = hp.strategy_action 
            AND h.hour = hp.hour
    ) t
),

-- Step 5: Calculate P1-P6 using LAG (EXACTLY like Python: pnls[0] to pnls[5])
pnl_windows AS (
    SELECT 
        strategy_action,
        hour as current_hour,
        filled_pnl as p1,
        COALESCE(LAG(filled_pnl, 1) OVER (PARTITION BY strategy_action ORDER BY hour), 0) as p2,
        COALESCE(LAG(filled_pnl, 2) OVER (PARTITION BY strategy_action ORDER BY hour), 0) as p3,
        COALESCE(LAG(filled_pnl, 3) OVER (PARTITION BY strategy_action ORDER BY hour), 0) as p4,
        COALESCE(LAG(filled_pnl, 4) OVER (PARTITION BY strategy_action ORDER BY hour), 0) as p5,
        COALESCE(LAG(filled_pnl, 5) OVER (PARTITION BY strategy_action ORDER BY hour), 0) as p6
    FROM filled_data
),

-- Step 6: Calculate momentum score (EXACTLY like Python: 5×max(m1,0) + 3×max(accel,0))
momentum_scores AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, p2, p3,
        (p1 - p2) as m1,
        (p2 - p3) as m2,
        ((p1 - p2) - (p2 - p3)) as acceleration,
        (5.0 * GREATEST((p1 - p2), 0) + 3.0 * GREATEST(((p1 - p2) - (p2 - p3)), 0)) as recent_raw
    FROM pnl_windows
),

-- Step 7: Get ONLY latest hour for each strategy (EXACTLY like Python: current state)
latest_only AS (
    SELECT DISTINCT ON (strategy_action)
        strategy_action,
        current_hour,
        p1, p2, p3,
        recent_raw
    FROM momentum_scores
    ORDER BY strategy_action, current_hour DESC
),

-- Step 8: Normalize score (EXACTLY like Python: KPI = mean + stddev)
normalized AS (
    SELECT 
        strategy_action,
        current_hour,
        p1, p2, p3,
        recent_raw,
        AVG(recent_raw) OVER () + STDDEV(recent_raw) OVER () as recent_kpi
    FROM latest_only
)

-- Final output
SELECT 
    SPLIT_PART(strategy_action, ' | ', 1) as strategy,
    SPLIT_PART(strategy_action, ' | ', 2) as action,
    ROUND(p1, 0) as "pnl_1h",
    ROUND(p2, 0) as "pnl_2h",
    ROUND(p3, 0) as "pnl_3h",
    ROUND(
        CASE 
            WHEN recent_kpi > 0 THEN LEAST((recent_raw / recent_kpi) * 30, 30)
            ELSE 0 
        END, 
        2
    ) as score,
    (NOW() AT TIME ZONE 'Asia/Bangkok')::timestamp as last_update
FROM normalized
ORDER BY 
    score DESC, 
    "pnl_1h" DESC, 
    "pnl_2h" DESC, 
    "pnl_3h" DESC;

-- Indexes
CREATE INDEX idx_strategy_acceleration_score_score 
    ON strategy_acceleration_score(score DESC);
    
CREATE INDEX idx_strategy_acceleration_score_strategy 
    ON strategy_acceleration_score(strategy, action);

-- Documentation
COMMENT ON MATERIALIZED VIEW strategy_acceleration_score IS 
'Strategy Acceleration Score - 100% Same Logic as Python Test 022
Formula: 5×M₁ + 3×Acceleration
Columns: strategy, action, pnl_1h, pnl_2h, pnl_3h, score, last_update (UTC+7)
Returns: One row per strategy-action (latest hour only)';

-- Initial refresh
REFRESH MATERIALIZED VIEW strategy_acceleration_score;

