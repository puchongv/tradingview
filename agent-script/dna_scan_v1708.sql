/*
 Time Bucket DNA Analysis - V17.0.8 (UTC Alignment, Heatmap Parity)
   Objective:
     - Keep structure/filters identical to V17.0.5
     - Add quality_mode param and output 2 columns only for ratings:
       * signal_quality (0–10) = practical/balanced/strict per latest calibration
       * stability (0–10)      = consistency-based, scaled per mode (practical/balanced/strict)

   Params (Metabase variables):
     target_interval            : '10min' | '30min' | '60min' | '10' | '30' | '60' (Text, default '10min')
     target_day_of_week         : 0-6 (Number, 0=Sun,...,6=Sat, default 0)
     target_hour                : 0-23 (Number, default 0)
     weeks_back                 : จำนวนสัปดาห์ย้อนหลัง หรือ 'all' (Text, default 'all')
     min_trades_per_strategy    : จำนวนเทรดขั้นต่ำต่อกลยุทธ์ (Number, default 1)
     payout_rate                : อัตราผลตอบแทนต่อ WIN (Number, default 0.8)
     investment_amount          : เงินลงทุนต่อ trade (Number, default 250)
     quality_mode               : 'practical' | 'balanced' | 'strict' (Text, default 'balanced')
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
    (CASE WHEN {{target_hour}}       = '' THEN 0 ELSE {{target_hour}}::integer       END) AS target_hr,
    LOWER(COALESCE(NULLIF({{weeks_back}}, ''), 'all')) AS weeks_back_param,
    GREATEST((CASE WHEN {{min_trades_per_strategy}} = '' THEN 1 ELSE {{min_trades_per_strategy}}::integer END), 0) AS min_trades,
    (CASE WHEN {{payout_rate}} = '' THEN 0.8  ELSE {{payout_rate}}::float  END) AS payout,
    (CASE WHEN {{investment_amount}} = '' THEN 250  ELSE {{investment_amount}}::float END) AS investment,
    LOWER(COALESCE(NULLIF({{quality_mode}}, ''), 'balanced')) AS quality_mode
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
components AS (
  SELECT
    base.strategy_action,
    base.total_trades,
    base.total_wins,
    base.win_rate,
    base.stddev_pct,
    base.investment,
    base.payout,
    base.exp_norm,
    base.sample21,
    base.sample51,
    base.rel_margin,
    LEAST(1.0, GREATEST(0.0, (base.rel_margin + 10.0) / 10.0)) AS rel_norm_practical,
    LEAST(1.0, GREATEST(0.0, (base.rel_margin + 20.0) / 30.0)) AS rel_norm_balanced,
    LEAST(1.0, GREATEST(0.0, (base.rel_margin + 10.0) / 10.0)) AS rel_norm_strict
  FROM (
    SELECT
      s.strategy_action,
      s.total_trades,
      s.total_wins,
      s.win_rate,
      cs.consistency_stddev_pct AS stddev_pct,
      p.investment,
      p.payout,
      LEAST(1.0, GREATEST(0.0, ((p.investment * ((s.win_rate/100.0)*p.payout - (1 - s.win_rate/100.0)))::numeric / (p.investment*p.payout)::numeric))) AS exp_norm,
      LEAST(1.0, GREATEST(0.0, LN(GREATEST(s.total_trades,1) + 1.0) / LN(21.0))) AS sample21,
      LEAST(1.0, GREATEST(0.0, LN(GREATEST(s.total_trades,1) + 1.0) / LN(51.0))) AS sample51,
      (
        100.0 * (
          (
            ( (s.total_wins::float8/NULLIF(s.total_trades,0)) + ( (1.96*1.96)::float8 / (2*NULLIF(s.total_trades::float8,0)) ) )
            - 1.96 * sqrt(
                ( (s.total_wins::float8/NULLIF(s.total_trades,0)) * (1 - (s.total_wins::float8/NULLIF(s.total_trades,0))) / NULLIF(s.total_trades::float8,0) )
                + ( (1.96*1.96)::float8 / (4*NULLIF(s.total_trades::float8,0)*NULLIF(s.total_trades::float8,0)) )
              )
          ) / (1 + ((1.96*1.96)::float8 / NULLIF(s.total_trades::float8,0)))
        ) - 100.0/(1+p.payout)
      )::numeric AS rel_margin
    FROM strategy_stats s
    LEFT JOIN consistency_stats cs ON cs.strategy_action = s.strategy_action
    CROSS JOIN params p
  ) base
)
SELECT
  p.target_dow AS day_of_week,
  p.target_hr  AS hour_of_day,
  s.strategy_action,
  s.total_trades AS trade,
  s.win_rate     AS winate,
  s.total_wins   AS trade_win,
  ROUND(((s.total_wins * p.payout - (s.total_trades - s.total_wins)) * p.investment)::numeric, 2) AS pnl,
  ROUND((p.investment * ((s.win_rate/100.0)*p.payout - (1 - s.win_rate/100.0)))::numeric, 2) AS expectancy_per_trade,
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
  b.bucket_total_trades AS bucket_total_trade,
  b.bucket_winrate      AS bucket_winrate,
  -- Ratings using precomputed components
  ROUND((
    CASE
      WHEN (SELECT quality_mode FROM params) = 'practical' THEN (
        10.0 * (0.70*comp.exp_norm + 0.20*comp.rel_norm_practical + 0.10*comp.sample21)
      )
      WHEN (SELECT quality_mode FROM params) = 'strict' THEN (
        CASE WHEN comp.rel_margin < 0 THEN LEAST(5.0, 10.0 * (0.60*comp.exp_norm + 0.25*comp.rel_norm_strict + 0.15*comp.sample51))
             ELSE 10.0 * (0.60*comp.exp_norm + 0.25*comp.rel_norm_strict + 0.15*comp.sample51)
        END
      )
      ELSE (
        LEAST(10.0, 10.0 * (0.60*comp.exp_norm + 0.25*comp.rel_norm_balanced + 0.15*comp.sample21))
      )
    END
  )::numeric, 2) AS signal_quality,
  ROUND((
    CASE
      WHEN (SELECT quality_mode FROM params) = 'practical' THEN LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(comp.stddev_pct, 30.0) / 3.0)))
      WHEN (SELECT quality_mode FROM params) = 'strict'    THEN LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(comp.stddev_pct, 30.0) / 2.5)))
      ELSE LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(comp.stddev_pct, 30.0) / 2.8)))
    END
  )::numeric, 2) AS stability
FROM strategy_stats s
LEFT JOIN consistency_stats cs ON cs.strategy_action = s.strategy_action
CROSS JOIN params p
CROSS JOIN bucket_stats b
LEFT JOIN components comp ON comp.strategy_action = s.strategy_action
WHERE s.total_trades >= p.min_trades
ORDER BY expectancy_per_trade DESC, s.total_trades DESC, s.strategy_action;
