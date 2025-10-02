-- File: Strategy Evalucation Score V1.0.2.sql
-- Purpose: Evaluate strategy/action signals across multiple time horizons with
--          scoring for PnL window, win-rate consistency, and recent performance.
-- Output columns (in order):
--   strategy | action | reverse | symbol | horizon | 24h_totaltrade | 24h_winrate | 24h_max_win_streak
--   | 24h_max_lose_streak | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl| pnl_score | win_con_scrore | perf_score | total score
-- Ordering: total score DESC, 6h_pnl DESC, 12h_pnl DESC
-- Version: 1.0.2

-- =======================================================================
-- Basic Setting & Filter Parameters
-- =======================================================================
-- {{horizon_list}} (Text, optional)     -> '10min,30min,60min' (default: '10min')
-- {{max_loss_streak_cap}} (Number)      -> 4 (loss streak threshold)
-- {{payout}} (Number)                   -> 0.8 (payout ratio per winning trade)
-- {{investment}} (Number)               -> 250 (stake size per trade)
-- {{reverse_enable}} (Boolean)          -> false (enable reverse mode for contrarian strategies)
-- {{abs_pnl}} (Boolean)                 -> false (show negative PNL as positive)
-- {{prime_list}} (Number)               -> 10 (number of top strategies to show)

-- =======================================================================
-- PNL Window Calibration Parameters (40 คะแนน)
-- =======================================================================
-- {{pnl_kpi}} (Number)                  -> 1000 (base PNL KPI)
-- {{pnl_score_72h}} (Number)            -> 5 (72H window score)
-- {{pnl_score_48h}} (Number)            -> 10 (48H window score)
-- {{pnl_score_24h}} (Number)            -> 15 (24H window score)
-- {{pnl_score_12h}} (Number)            -> 10 (12H window score)

-- =======================================================================
-- Winrate Window Consistency Calibration Parameters (30 คะแนน)
-- =======================================================================
-- {{winrate_score_72h}} (Number)        -> 8 (72H winrate score)
-- {{winrate_score_48h}} (Number)        -> 8 (48H winrate score)
-- {{winrate_score_24h}} (Number)        -> 8 (24H winrate score)
-- {{winrate_consistency_score}} (Number)-> 6 (Cross-window consistency score)

-- =======================================================================
-- Recent Performance Calibration Parameters (30 คะแนน)
-- =======================================================================
-- {{recent_performance_max_score}} (Number) -> 30 (Recent Performance max score)

