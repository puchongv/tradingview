-- Fixed Dynamic Win Rate Query with Custom Time Periods
-- Parameter 1: {{timeframe}} (10min, 30min, 60min)
-- Parameter 2: {{time_period}} (last6hr, 6-12hr, 12-24hr, day, week, month, all)

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    '{{timeframe}}' as timeframe,
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
    COUNT(*) as total_signals
FROM tradingviewdata
WHERE 
    -- Custom Time Period Filter
    (
        CASE 
            -- 6 ชั่วโมงล่าสุด
            WHEN '{{time_period}}' = 'last6hr' THEN 
                entry_time >= NOW() - INTERVAL '6 hours'
            
            -- ข้อมูลช่วงหลังจาก last6hr เลยไปอีก 6 ชั่วโมง (6-12 ชั่วโมงที่แล้ว)
            WHEN '{{time_period}}' = '6-12hr' THEN 
                entry_time >= NOW() - INTERVAL '12 hours' 
                AND entry_time < NOW() - INTERVAL '6 hours'
            
            -- ข้อมูลช่วงหลังจาก 6-12hr เลยไปอีก 12 ชั่วโมง (12-24 ชั่วโมงที่แล้ว)
            WHEN '{{time_period}}' = '12-24hr' THEN 
                entry_time >= NOW() - INTERVAL '24 hours' 
                AND entry_time < NOW() - INTERVAL '12 hours'
            
            -- ข้อมูลของวันนี้ (00:00 - 23:59 วันนี้)
            WHEN '{{time_period}}' = 'day' THEN 
                DATE(entry_time) = CURRENT_DATE
            
            -- ข้อมูลของอาทิตย์นี้ (จันทร์ - อาทิตย์)
            WHEN '{{time_period}}' = 'week' THEN 
                entry_time >= DATE_TRUNC('week', CURRENT_DATE)
                AND entry_time < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week'
            
            -- ข้อมูลของเดือนนี้ (วันที่ 1 - สิ้นเดือน)
            WHEN '{{time_period}}' = 'month' THEN 
                entry_time >= DATE_TRUNC('month', CURRENT_DATE)
                AND entry_time < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            
            -- ข้อมูลทั้งหมด
            WHEN '{{time_period}}' = 'all' THEN 
                TRUE
            
            ELSE 
                entry_time >= NOW() - INTERVAL '6 hours'
        END
    )
    -- Timeframe Result Filter (มีข้อมูล WIN/LOSE)
    AND (
        ('{{timeframe}}' = '10min' AND result_10min IS NOT NULL AND result_10min IN ('WIN', 'LOSE'))
        OR
        ('{{timeframe}}' = '30min' AND result_30min IS NOT NULL AND result_30min IN ('WIN', 'LOSE'))
        OR
        ('{{timeframe}}' = '60min' AND result_60min IS NOT NULL AND result_60min IN ('WIN', 'LOSE'))
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Alternative Approach: Use Column-based Selection
-- This avoids the CASE statement issue entirely

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
    COUNT(*) as total_signals
FROM tradingviewdata
WHERE 
    -- Time Period Filters
    (
        ('{{time_period}}' = 'last6hr' AND entry_time >= NOW() - INTERVAL '6 hours')
        OR
        ('{{time_period}}' = '6-12hr' AND entry_time >= NOW() - INTERVAL '12 hours' AND entry_time < NOW() - INTERVAL '6 hours')
        OR
        ('{{time_period}}' = '12-24hr' AND entry_time >= NOW() - INTERVAL '24 hours' AND entry_time < NOW() - INTERVAL '12 hours')
        OR
        ('{{time_period}}' = 'day' AND DATE(entry_time) = CURRENT_DATE)
        OR
        ('{{time_period}}' = 'week' AND entry_time >= DATE_TRUNC('week', CURRENT_DATE) AND entry_time < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week')
        OR
        ('{{time_period}}' = 'month' AND entry_time >= DATE_TRUNC('month', CURRENT_DATE) AND entry_time < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
        OR
        ('{{time_period}}' = 'all')
    )
    -- Timeframe Filters
    AND (
        ('{{timeframe}}' = '10min' AND result_10min IN ('WIN', 'LOSE'))
        OR
        ('{{timeframe}}' = '30min' AND result_30min IN ('WIN', 'LOSE'))
        OR
        ('{{timeframe}}' = '60min' AND result_60min IN ('WIN', 'LOSE'))
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Simple Version (Most Compatible)
-- Use this if the above still has issues

SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    ROUND(
        CASE 
            WHEN '{{timeframe}}' = '10min' THEN
                (SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
            WHEN '{{timeframe}}' = '30min' THEN
                (SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
            WHEN '{{timeframe}}' = '60min' THEN
                (SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
            ELSE 0
        END, 2
    ) as win_rate_percent,
    COUNT(*) as total_signals
FROM tradingviewdata
WHERE 1=1
    -- Time Period Filter
    AND (
        ('{{time_period}}' = 'last6hr' AND entry_time >= NOW() - INTERVAL '6 hours')
        OR ('{{time_period}}' = '6-12hr' AND entry_time >= NOW() - INTERVAL '12 hours' AND entry_time < NOW() - INTERVAL '6 hours')
        OR ('{{time_period}}' = '12-24hr' AND entry_time >= NOW() - INTERVAL '24 hours' AND entry_time < NOW() - INTERVAL '12 hours')
        OR ('{{time_period}}' = 'day' AND DATE(entry_time) = CURRENT_DATE)
        OR ('{{time_period}}' = 'week' AND entry_time >= DATE_TRUNC('week', CURRENT_DATE))
        OR ('{{time_period}}' = 'month' AND entry_time >= DATE_TRUNC('month', CURRENT_DATE))
        OR ('{{time_period}}' = 'all')
    )
    -- Result Filter
    AND (
        ('{{timeframe}}' = '10min' AND result_10min IN ('WIN', 'LOSE'))
        OR ('{{timeframe}}' = '30min' AND result_30min IN ('WIN', 'LOSE'))
        OR ('{{timeframe}}' = '60min' AND result_60min IN ('WIN', 'LOSE'))
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;
