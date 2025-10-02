-- File: barchart winrate overtime_v1_0_3.sql
-- Purpose: v1.0.2 + optional "past_days" filter to fetch latest N days.
-- Version: 1.0.3 (new file; previous versions untouched)

-- Metabase params (same as v1_0_2, plus past_days):
--   {{interval_target}} (Text, optional)   -> '10min' | '30min' | '60min'
--   {{exclude_strategy}} (Text, optional)  -> CSV list
--   {{exclude_action}} (Text, optional)    -> CSV list
--   {{start_date}} (Date, optional)        -> inclusive
--   {{end_date}} (Date, optional)          -> inclusive
--   {{payout}} (Number, required, default 0.8)
--   {{investment}} (Number, required, default 250)
--   {{past_days}} (Number, optional)       -> latest N calendar days; if blank/0, no effect

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
strategy_action_agg AS (
    SELECT
        (strategy || ' | ' || action)               AS strategy_action,
        COUNT(*)                                      AS total_trades,
        COUNT(*) FILTER (WHERE result_selected='WIN') AS wins,
        COUNT(*) FILTER (WHERE result_selected='LOSE') AS losses,
        COUNT(DISTINCT entry_time::date)              AS active_days
    FROM filtered_recent
    GROUP BY strategy, action
)
SELECT
    a.strategy_action,
    ROUND(100.0 * a.wins::numeric / NULLIF(a.total_trades,0), 1) AS win_rate_pct,
    a.total_trades,
    a.wins,
    a.losses,
    (
        a.wins * COALESCE(NULLIF(CAST({{payout}} AS text), '')::numeric, 0.8)
        - a.losses
    ) * COALESCE(NULLIF(CAST({{investment}} AS text), '')::numeric, 250) AS pnl,
    (
        (
            a.wins * COALESCE(NULLIF(CAST({{payout}} AS text), '')::numeric, 0.8)
            - a.losses
        ) * COALESCE(NULLIF(CAST({{investment}} AS text), '')::numeric, 250)
    ) / NULLIF(a.active_days, 0) AS est_pnl_per_day
FROM strategy_action_agg a
ORDER BY win_rate_pct DESC, a.total_trades DESC;


