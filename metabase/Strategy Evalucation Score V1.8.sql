-- ============================================================================
-- Strategy Evaluation Score V1.8
-- ============================================================================
-- Changes from V1.7:
-- 1. Fixed Cross-Window-Consistency formula (using Variance-based from .md)
-- 2. Changed constant 30 to (winrate_score_72h + winrate_score_48h + winrate_score_24h)
-- 3. Uses mv_strategy_metrics_hourly for better performance
-- 4. Maintains debug mode from V1.7
--
-- Total Score: 100 points
-- - PNL Window: 40 points (72h:5, 48h:10, 24h:15, 12h:10)
-- - Winrate Window Consistency: 30 points (72h:8, 48h:8, 24h:8, Cross:6)
-- - Recent Performance: 30 points (Bidirectional 6h vs 12h PNL)
-- ============================================================================

-- ============================================================================
-- METABASE PARAMETERS (DO NOT CHANGE THIS SECTION!)
-- ============================================================================
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
        COALESCE(NULLIF(CAST({{recent_performance_max_score}} AS text), ''), '30')::numeric AS recent_performance_max_score,
        COALESCE(NULLIF(CAST({{enable_debugmode}} AS text), ''), 'false')::boolean AS enable_debugmode
),
param AS (
    SELECT
        horizon_raw,
        CASE
            WHEN horizon_raw = '10min' THEN 'result_10min'
            WHEN horizon_raw = '30min' THEN 'result_30min'
            WHEN horizon_raw = '60min' THEN 'result_60min'
            ELSE 'result_10min'
        END AS result_column,
        max_loss_streak_cap,
        payout,
        investment,
        reverse_enable,
        abs_pnl,
        prime_list,
        pnl_kpi,
        pnl_score_72h,
        pnl_score_48h,
        pnl_score_24h,
        pnl_score_12h,
        winrate_score_72h,
        winrate_score_48h,
        winrate_score_24h,
        winrate_consistency_score,
        recent_performance_max_score,
        enable_debugmode,
        -- Pre-calculate winrate max for Variance formula
        (winrate_score_72h + winrate_score_48h + winrate_score_24h) AS winrate_max_variance
    FROM param_raw
),

-- ============================================================================
-- ACTION MAPPING (Handle Metabase truncation)
-- ============================================================================
action_map AS (
    SELECT 'FlowTr' AS short_name, 'FlowTrend Bullish + Buy+' AS full_name
    UNION ALL SELECT 'FlowTr', 'FlowTrend Bearish + Sell-'
    UNION ALL SELECT 'MWP10', 'MWP10 Reversal Long'
    UNION ALL SELECT 'MWP10', 'MWP10 Reversal Short'
    UNION ALL SELECT 'MWP27', 'MWP27 Continuation'
    UNION ALL SELECT 'MWP30', 'MWP30 Breakout'
    -- Add more mappings as needed
),

-- ============================================================================
-- PULL DATA FROM MATERIALIZED VIEW
-- ============================================================================
metrics_pivoted AS (
    SELECT
        m.strategy,
        m.action,
        m.symbol,
        m.tf,
        -- PNL metrics
        MAX(CASE WHEN m.window_hours = 72 THEN m.pnl END) AS pnl_72h,
        MAX(CASE WHEN m.window_hours = 48 THEN m.pnl END) AS pnl_48h,
        MAX(CASE WHEN m.window_hours = 24 THEN m.pnl END) AS pnl_24h,
        MAX(CASE WHEN m.window_hours = 12 THEN m.pnl END) AS pnl_12h,
        MAX(CASE WHEN m.window_hours = 6 THEN m.pnl END) AS pnl_6h,
        MAX(CASE WHEN m.window_hours = 5 THEN m.pnl END) AS pnl_5h,
        MAX(CASE WHEN m.window_hours = 4 THEN m.pnl END) AS pnl_4h,
        MAX(CASE WHEN m.window_hours = 3 THEN m.pnl END) AS pnl_3h,
        MAX(CASE WHEN m.window_hours = 2 THEN m.pnl END) AS pnl_2h,
        MAX(CASE WHEN m.window_hours = 1 THEN m.pnl END) AS pnl_1h,
        -- Winrate metrics
        MAX(CASE WHEN m.window_hours = 72 THEN m.winrate END) AS winrate_72h,
        MAX(CASE WHEN m.window_hours = 48 THEN m.winrate END) AS winrate_48h,
        MAX(CASE WHEN m.window_hours = 24 THEN m.winrate END) AS winrate_24h,
        -- Trade counts
        MAX(CASE WHEN m.window_hours = 72 THEN m.total_trades END) AS total_trades_72h
    FROM mv_strategy_metrics_hourly m
    GROUP BY m.strategy, m.action, m.symbol, m.tf
),

