/*
 Signal Scan - V17.0.9 (Time Bucket → Signal) 
   Purpose:
     - Scan all day_of_week × hour_of_day across selected timeframes
     - Compute signal_quality (0–10) and stability (0–10) per V17.0.8 logic
     - Filter by user-defined thresholds and weeks_back

   Params (Metabase variables):
     timeframes_csv            : '10,30,60' (Text; accepts 10|10min|30|30min|60|60min)
     weeks_back                : 'all' or integer weeks (Text, default 'all')
     min_trades_per_strategy   : Number, default 1
     payout_rate               : Number, default 0.8
     investment_amount         : Number, default 250
     quality_mode              : 'practical' | 'balanced' | 'strict' (Text, default 'balanced')
     min_signal_quality        : Number 0–10, default 7
     min_stability             : Number 0–10, default 7
*/

WITH params AS (
  SELECT
    LOWER(COALESCE(NULLIF({{weeks_back}}, ''), 'all'))                       AS weeks_back_param,
    GREATEST((CASE WHEN {{min_trades_per_strategy}} = '' THEN 1 ELSE {{min_trades_per_strategy}}::integer END), 0) AS min_trades,
    (CASE WHEN {{payout_rate}}       = '' THEN 0.8  ELSE {{payout_rate}}::float  END) AS payout,
    (CASE WHEN {{investment_amount}} = '' THEN 250  ELSE {{investment_amount}}::float END) AS investment,
    LOWER(COALESCE(NULLIF({{quality_mode}}, ''), 'balanced'))               AS quality_mode,
    (CASE WHEN {{min_signal_quality}} = '' THEN 7 ELSE {{min_signal_quality}}::float END) AS min_signal_quality,
    (CASE WHEN {{min_stability}}      = '' THEN 7 ELSE {{min_stability}}::float END)      AS min_stability
),
frames AS (
  SELECT CASE LOWER(TRIM(val))
           WHEN '10' THEN '10' WHEN '10min' THEN '10'
           WHEN '30' THEN '30' WHEN '30min' THEN '30'
           WHEN '60' THEN '60' WHEN '60min' THEN '60'
         END AS timeframe
  FROM regexp_split_to_table(COALESCE(NULLIF({{timeframes_csv}}, ''), '10,30,60'), ',') AS val
),
buckets AS (
  SELECT d AS dow, h AS hr FROM generate_series(0,6) d CROSS JOIN generate_series(0,23) h
),
base AS (
  SELECT f.timeframe, b.dow, b.hr,
         t.strategy || ' | ' || t.action AS strategy_action,
         EXTRACT(WEEK FROM t.entry_time)::int AS week_num,
         CASE f.timeframe
           WHEN '10' THEN CASE WHEN t.result_10min = 'WIN' THEN 'WIN' WHEN t.result_10min IN ('LOSE','LOST') THEN 'LOSE' END
           WHEN '30' THEN CASE WHEN t.result_30min = 'WIN' THEN 'WIN' WHEN t.result_30min IN ('LOSE','LOST') THEN 'LOSE' END
           WHEN '60' THEN CASE WHEN t.result_60min = 'WIN' THEN 'WIN' WHEN t.result_60min IN ('LOSE','LOST') THEN 'LOSE' END
         END AS normalized_result
  FROM tradingviewdata t
  CROSS JOIN frames f
  CROSS JOIN buckets b
  CROSS JOIN params p
  WHERE EXTRACT(DOW FROM t.entry_time)::int = b.dow
    AND EXTRACT(HOUR FROM t.entry_time)::int = b.hr
    AND (
      p.weeks_back_param = 'all'
      OR t.entry_time >= NOW() - ((CASE WHEN p.weeks_back_param = '' THEN '12' ELSE p.weeks_back_param END)::integer || ' weeks')::interval
    )
    AND CASE f.timeframe
          WHEN '10' THEN t.result_10min
          WHEN '30' THEN t.result_30min
          WHEN '60' THEN t.result_60min
        END IN ('WIN','LOSE')
),
bucket_stats AS (
  SELECT timeframe, dow, hr,
         COUNT(*)::int AS bucket_total_trades,
         SUM((normalized_result='WIN')::int)::int AS bucket_total_wins,
         SUM((normalized_result='LOSE')::int)::int AS bucket_total_losses,
         ROUND(100.0 * SUM((normalized_result='WIN')::int)::numeric / NULLIF(COUNT(*),0), 2) AS bucket_winrate
  FROM base
  GROUP BY timeframe, dow, hr
),
strategy_weekly AS (
  SELECT timeframe, dow, hr, strategy_action, week_num,
         COUNT(*)::int AS trades_in_week,
         SUM((normalized_result='WIN')::int)::int AS wins_in_week,
         ROUND(100.0 * SUM((normalized_result='WIN')::int)::numeric / NULLIF(COUNT(*),0), 2) AS weekly_win_rate_pct
  FROM base
  GROUP BY timeframe, dow, hr, strategy_action, week_num
),
consistency_stats AS (
  SELECT timeframe, dow, hr, strategy_action,
         COUNT(*)::int AS weeks_for_consistency,
         ROUND(stddev_samp(weekly_win_rate_pct)::numeric, 2) AS consistency_stddev_pct
  FROM strategy_weekly
  GROUP BY timeframe, dow, hr, strategy_action
),
strategy_stats AS (
  SELECT timeframe, dow, hr, strategy_action,
         COUNT(*)::int AS total_trades,
         SUM((normalized_result='WIN')::int)::int AS total_wins,
         SUM((normalized_result='LOSE')::int)::int AS total_losses,
         ROUND(100.0 * SUM((normalized_result='WIN')::int)::numeric / NULLIF(COUNT(*),0), 2) AS win_rate
  FROM base
  GROUP BY timeframe, dow, hr, strategy_action
),
components AS (
  SELECT s.timeframe, s.dow, s.hr, s.strategy_action,
         s.total_trades, s.total_wins, s.win_rate,
         cs.consistency_stddev_pct AS stddev_pct,
         p.investment, p.payout,
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
         )::numeric AS rel_margin,
         p.quality_mode
  FROM strategy_stats s
  LEFT JOIN consistency_stats cs ON cs.timeframe=s.timeframe AND cs.dow=s.dow AND cs.hr=s.hr AND cs.strategy_action=s.strategy_action
  CROSS JOIN params p
)
SELECT
  c.timeframe,
  c.dow AS day_of_week,
  c.hr  AS hour_of_day,
  c.strategy_action,
  c.total_trades AS trade,
  c.total_wins   AS trade_win,
  c.win_rate     AS winate,
  ROUND(((c.total_wins * c.payout - (c.total_trades - c.total_wins)) * c.investment)::numeric, 2) AS pnl,
  bs.bucket_total_trades AS bucket_total_trade,
  bs.bucket_winrate,
  ROUND((c.total_trades * 100.0 / NULLIF(bs.bucket_total_trades,0))::numeric, 2) AS contribution_pct,
  -- Ratings
  ROUND((
    CASE
      WHEN c.quality_mode = 'practical' THEN 10.0 * (0.70*exp_norm + 0.20*LEAST(1.0, GREATEST(0.0, (rel_margin + 10.0)/10.0)) + 0.10*sample21)
      WHEN c.quality_mode = 'strict' THEN (
        CASE WHEN rel_margin < 0 THEN LEAST(5.0, 10.0 * (0.60*exp_norm + 0.25*LEAST(1.0, GREATEST(0.0, (rel_margin + 10.0)/10.0)) + 0.15*sample51))
             ELSE 10.0 * (0.60*exp_norm + 0.25*LEAST(1.0, GREATEST(0.0, (rel_margin + 10.0)/10.0)) + 0.15*sample51)
        END)
      ELSE LEAST(10.0, 10.0 * (0.60*exp_norm + 0.25*LEAST(1.0, GREATEST(0.0, (rel_margin + 20.0)/30.0)) + 0.15*sample21))
    END
  )::numeric, 2) AS signal_quality,
  ROUND((
    CASE
      WHEN c.quality_mode = 'practical' THEN LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(c.stddev_pct, 30.0) / 3.0)))
      WHEN c.quality_mode = 'strict'    THEN LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(c.stddev_pct, 30.0) / 2.5)))
      ELSE LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(c.stddev_pct, 30.0) / 2.8)))
    END
  )::numeric, 2) AS stability
