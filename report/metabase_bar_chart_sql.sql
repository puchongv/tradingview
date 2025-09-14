-- SQL สำหรับ Bar Chart วิเคราะห์ Noise
-- เป้าหมาย: ดู pattern ของแต่ละ strategy ตาม day เพื่อหา noise
-- 
-- 🎯 NOISE FILTERING STRATEGY:
-- 1. กรองข้อมูลที่มี sample size น้อยเกินไป (< 2 trades/day)
-- 2. กรองช่วงเวลาที่เหมาะสม (30 วันล่าสุด)
-- 3. กรองข้อมูลที่ไม่สมบูรณ์ (result_60min IS NOT NULL)
-- 4. จัดกลุ่มตาม volume และ performance เพื่อเห็น pattern

WITH params AS (
  SELECT
    LOWER(COALESCE({{period}}, 'month'))::text AS period,
    COALESCE({{investment}}::numeric, 250)::numeric AS investment,
    COALESCE({{payout}}::numeric, 0.80)::numeric AS payout,
    CASE
      WHEN LOWER(COALESCE({{interval_target}}, '60m')) IN ('10','10m','10min') THEN '10min'
      WHEN LOWER(COALESCE({{interval_target}}, '60m')) IN ('30','30m','30min') THEN '30min'
      WHEN LOWER(COALESCE({{interval_target}}, '60m')) IN ('60','60m','60min') THEN '60min'
      ELSE '60min'
    END AS horizon_target
),
filtered AS (
  SELECT
    t.strategy, 
    t.action, 
    t.entry_time,
    t.result_10min, 
    t.result_30min, 
    t.result_60min,
    (t.entry_time AT TIME ZONE 'Asia/Bangkok')::date AS day,
    -- เพิ่ม day name สำหรับ analysis
    CASE EXTRACT(DOW FROM t.entry_time)
      WHEN 0 THEN 'Sunday'
      WHEN 1 THEN 'Monday' 
      WHEN 2 THEN 'Tuesday'
      WHEN 3 THEN 'Wednesday'
      WHEN 4 THEN 'Thursday'
      WHEN 5 THEN 'Friday'
      WHEN 6 THEN 'Saturday'
    END AS day_name,
    EXTRACT(HOUR FROM t.entry_time)::int AS hour
  FROM tradingviewdata t
  CROSS JOIN params p
  WHERE 
    -- 📅 FILTER 1: Time Range (เอาแค่ 30 วันล่าสุด เพื่อดูข้อมูลปัจจุบัน)
    t.entry_time >= (now() - interval '30 days') 
    
    -- 🎯 FILTER 2: Complete Data Only (เอาแค่ข้อมูลที่มีผลลัพธ์ครบ)
    AND t.result_60min IS NOT NULL
    AND t.result_60min IN ('WIN', 'LOSE')  -- เอาแค่ผลลัพธ์ที่ชัดเจน
    
    -- ⏰ FILTER 3: Trading Hours (เอาแค่ช่วงเวลาที่มีการเทรดจริง)
    AND EXTRACT(HOUR FROM t.entry_time) BETWEEN 0 AND 23
    
    -- 💰 FILTER 4: Valid Strategies (กรอง strategy ที่เราสนใจ)
    AND t.strategy IS NOT NULL
    AND t.action IS NOT NULL
    
    -- 🚫 OPTIONAL FILTERS (uncomment ถ้าต้องการใช้):
    -- AND t.strategy NOT IN ('Range FRAMA3-99')  -- หลีกเลี่ยง strategy ที่แย่
    -- AND EXTRACT(HOUR FROM t.entry_time) NOT IN (19, 22, 23)  -- หลีกเลี่ยง death zones
    -- AND EXTRACT(DOW FROM t.entry_time) NOT IN (2)  -- หลีกเลี่ยงวันอังคาร
),
daily_strategy_agg AS (
  SELECT
    day,
    day_name,
    strategy,
    action,
    COUNT(*)::bigint AS total_trades,
    SUM((result_60min='WIN')::int)::bigint AS wins,
    SUM((result_60min='LOSE')::int)::bigint AS losses,
    ROUND(100.0 * SUM((result_60min='WIN')::int)::numeric / COUNT(*), 2) AS win_rate,
    -- คำนวณ PnL แบบ Binary Options
    (
      (SELECT payout FROM params) * SUM((result_60min='WIN')::int)::numeric * (SELECT investment FROM params)
      - SUM((result_60min='LOSE')::int)::numeric * (SELECT investment FROM params)
    ) AS pnl
  FROM filtered
  GROUP BY day, day_name, strategy, action
  HAVING COUNT(*) >= 2 -- กรอง noise: อย่างน้อย 2 trades/day
)
SELECT
  day,
  day_name,
  strategy,
  action,
  total_trades,
  win_rate,
  pnl,
  -- เพิ่ม metrics สำหรับ noise analysis
  CASE 
    WHEN total_trades >= 10 THEN 'High Volume'
    WHEN total_trades >= 5 THEN 'Medium Volume'
    ELSE 'Low Volume'
  END AS volume_category,
  CASE
    WHEN pnl > 500 THEN 'Highly Profitable'
    WHEN pnl > 0 THEN 'Profitable'
    WHEN pnl > -500 THEN 'Small Loss'
    ELSE 'Large Loss'
  END AS profit_category,
  -- Consistency score (ใช้สำหรับ identify noise)
  CASE
    WHEN win_rate >= 70 THEN 'Very Consistent'
    WHEN win_rate >= 60 THEN 'Consistent'  
    WHEN win_rate >= 40 THEN 'Inconsistent'
    ELSE 'Very Inconsistent'
  END AS consistency_level
FROM daily_strategy_agg
ORDER BY day DESC, pnl DESC;

-- Alternative: Aggregated by Day (สำหรับ Bar Chart ที่ไม่มี error)
/*
SELECT
  day,
  day_name,
  SUM(total_trades) AS total_daily_trades,
  AVG(win_rate) AS avg_win_rate,
  SUM(pnl) AS total_daily_pnl,
  COUNT(DISTINCT CONCAT(strategy, '-', action)) AS active_strategies,
  -- Noise indicator
  STDDEV(pnl) AS pnl_volatility,
  MAX(pnl) - MIN(pnl) AS pnl_range
FROM daily_strategy_agg  
GROUP BY day, day_name
ORDER BY day DESC;
*/
