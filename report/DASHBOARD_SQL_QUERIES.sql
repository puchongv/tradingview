-- DASHBOARD SQL QUERIES
-- Generated: 2025-09-14 00:30:01

-- 1. PATTERN PERFORMANCE OVERVIEW
CREATE VIEW pattern_performance AS
SELECT 
    'Hour Patterns' as category,
    CONCAT('Hour ', LPAD(EXTRACT(HOUR FROM entry_time)::text, 2, '0'), ':00') as pattern_name,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
    STDDEV(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate_stddev
FROM tradingviewdata 
WHERE strategy IN ('MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20')
GROUP BY EXTRACT(HOUR FROM entry_time)
HAVING COUNT(*) >= 50

UNION ALL

SELECT 
    'Day Patterns' as category,
    CASE EXTRACT(DOW FROM entry_time)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday' 
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as pattern_name,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
    STDDEV(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate_stddev
FROM tradingviewdata 
WHERE strategy IN ('MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20')
GROUP BY EXTRACT(DOW FROM entry_time)
HAVING COUNT(*) >= 50
ORDER BY win_rate DESC;

-- 2. TOP PATTERNS ONLY (Win Rate > 55% OR < 45%)
SELECT * FROM pattern_performance 
WHERE win_rate > 0.55 OR win_rate < 0.45
ORDER BY win_rate DESC;

-- 3. TIME HEATMAP DATA
SELECT 
    EXTRACT(DOW FROM entry_time) as day_of_week,
    EXTRACT(HOUR FROM entry_time) as hour,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE strategy IN ('MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20')
GROUP BY day_of_week, hour
HAVING COUNT(*) >= 10
ORDER BY day_of_week, hour;

-- 4. GOLDEN COMBINATIONS
SELECT 
    'Tuesday + Hour 21' as combination,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE EXTRACT(DOW FROM entry_time) = 2 
  AND EXTRACT(HOUR FROM entry_time) = 21
  AND strategy IN ('MWP-25', 'MWP-27', 'MWP-30')

UNION ALL

SELECT 
    'Golden Hours (08,15,21)' as combination,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE EXTRACT(HOUR FROM entry_time) IN (8, 15, 21)
  AND strategy IN ('MWP-25', 'MWP-27', 'MWP-30')

UNION ALL

SELECT 
    'Danger Hours (17,19,23)' as combination,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE EXTRACT(HOUR FROM entry_time) IN (17, 19, 23)
  AND strategy IN ('MWP-25', 'MWP-27', 'MWP-30')
ORDER BY win_rate DESC;
