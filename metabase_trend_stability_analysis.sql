-- Trend Change & Win Rate Stability Analysis
-- For detecting strategy behavior changes and signal reliability

-- 1. Win Rate Trend Over Time (Weekly Rolling)
-- Purpose: Detect trend changes and stability of each strategy
SELECT 
    strategy,
    action,
    DATE_TRUNC('week', entry_time) as week_start,
    DATE_TRUNC('day', entry_time) as trade_date,
    
    -- Basic metrics
    COUNT(*) as daily_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as daily_wins,
    ROUND(AVG((result_60min = 'WIN')::int) * 100, 2) as daily_win_rate,
    
    -- Rolling averages (7-day window)
    ROUND(AVG(AVG((result_60min = 'WIN')::int)) OVER (
        PARTITION BY strategy, action 
        ORDER BY DATE_TRUNC('day', entry_time) 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) * 100, 2) as rolling_7day_winrate,
    
    -- Rolling averages (14-day window)
    ROUND(AVG(AVG((result_60min = 'WIN')::int)) OVER (
        PARTITION BY strategy, action 
        ORDER BY DATE_TRUNC('day', entry_time) 
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) * 100, 2) as rolling_14day_winrate,
    
    -- Trend detection
    ROUND(
        AVG(AVG((result_60min = 'WIN')::int)) OVER (
            PARTITION BY strategy, action 
            ORDER BY DATE_TRUNC('day', entry_time) 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) - 
        AVG(AVG((result_60min = 'WIN')::int)) OVER (
            PARTITION BY strategy, action 
            ORDER BY DATE_TRUNC('day', entry_time) 
            ROWS BETWEEN 13 PRECEDING AND 7 PRECEDING
        ), 2
    ) * 100 as trend_change_7vs14_day,
    
    -- Volatility measure (standard deviation)
    ROUND(STDDEV(AVG((result_60min = 'WIN')::int)) OVER (
        PARTITION BY strategy, action 
        ORDER BY DATE_TRUNC('day', entry_time) 
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) * 100, 2) as volatility_14day,
    
    -- Stability score (lower volatility = more stable)
    CASE 
        WHEN STDDEV(AVG((result_60min = 'WIN')::int)) OVER (
            PARTITION BY strategy, action 
            ORDER BY DATE_TRUNC('day', entry_time) 
            ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
        ) * 100 < 5 THEN 'VERY_STABLE'
        WHEN STDDEV(AVG((result_60min = 'WIN')::int)) OVER (
            PARTITION BY strategy, action 
            ORDER BY DATE_TRUNC('day', entry_time) 
            ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
        ) * 100 < 10 THEN 'STABLE'
        WHEN STDDEV(AVG((result_60min = 'WIN')::int)) OVER (
            PARTITION BY strategy, action 
            ORDER BY DATE_TRUNC('day', entry_time) 
            ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
        ) * 100 < 20 THEN 'MODERATE'
        ELSE 'UNSTABLE'
    END as stability_rating

FROM tradingviewdata 
WHERE result_60min IN ('WIN', 'LOSE')
    AND entry_time >= CURRENT_DATE - INTERVAL '60 days'  -- Last 60 days
GROUP BY strategy, action, DATE_TRUNC('week', entry_time), DATE_TRUNC('day', entry_time)
HAVING COUNT(*) >= 3  -- Minimum 3 trades per day for meaningful analysis
ORDER BY strategy, action, trade_date;

-- 2. Strategy Performance Change Detection
-- Purpose: Identify significant behavior changes
WITH daily_performance AS (
    SELECT 
        strategy,
        action,
        DATE_TRUNC('day', entry_time) as trade_date,
        COUNT(*) as trades,
        AVG((result_60min = 'WIN')::int) * 100 as daily_winrate
    FROM tradingviewdata 
    WHERE result_60min IN ('WIN', 'LOSE')
        AND entry_time >= CURRENT_DATE - INTERVAL '45 days'
    GROUP BY strategy, action, DATE_TRUNC('day', entry_time)
    HAVING COUNT(*) >= 2
),
performance_changes AS (
    SELECT 
        strategy,
        action,
        trade_date,
        daily_winrate,
        LAG(daily_winrate) OVER (PARTITION BY strategy, action ORDER BY trade_date) as prev_winrate,
        
        -- Calculate day-to-day change
        daily_winrate - LAG(daily_winrate) OVER (PARTITION BY strategy, action ORDER BY trade_date) as winrate_change,
        
        -- Calculate 7-day moving average change
        AVG(daily_winrate) OVER (
            PARTITION BY strategy, action 
            ORDER BY trade_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) - AVG(daily_winrate) OVER (
            PARTITION BY strategy, action 
            ORDER BY trade_date 
            ROWS BETWEEN 13 PRECEDING AND 7 PRECEDING
        ) as ma7_change
    FROM daily_performance
)
SELECT 
    strategy,
    action,
    trade_date,
    daily_winrate,
    prev_winrate,
    ROUND(winrate_change, 2) as daily_change_pct,
    ROUND(ma7_change, 2) as ma7_change_pct,
    
    -- Significance flags
    CASE 
        WHEN ABS(winrate_change) > 30 THEN 'MAJOR_CHANGE'
        WHEN ABS(winrate_change) > 15 THEN 'MODERATE_CHANGE'
        WHEN ABS(winrate_change) > 5 THEN 'MINOR_CHANGE'
        ELSE 'STABLE'
    END as change_significance,
    
    -- Trend direction
    CASE 
        WHEN ma7_change > 5 THEN 'IMPROVING'
        WHEN ma7_change < -5 THEN 'DECLINING'
        ELSE 'STABLE'
    END as trend_direction

