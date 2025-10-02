#!/usr/bin/env python3
"""
DNA Scanner (V17.0.5 logic) for selected buckets
- Parameters fixed per user: interval=10min, min_trades=1, payout=0.8, investment=250, weeks_back='all'
- Buckets: provided list of (dow, hour)
- Saves per-bucket CSV under report/, prints concise summaries for approval
"""
import os
import psycopg2
import pandas as pd
from datetime import datetime
from database_connection import DB_CONFIG

SQL_V1705 = """
WITH params AS (
  SELECT
    CASE LOWER(COALESCE(NULLIF(%(target_interval)s, ''), '10min'))
      WHEN '10' THEN '10' WHEN '10min' THEN '10'
      WHEN '30' THEN '30' WHEN '30min' THEN '30'
      WHEN '60' THEN '60' WHEN '60min' THEN '60'
      ELSE '10'
    END AS timeframe,
    (CASE WHEN %(target_day_of_week)s::text = '' THEN 0 ELSE %(target_day_of_week)s::integer END) AS target_dow,
    (CASE WHEN %(target_hour)s::text       = '' THEN 0 ELSE %(target_hour)s::integer       END) AS target_hr,
    LOWER(COALESCE(NULLIF(%(weeks_back)s, ''), 'all')) AS weeks_back_param,
    GREATEST((CASE WHEN %(min_trades_per_strategy)s::text = '' THEN 1 ELSE %(min_trades_per_strategy)s::integer END), 0) AS min_trades,
    (CASE WHEN %(payout_rate)s::text       = '' THEN 0.8  ELSE %(payout_rate)s::float       END) AS payout,
    (CASE WHEN %(investment_amount)s::text = '' THEN 250  ELSE %(investment_amount)s::float END) AS investment
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
)
SELECT
  p.target_dow AS day_of_week,
  p.target_hr AS hour_of_day,
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
  b.bucket_winrate      AS bucket_winrate
FROM strategy_stats s
LEFT JOIN consistency_stats cs ON cs.strategy_action = s.strategy_action
CROSS JOIN params p
CROSS JOIN bucket_stats b
WHERE s.total_trades >= (SELECT min_trades FROM params)
ORDER BY expectancy_per_trade DESC, s.total_trades DESC, s.strategy_action;
"""

BUCKETS = [
  # High
  (0,16), (3,9), (6,16), (6,11),
  # Mid
  (1,11), (0,10), (0,2), (6,19),
  # Low
  (0,21), (3,6), (0,19), (4,19),
  # Explicit danger + near-55 (previous set)
  (1,2), (2,2), (2,20), (1,1), (6,20),
  # New near-55 additions
  (0,7), (4,14), (6,14), (3,19), (1,21), (3,5)
]

def scan_bucket(conn, dow: int, hour: int) -> pd.DataFrame:
    params = dict(
        target_interval='10min',
        target_day_of_week=dow,
        target_hour=hour,
        weeks_back='all',
        min_trades_per_strategy=1,
        payout_rate=0.8,
        investment_amount=250,
    )
    df = pd.read_sql_query(SQL_V1705, conn, params=params)
    return df


def summarize_bucket(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"trade_sum":0, "wins_sum":0, "losing_volume_share":None, "top_exp":None}
    trade_sum = int(df["trade"].sum())
    wins_sum  = int(df["trade_win"].sum())
    losing_volume = int(df.loc[df["expectancy_per_trade"] <= 0, "trade"].sum())
    losing_volume_share = round(losing_volume / trade_sum, 2) if trade_sum>0 else None
    top_row = df.sort_values(["expectancy_per_trade","trade"], ascending=[False, False]).head(1)
    top_exp = None
    if not top_row.empty:
        r = top_row.iloc[0]
        top_exp = dict(strategy_action=r["strategy_action"], exp=float(r["expectancy_per_trade"]), trade=int(r["trade"]))
    return {"trade_sum":trade_sum, "wins_sum":wins_sum, "losing_volume_share":losing_volume_share, "top_exp":top_exp}


def main():
    os.makedirs("report", exist_ok=True)
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        print("Scanning DNA V17.0.5 with params: interval=10min, min_trades=1, payout=0.8, investment=250, weeks_back=all")
        for idx,(dow,hour) in enumerate(BUCKETS, start=1):
            print(f"[{idx}/{len(BUCKETS)}] Bucket (dow={dow}, hour={hour}) ...", flush=True)
            df = scan_bucket(conn, dow, hour)
            out_csv = f"report/dna_v1705_dow{dow}_hour{hour}.csv"
            df.to_csv(out_csv, index=False)
            summary = summarize_bucket(df)
            print(f"  -> rows={len(df)} trade_sum={summary['trade_sum']} wins_sum={summary['wins_sum']} losing_share={summary['losing_volume_share']}")
            if summary["top_exp"]:
                te = summary["top_exp"]
                print(f"  -> top_exp: {te['strategy_action']} exp={te['exp']} trade={te['trade']}")
    finally:
        conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
