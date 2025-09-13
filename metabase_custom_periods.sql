-- Dynamic Win Rate Query with Custom Time Periods
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
        CASE 
            WHEN '{{timeframe}}' = '10min' THEN 
                result_10min IS NOT NULL AND result_10min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '30min' THEN 
                result_30min IS NOT NULL AND result_30min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '60min' THEN 
                result_60min IS NOT NULL AND result_60min IN ('WIN', 'LOSE')
            ELSE TRUE
        END
    )
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- Summary Query: Total Signals by Time Period and Timeframe
-- Shows total count for each combination

SELECT 
    '{{time_period}}' as time_period,
    '{{timeframe}}' as timeframe,
    COUNT(*) as total_signals,
    SUM(
        CASE 
            WHEN '{{timeframe}}' = '10min' AND result_10min = 'WIN' THEN 1
            WHEN '{{timeframe}}' = '30min' AND result_30min = 'WIN' THEN 1
            WHEN '{{timeframe}}' = '60min' AND result_60min = 'WIN' THEN 1
            ELSE 0 
        END
    ) as total_wins,
    ROUND(
        (SUM(
            CASE 
                WHEN '{{timeframe}}' = '10min' AND result_10min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '30min' AND result_30min = 'WIN' THEN 1
                WHEN '{{timeframe}}' = '60min' AND result_60min = 'WIN' THEN 1
                ELSE 0 
            END
        ) * 100.0 / COUNT(*)), 2
    ) as overall_win_rate_percent,
    MIN(entry_time) as earliest_signal,
    MAX(entry_time) as latest_signal
FROM tradingviewdata
WHERE 
    -- Same time period filter as above
    (
        CASE 
            WHEN '{{time_period}}' = 'last6hr' THEN 
                entry_time >= NOW() - INTERVAL '6 hours'
            WHEN '{{time_period}}' = '6-12hr' THEN 
                entry_time >= NOW() - INTERVAL '12 hours' 
                AND entry_time < NOW() - INTERVAL '6 hours'
            WHEN '{{time_period}}' = '12-24hr' THEN 
                entry_time >= NOW() - INTERVAL '24 hours' 
                AND entry_time < NOW() - INTERVAL '12 hours'
            WHEN '{{time_period}}' = 'day' THEN 
                DATE(entry_time) = CURRENT_DATE
            WHEN '{{time_period}}' = 'week' THEN 
                entry_time >= DATE_TRUNC('week', CURRENT_DATE)
                AND entry_time < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week'
            WHEN '{{time_period}}' = 'month' THEN 
                entry_time >= DATE_TRUNC('month', CURRENT_DATE)
                AND entry_time < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            WHEN '{{time_period}}' = 'all' THEN 
                TRUE
            ELSE 
                entry_time >= NOW() - INTERVAL '6 hours'
        END
    )
    AND (
        CASE 
            WHEN '{{timeframe}}' = '10min' THEN 
                result_10min IS NOT NULL AND result_10min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '30min' THEN 
                result_30min IS NOT NULL AND result_30min IN ('WIN', 'LOSE')
            WHEN '{{timeframe}}' = '60min' THEN 
                result_60min IS NOT NULL AND result_60min IN ('WIN', 'LOSE')
            ELSE TRUE
        END
    );

-- Debug Query: Check time ranges
-- Use this to verify the time period logic is working correctly

SELECT 
    '{{time_period}}' as selected_period,
    CASE 
        WHEN '{{time_period}}' = 'last6hr' THEN 
            CONCAT('From: ', (NOW() - INTERVAL '6 hours')::text, ' To: ', NOW()::text)
        WHEN '{{time_period}}' = '6-12hr' THEN 
            CONCAT('From: ', (NOW() - INTERVAL '12 hours')::text, ' To: ', (NOW() - INTERVAL '6 hours')::text)
        WHEN '{{time_period}}' = '12-24hr' THEN 
            CONCAT('From: ', (NOW() - INTERVAL '24 hours')::text, ' To: ', (NOW() - INTERVAL '12 hours')::text)
        WHEN '{{time_period}}' = 'day' THEN 
            CONCAT('Today: ', CURRENT_DATE::text)
        WHEN '{{time_period}}' = 'week' THEN 
            CONCAT('Week: ', DATE_TRUNC('week', CURRENT_DATE)::text, ' to ', (DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '1 week')::text)
        WHEN '{{time_period}}' = 'month' THEN 
            CONCAT('Month: ', DATE_TRUNC('month', CURRENT_DATE)::text, ' to ', (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')::text)
        ELSE 'All time'
    END as time_range_description;
