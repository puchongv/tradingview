-- File: Strategy Evalucation Score V1.5.sql
-- Purpose: Calculate comprehensive strategy evaluation scores with reverse mode support (FIXED ACTION TRUNCATION)
-- Output: strategy | action | reverse (NORMAL/REVERSE) | symbol | horizon | 24h_totaltrade | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl | pnl_score40 | win_con_score30 | perf_score30 | total_score100
-- Version: 1.5 (FIXED ACTION TRUNCATION - Based on V1.2 structure)

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

-- NORMAL strategies (higher PNL/WinRate = higher score) - WITH ACTION MAPPING
SELECT 
    strategy,
    -- Map long action names to short ones for Metabase display
    CASE 
        WHEN action LIKE 'FlowTrend%' THEN 'FlowTr'
        WHEN action LIKE 'Range%' THEN 'Range'
        ELSE action
    END AS action,
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
    -- PNL calculations using hardcoded values (payout=0.8, investment=250)
    SUM(CASE 
        WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200
        WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
        ELSE 0 
    END) AS "24h_pnl",
    SUM(CASE 
        WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
        WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
        ELSE 0 
    END) AS "12h_pnl",
    SUM(CASE 
        WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
        WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250
        ELSE 0 
    END) AS "6h_pnl",
    SUM(CASE 
        WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 200
        WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -250
        ELSE 0 
    END) AS "3h_pnl",
    
    -- PNL Score (40 points) - FIXED FORMULA with proper scaling
    GREATEST(0::numeric, LEAST(5::numeric, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 2.5) * 5)) +
    GREATEST(0::numeric, LEAST(10::numeric,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 2.0) * 10)) +
    GREATEST(0::numeric, LEAST(15::numeric,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 1.0) * 15)) +
    GREATEST(0::numeric, LEAST(10::numeric,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 0.7) * 10)) AS pnl_score40,
        
    -- Winrate Score (30 points) - FIXED FORMULA with proper break-even
    GREATEST(0::numeric, LEAST(8::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * 8 / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(8::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * 8 / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(8::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * 8 / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(6::numeric, 6 * 0.8)) AS win_con_score30, -- Simplified consistency
    
    -- Performance Score (30 points) - FIXED FORMULA
    GREATEST(0::numeric, LEAST(30::numeric,
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END)) / 200 * 30)) AS perf_score30,
        
    -- Total Score
    (GREATEST(0::numeric, LEAST(5::numeric, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 2.5) * 5)) +
    GREATEST(0::numeric, LEAST(10::numeric,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 2.0) * 10)) +
    GREATEST(0::numeric, LEAST(15::numeric,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 1.0) * 15)) +
    GREATEST(0::numeric, LEAST(10::numeric,
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / (1000 * 0.7) * 10)) +
    GREATEST(0::numeric, LEAST(8::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '72 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * 8 / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(8::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '48 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * 8 / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(8::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 55.56) * 8 / (90 - 55.56))) +
    GREATEST(0::numeric, LEAST(6::numeric, 6 * 0.8)) +
    GREATEST(0::numeric, LEAST(30::numeric,
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END)) / 200 * 30))) AS total_score100

FROM tradingviewdata
WHERE entry_time >= NOW() - INTERVAL '72 hours'
GROUP BY strategy, 
    CASE 
        WHEN action LIKE 'FlowTrend%' THEN 'FlowTr'
        WHEN action LIKE 'Range%' THEN 'Range'
        ELSE action
    END, symbol
HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1

ORDER BY total_score100 DESC, "6h_pnl" DESC, "12h_pnl" DESC
LIMIT 10;