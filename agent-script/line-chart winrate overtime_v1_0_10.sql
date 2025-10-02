-- File: line-chart winrate overtime_v1_0_10.sql
-- Purpose: Win rate over time per strategy | action with automatic top-strategy selection
--          and optional manual includes; time aggregated into configurable hour bins.
-- Chart: X = y_ts (formatted string), Y = x_win_rate_pct, Series = series
-- Version: 1.0.10 (new file)

-- Params (extends v1_0_4):
--   {{interval_target}} (Text, optional)   -> '10min' | '30min' | '60min'
--   {{exclude_strategy}} (Text, optional)  -> CSV list
--   {{exclude_action}} (Text, optional)    -> CSV list
--   {{start_date}} (Date, optional)
--   {{end_date}} (Date, optional)
--   {{past_hours}} (Number, optional)      -> look-back window in hours relative to current time
--   {{bin_hours}} (Number, optional)       -> time bucket size in hours (default 1)
--   {{top_strategy}} (Number, optional)    -> max auto-selected strategies (default 12; negative pulls worst PnL)
--   {{include_strategy}} (Text, optional)  -> CSV list; when set, only these strategies are processed
--   {{include_action}} (Text, optional)    -> CSV list; when set, only these actions are processed
--   {{payout}} (Number, optional)          -> payout ratio per winning trade (default 0.8)
--   {{investment}} (Number, optional)      -> stake size per trade (default 250)

WITH config_input AS (
    SELECT
        GREATEST(1, COALESCE(NULLIF(CAST({{bin_hours}} AS text), '')::int, 1)) AS bin_hours,
        COALESCE(
            NULLIF(CAST({{top_strategy}} AS text), '')::int,
            12
        ) AS top_strategy_raw,
        COALESCE(NULLIF(CAST({{payout}} AS text), '')::numeric, 0.8) AS payout,
        COALESCE(NULLIF(CAST({{investment}} AS text), '')::numeric, 250) AS investment
),
config AS (
    SELECT
        bin_hours,
        payout,
        investment,
        CASE
            WHEN top_strategy_raw IS NULL OR top_strategy_raw = 0 THEN 12
            ELSE ABS(top_strategy_raw)
        END AS top_strategy_limit,
        CASE
            WHEN top_strategy_raw IS NOT NULL AND top_strategy_raw < 0 THEN -1
            ELSE 1
        END AS top_strategy_direction
    FROM config_input
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
include_strategy_list AS (
    SELECT NULL::text AS strategy
    WHERE FALSE
    [[
    UNION ALL
    SELECT DISTINCT TRIM(val) AS strategy
    FROM (
        SELECT UNNEST(string_to_array(replace({{include_strategy}}, ' ', ''), ',')) AS val
    ) raw
    WHERE TRIM(val) <> ''
    ]]
),
include_action_list AS (
    SELECT NULL::text AS action
    WHERE FALSE
    [[
    UNION ALL
    SELECT DISTINCT TRIM(val) AS action
    FROM (
        SELECT UNNEST(string_to_array(replace({{include_action}}, ' ', ''), ',')) AS val
    ) raw
    WHERE TRIM(val) <> ''
    ]]
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
    [[ AND (
        COALESCE(NULLIF({{include_strategy}}, ''), '') = ''
        OR strategy IN (
            SELECT strategy FROM include_strategy_list
        )
    ) ]]
    [[ AND (
        COALESCE(NULLIF({{include_action}}, ''), '') = ''
        OR action IN (
            SELECT action FROM include_action_list
        )
    ) ]]
),
filtered_recent AS (
    SELECT f.*
    FROM filtered f
    WHERE 1=1
    [[ AND f.entry_time >= NOW() - (CAST({{past_hours}} AS int) * INTERVAL '1 hour') ]]
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
        ) AS rank_best,
        ROW_NUMBER() OVER (
            ORDER BY so.pnl_total ASC,
                     so.total_trades ASC,
                     so.win_rate ASC NULLS LAST,
                     so.series
        ) AS rank_worst
    FROM series_overall so
),
selected_series AS (
    SELECT DISTINCT
        ranked.strategy,
        ranked.action,
        ranked.series
    FROM (
        SELECT
            sr.strategy,
            sr.action,
            sr.series,
            CASE
                WHEN c.top_strategy_direction = -1 THEN sr.rank_worst
                ELSE sr.rank_best
            END AS effective_rank,
            c.top_strategy_limit
        FROM series_ranked sr
        CROSS JOIN config c
    ) ranked
    WHERE ranked.effective_rank <= ranked.top_strategy_limit
    UNION
    SELECT sr.strategy, sr.action, sr.series
    FROM series_ranked sr
    WHERE EXISTS (
        SELECT 1
        FROM include_strategy_list isl
        WHERE isl.strategy = sr.strategy
    )
    OR EXISTS (
        SELECT 1
        FROM include_action_list ial
        WHERE ial.action = sr.action
    )
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
limits AS (
    SELECT
        MIN(b.y_ts_bin_start) AS min_bin_start,
        MAX(b.y_ts_bin_end)   AS max_bin_end
    FROM bucketed b
),
series_bins AS (
    -- build full timeline per selected series so charts show every bin across the actual data window
    SELECT
        ss.series,
        gs AS y_ts_bin_start,
        gs + c.bin_hours * INTERVAL '1 hour' AS y_ts_bin_end
    FROM selected_series ss
    CROSS JOIN config c
    CROSS JOIN limits l
    CROSS JOIN LATERAL generate_series(
        l.min_bin_start,
        l.max_bin_end - c.bin_hours * INTERVAL '1 hour',
        c.bin_hours * INTERVAL '1 hour'
    ) AS gs
    WHERE l.min_bin_start IS NOT NULL AND l.max_bin_end IS NOT NULL
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
    TO_CHAR(c.y_ts_bin_end, 'YYYY-MM-DD HH24:MI') AS y_ts,
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


