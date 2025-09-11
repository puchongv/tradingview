-- Metabase Queries for Trading Signal Analysis
-- สำหรับสร้าง Dashboard แสดง Performance ของทุกสัญญาณ

-- 1. Strategy Performance Overview
-- แสดง performance ของทุก strategy
SELECT 
    strategy,
    action,
    tf as timeframe,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) as wins_10min,
    SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) as wins_30min,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins_60min,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min,
    ROUND(SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_30min,
    ROUND(SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_60min,
    ROUND(AVG(pnl), 2) as avg_pnl,
    SUM(pnl) as total_pnl
FROM tradingviewdata 
WHERE result_10min IS NOT NULL
GROUP BY strategy, action, tf
ORDER BY win_rate_10min DESC;

-- 2. Time Pattern Analysis
-- แสดง performance ตามชั่วโมง
SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) as wins_10min,
    SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) as wins_30min,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins_60min,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min,
    ROUND(SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_30min,
    ROUND(SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_60min
FROM tradingviewdata 
WHERE result_10min IS NOT NULL
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- 3. Strategy + Time Heatmap
-- แสดง performance ตาม strategy และเวลา
SELECT 
    strategy,
    EXTRACT(HOUR FROM entry_time) as hour,
    COUNT(*) as total_trades,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min
FROM tradingviewdata 
WHERE result_10min IS NOT NULL
GROUP BY strategy, EXTRACT(HOUR FROM entry_time)
HAVING COUNT(*) >= 5  -- เฉพาะที่มีข้อมูลอย่างน้อย 5 ครั้ง
ORDER BY strategy, hour;

-- 4. Action + Time Heatmap
-- แสดง performance ตาม action และเวลา
SELECT 
    action,
    EXTRACT(HOUR FROM entry_time) as hour,
    COUNT(*) as total_trades,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min
FROM tradingviewdata 
WHERE result_10min IS NOT NULL
GROUP BY action, EXTRACT(HOUR FROM entry_time)
HAVING COUNT(*) >= 5
ORDER BY action, hour;

-- 5. Pre-Loss Streak Analysis
-- แสดงผลกระทบของ pre-loss streak
WITH streak_data AS (
    SELECT 
        *,
        LAG(result_10min) OVER (PARTITION BY strategy ORDER BY entry_time) as prev_result,
        CASE 
            WHEN LAG(result_10min) OVER (PARTITION BY strategy ORDER BY entry_time) = 'LOSE' 
            THEN 1 
            ELSE 0 
        END as is_after_loss
    FROM tradingviewdata 
    WHERE result_10min IS NOT NULL
)
SELECT 
    strategy,
    action,
    is_after_loss,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate
FROM streak_data
GROUP BY strategy, action, is_after_loss
HAVING COUNT(*) >= 5
ORDER BY strategy, action, is_after_loss;

-- 6. Daily Performance Trend
-- แสดง performance ตามวัน
SELECT 
    DATE(entry_time) as trade_date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) as wins_10min,
    SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) as wins_30min,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins_60min,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min,
    ROUND(SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_30min,
    ROUND(SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_60min,
    SUM(pnl) as total_pnl
FROM tradingviewdata 
WHERE result_10min IS NOT NULL
GROUP BY DATE(entry_time)
ORDER BY trade_date;

-- 7. Price Movement Analysis
-- แสดง performance ตาม price movement
SELECT 
    CASE 
        WHEN (price_10min - entry_price) / entry_price * 100 < -0.1 THEN 'Strong Down'
        WHEN (price_10min - entry_price) / entry_price * 100 < -0.05 THEN 'Down'
        WHEN (price_10min - entry_price) / entry_price * 100 < 0.05 THEN 'Sideways'
        WHEN (price_10min - entry_price) / entry_price * 100 < 0.1 THEN 'Up'
        ELSE 'Strong Up'
    END as price_movement,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate
FROM tradingviewdata 
WHERE result_10min IS NOT NULL AND price_10min IS NOT NULL
GROUP BY 
    CASE 
        WHEN (price_10min - entry_price) / entry_price * 100 < -0.1 THEN 'Strong Down'
        WHEN (price_10min - entry_price) / entry_price * 100 < -0.05 THEN 'Down'
        WHEN (price_10min - entry_price) / entry_price * 100 < 0.05 THEN 'Sideways'
        WHEN (price_10min - entry_price) / entry_price * 100 < 0.1 THEN 'Up'
        ELSE 'Strong Up'
    END
ORDER BY win_rate DESC;

-- 8. Risk Assessment
-- แสดง risk score ของแต่ละ strategy
WITH risk_data AS (
    SELECT 
        strategy,
        action,
        COUNT(*) as total_trades,
        ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate,
        -- คำนวณ max consecutive losses
        MAX(
            CASE 
                WHEN result_10min = 'LOSE' THEN 
                    ROW_NUMBER() OVER (PARTITION BY strategy, action, 
                        ROW_NUMBER() OVER (PARTITION BY strategy, action ORDER BY entry_time) - 
                        ROW_NUMBER() OVER (PARTITION BY strategy, action, result_10min ORDER BY entry_time)
                    ORDER BY entry_time)
                ELSE 0
            END
        ) as max_consecutive_losses
    FROM tradingviewdata 
    WHERE result_10min IS NOT NULL
    GROUP BY strategy, action
)
SELECT 
    strategy,
    action,
    total_trades,
    win_rate,
    max_consecutive_losses,
    CASE 
        WHEN max_consecutive_losses <= 3 THEN 'Low Risk'
        WHEN max_consecutive_losses <= 5 THEN 'Medium Risk'
        ELSE 'High Risk'
    END as risk_level
FROM risk_data
WHERE total_trades >= 10
ORDER BY win_rate DESC, max_consecutive_losses ASC;

-- 9. Best Combinations
-- แสดง combination ที่ดีที่สุด
SELECT 
    strategy,
    action,
    EXTRACT(HOUR FROM entry_time) as hour,
    COUNT(*) as total_trades,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min,
    ROUND(SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_30min,
    ROUND(SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_60min
FROM tradingviewdata 
WHERE result_10min IS NOT NULL
GROUP BY strategy, action, EXTRACT(HOUR FROM entry_time)
HAVING COUNT(*) >= 5
ORDER BY win_rate_10min DESC
LIMIT 20;

-- 10. Recent Performance (Last 24 hours)
-- แสดง performance ล่าสุด
SELECT 
    strategy,
    action,
    tf as timeframe,
    COUNT(*) as total_trades,
    ROUND(SUM(CASE WHEN result_10min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_10min,
    ROUND(SUM(CASE WHEN result_30min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_30min,
    ROUND(SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate_60min,
    SUM(pnl) as total_pnl
FROM tradingviewdata 
WHERE result_10min IS NOT NULL 
    AND entry_time >= NOW() - INTERVAL '24 hours'
GROUP BY strategy, action, tf
ORDER BY win_rate_10min DESC;
