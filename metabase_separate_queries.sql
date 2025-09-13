-- Option 1: 10min Win Rate Query
-- Parameter: time_period (Text: last6hr, 6-12hr, 12-24hr, day, week, month, all)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        (SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_signals
FROM tradingviewdata
WHERE 1=1
    AND result_10min IN ('WIN', 'LOSE')
    AND (
        ({{time_period}} = 'last6hr' AND entry_time >= NOW() - INTERVAL '6 hours')
        OR ({{time_period}} = '6-12hr' AND entry_time >= NOW() - INTERVAL '12 hours' AND entry_time < NOW() - INTERVAL '6 hours')
        OR ({{time_period}} = '12-24hr' AND entry_time >= NOW() - INTERVAL '24 hours' AND entry_time < NOW() - INTERVAL '12 hours')
        OR ({{time_period}} = 'day' AND DATE(entry_time) = CURRENT_DATE)
        OR ({{time_period}} = 'week' AND entry_time >= DATE_TRUNC('week', CURRENT_DATE))
        OR ({{time_period}} = 'month' AND entry_time >= DATE_TRUNC('month', CURRENT_DATE))
        OR ({{time_period}} = 'all')
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Option 2: 30min Win Rate Query
-- Parameter: time_period (Text: last6hr, 6-12hr, 12-24hr, day, week, month, all)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        (SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_signals
FROM tradingviewdata
WHERE 1=1
    AND result_30min IN ('WIN', 'LOSE')
    AND (
        ({{time_period}} = 'last6hr' AND entry_time >= NOW() - INTERVAL '6 hours')
        OR ({{time_period}} = '6-12hr' AND entry_time >= NOW() - INTERVAL '12 hours' AND entry_time < NOW() - INTERVAL '6 hours')
        OR ({{time_period}} = '12-24hr' AND entry_time >= NOW() - INTERVAL '24 hours' AND entry_time < NOW() - INTERVAL '12 hours')
        OR ({{time_period}} = 'day' AND DATE(entry_time) = CURRENT_DATE)
        OR ({{time_period}} = 'week' AND entry_time >= DATE_TRUNC('week', CURRENT_DATE))
        OR ({{time_period}} = 'month' AND entry_time >= DATE_TRUNC('month', CURRENT_DATE))
        OR ({{time_period}} = 'all')
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Option 3: 60min Win Rate Query
-- Parameter: time_period (Text: last6hr, 6-12hr, 12-24hr, day, week, month, all)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        (SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_signals
FROM tradingviewdata
WHERE 1=1
    AND result_60min IN ('WIN', 'LOSE')
    AND (
        ({{time_period}} = 'last6hr' AND entry_time >= NOW() - INTERVAL '6 hours')
        OR ({{time_period}} = '6-12hr' AND entry_time >= NOW() - INTERVAL '12 hours' AND entry_time < NOW() - INTERVAL '6 hours')
        OR ({{time_period}} = '12-24hr' AND entry_time >= NOW() - INTERVAL '24 hours' AND entry_time < NOW() - INTERVAL '12 hours')
        OR ({{time_period}} = 'day' AND DATE(entry_time) = CURRENT_DATE)
        OR ({{time_period}} = 'week' AND entry_time >= DATE_TRUNC('week', CURRENT_DATE))
        OR ({{time_period}} = 'month' AND entry_time >= DATE_TRUNC('month', CURRENT_DATE))
        OR ({{time_period}} = 'all')
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;
