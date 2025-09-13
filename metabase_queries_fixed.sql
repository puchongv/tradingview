-- Win Rate 10min Query - Last 6 Hours Only
-- Fixed version: Shows only hours that have data in the specified time period

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        (SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_trades
FROM tradingviewdata
WHERE 
    entry_time >= NOW() - INTERVAL '6 hours'
    AND result_10min IS NOT NULL
    AND result_10min IN ('WIN', 'LOSE')
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Win Rate 10min Query with Time Period Parameter (Fixed)
-- Parameter: {{time_period}} (last_6hr, last_6_12hr, last_12_18hr, last_18_24hr, today, week, month, all)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        (SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_trades
FROM tradingviewdata
WHERE 
    result_10min IS NOT NULL
    AND result_10min IN ('WIN', 'LOSE')
    AND (
        CASE 
            WHEN '{{time_period}}' = 'last_6hr' THEN 
                entry_time >= NOW() - INTERVAL '6 hours'
            WHEN '{{time_period}}' = 'last_6_12hr' THEN 
                entry_time >= NOW() - INTERVAL '12 hours' 
                AND entry_time < NOW() - INTERVAL '6 hours'
            WHEN '{{time_period}}' = 'last_12_18hr' THEN 
                entry_time >= NOW() - INTERVAL '18 hours' 
                AND entry_time < NOW() - INTERVAL '12 hours'
            WHEN '{{time_period}}' = 'last_18_24hr' THEN 
                entry_time >= NOW() - INTERVAL '24 hours' 
                AND entry_time < NOW() - INTERVAL '18 hours'
            WHEN '{{time_period}}' = 'today' THEN 
                DATE(entry_time) = CURRENT_DATE
            WHEN '{{time_period}}' = 'week' THEN 
                entry_time >= DATE_TRUNC('week', CURRENT_DATE)
            WHEN '{{time_period}}' = 'month' THEN 
                entry_time >= DATE_TRUNC('month', CURRENT_DATE)
            WHEN '{{time_period}}' = 'all' THEN 
                TRUE
            ELSE 
                entry_time >= NOW() - INTERVAL '6 hours'
        END
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Alternative: Show only hours with actual data in time range
-- This version will NOT show hours 0-23 if they don't have data

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    TO_CHAR(entry_time, 'HH24:MI') as time_range,
    ROUND(
        (SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_trades
FROM tradingviewdata
WHERE 
    entry_time >= NOW() - INTERVAL '6 hours'
    AND result_10min IS NOT NULL
    AND result_10min IN ('WIN', 'LOSE')
GROUP BY 
    EXTRACT(HOUR FROM entry_time),
    TO_CHAR(entry_time, 'HH24:MI')
ORDER BY hour;

-- Debug Query: Check what data exists in last 6 hours
SELECT 
    entry_time,
    EXTRACT(HOUR FROM entry_time) as hour,
    result_10min,
    COUNT(*) OVER (PARTITION BY EXTRACT(HOUR FROM entry_time)) as trades_in_hour
FROM tradingviewdata
WHERE 
    entry_time >= NOW() - INTERVAL '6 hours'
    AND result_10min IS NOT NULL
ORDER BY entry_time DESC
LIMIT 20;