FROM components c
JOIN bucket_stats bs ON bs.timeframe=c.timeframe AND bs.dow=c.dow AND bs.hr=c.hr
JOIN params p ON TRUE
WHERE c.total_trades >= p.min_trades
  AND (
    CASE WHEN c.quality_mode = 'strict' THEN rel_margin > 0 ELSE TRUE END
  )
  AND (
    CASE WHEN p.min_signal_quality IS NULL THEN TRUE ELSE (
      (CASE WHEN c.quality_mode='practical' THEN 10.0 * (0.70*exp_norm + 0.20*LEAST(1.0, GREATEST(0.0, (rel_margin + 10.0)/10.0)) + 0.10*sample21)
            WHEN c.quality_mode='strict' THEN (
              CASE WHEN rel_margin < 0 THEN LEAST(5.0, 10.0 * (0.60*exp_norm + 0.25*LEAST(1.0, GREATEST(0.0, (rel_margin + 10.0)/10.0)) + 0.15*sample51))
                   ELSE 10.0 * (0.60*exp_norm + 0.25*LEAST(1.0, GREATEST(0.0, (rel_margin + 10.0)/10.0)) + 0.15*sample51)
              END)
            ELSE LEAST(10.0, 10.0 * (0.60*exp_norm + 0.25*LEAST(1.0, GREATEST(0.0, (rel_margin + 20.0)/30.0)) + 0.15*sample21))
       END) >= p.min_signal_quality END
  )
  AND (
    CASE WHEN p.min_stability IS NULL THEN TRUE ELSE (
      CASE
        WHEN c.quality_mode='practical' THEN LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(c.stddev_pct, 30.0) / 3.0)))
        WHEN c.quality_mode='strict'    THEN LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(c.stddev_pct, 30.0) / 2.5)))
        ELSE LEAST(10.0, GREATEST(1.0, 10.0 - (COALESCE(c.stddev_pct, 30.0) / 2.8)))
      END >= p.min_stability END
  )
ORDER BY c.timeframe, signal_quality DESC, stability DESC, c.total_trades DESC, c.strategy_action;
