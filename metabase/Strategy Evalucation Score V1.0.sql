-- File: Strategy Evalucation Score V1.0.sql
-- Purpose: Calculate comprehensive strategy evaluation scores with reverse mode support
-- Output: strategy | action | reverse (NORMAL/REVERSE) | symbol | horizon | 24h_totaltrade | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl | pnl_score40 | win_con_score30 | perf_score30 | total_score100
-- Version: 1.0

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

WITH config AS (
    SELECT
        -- Basic Settings
        COALESCE(NULLIF('{{horizon_list}}', ''), '10min') AS horizon_list,
        COALESCE(CASE WHEN '{{max_loss_streak_cap}}' = '' THEN NULL ELSE '{{max_loss_streak_cap}}'::int END, 4) AS max_loss_streak_cap,
        COALESCE(CASE WHEN '{{payout}}' = '' THEN NULL ELSE '{{payout}}'::numeric END, 0.8) AS payout,
        COALESCE(CASE WHEN '{{investment}}' = '' THEN NULL ELSE '{{investment}}'::numeric END, 250) AS investment,
        COALESCE(CASE WHEN '{{reverse_enable}}' = '' THEN NULL ELSE '{{reverse_enable}}'::boolean END, true) AS reverse_enable,
        COALESCE(CASE WHEN '{{abs_pnl}}' = '' THEN NULL ELSE '{{abs_pnl}}'::boolean END, true) AS abs_pnl,
        COALESCE(CASE WHEN '{{prime_list}}' = '' THEN NULL ELSE '{{prime_list}}'::int END, 10) AS prime_list,
        
        -- PNL Window Calibration
        COALESCE(CASE WHEN '{{pnl_kpi}}' = '' THEN NULL ELSE '{{pnl_kpi}}'::numeric END, 1000) AS pnl_kpi,
        COALESCE(CASE WHEN '{{pnl_score_72h}}' = '' THEN NULL ELSE '{{pnl_score_72h}}'::int END, 5) AS pnl_score_72h,
        COALESCE(CASE WHEN '{{pnl_score_48h}}' = '' THEN NULL ELSE '{{pnl_score_48h}}'::int END, 10) AS pnl_score_48h,
        COALESCE(CASE WHEN '{{pnl_score_24h}}' = '' THEN NULL ELSE '{{pnl_score_24h}}'::int END, 15) AS pnl_score_24h,
        COALESCE(CASE WHEN '{{pnl_score_12h}}' = '' THEN NULL ELSE '{{pnl_score_12h}}'::int END, 10) AS pnl_score_12h,
        
        -- Winrate Window Calibration
        COALESCE(CASE WHEN '{{winrate_score_72h}}' = '' THEN NULL ELSE '{{winrate_score_72h}}'::int END, 8) AS winrate_score_72h,
        COALESCE(CASE WHEN '{{winrate_score_48h}}' = '' THEN NULL ELSE '{{winrate_score_48h}}'::int END, 8) AS winrate_score_48h,
        COALESCE(CASE WHEN '{{winrate_score_24h}}' = '' THEN NULL ELSE '{{winrate_score_24h}}'::int END, 8) AS winrate_score_24h,
        COALESCE(CASE WHEN '{{winrate_consistency_score}}' = '' THEN NULL ELSE '{{winrate_consistency_score}}'::int END, 6) AS winrate_consistency_score,
        
        -- Recent Performance Calibration
        COALESCE(CASE WHEN '{{recent_performance_max_score}}' = '' THEN NULL ELSE '{{recent_performance_max_score}}'::int END, 30) AS recent_performance_max_score
),
horizon_list AS (
    SELECT DISTINCT TRIM(val) AS horizon
    FROM (
        SELECT UNNEST(string_to_array((SELECT horizon_list FROM config), ',')) AS val
    ) raw
    WHERE TRIM(val) IN ('10min', '30min', '60min')
),
base_data AS (
    SELECT 
        strategy,
        action,
        symbol,
        tf,
        entry_time,
        entry_price,
        CASE 
            WHEN '10min' IN (SELECT horizon FROM horizon_list) THEN '10min'
            WHEN '30min' IN (SELECT horizon FROM horizon_list) THEN '30min'
            WHEN '60min' IN (SELECT horizon FROM horizon_list) THEN '60min'
        END AS horizon,
        CASE 
            WHEN '10min' IN (SELECT horizon FROM horizon_list) THEN result_10min
            WHEN '30min' IN (SELECT horizon FROM horizon_list) THEN result_30min
            WHEN '60min' IN (SELECT horizon FROM horizon_list) THEN result_60min
        END AS result
    FROM tradingviewdata
    WHERE entry_time >= NOW() - INTERVAL '72 hours'
    AND (
        ('10min' IN (SELECT horizon FROM horizon_list) AND result_10min IN ('WIN', 'LOSE')) OR
        ('30min' IN (SELECT horizon FROM horizon_list) AND result_30min IN ('WIN', 'LOSE')) OR  
        ('60min' IN (SELECT horizon FROM horizon_list) AND result_60min IN ('WIN', 'LOSE'))
    )
),
-- Calculate PNL for each trade
trades_with_pnl AS (
    SELECT 
        bd.*,
        c.payout,
        c.investment,
        CASE 
            WHEN bd.result = 'WIN' THEN c.investment * c.payout
            WHEN bd.result = 'LOSE' THEN -c.investment
            ELSE 0
        END AS trade_pnl
    FROM base_data bd
    CROSS JOIN config c
),
-- Calculate hourly PNL for Recent Performance Score
hourly_pnl AS (
    SELECT 
        strategy,
        action,
        symbol,
        horizon,
        DATE_TRUNC('hour', entry_time) AS hour_bucket,
        SUM(trade_pnl) AS hour_pnl,
        COUNT(*) AS hour_trades,
        COUNT(*) FILTER (WHERE result = 'WIN') AS hour_wins,
        COUNT(*) FILTER (WHERE result = 'LOSE') AS hour_losses
    FROM trades_with_pnl
    GROUP BY strategy, action, symbol, horizon, DATE_TRUNC('hour', entry_time)
),
-- Calculate cumulative PNL
hourly_cumulative AS (
    SELECT 
        *,
        SUM(hour_pnl) OVER (
            PARTITION BY strategy, action, symbol, horizon
            ORDER BY hour_bucket
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_pnl
    FROM hourly_pnl
    WHERE hour_bucket >= NOW() - INTERVAL '6 hours'
),
-- Calculate Recent Performance using PNL1H - PNL6H
recent_performance_data AS (
    SELECT 
        strategy,
        action,
        symbol,
        horizon,
        hour_bucket,
        cumulative_pnl,
        ROW_NUMBER() OVER (
            PARTITION BY strategy, action, symbol, horizon
            ORDER BY hour_bucket DESC
        ) AS hour_rank
    FROM hourly_cumulative
),
recent_performance_scores AS (
    SELECT 
        strategy,
        action,
        symbol,
        horizon,
        MAX(CASE WHEN hour_rank = 1 THEN cumulative_pnl END) AS pnl_1h,
        MAX(CASE WHEN hour_rank = 2 THEN cumulative_pnl END) AS pnl_2h,
        MAX(CASE WHEN hour_rank = 3 THEN cumulative_pnl END) AS pnl_3h,
        MAX(CASE WHEN hour_rank = 4 THEN cumulative_pnl END) AS pnl_4h,
        MAX(CASE WHEN hour_rank = 5 THEN cumulative_pnl END) AS pnl_5h,
        MAX(CASE WHEN hour_rank = 6 THEN cumulative_pnl END) AS pnl_6h
    FROM recent_performance_data
    GROUP BY strategy, action, symbol, horizon
),
recent_performance_raw AS (
    SELECT 
        *,
        GREATEST(0,
            5 * GREATEST(0, COALESCE(pnl_1h, 0) - COALESCE(pnl_2h, 0)) +
            4 * GREATEST(0, COALESCE(pnl_1h, 0) - COALESCE(pnl_3h, 0)) +
            3 * GREATEST(0, COALESCE(pnl_1h, 0) - COALESCE(pnl_4h, 0)) +
            2 * GREATEST(0, COALESCE(pnl_1h, 0) - COALESCE(pnl_5h, 0)) +
            1 * GREATEST(0, COALESCE(pnl_1h, 0) - COALESCE(pnl_6h, 0))
        ) AS recent_performance_raw
    FROM recent_performance_scores
),
-- Calculate streaks for 24H period - Step 1: Mark streak changes
streak_changes AS (
    SELECT 
        strategy,
        action,  
        symbol,
        horizon,
        entry_time,
        result,
        trade_pnl,
        LAG(result, 1, result) OVER (PARTITION BY strategy, action, symbol, horizon ORDER BY entry_time) AS prev_result,
        CASE WHEN result <> LAG(result, 1, result) OVER (PARTITION BY strategy, action, symbol, horizon ORDER BY entry_time) THEN 1 ELSE 0 END AS streak_change
    FROM trades_with_pnl  
    WHERE entry_time >= NOW() - INTERVAL '24 hours'
),
-- Step 2: Create streak groups
streak_analysis AS (
    SELECT 
        *,
        SUM(streak_change) OVER (PARTITION BY strategy, action, symbol, horizon ORDER BY entry_time) AS streak_group
    FROM streak_changes
),
-- Calculate max streaks
max_streaks AS (
    SELECT
        strategy,
        action,
        symbol, 
        horizon,
        COALESCE(MAX(CASE WHEN result = 'WIN' THEN streak_length END), 0) AS max_win_streak,
        COALESCE(MAX(CASE WHEN result = 'LOSE' THEN streak_length END), 0) AS max_lose_streak
    FROM (
        SELECT
            strategy,
            action,
            symbol,
            horizon,
            result,
            streak_group,
            COUNT(*) AS streak_length
        FROM streak_analysis
        GROUP BY strategy, action, symbol, horizon, result, streak_group
    ) streaks
    GROUP BY strategy, action, symbol, horizon
),
-- Main statistics calculation
strategy_stats AS (
    SELECT 
        twp.strategy,
        twp.action,
        twp.symbol,
        twp.horizon,
        
        -- 24H Statistics  
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours') AS h24_total_trades,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours' AND twp.result = 'WIN') AS h24_wins,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours' AND twp.result = 'LOSE') AS h24_losses,
        CASE 
            WHEN COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours') = 0 THEN 0
            ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours' AND twp.result = 'WIN')::numeric 
                      / COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours'), 1)
        END AS h24_winrate,
        SUM(twp.trade_pnl) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours') AS h24_pnl,
        
        -- 12H Statistics
        SUM(twp.trade_pnl) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '12 hours') AS h12_pnl,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '12 hours' AND twp.result = 'WIN') AS h12_wins,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '12 hours') AS h12_total,
        
        -- 6H Statistics  
        SUM(twp.trade_pnl) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '6 hours') AS h6_pnl,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '6 hours' AND twp.result = 'WIN') AS h6_wins,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '6 hours') AS h6_total,
        
        -- 3H Statistics
        SUM(twp.trade_pnl) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '3 hours') AS h3_pnl,
        
        -- 48H Statistics 
        SUM(twp.trade_pnl) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '48 hours') AS h48_pnl,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '48 hours' AND twp.result = 'WIN') AS h48_wins,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '48 hours') AS h48_total,
        
        -- 72H Statistics
        SUM(twp.trade_pnl) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '72 hours') AS h72_pnl,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '72 hours' AND twp.result = 'WIN') AS h72_wins,
        COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '72 hours') AS h72_total
        
    FROM trades_with_pnl twp
    GROUP BY twp.strategy, twp.action, twp.symbol, twp.horizon
    HAVING COUNT(*) FILTER (WHERE twp.entry_time >= NOW() - INTERVAL '24 hours') >= 5 -- Minimum trades filter
),
-- Join with streaks and recent performance
strategy_complete AS (
    SELECT 
        ss.*,
        COALESCE(ms.max_win_streak, 0) AS h24_max_win_streak,
        COALESCE(ms.max_lose_streak, 0) AS h24_max_lose_streak,
        COALESCE(rps.recent_performance_raw, 0) AS recent_performance_raw
    FROM strategy_stats ss
    LEFT JOIN max_streaks ms ON ss.strategy = ms.strategy AND ss.action = ms.action AND ss.symbol = ms.symbol AND ss.horizon = ms.horizon
    LEFT JOIN recent_performance_raw rps ON ss.strategy = rps.strategy AND ss.action = rps.action AND ss.symbol = rps.symbol AND ss.horizon = rps.horizon
),
-- Calculate win rates for each time window
winrate_stats AS (
    SELECT 
        *,
        CASE WHEN h72_total = 0 THEN 0 ELSE ROUND(100.0 * h72_wins::numeric / h72_total, 1) END AS h72_winrate,
        CASE WHEN h48_total = 0 THEN 0 ELSE ROUND(100.0 * h48_wins::numeric / h48_total, 1) END AS h48_winrate,
        CASE WHEN h12_total = 0 THEN 0 ELSE ROUND(100.0 * h12_wins::numeric / h12_total, 1) END AS h12_winrate
    FROM strategy_complete
),
-- Calculate Recent Performance KPI and normalization
recent_performance_kpi AS (
    SELECT 
        COALESCE(AVG(recent_performance_raw) + COALESCE(STDDEV(recent_performance_raw), 0), 1000) AS recent_kpi
    FROM strategy_complete
    WHERE recent_performance_raw > 0
),
-- Calculate all scores
scored_strategies AS (
    SELECT 
        ws.*,
        c.pnl_kpi,
        c.pnl_score_72h,
        c.pnl_score_48h, 
        c.pnl_score_24h,
        c.pnl_score_12h,
        c.winrate_score_72h,
        c.winrate_score_48h,
        c.winrate_score_24h,
        c.winrate_consistency_score,
        c.recent_performance_max_score,
        rpkpi.recent_kpi,
        
        -- PNL Window Scores (40 points total)
        GREATEST(0, LEAST(c.pnl_score_72h, (COALESCE(ws.h72_pnl, 0) / (c.pnl_kpi * 2.5)) * c.pnl_score_72h)) AS pnl_score_72h_calc,
        GREATEST(0, LEAST(c.pnl_score_48h, (COALESCE(ws.h48_pnl, 0) / (c.pnl_kpi * 2.0)) * c.pnl_score_48h)) AS pnl_score_48h_calc,
        GREATEST(0, LEAST(c.pnl_score_24h, (COALESCE(ws.h24_pnl, 0) / (c.pnl_kpi * 1.0)) * c.pnl_score_24h)) AS pnl_score_24h_calc,
        GREATEST(0, LEAST(c.pnl_score_12h, (COALESCE(ws.h12_pnl, 0) / (c.pnl_kpi * 0.7)) * c.pnl_score_12h)) AS pnl_score_12h_calc,
        
        -- Winrate Window Consistency Scores (30 points total)
        GREATEST(0, LEAST(c.winrate_score_72h, (ws.h72_winrate - 55) * c.winrate_score_72h / 35)) AS winrate_score_72h_calc,
        GREATEST(0, LEAST(c.winrate_score_48h, (ws.h48_winrate - 55) * c.winrate_score_48h / 35)) AS winrate_score_48h_calc,
        GREATEST(0, LEAST(c.winrate_score_24h, (ws.h24_winrate - 55) * c.winrate_score_24h / 35)) AS winrate_score_24h_calc,
        
        -- Cross-Window Consistency Score (6 points)
        GREATEST(0, LEAST(c.winrate_consistency_score, 
            c.winrate_consistency_score - (ABS(ws.h24_winrate - ws.h72_winrate) + ABS(ws.h48_winrate - ws.h72_winrate)) * c.winrate_consistency_score / 30)) AS winrate_consistency_calc,
        
        -- Recent Performance Score (30 points) 
        CASE 
            WHEN rpkpi.recent_kpi > 0 THEN LEAST(c.recent_performance_max_score, (ws.recent_performance_raw / rpkpi.recent_kpi) * c.recent_performance_max_score)
            ELSE 0
        END AS recent_performance_score_calc
        
    FROM winrate_stats ws
    CROSS JOIN config c
    CROSS JOIN recent_performance_kpi rpkpi
),
-- Calculate Normal Scores (เชิงบวก)
normal_scores AS (
    SELECT 
        *,
        'NORMAL' AS strategy_type,
        -- Normal PNL Score (40 points): สูง = ดี
        (pnl_score_72h_calc + pnl_score_48h_calc + pnl_score_24h_calc + pnl_score_12h_calc) AS normal_pnl_score,
        
        -- Normal Winrate Score (30 points): สูง = ดี  
        (winrate_score_72h_calc + winrate_score_48h_calc + winrate_score_24h_calc + winrate_consistency_calc) AS normal_win_con_score,
        
        -- Recent Performance Score (30 points): พุ่งขึ้น = ดี
        GREATEST(0, COALESCE(recent_performance_score_calc, 0)) AS normal_perf_score
    FROM scored_strategies
),
-- Calculate Reverse Scores (เชิงลบที่นิ่ง)  
reverse_scores AS (
    SELECT 
        *,
        'REVERSE' AS strategy_type,
        -- Reverse PNL Score (40 points): ต่ำ = ดี (สำหรับแทงกลับทาง)
        GREATEST(0,
            GREATEST(0, LEAST(pnl_score_72h, ((pnl_kpi * 2.5 - COALESCE(h72_pnl, 0)) / (pnl_kpi * 2.5)) * pnl_score_72h)) +
            GREATEST(0, LEAST(pnl_score_48h, ((pnl_kpi * 2.0 - COALESCE(h48_pnl, 0)) / (pnl_kpi * 2.0)) * pnl_score_48h)) +
            GREATEST(0, LEAST(pnl_score_24h, ((pnl_kpi * 1.0 - COALESCE(h24_pnl, 0)) / (pnl_kpi * 1.0)) * pnl_score_24h)) +
            GREATEST(0, LEAST(pnl_score_12h, ((pnl_kpi * 0.7 - COALESCE(h12_pnl, 0)) / (pnl_kpi * 0.7)) * pnl_score_12h))
        ) AS reverse_pnl_score,
        
        -- Reverse Winrate Score (30 points): ต่ำ = ดี (สำหรับแทงกลับทาง)
        GREATEST(0,
            GREATEST(0, LEAST(winrate_score_72h, (45 - h72_winrate) * winrate_score_72h / 35)) +
            GREATEST(0, LEAST(winrate_score_48h, (45 - h48_winrate) * winrate_score_48h / 35)) +
            GREATEST(0, LEAST(winrate_score_24h, (45 - h24_winrate) * winrate_score_24h / 35)) +
            winrate_consistency_calc -- ความเสถียร = ดี (เหมือนกันทั้ง 2 ฝั่ง)
        ) AS reverse_win_con_score,
        
        -- Reverse Recent Performance Score (30 points): ลงต่อเนื่อง = ดี (สำหรับแทงกลับทาง)
        GREATEST(0, 
            CASE 
                WHEN COALESCE(recent_performance_score_calc, 0) > 0 THEN 0  -- ถ้าพุ่งขึ้น = ไม่เหมาะแทงกลับ
                ELSE (recent_performance_max_score - COALESCE(recent_performance_score_calc, 0)) -- ลงมาก = เหมาะแทงกลับ
            END
        ) AS reverse_perf_score
    FROM scored_strategies
),
-- Combine Normal and Reverse Strategies
combined_strategies AS (
    -- Normal strategies with normal scoring
    SELECT 
        strategy, action, symbol, horizon, h24_total_trades, h24_winrate, h24_max_win_streak, h24_max_lose_streak,
        h24_pnl, h12_pnl, h6_pnl, h3_pnl,
        normal_pnl_score AS final_pnl_score,
        normal_win_con_score AS final_win_con_score,
        normal_perf_score AS final_perf_score,
        (normal_pnl_score + normal_win_con_score + normal_perf_score) AS total_score,
        strategy_type
    FROM normal_scores
    
    UNION ALL
    
    -- Reverse strategies with reverse scoring (only when reverse_enable = true)
    SELECT 
        strategy, action, symbol, horizon, h24_total_trades, h24_winrate, h24_max_win_streak, h24_max_lose_streak,
        h24_pnl, h12_pnl, h6_pnl, h3_pnl,
        reverse_pnl_score AS final_pnl_score,
        reverse_win_con_score AS final_win_con_score, 
        reverse_perf_score AS final_perf_score,
        (reverse_pnl_score + reverse_win_con_score + reverse_perf_score) AS total_score,
        strategy_type
    FROM reverse_scores
    CROSS JOIN config cfg
    WHERE cfg.reverse_enable = true
),
-- Final ranking from combined results
ranked_strategies AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY total_score DESC, h6_pnl DESC, h12_pnl DESC) AS rank
    FROM combined_strategies
    WHERE h24_total_trades >= 3 -- Minimum quality filter
)
SELECT 
    r.strategy,
    r.action,
    r.strategy_type AS reverse,
    r.symbol,
    r.horizon,
    r.h24_total_trades AS "24h_totaltrade",
    r.h24_winrate AS "24h_winrate", 
    r.h24_max_win_streak AS "24h_max_win_streak",
    r.h24_max_lose_streak AS "24h_max_lose_streak",
    CASE 
        WHEN c.abs_pnl = true AND r.h24_pnl < 0 THEN ABS(r.h24_pnl)
        ELSE r.h24_pnl 
    END AS "24h_pnl",
    CASE 
        WHEN c.abs_pnl = true AND r.h12_pnl < 0 THEN ABS(r.h12_pnl)
        ELSE r.h12_pnl 
    END AS "12h_pnl",
    CASE 
        WHEN c.abs_pnl = true AND r.h6_pnl < 0 THEN ABS(r.h6_pnl)
        ELSE r.h6_pnl 
    END AS "6h_pnl", 
    CASE 
        WHEN c.abs_pnl = true AND r.h3_pnl < 0 THEN ABS(r.h3_pnl)
        ELSE r.h3_pnl 
    END AS "3h_pnl",
    ROUND(r.final_pnl_score, 2) AS pnl_score40,
    ROUND(r.final_win_con_score, 2) AS win_con_score30,  
    ROUND(r.final_perf_score, 2) AS perf_score30,
    ROUND(r.total_score, 2) AS total_score100
FROM ranked_strategies r
CROSS JOIN config c
WHERE r.rank <= c.prime_list
ORDER BY r.total_score DESC, r.h6_pnl DESC, r.h12_pnl DESC;
