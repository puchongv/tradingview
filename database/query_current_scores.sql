-- ========================================================================================================
-- Query Current Strategy Scores
-- Description: Get current hour's strategy scores sorted by score
-- ========================================================================================================

-- Get latest hour scores (TOP 10)
SELECT 
    ROW_NUMBER() OVER (ORDER BY score DESC) as rank,
    strategy_action,
    current_pnl,
    momentum,
    acceleration,
    score,
    trade_count,
    win_count,
    win_rate,
    current_hour,
    updated_at
FROM strategy_score_acceleration
WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
ORDER BY score DESC
LIMIT 10;

-- Summary statistics
SELECT 
    current_hour,
    COUNT(*) as total_strategies,
    ROUND(AVG(score), 2) as avg_score,
    ROUND(MAX(score), 2) as max_score,
    ROUND(MIN(score), 2) as min_score,
    SUM(trade_count) as total_trades,
    SUM(win_count) as total_wins,
    ROUND((SUM(win_count)::numeric / NULLIF(SUM(trade_count), 0)) * 100, 2) as overall_win_rate
FROM strategy_score_acceleration
WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
GROUP BY current_hour;

