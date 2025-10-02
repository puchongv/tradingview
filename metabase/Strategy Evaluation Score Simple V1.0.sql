-- File: Strategy Evaluation Score Simple V1.0.sql  
-- Purpose: Simplified strategy evaluation (for testing)
-- Basic Parameters Only

WITH basic_stats AS (
    SELECT 
        strategy,
        action,
        symbol,
        '10min' AS horizon,
        'NORMAL' AS strategy_type,
        
        -- 24H Stats
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) AS h24_total_trades,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN') AS h24_wins,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE') AS h24_losses,
        
        -- Win Rate
        CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0
            ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                      / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
        END AS h24_winrate,
        
        -- PNL (simple calculation)
        SUM(
            CASE 
                WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200  -- 0.8 * 250
                WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
                ELSE 0
            END
        ) AS h24_pnl,
        
        SUM(
            CASE 
                WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
                WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
                ELSE 0
            END
        ) AS h12_pnl,
        
        SUM(
            CASE 
                WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
                WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250  
                ELSE 0
            END
        ) AS h6_pnl,
        
        SUM(
            CASE 
                WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 200
                WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -250
                ELSE 0
            END
        ) AS h3_pnl
        
    FROM tradingviewdata
    WHERE entry_time >= NOW() - INTERVAL '72 hours'
    GROUP BY strategy, action, symbol
    HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1
),
scored AS (
    SELECT 
        *,
        -- Simple PNL Score (40 points max)
        GREATEST(0, LEAST(40, h24_pnl / 25)) AS pnl_score40,
        
        -- Simple Winrate Score (30 points max)  
        GREATEST(0, LEAST(30, (h24_winrate - 50) / 2)) AS win_con_score30,
        
        -- Simple Recent Performance (20 points max)
        GREATEST(0, LEAST(20, (h6_pnl - h12_pnl) / 10)) AS perf_score20,
        
        0 AS streak_score10  -- Placeholder
        
    FROM basic_stats
),
final_scored AS (
    SELECT 
        *,
        (pnl_score40 + win_con_score30 + perf_score20 + streak_score10) AS total_score90
    FROM scored
)
SELECT 
    strategy,
    action,
    strategy_type AS reverse,
    symbol,
    horizon,
    h24_total_trades AS "24h_totaltrade",
    h24_winrate AS "24h_winrate",
    0::bigint AS "24h_max_win_streak",
    0::bigint AS "24h_max_lose_streak", 
    h24_pnl AS "24h_pnl",
    h12_pnl AS "12h_pnl",
    h6_pnl AS "6h_pnl",
    h3_pnl AS "3h_pnl",
    ROUND(pnl_score40, 2) AS pnl_score40,
    ROUND(win_con_score30, 2) AS win_con_score30,
    ROUND(perf_score20, 2) AS perf_score30,
    ROUND(total_score90, 2) AS total_score100
FROM final_scored
WHERE h24_total_trades > 0

UNION ALL

-- Fallback result
SELECT 
    'NO_DATA' AS strategy,
    'NO_DATA' AS action, 
    'NO_DATA' AS reverse,
    'NO_DATA' AS symbol,
    '10min' AS horizon,
    0::bigint AS "24h_totaltrade",
    0::numeric AS "24h_winrate",
    0::bigint AS "24h_max_win_streak",
    0::bigint AS "24h_max_lose_streak",
    0::numeric AS "24h_pnl", 
    0::numeric AS "12h_pnl",
    0::numeric AS "6h_pnl",
    0::numeric AS "3h_pnl",
    0::numeric AS pnl_score40,
    0::numeric AS win_con_score30,
    0::numeric AS perf_score30,
    0::numeric AS total_score100
WHERE NOT EXISTS (SELECT 1 FROM final_scored WHERE h24_total_trades > 0)

ORDER BY total_score100 DESC
LIMIT 10;
