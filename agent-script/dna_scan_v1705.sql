/*
 Time Bucket DNA Analysis - V17.0.5 (UTC + Heatmap Parity, Minimal Fields + Ratings)

 Objective:
   - bucket_winrate ตรงกับ Heatmap 100% (คำนวณจาก base_data รวมทุกสัญญาณ)
   - ตารางใช้งานง่าย: trade, winate, trade_win, pnl, expectancy_per_trade, reliability_margin_pct,
     consistency_stddev_pct, contribution_pct, bucket_total_trade, bucket_winrate
   - เพิ่มตัวสรุปสำหรับตัดสินใจ:
     * performance_rating_10 (1–10): รวมกำไรคาดหวัง/ความมั่นใจ/ปริมาณข้อมูล แบบไม่ฟิลเตอร์หนัก
       - 1–3 ต่ำ (ยังไม่น่าใช้จริง), 4–6 กลาง (ทดลองได้), 7–8 สูง (ใช้งานจริง), 9–10 สูงมาก (ตัวเต็ง)
     * stability_10 (1–10): ความนิ่งจาก stddev ของ weekly win-rate (ยิ่งสูงยิ่งนิ่ง)
       - 1–3 แกว่งมาก, 4–6 พอใช้, 7–8 ค่อนข้างนิ่ง, 9–10 นิ่งมาก

 Params (Metabase variables):
   target_interval            : '10min' | '30min' | '60min' | '10' | '30' | '60' (Text, default '10min')
   target_day_of_week         : 0-6 (Number, 0=Sun,...,6=Sat, default 0)
   target_hour                : 0-23 (Number, default 0)
   weeks_back                 : จำนวนสัปดาห์ย้อนหลัง หรือ 'all' (Text, default 'all')
   min_trades_per_strategy    : จำนวนเทรดขั้นต่ำต่อกลยุทธ์ (Number, default 1)
   payout_rate                : อัตราผลตอบแทนต่อ WIN (Number, default 0.8)
   investment_amount          : เงินลงทุนต่อ trade (Number, default 250)

 IMPORTANT (เพื่อให้ parity กับ Heatmap):
   - ตั้ง weeks_back = 'all' ถ้า Heatmap ไม่ได้จำกัดช่วงเวลา มิฉะนั้น bucket_winrate จะต่าง
   - อย่ากรอง strategy/action เพิ่มเฉพาะฝั่ง DNA ถ้า Heatmap ไม่ได้กรอง
   - Normalize ผลลัพธ์ 'LOST' -> 'LOSE' ให้เหมือนกันทั้งสองฝั่ง
   - min_trades_per_strategy มีผลเฉพาะการแสดง/ซ่อนแถว breakdown เท่านั้น ไม่กระทบ bucket_winrate
*/