FROM performance_changes
WHERE winrate_change IS NOT NULL
ORDER BY strategy, action, trade_date;

-- 3. Time Slot Stability Analysis
-- Purpose: Check stability of hour×day patterns over time
WITH weekly_slot_performance AS (
    SELECT 
        strategy,
        action,
        EXTRACT(HOUR FROM entry_time) as hour_of_day,
        EXTRACT(DOW FROM entry_time) as day_of_week,
        CASE EXTRACT(DOW FROM entry_time)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
        END as day_name,
        DATE_TRUNC('week', entry_time) as week_start,
        COUNT(*) as weekly_trades,
        AVG((result_60min = 'WIN')::int) * 100 as weekly_winrate
    FROM tradingviewdata 
    WHERE result_60min IN ('WIN', 'LOSE')
        AND entry_time >= CURRENT_DATE - INTERVAL '45 days'
    GROUP BY strategy, action, hour_of_day, day_of_week, day_name, week_start
    HAVING COUNT(*) >= 2  -- At least 2 trades per week for this slot
)
SELECT 
    strategy,
    action,
    hour_of_day,
    day_name,
    
    -- Aggregated metrics
    COUNT(*) as total_weeks,
    SUM(weekly_trades) as total_trades,
    ROUND(AVG(weekly_winrate), 2) as avg_winrate,
    ROUND(STDDEV(weekly_winrate), 2) as winrate_volatility,
    ROUND(MIN(weekly_winrate), 2) as min_weekly_winrate,
    ROUND(MAX(weekly_winrate), 2) as max_weekly_winrate,
    
    -- Consistency score
    CASE 
        WHEN STDDEV(weekly_winrate) < 10 AND COUNT(*) >= 3 THEN 'HIGH_CONSISTENCY'
        WHEN STDDEV(weekly_winrate) < 20 AND COUNT(*) >= 2 THEN 'MODERATE_CONSISTENCY'
        ELSE 'LOW_CONSISTENCY'
    END as consistency_rating,
    
    -- Reliability flag
    CASE 
        WHEN COUNT(*) >= 4 AND STDDEV(weekly_winrate) < 15 AND AVG(weekly_winrate) > 60 THEN 'HIGHLY_RELIABLE'
        WHEN COUNT(*) >= 3 AND STDDEV(weekly_winrate) < 20 AND AVG(weekly_winrate) > 55 THEN 'RELIABLE'
        WHEN COUNT(*) >= 2 AND AVG(weekly_winrate) > 50 THEN 'MODERATELY_RELIABLE'
        ELSE 'UNRELIABLE'
    END as reliability_flag

FROM weekly_slot_performance
GROUP BY strategy, action, hour_of_day, day_name
HAVING COUNT(*) >= 2  -- At least 2 weeks of data
ORDER BY strategy, action, hour_of_day;

