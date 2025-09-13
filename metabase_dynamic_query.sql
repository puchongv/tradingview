-- Dynamic Win Rate Query - Support Multiple Parameters
-- Parameter 1: {{timeframe}} (10min, 30min, 60min, 1day)
-- Parameter 2: {{time_period}} (last_6hr, last_6_12hr, last_12_18hr, last_18_24hr, today, week, month, all)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    '{{timeframe}}' as timeframe,
    ROUND(
        (SUM(
            CASE 
                WHEN '{{timeframe}}' = '10min' AND result_10min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '30min' AND result_30min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '60min' AND result_60min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '1day' AND result_1day = 'WIN' THEN 1
                ELSE 0 
            END
        ) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_trades
FROM tradingviewdata
WHERE 
    -- Time Period Filter
    (
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
    -- Timeframe Result Filter
    AND (
        CASE 
            WHEN '{{timeframe}}' = '10min' THEN result_10min IS NOT NULL AND result_10min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '30min' THEN result_30min IS NOT NULL AND result_30min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '60min' THEN result_60min IS NOT NULL AND result_60min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '1day' THEN result_1day IS NOT NULL AND result_1day IN ('WIN', 'LOSE')
            ELSE TRUE
        END
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Alternative Version: More Parameters
-- Parameter 1: {{timeframe}} (10min, 30min, 60min, 1day)
-- Parameter 2: {{time_period}} (last_6hr, today, week, etc.)
-- Parameter 3: {{strategy}} (optional strategy filter)
-- Parameter 4: {{action}} (optional action filter)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    '{{timeframe}}' as timeframe,
    ROUND(
        (SUM(
            CASE 
                WHEN '{{timeframe}}' = '10min' AND result_10min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '30min' AND result_30min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '60min' AND result_60min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '1day' AND result_1day = 'WIN' THEN 1
                ELSE 0 
            END
        ) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_trades,
    -- Additional info
    STRING_AGG(DISTINCT strategy, ', ') as strategies_used,
    STRING_AGG(DISTINCT action, ', ') as actions_used
FROM tradingviewdata
WHERE 
    -- Time Period Filter
    (
        CASE 
            WHEN '{{time_period}}' = 'last_6hr' THEN entry_time >= NOW() - INTERVAL '6 hours'
            WHEN '{{time_period}}' = 'last_6_12hr' THEN entry_time >= NOW() - INTERVAL '12 hours' AND entry_time < NOW() - INTERVAL '6 hours'
            WHEN '{{time_period}}' = 'last_12_18hr' THEN entry_time >= NOW() - INTERVAL '18 hours' AND entry_time < NOW() - INTERVAL '12 hours'
            WHEN '{{time_period}}' = 'last_18_24hr' THEN entry_time >= NOW() - INTERVAL '24 hours' AND entry_time < NOW() - INTERVAL '18 hours'
            WHEN '{{time_period}}' = 'today' THEN DATE(entry_time) = CURRENT_DATE
            WHEN '{{time_period}}' = 'week' THEN entry_time >= DATE_TRUNC('week', CURRENT_DATE)
            WHEN '{{time_period}}' = 'month' THEN entry_time >= DATE_TRUNC('month', CURRENT_DATE)
            WHEN '{{time_period}}' = 'all' THEN TRUE
            ELSE entry_time >= NOW() - INTERVAL '6 hours'
        END
    )
    -- Timeframe Result Filter
    AND (
        CASE 
            WHEN '{{timeframe}}' = '10min' THEN result_10min IS NOT NULL AND result_10min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '30min' THEN result_30min IS NOT NULL AND result_30min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '60min' THEN result_60min IS NOT NULL AND result_60min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '1day' THEN result_1day IS NOT NULL AND result_1day IN ('WIN', 'LOSE')
            ELSE TRUE
        END
    )
    -- Optional Strategy Filter
    AND (
        CASE 
            WHEN '{{strategy}}' IS NULL OR '{{strategy}}' = '' OR '{{strategy}}' = 'all' THEN TRUE
            ELSE strategy = '{{strategy}}'
        END
    )
    -- Optional Action Filter  
    AND (
        CASE 
            WHEN '{{action}}' IS NULL OR '{{action}}' = '' OR '{{action}}' = 'all' THEN TRUE
            ELSE action = '{{action}}'
        END
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Simple Version (Recommended for Dashboard)
-- Parameter 1: {{timeframe}} (10min, 30min, 60min)
-- Parameter 2: {{hours_back}} (6, 12, 24, 168 for week)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        (SUM(
            CASE 
                WHEN '{{timeframe}}' = '10min' AND result_10min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '30min' AND result_30min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '60min' AND result_60min = 'WIN' THEN 1
                ELSE 0 
            END
        ) * 100.0 / COUNT(*)), 2
    ) as win_rate_percent,
    COUNT(*) as total_trades
FROM tradingviewdata
WHERE 
    entry_time >= NOW() - INTERVAL '{{hours_back}} hours'
    AND (
        CASE 
            WHEN '{{timeframe}}' = '10min' THEN result_10min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '30min' THEN result_30min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '60min' THEN result_60min IN ('WIN', 'LOSE')
            ELSE FALSE
        END
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;
