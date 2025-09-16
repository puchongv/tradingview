/*
 [L4] The Unified Strategy Analyzer - V26
   Version: 26.0 (Added Total Trades ranking and integer formatting for PNL/Winrate)
   Objective: สร้าง Query อัจฉริยะที่สามารถแสดงผลได้ 2 รูปแบบ:
              1. (display_kpi=false): แสดง "แผนที่" ชื่อของ Strategy ที่ดีที่สุด
              2. (display_kpi=true): แสดง "KPI" ที่สอดคล้องกับ Ranking Filter ที่เลือก

   Params (กำหนดเป็น Metabase variables):
     display_kpi          : true | false (Boolean, default false)
     ranking_filter       : 'Highest PNL' | 'Highest Winrate' | 'Best Std Dev' | 'Highest Contribution' | 'Highest Total Trade' (Text)
     target_interval      : '10min' | '30min' | '60min' (Text, default '10min')
     weeks_back           : จำนวนสัปดาห์ย้อนหลัง หรือ 'all' (Text, default 'all')
     min_trades_per_bucket: จำนวนเทรดขั้นต่ำในช่องเวลานั้นๆ (Number, default 10)
     min_trades_per_strategy : จำนวนเทรดขั้นต่ำสำหรับแต่ละ Strategy (Number, default 5)
     payout_rate          : อัตราผลตอบแทนเมื่อชนะ (Number, default 0.8)
     investment_amount    : เงินลงทุนต่อไม้ (Number, default 250)
*/