WITH param_raw AS (
    SELECT
        COALESCE(NULLIF({{horizon_list}}, ''), '10min')                       AS horizon_raw,
        COALESCE(NULLIF(CAST({{max_loss_streak_cap}} AS text), ''), '4')::int AS max_loss_streak_cap,
        COALESCE(NULLIF(CAST({{payout}} AS text), ''), '0.8')::numeric        AS payout,
        COALESCE(NULLIF(CAST({{investment}} AS text), ''), '250')::numeric    AS investment,
        COALESCE(NULLIF(CAST({{reverse_enable}} AS text), ''), 'false')::boolean AS reverse_enable,
        COALESCE(NULLIF(CAST({{abs_pnl}} AS text), ''), 'false')::boolean        AS abs_pnl,
        COALESCE(NULLIF(CAST({{prime_list}} AS text), ''), '10')::int         AS prime_list,
        COALESCE(NULLIF(CAST({{pnl_kpi}} AS text), ''), '1000')::numeric      AS pnl_kpi,
        COALESCE(NULLIF(CAST({{pnl_score_72h}} AS text), ''), '5')::numeric   AS pnl_score_72h,
        COALESCE(NULLIF(CAST({{pnl_score_48h}} AS text), ''), '10')::numeric  AS pnl_score_48h,
        COALESCE(NULLIF(CAST({{pnl_score_24h}} AS text), ''), '15')::numeric  AS pnl_score_24h,
        COALESCE(NULLIF(CAST({{pnl_score_12h}} AS text), ''), '10')::numeric  AS pnl_score_12h,
        COALESCE(NULLIF(CAST({{winrate_score_72h}} AS text), ''), '8')::numeric   AS winrate_score_72h,
        COALESCE(NULLIF(CAST({{winrate_score_48h}} AS text), ''), '8')::numeric   AS winrate_score_48h,
        COALESCE(NULLIF(CAST({{winrate_score_24h}} AS text), ''), '8')::numeric   AS winrate_score_24h,
        COALESCE(NULLIF(CAST({{winrate_consistency_score}} AS text), ''), '6')::numeric AS winrate_consistency_score,
        COALESCE(NULLIF(CAST({{recent_performance_max_score}} AS text), ''), '30')::numeric AS recent_performance_max_score
),
params AS (
    SELECT
        CASE
            WHEN horizons IS NULL OR array_length(horizons, 1) = 0 THEN ARRAY['10min']::text[]
            ELSE horizons
        END                                           AS horizons,
        pr.max_loss_streak_cap,
        pr.payout,
        pr.investment,
        pr.reverse_enable,
        pr.abs_pnl,
        pr.prime_list,
        (CASE WHEN pr.reverse_enable THEN -1 ELSE 1 END)::numeric             AS direction,
        -- Gain calibration constants
        pr.pnl_kpi,
        2.5::numeric AS pnl_kpi_factor_72,
        2.0::numeric AS pnl_kpi_factor_48,
        1.0::numeric AS pnl_kpi_factor_24,
        0.7::numeric AS pnl_kpi_factor_12,
        pr.pnl_score_72h,
        pr.pnl_score_48h,
        pr.pnl_score_24h,
        pr.pnl_score_12h,
        pr.winrate_score_72h,
        pr.winrate_score_48h,
        pr.winrate_score_24h,
        pr.winrate_consistency_score,
        pr.recent_performance_max_score
    FROM (
        SELECT
            pr.*,
            (
                SELECT ARRAY(
                    SELECT TRIM(val)
                    FROM UNNEST(string_to_array(replace(pr.horizon_raw, ' ', ''), ',')) AS val
                    WHERE TRIM(val) <> ''
                )
            ) AS horizons
        FROM param_raw pr
    ) pr
),
base AS (
    SELECT strategy, action, symbol, entry_time, '10min'::text AS horizon, result_10min AS result
    FROM public.tradingviewdata
    UNION ALL
    SELECT strategy, action, symbol, entry_time, '30min'::text AS horizon, result_30min AS result
    FROM public.tradingviewdata
    UNION ALL
    SELECT strategy, action, symbol, entry_time, '60min'::text AS horizon, result_60min AS result
    FROM public.tradingviewdata
),
filtered AS (
    SELECT b.*
    FROM base b
    CROSS JOIN params p
    WHERE b.result IN ('WIN','LOSE')
      AND b.horizon = ANY (p.horizons)
      AND b.entry_time >= NOW() - INTERVAL '72 hour'
),
metrics_base AS (
    SELECT
        f.strategy,
        f.action,
        f.symbol,
        f.horizon,
        f.entry_time,
        f.result,
        CASE WHEN f.result = 'WIN' THEN p.payout * p.investment ELSE -p.investment END AS pnl_value,
        (CASE WHEN f.result = 'WIN' THEN 1 ELSE 0 END) AS is_win,
        (CASE WHEN f.result = 'LOSE' THEN 1 ELSE 0 END) AS is_loss,
        (CASE WHEN f.result = 'WIN' THEN p.payout * p.investment ELSE -p.investment END) * p.direction AS pnl_scoring,
        p.direction,
        p.max_loss_streak_cap,
        p.abs_pnl,
        p.reverse_enable,
        p.prime_list,
        p.pnl_kpi,
        p.pnl_kpi_factor_72,
        p.pnl_kpi_factor_48,
        p.pnl_kpi_factor_24,
        p.pnl_kpi_factor_12,
        p.pnl_score_72h,
        p.pnl_score_48h,
        p.pnl_score_24h,
        p.pnl_score_12h,
        p.winrate_score_72h,
        p.winrate_score_48h,
        p.winrate_score_24h,
        p.winrate_consistency_score,
        p.recent_performance_max_score
    FROM filtered f
    CROSS JOIN params p
),
agg_windows AS (
    SELECT
        strategy,
        action,
        symbol,
        horizon,
        MAX(direction) AS direction,
        MAX(max_loss_streak_cap) AS max_loss_streak_cap,
        BOOL_OR(abs_pnl) AS abs_pnl,
        BOOL_OR(reverse_enable) AS reverse_enable,
        MAX(prime_list) AS prime_list,
        MAX(pnl_kpi) AS pnl_kpi,
        MAX(p.pnl_kpi_factor_72) AS pnl_kpi_factor_72,
        MAX(p.pnl_kpi_factor_48) AS pnl_kpi_factor_48,
        MAX(p.pnl_kpi_factor_24) AS pnl_kpi_factor_24,
        MAX(p.pnl_kpi_factor_12) AS pnl_kpi_factor_12,
        MAX(p.pnl_score_72h) AS pnl_score_72h,
        MAX(p.pnl_score_48h) AS pnl_score_48h,
        MAX(p.pnl_score_24h) AS pnl_score_24h,
        MAX(p.pnl_score_12h) AS pnl_score_12h,
        MAX(p.winrate_score_72h) AS winrate_score_72h,
        MAX(p.winrate_score_48h) AS winrate_score_48h,
        MAX(p.winrate_score_24h) AS winrate_score_24h,
        MAX(p.winrate_consistency_score) AS winrate_consistency_score,
        MAX(p.recent_performance_max_score) AS recent_performance_max_score,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hour') AS trades_24h,
        SUM(is_win) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hour') AS wins_24h,
        SUM(is_loss) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hour') AS losses_24h,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hour') AS trades_48h,
        SUM(is_win) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hour') AS wins_48h,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hour') AS trades_72h,
        SUM(is_win) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hour') AS wins_72h,
        SUM(pnl_value) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hour') AS pnl_72h_raw,
        SUM(pnl_value) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hour') AS pnl_48h_raw,
        SUM(pnl_value) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hour') AS pnl_24h_raw,
        SUM(pnl_value) FILTER (WHERE entry_time >= NOW() - INTERVAL '12 hour') AS pnl_12h_raw,
        SUM(pnl_value) FILTER (WHERE entry_time >= NOW() - INTERVAL '6 hour')  AS pnl_6h_raw,
        SUM(pnl_value) FILTER (WHERE entry_time >= NOW() - INTERVAL '3 hour')  AS pnl_3h_raw,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hour') AS pnl_72h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hour') AS pnl_48h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hour') AS pnl_24h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '12 hour') AS pnl_12h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '6 hour')  AS pnl_6h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '5 hour')  AS pnl_5h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '4 hour')  AS pnl_4h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '3 hour')  AS pnl_3h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '2 hour')  AS pnl_2h_scoring,
        SUM(pnl_scoring) FILTER (WHERE entry_time >= NOW() - INTERVAL '1 hour')  AS pnl_1h_scoring
    FROM metrics_base p
    GROUP BY strategy, action, symbol, horizon
),
streak_base AS (
    SELECT
        strategy,
        action,
        symbol,
        horizon,
        entry_time,
        result
    FROM filtered
    WHERE entry_time >= NOW() - INTERVAL '24 hour'
),
streak_groups AS (
    SELECT
        sb.*,
        ROW_NUMBER() OVER (PARTITION BY strategy, action, symbol, horizon ORDER BY entry_time)
        - ROW_NUMBER() OVER (PARTITION BY strategy, action, symbol, horizon, result ORDER BY entry_time) AS grp_id
    FROM streak_base sb
),
streak_summary AS (
    SELECT
        strategy,
        action,
        symbol,
        horizon,
        COALESCE(MAX(streak_len) FILTER (WHERE result = 'WIN'), 0)  AS max_win_streak_24h,
        COALESCE(MAX(streak_len) FILTER (WHERE result = 'LOSE'), 0) AS max_loss_streak_24h
    FROM (
        SELECT
            strategy,
            action,
            symbol,
            horizon,
            result,
            grp_id,
            COUNT(*) AS streak_len
        FROM streak_groups
        GROUP BY strategy, action, symbol, horizon, result, grp_id
    ) g
    GROUP BY strategy, action, symbol, horizon
),
recent_raw AS (
    SELECT
        base.*,
        CASE
            WHEN base.pnl_1h > 0 THEN
                  GREATEST(0::numeric, base.pnl_1h - base.prev_1h_total) * 5
                + GREATEST(0::numeric, base.pnl_1h - base.prev_2h_avg)   * 4
                + GREATEST(0::numeric, base.pnl_1h - base.prev_3h_avg)   * 3
                + GREATEST(0::numeric, base.pnl_1h - base.prev_4h_avg)   * 2
                + GREATEST(0::numeric, base.pnl_1h - base.prev_5h_avg)   * 1
            ELSE 0::numeric
        END AS recent_score_raw
    FROM (
        SELECT
            aw.*,
            COALESCE(aw.pnl_1h_scoring, 0) AS pnl_1h,
            -- Previous hour absolute PnL (last 2h window minus latest 1h)
            COALESCE(aw.pnl_2h_scoring, COALESCE(aw.pnl_1h_scoring, 0))
              - COALESCE(aw.pnl_1h_scoring, 0) AS prev_1h_total,
            -- Average PnL per hour for the prior 2,3,4,5 hours (excluding the latest 1h)
            (COALESCE(aw.pnl_3h_scoring, COALESCE(aw.pnl_1h_scoring, 0))
              - COALESCE(aw.pnl_1h_scoring, 0)) / 2::numeric AS prev_2h_avg,
            (COALESCE(aw.pnl_4h_scoring, COALESCE(aw.pnl_1h_scoring, 0))
              - COALESCE(aw.pnl_1h_scoring, 0)) / 3::numeric AS prev_3h_avg,
            (COALESCE(aw.pnl_5h_scoring, COALESCE(aw.pnl_1h_scoring, 0))
              - COALESCE(aw.pnl_1h_scoring, 0)) / 4::numeric AS prev_4h_avg,
            (COALESCE(aw.pnl_6h_scoring, COALESCE(aw.pnl_1h_scoring, 0))
              - COALESCE(aw.pnl_1h_scoring, 0)) / 5::numeric AS prev_5h_avg
        FROM agg_windows aw
    ) base
),
recent_stats AS (
    SELECT
        COALESCE(AVG(recent_score_raw), 0) AS mean_recent,
        COALESCE(STDDEV_POP(recent_score_raw), 0) AS std_recent
    FROM recent_raw
),
scored AS (
    SELECT
        rr.strategy,
        rr.action,
        rr.symbol,
        rr.horizon,
        rr.direction,
        rr.abs_pnl,
        rr.reverse_enable,
        rr.prime_list,
        rr.max_loss_streak_cap,
        rr.pnl_kpi,
        rr.pnl_kpi_factor_72,
        rr.pnl_kpi_factor_48,
        rr.pnl_kpi_factor_24,
        rr.pnl_kpi_factor_12,
        rr.pnl_score_72h,
        rr.pnl_score_48h,
        rr.pnl_score_24h,
        rr.pnl_score_12h,
        rr.winrate_score_72h,
        rr.winrate_score_48h,
        rr.winrate_score_24h,
        rr.winrate_consistency_score,
        rr.trades_24h,
        rr.wins_24h,
        rr.losses_24h,
        rr.trades_48h,
        rr.wins_48h,
        rr.trades_72h,
        rr.wins_72h,
        rr.pnl_72h_raw,
        rr.pnl_48h_raw,
        rr.pnl_24h_raw,
        rr.pnl_12h_raw,
        rr.pnl_6h_raw,
        rr.pnl_3h_raw,
        rr.pnl_72h_scoring,
        rr.pnl_48h_scoring,
        rr.pnl_24h_scoring,
        rr.pnl_12h_scoring,
        rr.pnl_6h_scoring,
        rr.pnl_5h_scoring,
        rr.pnl_4h_scoring,
        rr.pnl_3h_scoring,
        rr.pnl_2h_scoring,
        rr.pnl_1h_scoring,
        rs.mean_recent,
        rs.std_recent,
        rr.recent_score_raw,
        rr.recent_performance_max_score
    FROM recent_raw rr
    CROSS JOIN recent_stats rs
),
score_calc AS (
    SELECT
        s.*,
        (s.pnl_kpi * s.pnl_kpi_factor_72) AS pnl_kpi_72,
        (s.pnl_kpi * s.pnl_kpi_factor_48) AS pnl_kpi_48,
        (s.pnl_kpi * s.pnl_kpi_factor_24) AS pnl_kpi_24,
        (s.pnl_kpi * s.pnl_kpi_factor_12) AS pnl_kpi_12,
        COALESCE(NULLIF(s.mean_recent + s.std_recent, 0), NULLIF(s.mean_recent, 0), 1) AS recent_kpi,
        CASE WHEN s.trades_24h > 0 THEN s.wins_24h::numeric / s.trades_24h ELSE 0 END AS winrate_24h,
        CASE WHEN s.trades_48h > 0 THEN s.wins_48h::numeric / s.trades_48h ELSE 0 END AS winrate_48h,
        CASE WHEN s.trades_72h > 0 THEN s.wins_72h::numeric / s.trades_72h ELSE 0 END AS winrate_72h
    FROM scored s
),
score_final AS (
    SELECT
        sc.strategy,
        sc.action,
        sc.symbol,
        sc.horizon,
        sc.abs_pnl,
        sc.reverse_enable,
        sc.prime_list,
        sc.max_loss_streak_cap,
        sc.trades_24h,
        sc.wins_24h,
        sc.losses_24h,
        sc.pnl_24h_raw,
        sc.pnl_12h_raw,
        sc.pnl_6h_raw,
        sc.pnl_3h_raw,
        sc.winrate_24h,
        sc.winrate_48h,
        sc.winrate_72h,
        sc.pnl_72h_scoring,
        sc.pnl_48h_scoring,
        sc.pnl_24h_scoring,
        sc.pnl_12h_scoring,
        sc.recent_score_raw,
        sc.recent_kpi,
        sc.recent_performance_max_score,
        sc.pnl_score_72h,
        sc.pnl_score_48h,
        sc.pnl_score_24h,
        sc.pnl_score_12h,
        sc.winrate_score_72h,
        sc.winrate_score_48h,
        sc.winrate_score_24h,
        sc.winrate_consistency_score,
        sc.pnl_kpi_72,
        sc.pnl_kpi_48,
        sc.pnl_kpi_24,
        sc.pnl_kpi_12,
        -- PnL score components (clamped between 0 and weight)
        LEAST(sc.pnl_score_72h, GREATEST(0::numeric, COALESCE(sc.pnl_72h_scoring, 0) / NULLIF(sc.pnl_kpi_72, 0) * sc.pnl_score_72h)) AS score_pnl_72,
        LEAST(sc.pnl_score_48h, GREATEST(0::numeric, COALESCE(sc.pnl_48h_scoring, 0) / NULLIF(sc.pnl_kpi_48, 0) * sc.pnl_score_48h)) AS score_pnl_48,
        LEAST(sc.pnl_score_24h, GREATEST(0::numeric, COALESCE(sc.pnl_24h_scoring, 0) / NULLIF(sc.pnl_kpi_24, 0) * sc.pnl_score_24h)) AS score_pnl_24,
        LEAST(sc.pnl_score_12h, GREATEST(0::numeric, COALESCE(sc.pnl_12h_scoring, 0) / NULLIF(sc.pnl_kpi_12, 0) * sc.pnl_score_12h)) AS score_pnl_12,
        -- Win-rate adjusted for reverse mode
        CASE WHEN sc.reverse_enable THEN 1 - sc.winrate_24h ELSE sc.winrate_24h END AS winrate_24h_adj,
        CASE WHEN sc.reverse_enable THEN 1 - sc.winrate_48h ELSE sc.winrate_48h END AS winrate_48h_adj,
        CASE WHEN sc.reverse_enable THEN 1 - sc.winrate_72h ELSE sc.winrate_72h END AS winrate_72h_adj
    FROM score_calc sc
),
score_compiled AS (
    SELECT
        sf.strategy,
        sf.action,
        sf.symbol,
        sf.horizon,
        sf.abs_pnl,
        sf.reverse_enable,
        sf.prime_list,
        sf.max_loss_streak_cap,
        sf.trades_24h,
        sf.wins_24h,
        sf.losses_24h,
        sf.pnl_24h_raw,
        sf.pnl_12h_raw,
        sf.pnl_6h_raw,
        sf.pnl_3h_raw,
        sf.winrate_24h,
        sf.winrate_48h,
        sf.winrate_72h,
        sf.score_pnl_72,
        sf.score_pnl_48,
        sf.score_pnl_24,
        sf.score_pnl_12,
        sf.recent_score_raw,
        sf.recent_kpi,
        sf.recent_performance_max_score,
        sf.winrate_score_72h,
        sf.winrate_score_48h,
        sf.winrate_score_24h,
        sf.winrate_consistency_score,
        sf.winrate_24h_adj,
        sf.winrate_48h_adj,
        sf.winrate_72h_adj,
        LEAST(sf.winrate_score_72h, GREATEST(0::numeric, (sf.winrate_72h_adj - 0.55) * sf.winrate_score_72h / 0.35)) AS score_wr_72,
        LEAST(sf.winrate_score_48h, GREATEST(0::numeric, (sf.winrate_48h_adj - 0.55) * sf.winrate_score_48h / 0.35)) AS score_wr_48,
        LEAST(sf.winrate_score_24h, GREATEST(0::numeric, (sf.winrate_24h_adj - 0.55) * sf.winrate_score_24h / 0.35)) AS score_wr_24,
        LEAST(sf.winrate_consistency_score, GREATEST(0::numeric,
            sf.winrate_consistency_score - (ABS((sf.winrate_24h_adj - sf.winrate_72h_adj) + (sf.winrate_48h_adj - sf.winrate_72h_adj))
            * sf.winrate_consistency_score / 30))) AS score_wr_cross
    FROM score_final sf
),
score_totals AS (
    SELECT
        sc.strategy,
        sc.action,
        sc.symbol,
        sc.horizon,
        sc.abs_pnl,
        sc.reverse_enable,
        sc.max_loss_streak_cap,
        sc.trades_24h,
        sc.wins_24h,
        sc.losses_24h,
        sc.pnl_24h_raw,
        sc.pnl_12h_raw,
        sc.pnl_6h_raw,
        sc.pnl_3h_raw,
        sc.winrate_24h,
        sc.score_pnl_72,
        sc.score_pnl_48,
        sc.score_pnl_24,
        sc.score_pnl_12,
        sc.recent_score_raw,
        sc.recent_kpi,
        sc.score_wr_72,
        sc.score_wr_48,
        sc.score_wr_24,
        sc.score_wr_cross,
        (sc.score_pnl_72 + sc.score_pnl_48 + sc.score_pnl_24 + sc.score_pnl_12) AS pnl_score,
        (sc.score_wr_72 + sc.score_wr_48 + sc.score_wr_24 + sc.score_wr_cross) AS win_con_score,
        LEAST(sc.recent_performance_max_score,
              GREATEST(0::numeric, sc.recent_score_raw / NULLIF(sc.recent_kpi, 0) * sc.recent_performance_max_score)) AS perf_score
    FROM score_compiled sc
),
joined AS (
    SELECT
        st.strategy,
        st.action,
        st.symbol,
        st.horizon,
        st.abs_pnl,
        st.reverse_enable,
        st.max_loss_streak_cap,
        st.trades_24h,
        st.wins_24h,
        st.losses_24h,
        st.pnl_24h_raw,
        st.pnl_12h_raw,
        st.pnl_6h_raw,
        st.pnl_3h_raw,
        st.winrate_24h,
        st.pnl_score,
        st.win_con_score,
        st.perf_score,
        (st.pnl_score + st.win_con_score + st.perf_score) AS total_score,
        ss.max_win_streak_24h,
        ss.max_loss_streak_24h
    FROM score_totals st
    LEFT JOIN streak_summary ss
        ON st.strategy = ss.strategy
       AND st.action = ss.action
       AND st.symbol = ss.symbol
       AND st.horizon = ss.horizon
)
SELECT
    j.strategy,
    j.action,
    j.reverse_enable AS reverse,
    j.symbol,
    j.horizon,
    j.trades_24h AS "24h_totaltrade",
    (j.winrate_24h * 100)::numeric AS "24h_winrate",
    COALESCE(j.max_win_streak_24h, 0) AS "24h_max_win_streak",
    COALESCE(j.max_loss_streak_24h, 0) AS "24h_max_lose_streak",
    CASE WHEN j.abs_pnl THEN ABS(COALESCE(j.pnl_24h_raw, 0)) ELSE COALESCE(j.pnl_24h_raw, 0) END AS "24h_pnl",
    CASE WHEN j.abs_pnl THEN ABS(COALESCE(j.pnl_12h_raw, 0)) ELSE COALESCE(j.pnl_12h_raw, 0) END AS "12h_pnl",
    CASE WHEN j.abs_pnl THEN ABS(COALESCE(j.pnl_6h_raw, 0)) ELSE COALESCE(j.pnl_6h_raw, 0) END AS "6h_pnl",
    CASE WHEN j.abs_pnl THEN ABS(COALESCE(j.pnl_3h_raw, 0)) ELSE COALESCE(j.pnl_3h_raw, 0) END AS "3h_pnl",
    ROUND(j.pnl_score, 2) AS pnl_score40,
    ROUND(j.win_con_score, 2) AS win_con_score30,
    ROUND(j.perf_score, 2) AS perf_score30,
    ROUND(j.total_score, 2) AS total_score100
FROM joined j
WHERE j.trades_24h > 0
  AND COALESCE(j.max_loss_streak_24h, 0) <= j.max_loss_streak_cap
ORDER BY total_score100 DESC, "6h_pnl" DESC, "12h_pnl" DESC
LIMIT (SELECT prime_list FROM params);
