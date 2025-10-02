-- Test V1.9 with default parameters hardcoded
-- This script replaces all Metabase parameters with default values for direct testing

WITH param_raw AS (
    SELECT
        '10min'::text                       AS horizon_raw,
        10::int                             AS prime_list,
        1000::numeric                       AS pnl_kpi,
        5::numeric                          AS pnl_score_72h,
        10::numeric                         AS pnl_score_48h,
        15::numeric                         AS pnl_score_24h,
        10::numeric                         AS pnl_score_12h,
        8::numeric                          AS winrate_score_72h,
        8::numeric                          AS winrate_score_48h,
        8::numeric                          AS winrate_score_24h,
        6::numeric                          AS winrate_consistency_score,
        55.0::numeric                       AS winrate_breakeven,
        90.0::numeric                       AS winrate_target,
        30::numeric                         AS recent_performance_max_score,
        true::boolean                       AS enable_debugmode
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
        MAX(CASE WHEN m.window_hours = 3 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_3h,
        MAX(CASE WHEN m.window_hours = 6 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS pnl_6h_for_recent,
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
        END) AS pnl_3h_for_recent,
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
        MAX(CASE WHEN m.window_hours = 3 THEN 
            CASE 
                WHEN pr.horizon_raw = '10min' THEN m.pnl_10min
                WHEN pr.horizon_raw = '30min' THEN m.pnl_30min
                WHEN pr.horizon_raw = '60min' THEN m.pnl_60min
                ELSE m.pnl_10min
            END
        END) AS "3h_pnl"
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
        (
            5.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_2h, 0), 0) +
            4.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_3h_for_recent, 0), 0) +
            3.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_4h, 0), 0) +
            2.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_5h, 0), 0) +
            1.0 * GREATEST(COALESCE(mp.pnl_1h, 0) - COALESCE(mp.pnl_6h_for_recent, 0), 0)
        ) AS recent_score_raw
    FROM metrics_pivoted mp
    CROSS JOIN param pr
    WHERE mp.total_trades_72h >= 1
),
recent_kpi AS (
    SELECT
        AVG(recent_score_raw) + COALESCE(STDDEV(recent_score_raw), 0) AS kpi_value
    FROM recent_scores_raw
    WHERE recent_score_raw > 0
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
        GREATEST(0, LEAST(
            pr.winrate_score_72h,
            (COALESCE(mp.winrate_72h, 0) - pr.winrate_breakeven) * pr.winrate_score_72h / (pr.winrate_target - pr.winrate_breakeven)
        )) AS winrate_score_72h_calc,
        
        GREATEST(0, LEAST(
            pr.winrate_score_48h,
            (COALESCE(mp.winrate_48h, 0) - pr.winrate_breakeven) * pr.winrate_score_48h / (pr.winrate_target - pr.winrate_breakeven)
        )) AS winrate_score_48h_calc,
        
        GREATEST(0, LEAST(
            pr.winrate_score_24h,
            (COALESCE(mp.winrate_24h, 0) - pr.winrate_breakeven) * pr.winrate_score_24h / (pr.winrate_target - pr.winrate_breakeven)
        )) AS winrate_score_24h_calc,
        
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
-- FINAL OUTPUT - SELECT TOP 3 FOR TESTING
-- ====================================================================
SELECT
    strategy,
    action,
    'NORMAL' AS reverse,
    symbol,
    horizon,
    total_trades_24h AS "24h_totaltrade",
    
    "72h_winrate",
    "48h_winrate",
    "24h_winrate",
    
    "72h_pnl",
    "48h_pnl",
    "24h_pnl",
    "12h_pnl",
    "6h_pnl",
    "3h_pnl",
    
    -- Show individual PNL scores for debugging
    ROUND(pnl_score_72h_calc, 2) AS pnl_score_72h,
    ROUND(pnl_score_48h_calc, 2) AS pnl_score_48h,
    ROUND(pnl_score_24h_calc, 2) AS pnl_score_24h,
    ROUND(pnl_score_12h_calc, 2) AS pnl_score_12h,
    
    ROUND(pnl_score_72h_calc + pnl_score_48h_calc + pnl_score_24h_calc + pnl_score_12h_calc, 2) AS "pnl_score40",
    
    ROUND(winrate_score_72h_calc + winrate_score_48h_calc + winrate_score_24h_calc + winrate_consistency_calc, 2) AS "winrate_score30",
    
    ROUND(recent_performance_calc, 2) AS "performance_score30",
    
    ROUND(
        pnl_score_72h_calc + pnl_score_48h_calc + pnl_score_24h_calc + pnl_score_12h_calc +
        winrate_score_72h_calc + winrate_score_48h_calc + winrate_score_24h_calc + winrate_consistency_calc +
        recent_performance_calc,
        2
    ) AS "total_score"
    
FROM scores
WHERE total_trades_72h >= 1
ORDER BY "total_score" DESC, "6h_pnl" DESC NULLS LAST, "12h_pnl" DESC NULLS LAST
LIMIT 3;




