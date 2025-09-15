-- Metabase Query for Rolling Win Rate and Trend Stability Analysis (v3)
-- This version uses a simple Text filter for strategies to avoid Field Filter configuration issues.
--
-- How to use in Metabase:
-- 1. Create a new SQL question. Paste this query.
-- 2. In the variables panel on the right, configure the following:
--    a. timeframe_minutes:
--       - Type: Number
--       - Label: "Timeframe (10, 30, or 60)"
--       - Default value: 10
--    b. strategy_name:
--       - Type: Text  <-- IMPORTANT: Use Text, not Field Filter
--       - Label: "Strategy Name (leave blank for all)"
--       - Leave the default value empty.
--
-- NOTE ON ROLLING WINDOW (ค่าที่จะเอาไปใช้คำนวน):
-- The rolling window size is currently hardcoded to 30 trades (`ROWS BETWEEN 29 PRECEDING...`).
-- You must manually edit the number '29' in this query to change the window size.

WITH TimeframeSelection AS (
    -- Step 1: Select the correct result column based on the timeframe parameter.
    SELECT
        strategy,
        entry_time,
        CASE {{timeframe_minutes}}
            WHEN 30 THEN result_30min
            WHEN 60 THEN result_60min
            ELSE result_10min -- Default to 10min if the parameter is something else
        END AS result
    FROM
        tradingviewdata
    WHERE
        1=1 -- This ensures the WHERE clause is always valid.
        -- Use a simple Text filter. It's less magical but more reliable.
        -- If the `strategy_name` filter is empty, Metabase ignores this line.
        [[AND strategy = {{strategy_name}}]]
),
NumberedTrades AS (
    -- Step 2: Convert WIN/LOSE to 1/0 and filter out nulls.
    SELECT
        strategy,
        entry_time,
        CASE
            WHEN result = 'WIN' THEN 1
            ELSE 0
        END AS win_numeric
    FROM
        TimeframeSelection
    WHERE
        result IS NOT NULL
)
-- Step 3: Calculate the rolling average win rate over a 30-trade window.
SELECT
    strategy,
    entry_time,
    AVG(win_numeric) OVER (
        PARTITION BY strategy
        ORDER BY entry_time ASC
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) * 100 AS rolling_win_rate
FROM
    NumberedTrades
ORDER BY
    strategy,
    entry_time;
