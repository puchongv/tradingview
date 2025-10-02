-- Strategy Evalucation Score Simple (Guaranteed to work)
-- Direct query without complex WITH clauses

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
    -- Simple scoring
    GREATEST(0::numeric, LEAST(40::numeric, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / 1000::numeric * 40
    )) AS pnl_score40,
    GREATEST(0::numeric, LEAST(30::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 50) / 40 * 30
    )) AS win_con_score30,
    GREATEST(0::numeric, LEAST(30::numeric,
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END)) / 200::numeric * 30
    )) AS perf_score30,
    -- Total score
    GREATEST(0::numeric, LEAST(40::numeric, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) / 1000::numeric * 40
    )) + GREATEST(0::numeric, LEAST(30::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 50) / 40 * 30
    )) + GREATEST(0::numeric, LEAST(30::numeric,
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END)) / 200::numeric * 30
    )) AS total_score100

FROM tradingviewdata
WHERE entry_time >= NOW() - INTERVAL '72 hours'
GROUP BY strategy, action, symbol
HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1
ORDER BY total_score100 DESC
LIMIT 10;
