-- File: line-chart winrate overtime_v1_0_5.sql
-- Purpose: Win rate over time per strategy | action with automatic top-strategy selection
--          and optional manual includes; time aggregated into configurable hour bins.
-- Chart: X = y_ts_bin_end (time), Y = x_win_rate_pct, Series = series
-- Version: 1.0.5 (new file)

-- Params (extends v1_0_4):
--   {{interval_target}} (Text, optional)   -> '10min' | '30min' | '60min'
--   {{exclude_strategy}} (Text, optional)  -> CSV list
--   {{exclude_action}} (Text, optional)    -> CSV list
--   {{start_date}} (Date, optional)
--   {{end_date}} (Date, optional)
--   {{past_days}} (Number, optional)       -> look-back window relative to latest date
--   {{bin_hours}} (Number, optional)       -> time bucket size in hours (default 1)
--   {{top_strategy}} (Number, optional)    -> max auto-selected strategies (default 12)
--   {{include_series}} (Text, optional)    -> CSV list of additional series to force-include
--   {{payout}} (Number, optional)          -> payout ratio per winning trade (default 0.8)
--   {{investment}} (Number, optional)      -> stake size per trade (default 250)

WITH config AS (
    SELECT
        GREATEST(1, COALESCE(NULLIF(CAST({{bin_hours}} AS text), '')::int, 1)) AS bin_hours,
        COALESCE(NULLIF(CAST({{top_strategy}} AS text), '')::int, 12) AS top_strategy,
        COALESCE(NULLIF(CAST({{payout}} AS text), '')::numeric, 0.8) AS payout,
        COALESCE(NULLIF(CAST({{investment}} AS text), '')::numeric, 250) AS investment
),
base AS (
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
series_overall AS (
    SELECT
        strategy,
        action,
        (strategy || ' | ' || action) AS series,
        COUNT(*) AS total_trades,
        COUNT(*) FILTER (WHERE result_selected='WIN')  AS wins,
        COUNT(*) FILTER (WHERE result_selected='LOSE') AS losses,
        COUNT(*) FILTER (WHERE result_selected='WIN')::numeric
            / NULLIF(COUNT(*), 0) AS win_rate,
        ((COUNT(*) FILTER (WHERE result_selected='WIN') * c.payout
          - (COUNT(*) - COUNT(*) FILTER (WHERE result_selected='WIN'))) * c.investment) AS pnl_total
    FROM filtered_recent
    CROSS JOIN config c
    GROUP BY strategy, action, c.payout, c.investment
),
series_ranked AS (
    SELECT
        so.*,
        ROW_NUMBER() OVER (
            ORDER BY so.pnl_total DESC,
                     so.total_trades DESC,
                     so.win_rate DESC NULLS LAST,
                     so.series
        ) AS series_rank
    FROM series_overall so
),
selected_series AS (
    SELECT DISTINCT
        sr.strategy,
        sr.action,
        sr.series
    FROM (
        SELECT sr.*
        FROM series_ranked sr
        CROSS JOIN config c
        WHERE sr.series_rank <= c.top_strategy
        [[
        UNION
        SELECT sr.*
        FROM series_ranked sr
        JOIN (
            SELECT DISTINCT TRIM(val) AS series
            FROM (
                SELECT UNNEST(string_to_array(replace({{include_series}}, ' ', ''), ',')) AS val
            ) raw
            WHERE TRIM(val) <> ''
        ) inc ON inc.series = sr.series
        ]]
    ) sr
),
filtered_selected AS (
    SELECT
        fr.*,
        ss.series
    FROM filtered_recent fr
    JOIN selected_series ss
      ON fr.strategy = ss.strategy
     AND fr.action = ss.action
),
timeframe AS (
    SELECT
        date_trunc('day', MIN(entry_time)) AS min_day,
        date_trunc('day', MAX(entry_time)) AS max_day
    FROM filtered_selected
),
bucketed AS (
    SELECT
        (date_trunc('day', fs.entry_time)
         + (FLOOR(EXTRACT(HOUR FROM fs.entry_time)::int / c.bin_hours) * c.bin_hours) * INTERVAL '1 hour') AS y_ts_bin_start,
        (date_trunc('day', fs.entry_time)
         + (FLOOR(EXTRACT(HOUR FROM fs.entry_time)::int / c.bin_hours) * c.bin_hours + c.bin_hours) * INTERVAL '1 hour') AS y_ts_bin_end,
        fs.series,
        fs.result_selected
    FROM filtered_selected fs
    CROSS JOIN config c
),
series_bins AS (
    -- build full timeline per selected series so charts show every bin across the chosen window
    SELECT
        ss.series,
        gs AS y_ts_bin_start,
        gs + c.bin_hours * INTERVAL '1 hour' AS y_ts_bin_end
    FROM selected_series ss
    CROSS JOIN config c
    CROSS JOIN timeframe tf
    CROSS JOIN LATERAL generate_series(
        tf.min_day,
        tf.max_day + INTERVAL '1 day' - c.bin_hours * INTERVAL '1 hour',
        c.bin_hours * INTERVAL '1 hour'
    ) AS gs
    WHERE tf.min_day IS NOT NULL AND tf.max_day IS NOT NULL
),
agg AS (
    SELECT
        y_ts_bin_end,
        series,
        COUNT(*)                                      AS total_trades,
        COUNT(*) FILTER (WHERE result_selected='WIN') AS wins
    FROM bucketed
    GROUP BY y_ts_bin_end, series
),
series_hourly AS (
    SELECT
        sb.series,
        sb.y_ts_bin_start,
        sb.y_ts_bin_end,
        COALESCE(a.total_trades, 0) AS bin_total_trades,
        COALESCE(a.wins, 0) AS bin_wins,
        COALESCE(a.total_trades, 0) - COALESCE(a.wins, 0) AS bin_losses,
        ((COALESCE(a.wins, 0) * c.payout
          - (COALESCE(a.total_trades, 0) - COALESCE(a.wins, 0))) * c.investment) AS bin_pnl
    FROM series_bins sb
    LEFT JOIN agg a
        ON a.series = sb.series
       AND a.y_ts_bin_end = sb.y_ts_bin_end
    CROSS JOIN config c
),
cumulative AS (
    SELECT
        sh.series,
        sh.y_ts_bin_start,
        sh.y_ts_bin_end,
        sh.bin_total_trades,
        sh.bin_wins,
        sh.bin_losses,
        sh.bin_pnl,
        SUM(sh.bin_total_trades) OVER (
            PARTITION BY sh.series
            ORDER BY sh.y_ts_bin_end
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS total_trades_cum,
        SUM(sh.bin_wins) OVER (
            PARTITION BY sh.series
            ORDER BY sh.y_ts_bin_end
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS wins_cum,
        SUM(sh.bin_losses) OVER (
            PARTITION BY sh.series
            ORDER BY sh.y_ts_bin_end
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS losses_cum,
        SUM(sh.bin_pnl) OVER (
            PARTITION BY sh.series
            ORDER BY sh.y_ts_bin_end
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS pnl_cum
    FROM series_hourly sh
)
SELECT
    c.y_ts_bin_end AS y_ts,
    c.series,
    CASE
        WHEN c.total_trades_cum = 0 THEN 0
        ELSE ROUND(100.0 * c.wins_cum::numeric / c.total_trades_cum, 1)
    END AS x_win_rate_pct,
    c.total_trades_cum AS total_trades,
    c.bin_total_trades AS bin_total_trades,
    c.bin_wins AS bin_wins,
    c.bin_losses AS bin_losses,
    c.bin_pnl AS bin_pnl,
    c.pnl_cum AS pnl_cum
FROM cumulative c
ORDER BY c.y_ts_bin_end ASC, c.series;