WITH params AS (
  SELECT
    CASE LOWER(COALESCE(NULLIF({{target_interval}}, ''), '10min'))
      WHEN '10' THEN '10' WHEN '10min' THEN '10'
      WHEN '30' THEN '30' WHEN '30min' THEN '30'
      WHEN '60' THEN '60' WHEN '60min' THEN '60'
      ELSE '10'
    END AS timeframe,
    (CASE WHEN {{target_day_of_week}} = '' THEN 0 ELSE {{target_day_of_week}}::integer END) AS target_dow,
    (CASE WHEN {{target_hour}} = '' THEN 0 ELSE {{target_hour}}::integer END) AS target_hr,
    LOWER(COALESCE(NULLIF({{weeks_back}}, ''), 'all')) AS weeks_back_param,
    GREATEST((CASE WHEN {{min_trades_per_strategy}} = '' THEN 1 ELSE {{min_trades_per_strategy}}::integer END), 0) AS min_trades,
    (CASE WHEN {{payout_rate}} = '' THEN 0.8 ELSE {{payout_rate}}::float END) AS payout,
    (CASE WHEN {{investment_amount}} = '' THEN 250 ELSE {{investment_amount}}::float END) AS investment
),
base_data AS (
  SELECT
    EXTRACT(DOW  FROM t.entry_time)::int  AS day_of_week,
    EXTRACT(HOUR FROM t.entry_time)::int  AS hour_of_day,
    t.strategy || ' | ' || t.action       AS strategy_action,
    EXTRACT(WEEK FROM t.entry_time)::int  AS week_num,
    CASE
      WHEN p.timeframe = '10' THEN
        CASE WHEN t.result_10min = 'WIN' THEN 'WIN'
             WHEN t.result_10min IN ('LOSE','LOST') THEN 'LOSE'
             ELSE NULL END
      WHEN p.timeframe = '30' THEN
        CASE WHEN t.result_30min = 'WIN' THEN 'WIN'
             WHEN t.result_30min IN ('LOSE','LOST') THEN 'LOSE'
             ELSE NULL END
      WHEN p.timeframe = '60' THEN
        CASE WHEN t.result_60min = 'WIN' THEN 'WIN'
             WHEN t.result_60min IN ('LOSE','LOST') THEN 'LOSE'
             ELSE NULL END
    END AS normalized_result
  FROM tradingviewdata t
  CROSS JOIN params p
  WHERE
    EXTRACT(DOW  FROM t.entry_time)::int = (SELECT target_dow FROM params)
    AND EXTRACT(HOUR FROM t.entry_time)::int = (SELECT target_hr FROM params)
    AND (
      (SELECT weeks_back_param FROM params) = 'all'
      OR t.entry_time >= NOW() - ((CASE WHEN (SELECT weeks_back_param FROM params) = '' THEN '12' ELSE (SELECT weeks_back_param FROM params) END)::integer || ' weeks')::interval
    )
    AND CASE
          WHEN (SELECT timeframe FROM params) = '10' THEN t.result_10min
          WHEN (SELECT timeframe FROM params) = '30' THEN t.result_30min
          WHEN (SELECT timeframe FROM params) = '60' THEN t.result_60min
        END IN ('WIN','LOSE')
),
bucket_stats AS (
  SELECT
    COUNT(*)::int AS bucket_total_trades,
    SUM(CASE WHEN normalized_result = 'WIN' THEN 1 ELSE 0 END)::int AS bucket_total_wins,
    SUM(CASE WHEN normalized_result = 'LOSE' THEN 1 ELSE 0 END)::int AS bucket_total_losses,
    ROUND(100.0 * SUM(CASE WHEN normalized_result='WIN' THEN 1 ELSE 0 END)::numeric
          / NULLIF(COUNT(*),0), 2) AS bucket_winrate
  FROM base_data
),
strategy_weekly AS (
  SELECT
    strategy_action,
    week_num,
    COUNT(*)::int AS trades_in_week,
    SUM(CASE WHEN normalized_result='WIN' THEN 1 ELSE 0 END)::int AS wins_in_week,
    ROUND(100.0 * SUM(CASE WHEN normalized_result='WIN' THEN 1 ELSE 0 END)::numeric
          / NULLIF(COUNT(*),0), 2) AS weekly_win_rate_pct
  FROM base_data
  WHERE normalized_result IN ('WIN','LOSE')
  GROUP BY strategy_action, week_num
),
consistency_stats AS (
  SELECT
    strategy_action,
    COUNT(*)::int AS weeks_for_consistency,
    ROUND(stddev_samp(weekly_win_rate_pct)::numeric, 2) AS consistency_stddev_pct
  FROM strategy_weekly
  GROUP BY strategy_action
),
strategy_stats AS (
  SELECT
    bd.strategy_action,
    COUNT(*)::int AS total_trades,
    SUM(CASE WHEN bd.normalized_result = 'WIN' THEN 1 ELSE 0 END)::int AS total_wins,
    SUM(CASE WHEN bd.normalized_result = 'LOSE' THEN 1 ELSE 0 END)::int AS total_losses,
    ROUND(100.0 * SUM(CASE WHEN bd.normalized_result='WIN' THEN 1 ELSE 0 END)::numeric
          / NULLIF(COUNT(*),0), 2) AS win_rate,
    COUNT(DISTINCT bd.week_num)::int AS weeks_analyzed
  FROM base_data bd
  WHERE bd.normalized_result IN ('WIN','LOSE')
  GROUP BY bd.strategy_action
),
core AS (
  SELECT
    p.target_dow AS day_of_week,
    p.target_hr  AS hour_of_day,
    s.strategy_action,

    -- per-strategy fields
    s.total_trades AS trade,
    s.win_rate     AS winate,
    s.total_wins   AS trade_win,

    -- PNL รวมของสัญญาณใน bucket
    ROUND(((s.total_wins * p.payout - (s.total_trades - s.total_wins)) * p.investment)::numeric, 2) AS pnl,

    -- Expectancy ต่อเทรด (หน่วยเงิน)
    ROUND((p.investment * ((s.win_rate/100.0)*p.payout - (1 - s.win_rate/100.0)))::numeric, 2) AS expectancy_per_trade,

    -- Reliability Margin = Wilson LB − Breakeven (คำนวณ inline)
    ROUND((
      100.0 * (
        (
          ( (s.total_wins::float8/NULLIF(s.total_trades,0)) + ( (1.96*1.96)::float8 / (2*NULLIF(s.total_trades::float8,0)) ) )
          - 1.96 * sqrt(
              ( (s.total_wins::float8/NULLIF(s.total_trades,0)) * (1 - (s.total_wins::float8/NULLIF(s.total_trades,0))) / NULLIF(s.total_trades::float8,0) )
              + ( (1.96*1.96)::float8 / (4*NULLIF(s.total_trades::float8,0)*NULLIF(s.total_trades::float8,0)) )
            )
        ) / (1 + ((1.96*1.96)::float8 / NULLIF(s.total_trades::float8,0)))
      ) - 100.0/(1+p.payout)
    )::numeric, 2) AS reliability_margin_pct,

    cs.consistency_stddev_pct,
    ROUND((s.total_trades * 100.0 / NULLIF(b.bucket_total_trades,0))::numeric, 2) AS contribution_pct,

    -- Bucket summary
    b.bucket_total_trades AS bucket_total_trade,
    b.bucket_winrate      AS bucket_winrate,

    -- keep for rating formula
    p.payout, p.investment
  FROM strategy_stats s
  LEFT JOIN consistency_stats cs ON cs.strategy_action = s.strategy_action
  CROSS JOIN params p
  CROSS JOIN bucket_stats b
  WHERE s.total_trades >= p.min_trades
)
SELECT
  core.day_of_week,
  core.hour_of_day,
  core.strategy_action,

  core.trade,
  core.winate,
  core.trade_win,
  core.pnl,

  core.expectancy_per_trade,
  core.reliability_margin_pct,
  core.consistency_stddev_pct,
  core.contribution_pct,

  core.bucket_total_trade,
  core.bucket_winrate,

  -- Stability 1–10: stddev ต่ำ = คะแนนสูง (1–3 ต่ำ, 4–6 กลาง, 7–8 สูง, 9–10 สูงมาก)
  ROUND(LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(core.consistency_stddev_pct, 30.0) / 3.0)))::numeric, 2) AS stability_10,

  -- Performance 1–10: Expectancy (60%) + Confidence (25%) + Sample (15%)
  -- 1–3 ต่ำ, 4–6 กลาง, 7–8 สูง (ใช้จริงได้), 9–10 สูงมาก (ตัวเต็ง)
  ROUND((
    10.0 * (
      0.60 * LEAST(1.0, GREATEST(0.0, core.expectancy_per_trade / NULLIF(core.investment * core.payout, 0))) +
      0.25 * LEAST(1.0, GREATEST(0.0, (core.reliability_margin_pct + 10.0) / 10.0)) +
      0.15 * LEAST(1.0, GREATEST(0.0, LN(GREATEST(core.trade,1) + 1.0) / LN(51.0)))
    )
  )::numeric, 2) AS performance_rating_10

FROM core
ORDER BY performance_rating_10 DESC, stability_10 DESC, core.trade DESC, core.strategy_action;