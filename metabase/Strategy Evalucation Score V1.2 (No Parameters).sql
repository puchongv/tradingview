-- File: Strategy Evalucation Score V1.2 (No Parameters).sql
-- Purpose: Strategy evaluation scores WITHOUT Metabase parameters (hardcoded values)
-- Output: strategy | action | reverse | symbol | horizon | 24h_totaltrade | 24h_winrate | 24h_max_win_streak | 24h_max_lose_streak | 24h_pnl | 12h_pnl | 6h_pnl | 3h_pnl | pnl_score40 | win_con_score30 | perf_score30 | total_score100
-- Version: 1.2 (No Parameters - Guaranteed to work)

WITH config AS (
    SELECT
        '10min' AS horizon_list,
        true AS reverse_enable,
        false AS abs_pnl,
        10 AS prime_list,
        1000::numeric AS pnl_kpi,
        40 AS pnl_score_max,
        30 AS winrate_score_max,
        30 AS perf_score_max
),
-- Get strategies with basic stats
strategy_stats AS (
    SELECT 
        strategy,
        action,
        symbol,
        '10min' AS horizon,
        
        -- 24H Statistics
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) AS h24_total_trades,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN') AS h24_wins,
        COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE') AS h24_losses,
        
        -- Win Rates
        CASE 
            WHEN COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) = 0 THEN 0
            ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN')::numeric 
                      / COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')), 1)
        END AS h24_winrate,
        
        -- PNL Calculations (0.8 payout, 250 investment)
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'WIN' THEN 200 
            WHEN entry_time >= NOW() - INTERVAL '24 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) AS h24_pnl,
        
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '12 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) AS h12_pnl,
        
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '6 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) AS h6_pnl,
        
        SUM(CASE 
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'WIN' THEN 200
            WHEN entry_time >= NOW() - INTERVAL '3 hours' AND result_10min = 'LOSE' THEN -250
            ELSE 0 
        END) AS h3_pnl
        
    FROM tradingviewdata
    WHERE entry_time >= NOW() - INTERVAL '72 hours'
    GROUP BY strategy, action, symbol
    HAVING COUNT(*) FILTER (WHERE entry_time >= NOW() - INTERVAL '24 hours' AND result_10min IN ('WIN', 'LOSE')) >= 1
),
-- Calculate scores for NORMAL strategies (good PNL/winrate = high score)
normal_scores AS (
    SELECT 
        *,
        'NORMAL' AS strategy_type,
        -- PNL Score: Higher PNL = Higher Score (max 40)
        GREATEST(0, LEAST(40::numeric, h24_pnl / 1000::numeric * 40)) AS pnl_score,
        -- Winrate Score: Higher winrate = Higher Score (max 30)  
        GREATEST(0, LEAST(30::numeric, (h24_winrate - 50) / 40 * 30)) AS winrate_score,
        -- Performance Score: Recent improvement = Higher Score (max 30)
        GREATEST(0, LEAST(30::numeric, (h6_pnl - h12_pnl) / 200::numeric * 30)) AS perf_score
    FROM strategy_stats
),
-- Calculate scores for REVERSE strategies (bad PNL/winrate = high score for contrarian trading)
reverse_scores AS (
    SELECT 
        *,
        'REVERSE' AS strategy_type,
        -- Reverse PNL Score: Lower/Negative PNL = Higher Score (for contrarian trades)
        GREATEST(0, LEAST(40::numeric, (1000 - h24_pnl) / 1000::numeric * 40)) AS pnl_score,
        -- Reverse Winrate Score: Lower winrate = Higher Score (for contrarian trades)
        GREATEST(0, LEAST(30::numeric, (50 - h24_winrate) / 40 * 30)) AS winrate_score,
        -- Reverse Performance Score: Declining performance = Higher Score (for contrarian trades)
        GREATEST(0, LEAST(30::numeric, (h12_pnl - h6_pnl) / 200::numeric * 30)) AS perf_score
    FROM strategy_stats
),
-- Combine normal and reverse strategies
combined_strategies AS (
    -- Normal strategies
    SELECT 
        strategy, action, symbol, horizon, strategy_type,
        h24_total_trades, h24_winrate, h24_pnl, h12_pnl, h6_pnl, h3_pnl,
        pnl_score, winrate_score, perf_score,
        (pnl_score + winrate_score + perf_score) AS total_score
    FROM normal_scores
    
    UNION ALL
    
    -- Reverse strategies (hardcoded enable = true)
    SELECT 
        strategy, action, symbol, horizon, strategy_type,
        h24_total_trades, h24_winrate, h24_pnl, h12_pnl, h6_pnl, h3_pnl,
        pnl_score, winrate_score, perf_score,
        (pnl_score + winrate_score + perf_score) AS total_score
    FROM reverse_scores
),
-- Rank all strategies by total score
ranked_strategies AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY total_score DESC, h6_pnl DESC, h12_pnl DESC) AS rank
    FROM combined_strategies
)
-- Final output
SELECT 
    strategy,
    action,
    strategy_type AS reverse,
    symbol,
    horizon,
    h24_total_trades AS "24h_totaltrade",
    h24_winrate AS "24h_winrate",
    0::bigint AS "24h_max_win_streak",     -- Placeholder 
    0::bigint AS "24h_max_lose_streak",    -- Placeholder
    h24_pnl AS "24h_pnl",                  -- No abs_pnl conversion (hardcoded false)
    h12_pnl AS "12h_pnl",
    h6_pnl AS "6h_pnl",
    h3_pnl AS "3h_pnl",
    ROUND(pnl_score, 2) AS pnl_score40,
    ROUND(winrate_score, 2) AS win_con_score30,
    ROUND(perf_score, 2) AS perf_score30,
    ROUND(total_score, 2) AS total_score100
FROM ranked_strategies
WHERE rank <= 10  -- Hardcoded prime_list = 10
ORDER BY total_score DESC, h6_pnl DESC, h12_pnl DESC;