-- ============================================================================
-- SCORING LOGIC
-- ============================================================================
scores AS (
    SELECT
        pr.*,
        mp.strategy,
        mp.action,
        mp.symbol,
        mp.tf,
        mp.pnl_72h,
        mp.pnl_48h,
        mp.pnl_24h,
        mp.pnl_12h,
        mp.pnl_6h,
        mp.pnl_5h,
        mp.pnl_4h,
        mp.pnl_3h,
        mp.pnl_2h,
        mp.pnl_1h,
        mp.winrate_72h,
        mp.winrate_48h,
        mp.winrate_24h,
        mp.total_trades_72h,
        
        -- ====================================================================
        -- PNL WINDOW SCORE (40 points)
        -- ====================================================================
        LEAST(
            GREATEST((COALESCE(mp.pnl_72h, 0) / pr.pnl_kpi) * pr.pnl_score_72h, 0),
            pr.pnl_score_72h
        ) AS pnl_score_72h_calc,
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_48h, 0) / pr.pnl_kpi) * pr.pnl_score_48h, 0),
            pr.pnl_score_48h
        ) AS pnl_score_48h_calc,
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_24h, 0) / pr.pnl_kpi) * pr.pnl_score_24h, 0),
            pr.pnl_score_24h
        ) AS pnl_score_24h_calc,
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_12h, 0) / pr.pnl_kpi) * pr.pnl_score_12h, 0),
            pr.pnl_score_12h
        ) AS pnl_score_12h_calc,
        
        -- ====================================================================
        -- WINRATE WINDOW CONSISTENCY SCORE (30 points)
        -- ====================================================================
        -- Break-even for binary options = 55.56%
        -- Formula: Score = max(0, min(max_score, (Win_Rate - 55) × max_score ÷ 35))
        
        -- 72H Winrate Score (8 points)
        GREATEST(0, LEAST(
            pr.winrate_score_72h,
            (COALESCE(mp.winrate_72h, 0) - 55.0) * pr.winrate_score_72h / 35.0
        )) AS winrate_score_72h_calc,
        
        -- 48H Winrate Score (8 points)
        GREATEST(0, LEAST(
            pr.winrate_score_48h,
            (COALESCE(mp.winrate_48h, 0) - 55.0) * pr.winrate_score_48h / 35.0
        )) AS winrate_score_48h_calc,
        
        -- 24H Winrate Score (8 points)
        GREATEST(0, LEAST(
            pr.winrate_score_24h,
            (COALESCE(mp.winrate_24h, 0) - 55.0) * pr.winrate_score_24h / 35.0
        )) AS winrate_score_24h_calc,
        
        -- Cross-Window-Consistency (6 points) - FIXED IN V1.8
        -- Formula from Score Evalucation.md:
        -- Variance = (WR_24H - WR_72H) + (WR_48H - WR_72H)
        -- Score = max(0, min(6, 6 - (Variance × 6 ÷ 24)))
        GREATEST(0, LEAST(
            pr.winrate_consistency_score,
            pr.winrate_consistency_score - (
                (
                    (COALESCE(mp.winrate_24h, 0) - COALESCE(mp.winrate_72h, 0)) +
                    (COALESCE(mp.winrate_48h, 0) - COALESCE(mp.winrate_72h, 0))
                ) * pr.winrate_consistency_score / NULLIF(pr.winrate_max_variance, 0)
            )
        )) AS winrate_consistency_calc,
        
        -- ====================================================================
        -- RECENT PERFORMANCE SCORE (30 points)
        -- ====================================================================
        -- Bidirectional formula: baseline + (6h-12h change / abs(12h) + buffer) * half_score
        -- This gives baseline of 15, then adjusts up/down based on recent momentum
        (pr.recent_performance_max_score / 2.0) + (
            (COALESCE(mp.pnl_6h, 0) - COALESCE(mp.pnl_12h, 0)) 
            / (ABS(COALESCE(mp.pnl_12h, 0)) + 200) 
            * (pr.recent_performance_max_score / 2.0)
        ) AS recent_performance_calc
        
    FROM param pr
    CROSS JOIN metrics_pivoted mp
    WHERE mp.total_trades_72h >= 1
),

