-- File: line-chart winrate overtime_v1_0_1.sql
-- Purpose: Hourly time series of win rate, breakout by strategy | action.
--          Configure chart as: Y = y_ts (time), X = x_win_rate_pct, Series = series.
-- Version: 1.0.1 (new file; v1_0_0 kept)

-- Metabase params (same as v1_0_0 / barchart v1_0_3):
--   {{interval_target}} (Text, optional)   -> '10min' | '30min' | '60min'
--   {{exclude_strategy}} (Text, optional)  -> CSV list
--   {{exclude_action}} (Text, optional)    -> CSV list
--   {{start_date}} (Date, optional)        -> inclusive
--   {{end_date}} (Date, optional)          -> inclusive
--   {{payout}} (Number, required, default 0.8)       -- not used here
--   {{investment}} (Number, required, default 250)   -- not used here
--   {{past_days}} (Number, optional)       -> latest N calendar days; if blank, ignored

WITH base AS (
    SELECT
        strategy,
        action,
        entry_time,
        '10min'::text AS interval_label,
        result_10min  AS result_selected
    FROM public.tradingviewdata
    UNION ALL
    SELECT
        strategy,
        action,
        entry_time,
        '30min'::text AS interval_label,
        result_30min  AS result_selected
    FROM public.tradingviewdata
    UNION ALL
    SELECT
        strategy,
        action,
        entry_time,
        '60min'::text AS interval_label,
        result_60min  AS result_selected
    FROM public.tradingviewdata
),
filtered AS (
    SELECT *
    FROM base
    WHERE result_selected IN ('WIN','LOSE')
    [[ AND interval_label = {{interval_target}} ]]
    [[ AND entry_time::date >= {{start_date}} ]]
    [[ AND entry_time::date <= {{end_date}} ]]
    [[ AND (
        COALESCE(NULLIF({{exclude_strategy}}, ''), '') = ''
        OR strategy NOT IN (
            SELECT UNNEST(string_to_array(replace({{exclude_strategy}}, ' ', ''), ','))
        )
    ) ]]
    [[ AND (
        COALESCE(NULLIF({{exclude_action}}, ''), '') = ''
        OR action NOT IN (
            SELECT UNNEST(string_to_array(replace({{exclude_action}}, ' ', ''), ','))
        )
    ) ]]
),
date_bounds AS (
    SELECT MAX(entry_time::date) AS max_date FROM filtered
),
filtered_recent AS (
    SELECT f.*
    FROM filtered f
    CROSS JOIN date_bounds b
    WHERE 1=1
    [[ AND f.entry_time::date >= b.max_date - ((CAST({{past_days}} AS int) - 1) * INTERVAL '1 day') ]]
),
hourly AS (
    SELECT
        date_trunc('hour', entry_time)                 AS y_ts,
        EXTRACT(HOUR FROM entry_time)::int             AS hour_of_day,
        (strategy || ' | ' || action)                  AS series,
        COUNT(*)                                       AS total_trades,
        COUNT(*) FILTER (WHERE result_selected='WIN')  AS wins
    FROM filtered_recent
    GROUP BY y_ts, hour_of_day, series
)
SELECT
    y_ts,
    series,
    ROUND(100.0 * wins::numeric / NULLIF(total_trades, 0), 1) AS x_win_rate_pct,
    total_trades,
    hour_of_day
FROM hourly
ORDER BY y_ts ASC, series;


