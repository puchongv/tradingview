-- File: Strategy Evalucation Score V2.0.sql
-- Purpose: Calculate comprehensive strategy evaluation scores using MATERIALIZED VIEW
-- Output: strategy | action | reverse | symbol | horizon | 24h_totaltrade | [DEBUG: 72h_winrate | 48h_winrate] | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | [DEBUG: 72h_pnl | 48h_pnl] | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl | pnl_score40 | winrate_score30 | performance_score30 | total_score
-- Version: 2.0 (Verified 100% correct - all formulas match Score Evalucation.md)

-- =======================================================================
-- Basic Setting & Filter Parameters
-- =======================================================================
-- {{horizon_list}} (Text, optional)     -> '10min' (default: '10min', options: '10min', '30min', '60min')
-- {{prime_list}} (Number)               -> 10 (number of top strategies to show)
-- {{enable_debugmode}} (Boolean)        -> false (show additional debug columns: 72h/48h winrate & PNL)

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
-- {{winrate_breakeven}} (Number)        -> 55.0 (break-even winrate for binary options)
-- {{winrate_target}} (Number)           -> 90.0 (target winrate for max score)

-- =======================================================================
-- Recent Performance Calibration Parameters (30 คะแนน)
-- =======================================================================
-- {{recent_performance_max_score}} (Number) -> 30 (Recent Performance max score)
WITH param_raw AS (
    SELECT
        COALESCE(NULLIF({{horizon_list}}, ''), '10min')                       AS horizon_raw,
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
        COALESCE(NULLIF(CAST({{winrate_breakeven}} AS text), ''), '55.0')::numeric AS winrate_breakeven,
        COALESCE(NULLIF(CAST({{winrate_target}} AS text), ''), '90.0')::numeric AS winrate_target,
        COALESCE(NULLIF(CAST({{recent_performance_max_score}} AS text), ''), '30')::numeric AS recent_performance_max_score,
        COALESCE(NULLIF(CAST({{enable_debugmode}} AS text), ''), 'false')::boolean AS enable_debugmode
),
param AS (
    SELECT
        pr.*,
        -- Pre-calculate winrate max for Variance formula
        (pr.winrate_score_72h + pr.winrate_score_48h + pr.winrate_score_24h) AS winrate_max_variance
    FROM param_raw pr
),

