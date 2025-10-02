-- File: Strategy Evalucation Score Final.sql
-- Purpose: Final working strategy evaluation scores WITH Metabase parameters support
-- Output: strategy | action | reverse | symbol | horizon | 24h_totaltrade | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl | pnl_score40 | win_con_score30 | perf_score30 | total_score100
-- Version: Final (Tested & Working with Metabase Parameters)

-- Basic Setting & Filter Parameters
-- {{prime_list}} (Number, default: 10)        -> Number of top strategies to show
-- {{abs_pnl}} (Boolean, default: false)       -> Show negative PNL as positive
-- {{pnl_kpi}} (Number, default: 1000)         -> Base PNL KPI for scoring
-- {{payout}} (Number, default: 0.8)           -> Payout ratio per winning trade  
-- {{investment}} (Number, default: 250)       -> Investment per trade

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
    -- PNL calculations with parameters
    CASE 
        WHEN COALESCE('{{abs_pnl}}'::text, 'false') = 'true' THEN
            ABS(SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END))
        ELSE
            SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END)
    END AS "24h_pnl",
    CASE 
        WHEN COALESCE('{{abs_pnl}}'::text, 'false') = 'true' THEN
            ABS(SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END))
        ELSE
            SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END)
    END AS "12h_pnl",
    CASE 
        WHEN COALESCE('{{abs_pnl}}'::text, 'false') = 'true' THEN
            ABS(SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END))
        ELSE
            SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END)
    END AS "6h_pnl",
    CASE 
        WHEN COALESCE('{{abs_pnl}}'::text, 'false') = 'true' THEN
            ABS(SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END))
        ELSE
            SUM(CASE 
                WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
                WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
                ELSE 0 
            END)
    END AS "3h_pnl",
    -- PNL Score (max 40 points)
    GREATEST(0::numeric, LEAST(40::numeric, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / COALESCE('{{pnl_kpi}}'::numeric, 1000) * 40
    )) AS pnl_score40,
    -- Winrate Score (max 30 points)
    GREATEST(0::numeric, LEAST(30::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 50) / 40 * 30
    )) AS win_con_score30,
    -- Performance Score (max 30 points) - Recent 6h vs 12h improvement
    GREATEST(0::numeric, LEAST(30::numeric,
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / 200::numeric * 30
    )) AS perf_score30,
    -- Total Score (sum of all scores)
    GREATEST(0::numeric, LEAST(40::numeric, 
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) / COALESCE('{{pnl_kpi}}'::numeric, 1000) * 40
    )) + GREATEST(0::numeric, LEAST(30::numeric,
        (CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0::numeric
            ELSE 100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                  / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE'))
        END - 50) / 40 * 30
    )) + GREATEST(0::numeric, LEAST(30::numeric,
        (SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END) - SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN COALESCE('{{payout}}'::numeric, 0.8) * COALESCE('{{investment}}'::numeric, 250)
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -1 * COALESCE('{{investment}}'::numeric, 250)
            ELSE 0 
        END)) / 200::numeric * 30
    )) AS total_score100

FROM tradingviewdata
WHERE entry_time >= NOW() - INTERVAL '72 hours'
GROUP BY strategy, action, symbol
HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1
ORDER BY total_score100 DESC
LIMIT COALESCE('{{prime_list}}'::int, 10);
