-- File: line-chart winrate overtime_v1_0_4.sql
-- Purpose: Win rate aggregated in 6-hour windows per day (bins ending at 06:00, 12:00, 18:00, 24:00),
--          breakout by strategy | action, for line chart.
-- Chart: X = y_ts_6h (time), Y = x_win_rate_pct, Series = series
-- Version: 1.0.4 (new file)

-- Params (same as previous line-chart versions):
--   {{interval_target}} (Text, optional)   -> '10min' | '30min' | '60min'
--   {{exclude_strategy}} (Text, optional)  -> CSV list
--   {{exclude_action}} (Text, optional)    -> CSV list
--   {{start_date}} (Date, optional)
--   {{end_date}} (Date, optional)
--   {{payout}} (Number, required, default 0.8)       -- not used here
--   {{investment}} (Number, required, default 250)   -- not used here
--   {{past_days}} (Number, optional)

WITH base AS (
    SELECT strategy, action, entry_time, '10min'::text AS interval_label, result_10min AS result_selected
    FROM public.tradingviewdata
    UNION ALL
    SELECT strategy, action, entry_time, '30min'::text AS interval_label, result_30min AS result_selected
    FROM public.tradingviewdata
    UNION ALL
    SELECT strategy, action, entry_time, '60min'::text AS interval_label, result_60min AS result_selected
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
bucketed AS (
    SELECT
        -- 6-hour bin start and end per day
        (date_trunc('day', entry_time)
         + ((EXTRACT(HOUR FROM entry_time)::int / 6) * 6) * INTERVAL '1 hour') AS y_ts_6h_start,
        (date_trunc('day', entry_time)
         + (((EXTRACT(HOUR FROM entry_time)::int / 6) * 6) + 6) * INTERVAL '1 hour') AS y_ts_6h_end,
        (strategy || ' | ' || action) AS series,
        result_selected
    FROM filtered_recent
),
agg AS (
    SELECT
        -- use bin end as the plotted timestamp: 06:00, 12:00, 18:00, 24:00 (next day's 00:00)
        y_ts_6h_end AS y_ts_6h,
        series,
        COUNT(*)                                       AS total_trades,
        COUNT(*) FILTER (WHERE result_selected='WIN')  AS wins
    FROM bucketed
    GROUP BY y_ts_6h, series
)
SELECT
    y_ts_6h,
    series,
    ROUND(100.0 * wins::numeric / NULLIF(total_trades, 0), 1) AS x_win_rate_pct,
    total_trades
FROM agg
ORDER BY y_ts_6h ASC, series;



