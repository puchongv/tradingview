-- ========================================================================================================
-- Strategy Acceleration Score (Aligned with Python Test 022)
-- Formula: 5×M₁ + 3×Acceleration (M₁ = P1 - P2, Acceleration = M₁ - M₂)
-- ========================================================================================================

DROP MATERIALIZED VIEW IF EXISTS strategy_acceleration_score CASCADE;

CREATE MATERIALIZED VIEW strategy_acceleration_score AS
WITH params AS (
    SELECT date_trunc('hour', now()) AS end_hour
),
window_hours AS (
    SELECT generate_series(
               (SELECT end_hour FROM params) - INTERVAL '5 hours',
               (SELECT end_hour FROM params),
               INTERVAL '1 hour'
           ) AS hour
),
raw_trades AS (
    SELECT
        strategy || ' | ' || action AS strategy_action,
        date_trunc('hour', entry_time) AS hour,
        CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END AS pnl_value
    FROM tradingviewdata
    WHERE action IN ('Buy', 'Sell')
      AND result_10min IS NOT NULL
      AND entry_time >= (SELECT hour FROM window_hours ORDER BY hour LIMIT 1)
),
strategies AS (
    SELECT DISTINCT strategy_action FROM raw_trades
),
hourly_changes AS (
    SELECT
        strategy_action,
        hour,
        SUM(pnl_value) AS hourly_change
    FROM raw_trades
    GROUP BY strategy_action, hour
),
strategy_hours AS (
    SELECT s.strategy_action, h.hour
    FROM strategies s
    CROSS JOIN window_hours h
),
hourly_series AS (
    SELECT
        sh.strategy_action,
        sh.hour,
        COALESCE(hc.hourly_change, 0) AS hourly_change
    FROM strategy_hours sh
    LEFT JOIN hourly_changes hc
           ON sh.strategy_action = hc.strategy_action
          AND sh.hour = hc.hour
),
cumulative AS (
    SELECT
        strategy_action,
        hour,
        hourly_change,
        SUM(hourly_change) OVER (
            PARTITION BY strategy_action
            ORDER BY hour
        ) AS cumulative_pnl
    FROM hourly_series
),
pnl_windows AS (
    SELECT
        strategy_action,
        hour AS current_hour,
        cumulative_pnl AS p1,
        COALESCE(LAG(cumulative_pnl, 1) OVER (PARTITION BY strategy_action ORDER BY hour), 0) AS p2,
        COALESCE(LAG(cumulative_pnl, 2) OVER (PARTITION BY strategy_action ORDER BY hour), 0) AS p3,
        COALESCE(LAG(cumulative_pnl, 3) OVER (PARTITION BY strategy_action ORDER BY hour), 0) AS p4,
        COALESCE(LAG(cumulative_pnl, 4) OVER (PARTITION BY strategy_action ORDER BY hour), 0) AS p5,
        COALESCE(LAG(cumulative_pnl, 5) OVER (PARTITION BY strategy_action ORDER BY hour), 0) AS p6
    FROM cumulative
),
momentum_scores AS (
    SELECT
        strategy_action,
        current_hour,
        p1,
        p2,
        p3,
        (p1 - p2) AS m1,
        (p2 - p3) AS m2,
        ((p1 - p2) - (p2 - p3)) AS acceleration,
        (5.0 * GREATEST(p1 - p2, 0) + 3.0 * GREATEST(((p1 - p2) - (p2 - p3)), 0)) AS recent_raw
    FROM pnl_windows
),
latest_only AS (
    SELECT DISTINCT ON (strategy_action)
        strategy_action,
        current_hour,
        p1,
        p2,
        p3,
        recent_raw
    FROM momentum_scores
    ORDER BY strategy_action, current_hour DESC
),
normalized AS (
    SELECT
        strategy_action,
        current_hour,
        p1,
        p2,
        p3,
        recent_raw,
        (AVG(recent_raw) OVER () + COALESCE(STDDEV_POP(recent_raw) OVER (), 0)) AS recent_kpi
    FROM latest_only
)
SELECT
    split_part(strategy_action, ' | ', 1) AS strategy,
    split_part(strategy_action, ' | ', 2) AS action,
    ROUND(p1, 0) AS "pnl_1h",
    ROUND(p2, 0) AS "pnl_2h",
    ROUND(p3, 0) AS "pnl_3h",
    ROUND(
        CASE
            WHEN recent_kpi > 0 THEN LEAST((recent_raw / recent_kpi) * 30, 30)
            ELSE 0
        END,
        2
    ) AS score,
    timezone('Asia/Bangkok', now())::timestamp AS last_update
FROM normalized
ORDER BY
    score DESC,
    "pnl_1h" DESC,
    "pnl_2h" DESC,
    "pnl_3h" DESC;

CREATE INDEX idx_strategy_acceleration_score_score
    ON strategy_acceleration_score(score DESC);

CREATE INDEX idx_strategy_acceleration_score_strategy
    ON strategy_acceleration_score(strategy, action);

COMMENT ON MATERIALIZED VIEW strategy_acceleration_score IS
'Strategy Acceleration Score - Logic aligned with Python Test 022
Formula: 5×M₁ + 3×Acceleration
Columns: strategy, action, pnl_1h, pnl_2h, pnl_3h, score, last_update (UTC+7)
Returns: One row per strategy-action (latest hour only).';

REFRESH MATERIALIZED VIEW strategy_acceleration_score;
