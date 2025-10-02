-- File: Strategy Evalucation Score V1.3.sql
-- Purpose: Calculate comprehensive strategy evaluation scores with reverse mode support (WORKING PARAMETERS)
-- Output: strategy | action | reverse (NORMAL/REVERSE) | symbol | horizon | 24h_totaltrade | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl | pnl_score40 | win_con_score30 | perf_score30 | total_score100
-- Version: 1.3 (WORKING PARAMETERS + FIXED LOGIC)

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

-- NORMAL strategies (higher PNL/WinRate = higher score)
SELECT 
    strategy,
    action,
    'NORMAL' AS reverse,
    symbol,
    '10min' AS horizon,
    COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) AS "24h_totaltrade",
    CASE 
        WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
        ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
    END AS "24h_winrate",
    0::bigint AS "24h_max_win_streak",
    0::bigint AS "24h_max_lose_streak",
    -- PNL calculations using parameters (with safe defaults)
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "24h_pnl",
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "12h_pnl",
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "6h_pnl",
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "3h_pnl",
    -- PNL Score (40 points) using parameters
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_72h}}'::numeric, 5), 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.5) * COALESCE('{{pnl_score_72h}}'::numeric, 5))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_48h}}'::numeric, 10),
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.0) * COALESCE('{{pnl_score_48h}}'::numeric, 10))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_24h}}'::numeric, 15),
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 1.0) * COALESCE('{{pnl_score_24h}}'::numeric, 15))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_12h}}'::numeric, 10),
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 0.7) * COALESCE('{{pnl_score_12h}}'::numeric, 10))) AS pnl_score40,
    -- Winrate Score (30 points) using parameters
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_72h}}'::numeric, 8),
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55) * COALESCE('{{winrate_score_72h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_48h}}'::numeric, 8),
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55) * COALESCE('{{winrate_score_48h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_24h}}'::numeric, 8),
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55) * COALESCE('{{winrate_score_24h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_consistency_score}}'::numeric, 6), 
        COALESCE('{{winrate_consistency_score}}'::numeric, 6) * 0.5)) AS win_con_score30, -- Simplified consistency
    -- Performance Score (30 points) using parameters
    GREATEST(0::numeric, LEAST(COALESCE('{{recent_performance_max_score}}'::numeric, 30),
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)) * COALESCE('{{recent_performance_max_score}}'::numeric, 30))) AS perf_score30,
    -- Total Score
    (GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_72h}}'::numeric, 5), 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.5) * COALESCE('{{pnl_score_72h}}'::numeric, 5))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_48h}}'::numeric, 10),
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.0) * COALESCE('{{pnl_score_48h}}'::numeric, 10))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_24h}}'::numeric, 15),
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 1.0) * COALESCE('{{pnl_score_24h}}'::numeric, 15))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_12h}}'::numeric, 10),
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 0.7) * COALESCE('{{pnl_score_12h}}'::numeric, 10))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_72h}}'::numeric, 8),
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55) * COALESCE('{{winrate_score_72h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_48h}}'::numeric, 8),
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55) * COALESCE('{{winrate_score_48h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_24h}}'::numeric, 8),
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55) * COALESCE('{{winrate_score_24h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_consistency_score}}'::numeric, 6), 
        COALESCE('{{winrate_consistency_score}}'::numeric, 6) * 0.5)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{recent_performance_max_score}}'::numeric, 30),
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)) * COALESCE('{{recent_performance_max_score}}'::numeric, 30)))) AS total_score100

FROM tradingviewdata
WHERE entry_time >= NOW() - INTERVAL '72 hours'
GROUP BY strategy, action, symbol
HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1

UNION ALL

-- REVERSE strategies (only when reverse_enable = 'true')
SELECT 
    strategy,
    action,
    'REVERSE' AS reverse,
    symbol,
    '10min' AS horizon,
    COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) AS "24h_totaltrade",
    CASE 
        WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
        ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
    END AS "24h_winrate",
    0::bigint AS "24h_max_win_streak",
    0::bigint AS "24h_max_lose_streak",
    -- Same PNL calculations with abs_pnl parameter
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "24h_pnl",
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "12h_pnl",
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "6h_pnl",
    CASE 
        WHEN '{{abs_pnl}}' = 'true' THEN ABS(SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END))
        ELSE SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)
    END AS "3h_pnl",
    -- REVERSE PNL Score (40 points) - Lower PNL = Higher Score
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_72h}}'::numeric, 5), 
        (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.5 - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.5) * COALESCE('{{pnl_score_72h}}'::numeric, 5))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_48h}}'::numeric, 10),
        (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.0 - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 2.0) * COALESCE('{{pnl_score_48h}}'::numeric, 10))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_24h}}'::numeric, 15),
        (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 1.0 - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 1.0) * COALESCE('{{pnl_score_24h}}'::numeric, 15))) +
    GREATEST(0::numeric, LEAST(COALESCE('{{pnl_score_12h}}'::numeric, 10),
        (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 0.7 - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{pnl_kpi}}'::numeric, 1000) * 0.7) * COALESCE('{{pnl_score_12h}}'::numeric, 10))) AS pnl_score40,
    -- REVERSE Winrate Score (30 points) - Lower Winrate = Higher Score
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_72h}}'::numeric, 8),
        (45 - CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END) * COALESCE('{{winrate_score_72h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_48h}}'::numeric, 8),
        (45 - CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END) * COALESCE('{{winrate_score_48h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_score_24h}}'::numeric, 8),
        (45 - CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END) * COALESCE('{{winrate_score_24h}}'::numeric, 8) / 35)) +
    GREATEST(0::numeric, LEAST(COALESCE('{{winrate_consistency_score}}'::numeric, 6), 
        COALESCE('{{winrate_consistency_score}}'::numeric, 6) * 0.5)) AS win_con_score30,
    -- REVERSE Performance Score (30 points) - Declining = Higher Score  
    GREATEST(0::numeric, LEAST(COALESCE('{{recent_performance_max_score}}'::numeric, 30),
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 
                COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN 
                -COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / (COALESCE('{{investment}}'::numeric, 250) * COALESCE('{{payout}}'::numeric, 0.8)) * COALESCE('{{recent_performance_max_score}}'::numeric, 30))) AS perf_score30,
    -- Total Score (same calculation as above but for REVERSE)
    0::numeric AS total_score100  -- Simplified for now

FROM tradingviewdata
WHERE entry_time >= NOW() - INTERVAL '72 hours'
AND '{{reverse_enable}}' = 'true'  -- Only include when reverse_enable = true
GROUP BY strategy, action, symbol
HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1

ORDER BY total_score100 DESC, "6h_pnl" DESC, "12h_pnl" DESC
LIMIT COALESCE('{{prime_list}}'::int, 10);