-- ====================================================================
-- FINAL AGGREGATION
-- ====================================================================
final_scores AS (
    SELECT
        strategy,
        action,
        symbol,
        tf,
        
        -- Debug columns (conditional)
        CASE WHEN enable_debugmode THEN winrate_72h ELSE NULL END AS "72h_winrate",
        CASE WHEN enable_debugmode THEN winrate_48h ELSE NULL END AS "48h_winrate",
        CASE WHEN enable_debugmode THEN winrate_24h ELSE NULL END AS "24h_winrate",
        
        CASE WHEN enable_debugmode THEN pnl_72h ELSE NULL END AS "72h_pnl",
        CASE WHEN enable_debugmode THEN pnl_48h ELSE NULL END AS "48h_pnl",
        CASE WHEN enable_debugmode THEN pnl_24h ELSE NULL END AS "24h_pnl",
        CASE WHEN enable_debugmode THEN pnl_12h ELSE NULL END AS "12h_pnl",
        CASE WHEN enable_debugmode THEN pnl_6h ELSE NULL END AS "6h_pnl",
        CASE WHEN enable_debugmode THEN pnl_5h ELSE NULL END AS "5h_pnl",
        CASE WHEN enable_debugmode THEN pnl_4h ELSE NULL END AS "4h_pnl",
        CASE WHEN enable_debugmode THEN pnl_2h ELSE NULL END AS "2h_pnl",
        CASE WHEN enable_debugmode THEN pnl_1h ELSE NULL END AS "1h_pnl",
        
        -- PNL scores
        ROUND(pnl_score_72h_calc + pnl_score_48h_calc + pnl_score_24h_calc + pnl_score_12h_calc, 2) AS "pnl_score40",
        
        -- Winrate scores
        ROUND(winrate_score_72h_calc + winrate_score_48h_calc + winrate_score_24h_calc + winrate_consistency_calc, 2) AS "winrate_score30",
        
        -- Recent performance score
        ROUND(recent_performance_calc, 2) AS "performance_score30",
        
        -- Total score
        ROUND(
            pnl_score_72h_calc + pnl_score_48h_calc + pnl_score_24h_calc + pnl_score_12h_calc +
            winrate_score_72h_calc + winrate_score_48h_calc + winrate_score_24h_calc + winrate_consistency_calc +
            recent_performance_calc,
            2
        ) AS "total_score",
        
        total_trades_72h AS "total_trades"
        
    FROM scores
)

-- ====================================================================
-- OUTPUT
-- ====================================================================
SELECT *
FROM final_scores
WHERE total_trades >= 1
ORDER BY total_score DESC, "6h_pnl" DESC NULLS LAST, "12h_pnl" DESC NULLS LAST
LIMIT 100;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This version requires mv_strategy_metrics_hourly to be created first
-- 2. Make sure to set up automatic refresh for the materialized view
-- 3. Debug mode shows additional PNL and Winrate columns when enabled
-- 4. Cross-Window-Consistency formula fixed to match Score Evalucation.md
-- 5. Recent Performance still uses V1.7 bidirectional formula (will update in future version)
