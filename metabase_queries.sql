-- Metabase SQL Queries for Binary Options Trading Pattern Analysis
-- Generated from ML Analysis Results

-- 1. Win Rate by Hour (Time Pattern Analysis)
SELECT 
    EXTRACT(HOUR FROM entry_time) as hour,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result_60min = 'LOST' THEN 1 ELSE 0 END) as losses
FROM trading_signals
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;

-- 2. Volatility Level Analysis
SELECT 
    CASE 
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.1 THEN 0
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.2 THEN 1
        ELSE 2
    END as volatility_level,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades,
    AVG(ABS((price_60min - entry_price) / entry_price * 100)) as avg_volatility
FROM trading_signals
GROUP BY 
    CASE 
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.1 THEN 0
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.2 THEN 1
        ELSE 2
    END
ORDER BY volatility_level;

-- 3. Strategy + Action Combination Performance
SELECT 
    CONCAT(strategy, ' + ', action) as combination,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result_60min = 'LOST' THEN 1 ELSE 0 END) as losses
FROM trading_signals
GROUP BY strategy, action
HAVING COUNT(*) >= 5
ORDER BY win_rate ASC;

-- 4. Win/Loss Streak Analysis
WITH streak_data AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY strategy ORDER BY entry_time) as row_num,
        LAG(result_60min) OVER (PARTITION BY strategy ORDER BY entry_time) as prev_result
    FROM trading_signals
),
streak_calculated AS (
    SELECT 
        *,
        CASE 
            WHEN result_60min = 'WIN' AND prev_result = 'WIN' THEN 1
            WHEN result_60min = 'WIN' AND prev_result != 'WIN' THEN 1
            ELSE 0
        END as win_streak,
        CASE 
            WHEN result_60min = 'LOST' AND prev_result = 'LOST' THEN 1
            WHEN result_60min = 'LOST' AND prev_result != 'LOST' THEN 1
            ELSE 0
        END as loss_streak
    FROM streak_data
)
SELECT 
    win_streak,
    loss_streak,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades
FROM streak_calculated
GROUP BY win_streak, loss_streak
HAVING COUNT(*) >= 3
ORDER BY win_streak, loss_streak;

-- 5. Rolling Win Rate Trend
SELECT 
    entry_time,
    strategy,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) OVER (
        PARTITION BY strategy 
        ORDER BY entry_time 
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) as rolling_win_rate_10,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) OVER (
        PARTITION BY strategy 
        ORDER BY entry_time 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as rolling_win_rate_20
FROM trading_signals
ORDER BY strategy, entry_time;

-- 6. Price Change vs Win Rate Analysis
SELECT 
    CASE 
        WHEN (price_10min - entry_price) / entry_price * 100 > 0.1 THEN 'High Positive'
        WHEN (price_10min - entry_price) / entry_price * 100 > 0 THEN 'Positive'
        WHEN (price_10min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        ELSE 'Negative'
    END as price_change_10min_category,
    CASE 
        WHEN (price_30min - entry_price) / entry_price * 100 > 0.1 THEN 'High Positive'
        WHEN (price_30min - entry_price) / entry_price * 100 > 0 THEN 'Positive'
        WHEN (price_30min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        ELSE 'Negative'
    END as price_change_30min_category,
    CASE 
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.1 THEN 'High Positive'
        WHEN (price_60min - entry_price) / entry_price * 100 > 0 THEN 'Positive'
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        ELSE 'Negative'
    END as price_change_60min_category,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades
FROM trading_signals
GROUP BY 
    CASE 
        WHEN (price_10min - entry_price) / entry_price * 100 > 0.1 THEN 'High Positive'
        WHEN (price_10min - entry_price) / entry_price * 100 > 0 THEN 'Positive'
        WHEN (price_10min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        ELSE 'Negative'
    END,
    CASE 
        WHEN (price_30min - entry_price) / entry_price * 100 > 0.1 THEN 'High Positive'
        WHEN (price_30min - entry_price) / entry_price * 100 > 0 THEN 'Positive'
        WHEN (price_30min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        ELSE 'Negative'
    END,
    CASE 
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.1 THEN 'High Positive'
        WHEN (price_60min - entry_price) / entry_price * 100 > 0 THEN 'Positive'
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        ELSE 'Negative'
    END
HAVING COUNT(*) >= 3
ORDER BY win_rate DESC;

-- 7. Market Trend Analysis
SELECT 
    CASE 
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.2 THEN 'Strong Bullish'
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.1 THEN 'Bullish'
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.2 THEN 'Bearish'
        ELSE 'Strong Bearish'
    END as market_trend,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades,
    AVG((price_60min - entry_price) / entry_price * 100) as avg_price_change
FROM trading_signals
GROUP BY 
    CASE 
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.2 THEN 'Strong Bullish'
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.1 THEN 'Bullish'
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.1 THEN 'Neutral'
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.2 THEN 'Bearish'
        ELSE 'Strong Bearish'
    END
ORDER BY 
    CASE 
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.2 THEN 1
        WHEN (price_60min - entry_price) / entry_price * 100 > 0.1 THEN 2
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.1 THEN 3
        WHEN (price_60min - entry_price) / entry_price * 100 > -0.2 THEN 4
        ELSE 5
    END;

-- 8. Day of Week Analysis
SELECT 
    EXTRACT(DOW FROM entry_time) as day_of_week_num,
    CASE EXTRACT(DOW FROM entry_time)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_of_week,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades
FROM trading_signals
GROUP BY EXTRACT(DOW FROM entry_time)
ORDER BY day_of_week_num;

-- 9. Strategy Performance Analysis
SELECT 
    strategy,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result_60min = 'LOST' THEN 1 ELSE 0 END) as losses,
    AVG(pnl) as avg_pnl
FROM trading_signals
GROUP BY strategy
ORDER BY win_rate DESC;

-- 10. Action Performance Analysis
SELECT 
    action,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result_60min = 'LOST' THEN 1 ELSE 0 END) as losses
FROM trading_signals
GROUP BY action
ORDER BY win_rate DESC;

-- 11. High Risk Conditions Alert Query
SELECT 
    entry_time,
    strategy,
    action,
    EXTRACT(HOUR FROM entry_time) as hour,
    CASE 
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.1 THEN 0
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.2 THEN 1
        ELSE 2
    END as volatility_level,
    result_60min,
    'HIGH RISK' as risk_level
FROM trading_signals
WHERE 
    EXTRACT(HOUR FROM entry_time) = 17  -- Bad time
    OR (
        CASE 
            WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.1 THEN 0
            WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.2 THEN 1
            ELSE 2
        END = 2  -- High volatility
    )
ORDER BY entry_time DESC;

-- 12. Optimal Trading Conditions Query
SELECT 
    entry_time,
    strategy,
    action,
    EXTRACT(HOUR FROM entry_time) as hour,
    CASE 
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.1 THEN 0
        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.2 THEN 1
        ELSE 2
    END as volatility_level,
    result_60min,
    'OPTIMAL' as condition_level
FROM trading_signals
WHERE 
    EXTRACT(HOUR FROM entry_time) = 2  -- Good time
    AND (
        CASE 
            WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.1 THEN 0
            WHEN ABS((price_60min - entry_price) / entry_price * 100) < 0.2 THEN 1
            ELSE 2
        END IN (0, 1)  -- Low to medium volatility
    )
ORDER BY entry_time DESC;