-- 4. Overall Strategy Health Score
-- Purpose: Comprehensive scoring for strategy trustworthiness
WITH strategy_metrics AS (
    SELECT 
        strategy,
        action,
        COUNT(*) as total_trades,
        AVG((result_60min = 'WIN')::int) * 100 as overall_winrate,
        
        -- Recent performance (last 14 days)
        AVG(CASE 
            WHEN entry_time >= CURRENT_DATE - INTERVAL '14 days' 
            THEN (result_60min = 'WIN')::int 
        END) * 100 as recent_winrate,
        
        -- Count of active days
        COUNT(DISTINCT DATE_TRUNC('day', entry_time)) as active_days,
        
        -- Consistency across time slots
        COUNT(DISTINCT CONCAT(EXTRACT(HOUR FROM entry_time), '_', EXTRACT(DOW FROM entry_time))) as unique_time_slots
        
    FROM tradingviewdata 
    WHERE result_60min IN ('WIN', 'LOSE')
        AND entry_time >= CURRENT_DATE - INTERVAL '45 days'
    GROUP BY strategy, action
)
SELECT 
    strategy,
    action,
    total_trades,
    ROUND(overall_winrate, 2) as overall_winrate,
    ROUND(recent_winrate, 2) as recent_14day_winrate,
    active_days,
    unique_time_slots,
    
    -- Performance change
    ROUND(recent_winrate - overall_winrate, 2) as performance_change,
    
    -- Health score (0-100)
    LEAST(100, GREATEST(0,
        -- Base score from sample size (max 25 points)
        LEAST(25, total_trades * 0.5) +
        
        -- Win rate score (max 30 points)
        CASE 
            WHEN overall_winrate >= 70 THEN 30
            WHEN overall_winrate >= 60 THEN 25
            WHEN overall_winrate >= 50 THEN 20
            WHEN overall_winrate >= 40 THEN 10
            ELSE 0
        END +
        
        -- Consistency score (max 20 points)
        LEAST(20, active_days * 2) +
        
        -- Diversification score (max 15 points)
        LEAST(15, unique_time_slots * 1.5) +
        
        -- Recent performance bonus/penalty (max ±10 points)
        CASE 
            WHEN recent_winrate - overall_winrate > 10 THEN 10
            WHEN recent_winrate - overall_winrate > 5 THEN 5
            WHEN recent_winrate - overall_winrate < -10 THEN -10
            WHEN recent_winrate - overall_winrate < -5 THEN -5
            ELSE 0
        END
    )) as health_score,
    
    -- Overall rating
    CASE 
        WHEN LEAST(100, GREATEST(0,
            LEAST(25, total_trades * 0.5) +
            CASE 
                WHEN overall_winrate >= 70 THEN 30
                WHEN overall_winrate >= 60 THEN 25
                WHEN overall_winrate >= 50 THEN 20
                WHEN overall_winrate >= 40 THEN 10
                ELSE 0
            END +
            LEAST(20, active_days * 2) +
            LEAST(15, unique_time_slots * 1.5) +
            CASE 
                WHEN recent_winrate - overall_winrate > 10 THEN 10
                WHEN recent_winrate - overall_winrate > 5 THEN 5
                WHEN recent_winrate - overall_winrate < -10 THEN -10
                WHEN recent_winrate - overall_winrate < -5 THEN -5
                ELSE 0
            END
        )) >= 80 THEN 'EXCELLENT'
        WHEN LEAST(100, GREATEST(0,
            LEAST(25, total_trades * 0.5) +
            CASE 
                WHEN overall_winrate >= 70 THEN 30
                WHEN overall_winrate >= 60 THEN 25
                WHEN overall_winrate >= 50 THEN 20
                WHEN overall_winrate >= 40 THEN 10
                ELSE 0
            END +
            LEAST(20, active_days * 2) +
            LEAST(15, unique_time_slots * 1.5) +
            CASE 
                WHEN recent_winrate - overall_winrate > 10 THEN 10
                WHEN recent_winrate - overall_winrate > 5 THEN 5
                WHEN recent_winrate - overall_winrate < -10 THEN -10
                WHEN recent_winrate - overall_winrate < -5 THEN -5
                ELSE 0
            END
        )) >= 60 THEN 'GOOD'
        WHEN LEAST(100, GREATEST(0,
            LEAST(25, total_trades * 0.5) +
            CASE 
                WHEN overall_winrate >= 70 THEN 30
                WHEN overall_winrate >= 60 THEN 25
                WHEN overall_winrate >= 50 THEN 20
                WHEN overall_winrate >= 40 THEN 10
                ELSE 0
            END +
            LEAST(20, active_days * 2) +
            LEAST(15, unique_time_slots * 1.5) +
            CASE 
                WHEN recent_winrate - overall_winrate > 10 THEN 10
                WHEN recent_winrate - overall_winrate > 5 THEN 5
                WHEN recent_winrate - overall_winrate < -10 THEN -10
                WHEN recent_winrate - overall_winrate < -5 THEN -5
                ELSE 0
            END
        )) >= 40 THEN 'FAIR'
        ELSE 'POOR'
    END as overall_rating

FROM strategy_metrics
ORDER BY health_score DESC, total_trades DESC;