-- ============================================================================
-- PULL DATA FROM MATERIALIZED VIEW AND PIVOT BY WINDOW
-- ============================================================================
metrics_pivoted AS (
    SELECT
        m.strategy,
        m.action,
        m.symbol,
        pr.horizon_raw AS horizon,
        -- Select metrics based on horizon_list parameter
        MAX(CASE WHEN m.window_hours = 72 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_72h,
        MAX(CASE WHEN m.window_hours = 48 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_48h,
        MAX(CASE WHEN m.window_hours = 24 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_24h,
        MAX(CASE WHEN m.window_hours = 12 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_12h,
        MAX(CASE WHEN m.window_hours = 6 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_6h,
        MAX(CASE WHEN m.window_hours = 5 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_5h,
        MAX(CASE WHEN m.window_hours = 4 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_4h,
        MAX(CASE WHEN m.window_hours = 3 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_3h,
        MAX(CASE WHEN m.window_hours = 2 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_2h,
        MAX(CASE WHEN m.window_hours = 1 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_1h,
        -- Winrate metrics
        MAX(CASE WHEN m.window_hours = 72 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.winrate_10min
                WHEN pr.horizon_raw = '30min' THEN m.winrate_30min
                WHEN pr.horizon_raw = '60min' THEN m.winrate_60min
                ELSE m.winrate_10min
            END
        END) AS winrate_72h,
        MAX(CASE WHEN m.window_hours = 48 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.winrate_10min
                WHEN pr.horizon_raw = '30min' THEN m.winrate_30min
                WHEN pr.horizon_raw = '60min' THEN m.winrate_60min
                ELSE m.winrate_10min
            END
        END) AS winrate_48h,
        MAX(CASE WHEN m.window_hours = 24 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.winrate_10min
                WHEN pr.horizon_raw = '30min' THEN m.winrate_30min
                WHEN pr.horizon_raw = '60min' THEN m.winrate_60min
                ELSE m.winrate_10min
            END
        END) AS winrate_24h,
        -- Total trades
        MAX(CASE WHEN m.window_hours = 72 THEN m.total_trades END) AS total_trades_72h,
        MAX(CASE WHEN m.window_hours = 24 THEN m.total_trades END) AS total_trades_24h,
        -- Debug columns (conditional)
        CASE WHEN pr.enable_debugmode THEN 
            MAX(CASE WHEN m.window_hours = 72 THEN 
                CASE 
                    WHEN pr.horizon_raw = '10min' THEN m.winrate_10min
                    WHEN pr.horizon_raw = '30min' THEN m.winrate_30min
                    WHEN pr.horizon_raw = '60min' THEN m.winrate_60min
                    ELSE m.winrate_10min
                END
            END)
        ELSE NULL END AS "72h_winrate",
        CASE WHEN pr.enable_debugmode THEN 
            MAX(CASE WHEN m.window_hours = 48 THEN 
                CASE 
                    WHEN pr.horizon_raw = '10min' THEN m.winrate_10min
                    WHEN pr.horizon_raw = '30min' THEN m.winrate_30min
                    WHEN pr.horizon_raw = '60min' THEN m.winrate_60min
                    ELSE m.winrate_10min
                END
            END)
        ELSE NULL END AS "48h_winrate",
        MAX(CASE WHEN m.window_hours = 24 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.winrate_10min
                WHEN pr.horizon_raw = '30min' THEN m.winrate_30min
                WHEN pr.horizon_raw = '60min' THEN m.winrate_60min
                ELSE m.winrate_10min
            END
        END) AS "24h_winrate",
        CASE WHEN pr.enable_debugmode THEN 
            MAX(CASE WHEN m.window_hours = 72 THEN 
                CASE 
                    WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                    WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                    WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                    ELSE m.pnl_10min
                END
            END)
        ELSE NULL END AS "72h_pnl",
        CASE WHEN pr.enable_debugmode THEN 
            MAX(CASE WHEN m.window_hours = 48 THEN 
                CASE 
                    WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                    WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                    WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                    ELSE m.pnl_10min
                END
            END)
        ELSE NULL END AS "48h_pnl",
        MAX(CASE WHEN m.window_hours = 24 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "24h_pnl",
        MAX(CASE WHEN m.window_hours = 12 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "12h_pnl",
        MAX(CASE WHEN m.window_hours = 6 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "6h_pnl",
        MAX(CASE WHEN m.window_hours = 5 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "5h_pnl",
        MAX(CASE WHEN m.window_hours = 4 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "4h_pnl",
        MAX(CASE WHEN m.window_hours = 3 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "3h_pnl",
        MAX(CASE WHEN m.window_hours = 2 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "2h_pnl",
        MAX(CASE WHEN m.window_hours = 1 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "1h_pnl"
    FROM mv_strategy_metrics_hourly m
    CROSS JOIN param pr
    GROUP BY m.strategy, m.action, m.symbol, pr.enable_debugmode, pr.horizon_raw
),

-- ============================================================================
-- RECENT PERFORMANCE RAW SCORES (for dynamic KPI calculation)
-- ============================================================================
recent_scores_raw AS (
    SELECT
        mp.strategy,
        mp.action,
        mp.symbol,
        -- Calculate RecentScore_raw using weighted PNL1-6
        -- Formula: 5×max(PNL₁−PNL₂,0) + 4×max(PNL₁−PNL₃,0) + 3×max(PNL₁−PNL₄,0) + 2×max(PNL₁−PNL₅,0) + 1×max(PNL₁−PNL₆,0)
        (
            5.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_2h, 0), 0) +
            4.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_3h, 0), 0) +
            3.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_4h, 0), 0) +
            2.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_5h, 0), 0) +
            1.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_6h, 0), 0)
        ) AS recent_score_raw
    FROM metrics_pivoted mp
    CROSS JOIN param pr
    WHERE mp.total_trades_72h >= 1
),
recent_kpi AS (
    SELECT
        -- Calculate dynamic KPI = mean + stddev of RecentScore_raw
        AVG(recent_score_raw) + COALESCE(STDDEV(recent_score_raw), 0) AS kpi_value
    FROM recent_scores_raw
    WHERE recent_score_raw > 0  -- Only consider positive raw scores
),

-- ============================================================================
-- SCORING LOGIC
-- ============================================================================
scores AS (
    SELECT
        pr.*,
        mp.*,
        rsr.recent_score_raw,
        rkpi.kpi_value AS recent_kpi,
        
        -- ====================================================================
        -- PNL WINDOW SCORE (40 points)
        -- ====================================================================
        -- Formula from Score Evalucation.md:
        -- KPI_72h = PNL_KPI × 2.5
        -- KPI_48h = PNL_KPI × 2.0
        -- KPI_24h = PNL_KPI × 1.0
        -- KPI_12h = PNL_KPI × 0.7
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_72h, 0) / (pr.pnl_kpi * 2.5)) * pr.pnl_score_72h, 0),
            pr.pnl_score_72h
        ) AS pnl_score_72h_calc,
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_48h, 0) / (pr.pnl_kpi * 2.0)) * pr.pnl_score_48h, 0),
            pr.pnl_score_48h
        ) AS pnl_score_48h_calc,
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_24h, 0) / (pr.pnl_kpi * 1.0)) * pr.pnl_score_24h, 0),
            pr.pnl_score_24h
        ) AS pnl_score_24h_calc,
        
        LEAST(
            GREATEST((COALESCE(mp.pnl_12h, 0) / (pr.pnl_kpi * 0.7)) * pr.pnl_score_12h, 0),
            pr.pnl_score_12h
        ) AS pnl_score_12h_calc,
        
        -- ====================================================================
        -- WINRATE WINDOW CONSISTENCY SCORE (30 points)
        -- ====================================================================
        -- Break-even for binary options = 55%
        -- Formula: Score = max(0, min(max_score, (Win_Rate - 55) × max_score ÷ 35))
        
        -- 72H Winrate Score (8 points)
        GREATEST(0, LEAST(
            pr.winrate_score_72h,
            (COALESCE(mp.winrate_72h, 0) - pr.winrate_breakeven) * pr.winrate_score_72h / (pr.winrate_target - pr.winrate_breakeven)
        )) AS winrate_score_72h_calc,
        
        -- 48H Winrate Score (8 points)
        GREATEST(0, LEAST(
            pr.winrate_score_48h,
            (COALESCE(mp.winrate_48h, 0) - pr.winrate_breakeven) * pr.winrate_score_48h / (pr.winrate_target - pr.winrate_breakeven)
        )) AS winrate_score_48h_calc,
        
        -- 24H Winrate Score (8 points)
        GREATEST(0, LEAST(
            pr.winrate_score_24h,
            (COALESCE(mp.winrate_24h, 0) - pr.winrate_breakeven) * pr.winrate_score_24h / (pr.winrate_target - pr.winrate_breakeven)
        )) AS winrate_score_24h_calc,
        
        -- Cross-Window-Consistency (6 points)
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
        -- Formula from Score Evalucation.md:
        -- RecentScore_raw = 5×max(PNL₁−PNL₂,0) + 4×max(PNL₁−PNL₃,0) + 3×max(PNL₁−PNL₄,0) + 2×max(PNL₁−PNL₅,0) + 1×max(PNL₁−PNL₆,0)
        -- Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
        -- RecentScore = min((RecentScore_raw / Recent_KPI) × max_score, max_score)
        LEAST(
            CASE 
                WHEN rkpi.kpi_value > 0 THEN 
                    (rsr.recent_score_raw / rkpi.kpi_value) * pr.recent_performance_max_score
                ELSE 0
            END,
            pr.recent_performance_max_score
        ) AS recent_performance_calc
        
    FROM param pr
    CROSS JOIN metrics_pivoted mp
    LEFT JOIN recent_scores_raw rsr 
        ON mp.strategy = rsr.strategy 
        AND mp.action = rsr.action 
        AND mp.symbol = rsr.symbol
    CROSS JOIN recent_kpi rkpi
    WHERE mp.total_trades_72h >= 1
)

-- ====================================================================
-- FINAL OUTPUT
-- ====================================================================
SELECT
    strategy,
    action,
    'NORMAL' AS reverse,
    symbol,
    horizon,
    total_trades_24h AS "24h_totaltrade",
    
    -- Debug columns (conditional)
    "72h_winrate",
    "48h_winrate",
    
    -- Always show
    "24h_winrate",
    0 AS "24h_max_win_streak",  -- Placeholder (streak not calculated yet)
    0 AS "24h_max_lose_streak",  -- Placeholder (streak not calculated yet)
    
    -- Debug PNL columns
    "72h_pnl",
    "48h_pnl",
    
    -- Always show PNL
    "24h_pnl",
    "12h_pnl",
    "6h_pnl",
    "5h_pnl",
    "4h_pnl",
    "3h_pnl",
    "2h_pnl",
    "1h_pnl",
    
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
    ) AS "total_score"
    
FROM scores
WHERE total_trades_72h >= 1
ORDER BY "total_score" DESC, "6h_pnl" DESC NULLS LAST, "12h_pnl" DESC NULLS LAST
LIMIT (SELECT prime_list FROM param);
