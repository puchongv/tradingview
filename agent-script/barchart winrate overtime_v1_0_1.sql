-- File: barchart winrate overtime_v1_0_1.sql
-- Purpose: Bar chart win rate per strategy (actions shown in tooltip), with
--          optional interval filter, excludes, date range, and PnL output.
-- Version: 1.0.1 (new file; original kept unchanged)

-- Metabase params (only those listed below):
--   {{interval_target}} (Text, optional)   -> '10min' | '30min' | '60min'
--   {{exclude_strategy}} (Text, optional)  -> CSV list, e.g. MWP-25,MWP-30
--   {{exclude_action}} (Text, optional)    -> CSV list, e.g. Buy,FlowTrend Bullish + Buy
--   {{start_date}} (Date, optional)        -> inclusive
--   {{end_date}} (Date, optional)          -> inclusive
--   {{payout}} (Number, required, default 0.8)
--   {{investment}} (Number, required, default 250)

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
    -- Exclude lists (if provided). If blank or NULL, do nothing.
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
strategy_action_agg AS (
    SELECT
        (strategy || ' | ' || action)               AS strategy_action,
        COUNT(*)                                      AS total_trades,
        COUNT(*) FILTER (WHERE result_selected='WIN') AS wins,
        COUNT(*) FILTER (WHERE result_selected='LOSE') AS losses
    FROM filtered
    GROUP BY strategy, action
)
SELECT
    a.strategy_action,
    ROUND(100.0 * a.wins::numeric / NULLIF(a.total_trades,0), 1) AS win_rate_pct,
    a.total_trades,
    a.wins,
    a.losses,
    -- Binary Options PnL: (wins * payout - losses) * investment
    (
        a.wins * COALESCE(NULLIF(CAST({{payout}} AS text), '')::numeric, 0.8)
        - a.losses
    ) * COALESCE(NULLIF(CAST({{investment}} AS text), '')::numeric, 250) AS pnl
FROM strategy_action_agg a
ORDER BY win_rate_pct DESC, a.total_trades DESC;


