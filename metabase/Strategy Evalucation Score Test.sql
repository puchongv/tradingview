-- Simple test query to diagnose the issue
-- Test basic data access first

SELECT 
    strategy,
    action,
    symbol,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE result_10min = 'WIN') as wins_10min,
    COUNT(*) FILTER (WHERE result_10min = 'LOSE') as losses_10min,
    SUM(CASE WHEN result_10min = 'WIN' THEN 200 WHEN result_10min = 'LOSE' THEN -250 ELSE 0 END) as pnl_10min
FROM tradingviewdata 
WHERE entry_time >= NOW() - INTERVAL '24 hours'
AND result_10min IN ('WIN', 'LOSE')
GROUP BY strategy, action, symbol
ORDER BY total_trades DESC
LIMIT 10;