WITH params AS (
  SELECT
    (CASE WHEN LOWER({{display_kpi}}::text) = 'true' THEN true ELSE false END) AS show_kpis,
    COALESCE(NULLIF({{ranking_filter}}, ''), 'Highest PNL')   AS ranking,
    LOWER(COALESCE(NULLIF({{target_interval}}, ''), '10min'))  AS timeframe,
    LOWER(COALESCE(NULLIF({{weeks_back}}, ''), 'all'))         AS weeks_back_param,
    (CASE WHEN {{min_trades_per_bucket}} = '' THEN 10 ELSE {{min_trades_per_bucket}}::integer END) AS min_trades_bucket,
    (CASE WHEN {{min_trades_per_strategy}} = '' THEN 5  ELSE {{min_trades_per_strategy}}::integer END) AS min_trades_strategy,
    (CASE WHEN {{payout_rate}} = '' THEN 0.8 ELSE {{payout_rate}}::float END) AS payout,
    (CASE WHEN {{investment_amount}} = '' THEN 250 ELSE {{investment_amount}}::float END) AS investment
),
base_data AS (
  SELECT
    EXTRACT(DOW FROM t.entry_time) AS day_of_week,
    EXTRACT(HOUR FROM t.entry_time) AS hour_of_day,
    t.strategy || ' | ' || t.action AS strategy_action,
    EXTRACT(WEEK FROM t.entry_time) AS week_num,
    (CASE WHEN p.timeframe = '10min' AND result_10min = 'WIN' THEN 1 WHEN p.timeframe = '30min' AND result_30min = 'WIN' THEN 1 WHEN p.timeframe = '60min' AND result_60min = 'WIN' THEN 1 ELSE 0 END) AS is_win,
    (CASE WHEN p.timeframe = '10min' AND result_10min IN ('WIN','LOSE') THEN 1 WHEN p.timeframe = '30min' AND result_30min IN ('WIN','LOSE') THEN 1 WHEN p.timeframe = '60min' AND result_60min IN ('WIN','LOSE') THEN 1 ELSE 0 END) AS is_trade
  FROM tradingviewdata t, params p
  WHERE (p.weeks_back_param = 'all' OR t.entry_time >= NOW() - ((CASE WHEN p.weeks_back_param = '' THEN '12' ELSE p.weeks_back_param END)::integer || ' weeks')::interval)
),
bucket_totals AS (
    SELECT day_of_week, hour_of_day, SUM(is_trade) as total_bucket_trades
    FROM base_data GROUP BY 1, 2
),
weekly_stats AS (
  SELECT day_of_week, hour_of_day, strategy_action, week_num,
         SUM(is_win) * 100.0 / NULLIF(SUM(is_trade), 0) AS weekly_win_rate
  FROM base_data GROUP BY 1, 2, 3, 4 HAVING SUM(is_trade) > 0
),
overall_stats AS (
  SELECT
    b.day_of_week, b.hour_of_day, b.strategy_action,
    ROUND(STDDEV(w.weekly_win_rate)::numeric, 2) AS consistency_stddev,
    SUM(b.is_win) AS total_wins,
    SUM(b.is_trade) - SUM(b.is_win) AS total_losses,
    SUM(b.is_trade) AS total_trades,
    ROUND((SUM(b.is_win) * 100.0 / NULLIF(SUM(b.is_trade), 0))::numeric, 2) AS win_rate
  FROM base_data b
  LEFT JOIN weekly_stats w ON b.day_of_week = w.day_of_week AND b.hour_of_day = w.hour_of_day AND b.strategy_action = w.strategy_action
  GROUP BY 1, 2, 3
),
final_scorecard AS (
  SELECT
    s.day_of_week, s.hour_of_day, s.strategy_action,
    (s.total_wins * p.payout - s.total_losses) * p.investment  AS total_pnl,
    s.win_rate,
    s.consistency_stddev,
    s.total_trades,
    ROUND((s.total_trades * 100.0 / NULLIF(bt.total_bucket_trades, 0))::numeric, 2) AS contribution_pct
  FROM overall_stats s
  JOIN params p ON 1=1
  JOIN bucket_totals bt ON s.day_of_week = bt.day_of_week AND s.hour_of_day = bt.hour_of_day
  WHERE s.total_trades >= p.min_trades_strategy AND bt.total_bucket_trades >= p.min_trades_bucket
),
ranked_scorecard AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY day_of_week, hour_of_day ORDER BY consistency_stddev ASC NULLS LAST, total_pnl DESC) AS rank_stddev,
    ROW_NUMBER() OVER (PARTITION BY day_of_week, hour_of_day ORDER BY win_rate DESC NULLS LAST, total_pnl DESC) AS rank_winrate,
    ROW_NUMBER() OVER (PARTITION BY day_of_week, hour_of_day ORDER BY total_pnl DESC NULLS LAST, win_rate DESC) AS rank_pnl,
    ROW_NUMBER() OVER (PARTITION BY day_of_week, hour_of_day ORDER BY contribution_pct DESC NULLS LAST, total_pnl DESC) AS rank_contribution,
    ROW_NUMBER() OVER (PARTITION BY day_of_week, hour_of_day ORDER BY total_trades DESC NULLS LAST, total_pnl DESC) AS rank_total_trades
  FROM final_scorecard
),
top_performers AS (
  SELECT *
  FROM ranked_scorecard, params p
  WHERE
    (p.ranking = 'Best Std Dev' AND rank_stddev = 1) OR
    (p.ranking = 'Highest Winrate' AND rank_winrate = 1) OR
    (p.ranking = 'Highest PNL' AND rank_pnl = 1) OR
    (p.ranking = 'Highest Contribution' AND rank_contribution = 1) OR
    (p.ranking = 'Highest Total Trade' AND rank_total_trades = 1)
)
-- Final Pivot Table with Dynamic Conditional Output
SELECT
  p.hour_of_day AS "Hour",
  MAX(CASE WHEN p.day_of_week = 0 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Sunday",
  MAX(CASE WHEN p.day_of_week = 1 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Monday",
  MAX(CASE WHEN p.day_of_week = 2 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Tuesday",
  MAX(CASE WHEN p.day_of_week = 3 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Wednesday",
  MAX(CASE WHEN p.day_of_week = 4 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Thursday",
  MAX(CASE WHEN p.day_of_week = 5 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Friday",
  MAX(CASE WHEN p.day_of_week = 6 THEN
      CASE
        WHEN NOT params.show_kpis THEN p.strategy_action
        WHEN params.ranking = 'Highest PNL' THEN p.total_pnl::integer::text
        WHEN params.ranking = 'Highest Winrate' THEN p.win_rate::integer::text
        WHEN params.ranking = 'Best Std Dev' THEN p.consistency_stddev::text
        WHEN params.ranking = 'Highest Contribution' THEN p.contribution_pct::text
        WHEN params.ranking = 'Highest Total Trade' THEN p.total_trades::text
      END
  END) AS "Saturday"
FROM top_performers p, params
GROUP BY p.hour_of_day
ORDER BY p.hour_of_day;

