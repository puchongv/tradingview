-- Rolling Win Rate & Trend Change Query for Metabase
-- Parameters (Metabase variables):
--   timeframe      : 10min | 30min | 60min   (required)
--   window_hours   : 6 | 12 | 24 | 48        (rolling window length in hours)
--   hours_back     : 24 | 72 | 168 ...       (look-back horizon)
--   strategy       : optional filter ("all" to ignore)
--   action         : optional filter ("all" to ignore)
--
-- Notes:
--   • 1 row per hour → use ROWS frame with window_hours PRECEDING
--   • PostgreSQL ≥ 11
--   • Keep header free of {{ }} braces to avoid Metabase param parser errors
--   • Uses a CTE to build per-hour aggregates, then applies a rolling window via
--     SUM() / COUNT() window functions (ROWS BETWEEN).
--   • Works in PostgreSQL ≥ 11 (Metabase v0.49+).
--   • Avoids timezone conversion – assumes entry_time stored in UTC or same TZ across table.
--   • Designed for Metabase line chart with: X-axis = bucket_hour, Y-axis = win_rate
--     plus custom columns win_rate_change / win_rate_pct_change for tooltip / alert rules.

WITH base AS (
    SELECT
        date_trunc('hour', entry_time)            AS bucket_hour,
        CASE
            WHEN '{{timeframe}}' = '10min' AND result_10min = 'WIN' THEN 1
            WHEN '{{timeframe}}' = '30min' AND result_30min = 'WIN' THEN 1
            WHEN '{{timeframe}}' = '60min' AND result_60min = 'WIN' THEN 1
            ELSE 0
        END                                        AS is_win,
        CASE
            WHEN '{{timeframe}}' = '10min' AND result_10min IS NOT NULL THEN 1
            WHEN '{{timeframe}}' = '30min' AND result_30min IS NOT NULL THEN 1
            WHEN '{{timeframe}}' = '60min' AND result_60min IS NOT NULL THEN 1
            ELSE 0
        END                                        AS is_trade
    FROM tradingviewdata
    WHERE entry_time >= NOW() - INTERVAL '{{hours_back}} hours'
      AND (
          CASE
              WHEN '{{timeframe}}' = '10min' THEN result_10min IN ('WIN','LOSE')
              WHEN '{{timeframe}}' = '30min' THEN result_30min IN ('WIN','LOSE')
              WHEN '{{timeframe}}' = '60min' THEN result_60min IN ('WIN','LOSE')
              ELSE FALSE
          END)
      AND (
          '{{strategy}}' IS NULL OR '{{strategy}}' = '' OR '{{strategy}}' = 'all' OR strategy = '{{strategy}}')
      AND (
          '{{action}}' IS NULL OR '{{action}}' = '' OR '{{action}}' = 'all' OR action = '{{action}}')
),
per_hour AS (
    SELECT
        bucket_hour,
        SUM(is_win)                        AS wins,
        SUM(is_trade)                      AS trades,
        CASE WHEN SUM(is_trade) > 0 THEN SUM(is_win)*100.0/SUM(is_trade) END AS win_rate
    FROM base
    GROUP BY bucket_hour
),
rolling AS (
    SELECT
        bucket_hour,
        -- Rolling sums for window_hours preceding (inclusive)
        SUM(wins)   OVER (ORDER BY bucket_hour
                         ROWS BETWEEN {{window_hours}} PRECEDING AND CURRENT ROW) AS rolling_wins,
        SUM(trades) OVER (ORDER BY bucket_hour
                         ROWS BETWEEN {{window_hours}} PRECEDING AND CURRENT ROW) AS rolling_trades
    FROM per_hour
)
SELECT
    bucket_hour,
    CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END            AS win_rate,
    rolling_trades                                                                      AS total_trades,
    -- Absolute change vs previous rolling window
    (CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END) -
    LAG(CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END)
        OVER (ORDER BY bucket_hour)                                                     AS win_rate_change,
    -- % change vs previous rolling window
    CASE
        WHEN LAG(CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END)
             OVER (ORDER BY bucket_hour) IS NULL THEN NULL
        WHEN LAG(CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END)
             OVER (ORDER BY bucket_hour) = 0 THEN NULL
        ELSE (
            (CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END) -
            LAG(CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END)
                OVER (ORDER BY bucket_hour)
        ) / LAG(CASE WHEN rolling_trades > 0 THEN rolling_wins*100.0/rolling_trades END)
            OVER (ORDER BY bucket_hour) * 100
    END                                                                                 AS win_rate_pct_change
FROM rolling
ORDER BY bucket_hour;
