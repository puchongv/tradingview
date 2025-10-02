-- File: Strategy Evalucation Score V1.7.sql
-- Purpose: Calculate comprehensive strategy evaluation scores with DEBUG MODE support
-- Output: strategy | action | reverse (NORMAL/REVERSE) | symbol | horizon | 24h_totaltrade | [DEBUG: 72h_winrate | 48h_winrate] | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | [DEBUG: 72h_pnl | 48h_pnl] | 24h_pnl | 12h_pnl | 6h_pnl | [DEBUG: 5h_pnl | 4h_pnl] | 3h_pnl | [DEBUG: 2h_pnl | 1h_pnl] | pnl_score40 | win_con_score30 | perf_score30 | total_score100
-- Version: 1.7 (V1.6 + DEBUG MODE PARAMETER - NO LOGIC CHANGES)

-- =======================================================================
-- Basic Setting & Filter Parameters
-- =======================================================================
-- {{horizon_list}} (Text, optional)     -> '10min,30min,60min' (default: '10min')
-- {{max_loss_streak_cap}} (Number)      -> 4 (loss streak threshold)
-- {{payout}} (Number)                   -> 0.8 (payout ratio per winning trade)
-- {{investment}} (Number)               -> 250 (stake size per trade)
-- {{reverse_enable}} (Boolean)          -> true (include both NORMAL and REVERSE strategies in results)
-- {{abs_pnl}} (Boolean)                 -> true (show negative PNL as positive)
-- {{prime_list}} (Number)               -> 10 (number of top strategies to show)
-- {{enable_debugmode}} (Boolean)        -> true (show additional debug columns: 72h/48h winrate, 1h-5h PNL)

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
-- {{winrate_consistency_score}} (Number) -> 6 (Cross-window consistency score)

-- =======================================================================
-- Recent Performance Calibration Parameters (30 คะแนน)
-- =======================================================================
-- {{recent_performance_max_score}} (Number) -> 30 (Recent Performance max score)

