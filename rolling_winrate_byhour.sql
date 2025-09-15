/* Rolling win-rate & change by clock hour (0–23)
   Parameters:
     timeframe      : 10min | 30min | 60min
     hours_back     : number (e.g. 24, 72, 168)
     window_hours   : number (e.g. 6, 12, 24)
     strategy       : text (optional, 'all' to ignore)
     action         : text (optional, 'all' to ignore)
*/
WITH params AS (
  SELECT
    LOWER(COALESCE({{timeframe}}, '10min'))::text           AS tf,
    COALESCE({{hours_back}}  ::int, 24)                     AS hrs_back,
    COALESCE({{window_hours}}::int, 6)                      AS win_rows,
    NULLIF({{strategy}}, 'all')::text                       AS strat,
    NULLIF({{action}},   'all')::text                       AS act
), base AS (
  SELECT
    date_trunc('hour', t.entry_time)                AS bucket_hour,
    EXTRACT(HOUR FROM t.entry_time)                 AS hr,
    (p.tf = '10min' AND t.result_10min = 'WIN')::int  AS win_flag,
    (p.tf = '10min' AND t.result_10min IN ('WIN','LOSE'))::int AS trade_flag
  FROM tradingviewdata t
  CROSS JOIN params p
  WHERE t.entry_time >= NOW() - (p.hrs_back || ' hours')::interval
    AND (
      (p.tf='10min' AND t.result_10min IS NOT NULL) OR
      (p.tf='30min' AND t.result_30min IS NOT NULL) OR
      (p.tf='60min' AND t.result_60min IS NOT NULL)
    )
    AND (p.strat IS NULL OR t.strategy = p.strat)
    AND (p.act   IS NULL OR t.action   = p.act)
), per_hr AS (
  SELECT bucket_hour, hr, SUM(win_flag) AS wins, SUM(trade_flag) AS trades
  FROM base
  GROUP BY bucket_hour, hr
), cumulative AS (
  SELECT bucket_hour, hr,
         SUM(wins)   OVER (ORDER BY bucket_hour) AS cum_wins,
         SUM(trades) OVER (ORDER BY bucket_hour) AS cum_trades
  FROM per_hr
), rolling AS (
  SELECT bucket_hour, hr,
         cum_wins   - COALESCE(LAG(cum_wins,   p.win_rows) OVER (ORDER BY bucket_hour), 0) AS rolling_wins,
         cum_trades - COALESCE(LAG(cum_trades, p.win_rows) OVER (ORDER BY bucket_hour), 0) AS rolling_trades
  FROM cumulative c CROSS JOIN params p
)
SELECT hr AS hour,
       ROUND(rolling_wins*100.0/NULLIF(rolling_trades,0),2)                AS win_rate,
       rolling_trades                                                      AS total_trades,
       ROUND(
         (rolling_wins*100.0/NULLIF(rolling_trades,0)) -
         LAG(rolling_wins*100.0/NULLIF(rolling_trades,0)) OVER (ORDER BY bucket_hour),2
       )                                                                   AS win_rate_change,
       ROUND(
         CASE
           WHEN LAG(rolling_wins*100.0/NULLIF(rolling_trades,0)) OVER (ORDER BY bucket_hour) IS NULL
             THEN NULL
           ELSE (
             (rolling_wins*100.0/NULLIF(rolling_trades,0)) -
             LAG(rolling_wins*100.0/NULLIF(rolling_trades,0)) OVER (ORDER BY bucket_hour)
           ) / LAG(rolling_wins*100.0/NULLIF(rolling_trades,0)) OVER (ORDER BY bucket_hour) * 100
         END,2)                                                           AS win_rate_pct_change
FROM rolling
ORDER BY hour;