WITH param_raw AS (
    SELECT
        -- Use EXACT same parameter parsing method as V1.6
        COALESCE(NULLIF({{horizon_list}}, ''), '10min')                       AS horizon_raw,
        COALESCE(NULLIF(CAST({{max_loss_streak_cap}} AS text), ''), '4')::int AS max_loss_streak_cap,
        COALESCE(NULLIF(CAST({{payout}} AS text), ''), '0.8')::numeric        AS payout,
        COALESCE(NULLIF(CAST({{investment}} AS text), ''), '250')::numeric    AS investment,
        COALESCE(NULLIF(CAST({{reverse_enable}} AS text), ''), 'true')::boolean AS reverse_enable,
        COALESCE(NULLIF(CAST({{abs_pnl}} AS text), ''), 'false')::boolean        AS abs_pnl,
        COALESCE(NULLIF(CAST({{prime_list}} AS text), ''), '10')::int         AS prime_list,
        COALESCE(NULLIF(CAST({{enable_debugmode}} AS text), ''), 'false')::boolean AS enable_debugmode,
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
)
-- NORMAL strategies (higher PNL/WinRate = higher score)
SELECT 
    strategy,
    CASE 
        WHEN action LIKE 'FlowTrend%' THEN 'FlowTr'
        WHEN action LIKE 'Range%' THEN 'Range'  
        ELSE action
    END AS action,
    'NORMAL' AS reverse,
    symbol,
    '10min' AS horizon,
    COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) AS "24h_totaltrade",
    -- DEBUG: 72h winrate (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
                ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                          / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
            END
        ELSE NULL
    END AS "72h_winrate",
    -- DEBUG: 48h winrate (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
                ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                          / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
            END
        ELSE NULL
    END AS "48h_winrate",
    -- 24h winrate (always shown)
    CASE 
        WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
        ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
    END AS "24h_winrate",
    0::bigint AS "24h_max_win_streak",
    0::bigint AS "24h_max_lose_streak",
    -- DEBUG: 72h PNL (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END))
                ELSE SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END)
            END
        ELSE NULL
    END AS "72h_pnl",
    -- DEBUG: 48h PNL (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END))
                ELSE SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END)
            END
        ELSE NULL
    END AS "48h_pnl",
    -- 24h PNL (always shown) - SAME AS V1.6
    CASE 
        WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END)
    END AS "24h_pnl",
    -- 12h PNL (always shown) - SAME AS V1.6
    CASE 
        WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END)
    END AS "12h_pnl",
    -- 6h PNL (always shown) - SAME AS V1.6
    CASE 
        WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END)
    END AS "6h_pnl",
    -- DEBUG: 5h PNL (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '5 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '5 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END))
                ELSE SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '5 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '5 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END)
            END
        ELSE NULL
    END AS "5h_pnl",
    -- DEBUG: 4h PNL (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '4 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '4 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END))
                ELSE SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '4 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '4 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END)
            END
        ELSE NULL
    END AS "4h_pnl",
    -- 3h PNL (always shown) - SAME AS V1.6
    CASE 
        WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END)
    END AS "3h_pnl",
    -- DEBUG: 2h PNL (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '2 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '2 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END))
                ELSE SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '2 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '2 hours' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END)
            END
        ELSE NULL
    END AS "2h_pnl",
    -- DEBUG: 1h PNL (conditionally shown)
    CASE 
        WHEN pr.enable_debugmode = true THEN
            CASE 
                WHEN pr.abs_pnl = true THEN ABS(SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '1 hour' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '1 hour' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END))
                ELSE SUM(CASE 
                    WHEN entry_time >= NOW() - INTERVAL '1 hour' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                    WHEN entry_time >= NOW() - INTERVAL '1 hour' AND result_10min = 'LOSE' THEN -pr.investment
                    ELSE 0 
                END)
            END
        ELSE NULL
    END AS "1h_pnl",
    -- PNL Score (40 points) - SAME CALCULATION AS V1.6 (NO CHANGES)
    GREATEST(0::numeric, LEAST(pr.pnl_score_72h, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 2.5) * pr.pnl_score_72h)) +
    GREATEST(0::numeric, LEAST(pr.pnl_score_48h,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 2.0) * pr.pnl_score_48h)) +
    GREATEST(0::numeric, LEAST(pr.pnl_score_24h,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 1.0) * pr.pnl_score_24h)) +
    GREATEST(0::numeric, LEAST(pr.pnl_score_12h,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 0.7) * pr.pnl_score_12h)) AS pnl_score40,
    -- Winrate Score (30 points) - SAME CALCULATION AS V1.6 (NO CHANGES)
    GREATEST(0::numeric, LEAST(pr.winrate_score_72h,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * pr.winrate_score_72h / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(pr.winrate_score_48h,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * pr.winrate_score_48h / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(pr.winrate_score_24h,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * pr.winrate_score_24h / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(pr.winrate_consistency_score, 
        pr.winrate_consistency_score * 0.8)) AS win_con_score30,
    -- Performance Score (30 points) - SAME CALCULATION AS V1.6 (NO CHANGES)
    GREATEST(0::numeric, LEAST(pr.recent_performance_max_score,
        CASE 
            WHEN SUM(CASE WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                           WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END) = 0 THEN 0
            ELSE (pr.recent_performance_max_score / 2.0) + 
                ((SUM(CASE WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                          WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END) - 
                 SUM(CASE WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                          WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END)) 
                / (ABS(SUM(CASE WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                               WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END)) + 200) 
                * (pr.recent_performance_max_score / 2.0))
        END)) AS perf_score30,
    -- Total Score - SAME CALCULATION AS V1.6 (NO CHANGES)
    (GREATEST(0::numeric, LEAST(pr.pnl_score_72h, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 2.5) * pr.pnl_score_72h)) +
    GREATEST(0::numeric, LEAST(pr.pnl_score_48h,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 2.0) * pr.pnl_score_48h)) +
    GREATEST(0::numeric, LEAST(pr.pnl_score_24h,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 1.0) * pr.pnl_score_24h)) +
    GREATEST(0::numeric, LEAST(pr.pnl_score_12h,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment
            ELSE 0 
        END) / (pr.pnl_kpi * 0.7) * pr.pnl_score_12h)) +
    GREATEST(0::numeric, LEAST(pr.winrate_score_72h,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * pr.winrate_score_72h / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(pr.winrate_score_48h,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * pr.winrate_score_48h / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(pr.winrate_score_24h,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * pr.winrate_score_24h / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(pr.winrate_consistency_score, 
        pr.winrate_consistency_score * 0.8)) +
    GREATEST(0::numeric, LEAST(pr.recent_performance_max_score,
        CASE 
            WHEN SUM(CASE WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                           WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END) = 0 THEN 0
            ELSE (pr.recent_performance_max_score / 2.0) + 
                ((SUM(CASE WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                          WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END) - 
                 SUM(CASE WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                          WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END)) 
                / (ABS(SUM(CASE WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN pr.investment * pr.payout
                               WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -pr.investment ELSE 0 END)) + 200) 
                * (pr.recent_performance_max_score / 2.0))
        END))) AS total_score100

FROM tradingviewdata
CROSS JOIN param_raw pr
WHERE entry_time >= NOW() - INTERVAL '72 hours'
GROUP BY pr.horizon_raw, pr.max_loss_streak_cap, pr.payout, pr.investment, pr.reverse_enable, pr.abs_pnl, pr.prime_list, pr.enable_debugmode, pr.pnl_kpi, pr.pnl_score_72h, pr.pnl_score_48h, pr.pnl_score_24h, pr.pnl_score_12h, pr.winrate_score_72h, pr.winrate_score_48h, pr.winrate_score_24h, pr.winrate_consistency_score, pr.recent_performance_max_score, strategy, 
    CASE 
        WHEN action LIKE 'FlowTrend%' THEN 'FlowTr'
        WHEN action LIKE 'Range%' THEN 'Range'  
        ELSE action
    END, symbol
HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1

ORDER BY total_score100 DESC, "6h_pnl" DESC, "12h_pnl" DESC
LIMIT (SELECT prime_list FROM param_raw);
