#!/usr/bin/env python3
"""
Heatmap Bucket Scanner (10min)
- Connects to PostgreSQL using existing DB config
- Runs provided heatmap SQLs for winrate and total signals
- Builds per-bucket (dow, hour) table
- Selects candidate buckets across high/mid/low bands for further DNA scan

Usage: python heatmap_bucket_scanner.py
"""
import psycopg2
import pandas as pd
from database_connection import DB_CONFIG

WINRATE_SQL = """
WITH p AS (
  SELECT CASE LOWER(COALESCE(%s, '60'))
           WHEN '10'  THEN '10' WHEN '10min' THEN '10'
           WHEN '30'  THEN '30' WHEN '30min' THEN '30'
           WHEN '60'  THEN '60' WHEN '60min' THEN '60'
           ELSE '60'
         END AS tgt
),
src AS (
  SELECT
    EXTRACT(HOUR FROM t.entry_time)::int AS hour,
    EXTRACT(DOW  FROM t.entry_time)::int AS dow,
    CASE (SELECT tgt FROM p)
      WHEN '10' THEN t.result_10min
      WHEN '30' THEN t.result_30min
      WHEN '60' THEN t.result_60min
    END AS result_target
  FROM tradingviewdata t
  WHERE (CASE (SELECT tgt FROM p)
           WHEN '10' THEN t.result_10min
           WHEN '30' THEN t.result_30min
           WHEN '60' THEN t.result_60min
         END) IN ('WIN','LOSE')
),
agg AS (
  SELECT hour, dow,
         COUNT(*) AS total,
         SUM((result_target='WIN')::int) AS wins
  FROM src GROUP BY hour, dow
)
SELECT
  hour,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=0)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=0),0), 2) AS sun,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=1)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=1),0), 2) AS mon,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=2)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=2),0), 2) AS tue,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=3)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=3),0), 2) AS wed,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=4)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=4),0), 2) AS thu,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=5)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=5),0), 2) AS fri,
  ROUND(100.0 * SUM(wins) FILTER (WHERE dow=6)::numeric / NULLIF(SUM(total) FILTER (WHERE dow=6),0), 2) AS sat
FROM agg
GROUP BY hour
ORDER BY hour;
"""

TOTAL_SQL = """
WITH p AS (
  SELECT CASE LOWER(COALESCE(%s, '60'))
           WHEN '10'  THEN '10' WHEN '10min' THEN '10'
           WHEN '30'  THEN '30' WHEN '30min' THEN '30'
           WHEN '60'  THEN '60' WHEN '60min' THEN '60'
           ELSE '60'
         END AS tgt
),
src AS (
  SELECT
    EXTRACT(HOUR FROM t.entry_time)::int AS hour,
    EXTRACT(DOW  FROM t.entry_time)::int AS dow,
    CASE (SELECT tgt FROM p)
      WHEN '10' THEN t.result_10min
      WHEN '30' THEN t.result_30min
      WHEN '60' THEN t.result_60min
    END AS result_target
  FROM tradingviewdata t
  WHERE (CASE (SELECT tgt FROM p)
           WHEN '10' THEN t.result_10min
           WHEN '30' THEN t.result_30min
           WHEN '60' THEN t.result_60min
         END) IN ('WIN','LOSE')
),
agg AS (
  SELECT hour, dow, COUNT(*) AS total
  FROM src
  GROUP BY hour, dow
)
SELECT
  hour,
  COALESCE(SUM(total) FILTER (WHERE dow = 0), 0) AS sun,
  COALESCE(SUM(total) FILTER (WHERE dow = 1), 0) AS mon,
  COALESCE(SUM(total) FILTER (WHERE dow = 2), 0) AS tue,
  COALESCE(SUM(total) FILTER (WHERE dow = 3), 0) AS wed,
  COALESCE(SUM(total) FILTER (WHERE dow = 4), 0) AS thu,
  COALESCE(SUM(total) FILTER (WHERE dow = 5), 0) AS fri,
  COALESCE(SUM(total) FILTER (WHERE dow = 6), 0) AS sat,
  SUM(total) AS total_all
FROM agg
GROUP BY hour
ORDER BY hour;
"""

def melt_heatmap(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    # df columns: hour, sun..sat
    day_map = {"sun":0, "mon":1, "tue":2, "wed":3, "thu":4, "fri":5, "sat":6}
    records = []
    for _, row in df.iterrows():
        hour = int(row["hour"])
        for day_name, dow in day_map.items():
            val = row.get(day_name)
            if pd.isna(val):
                continue
            records.append({"dow": dow, "hour": hour, value_name: float(val)})
    return pd.DataFrame(records)


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(WINRATE_SQL, ("10min",))
            wr_rows = cur.fetchall()
            wr_cols = [desc[0] for desc in cur.description]
            wr_df = pd.DataFrame(wr_rows, columns=wr_cols)

            cur.execute(TOTAL_SQL, ("10min",))
            tt_rows = cur.fetchall()
            tt_cols = [desc[0] for desc in cur.description]
            tt_df = pd.DataFrame(tt_rows, columns=tt_cols)
    finally:
        conn.close()

    wr_long = melt_heatmap(wr_df, "winrate")
    tt_long = melt_heatmap(tt_df, "signals")
    grid = wr_long.merge(tt_long, on=["dow", "hour"], how="inner")

    # Select candidates by bands
    high = grid[(grid["winrate"] >= 75) & (grid["signals"] >= 20)].copy()
    mid  = grid[(grid["winrate"].between(55, 65, inclusive="left")) & (grid["signals"].between(20, 60, inclusive="both"))].copy()
    low  = grid[(grid["winrate"] <= 40) & (grid["signals"] >= 20)].copy()

    # Pick top-N per band by signals descending to ensure robustness
    def pick(df, n):
        if df.empty:
            return df
        return df.sort_values(["signals", "winrate"], ascending=[False, False]).head(n)

    cand_high = pick(high, 4)
    cand_mid  = pick(mid, 4)
    cand_low  = pick(low, 4)

    result = pd.concat([
        cand_high.assign(band="high"),
        cand_mid.assign(band="mid"),
        cand_low.assign(band="low")
    ], ignore_index=True)

    # User-requested danger buckets near specific coordinates and near-breakeven
    danger_list = [(0,2), (1,2), (2,2), (2,20)]
    # Include more 4-5 buckets: low winrate (<=45) but high volume (>=30)
    extra_low = grid[(grid["winrate"] <= 45) & (grid["signals"] >= 30)].copy()
    extra_low = extra_low.sort_values(["signals", "winrate"], ascending=[False, True]).head(5)

    print("Proposed target buckets (dow, hour, winrate, signals, band):")
    if not result.empty:
        result = result.sort_values(["band", "signals"], ascending=[True, False])
        for _, r in result.iterrows():
            print(f"  (dow={int(r['dow'])}, hour={int(r['hour'])}) wr={r['winrate']:.2f}% signals={int(r['signals'])} band={r['band']}")

    print("\nDanger buckets (explicit & near-breakeven requests):")
    # explicit
    for (d,h) in danger_list:
        row = grid[(grid["dow"]==d) & (grid["hour"]==h)]
        if not row.empty:
            wr = float(row.iloc[0]["winrate"]) ; sig = int(row.iloc[0]["signals"]) ;
            print(f"  explicit (dow={d}, hour={h}) wr={wr:.2f}% signals={sig}")
    # near-breakeven candidates (55±3)
    near = grid[(grid["winrate"]>=52) & (grid["winrate"]<=58) & (grid["signals"]>=25)].copy()
    near = near.sort_values(["signals"], ascending=[False]).head(12)
    for _, r in near.iterrows():
        print(f"  near-55 (dow={int(r['dow'])}, hour={int(r['hour'])}) wr={r['winrate']:.2f}% signals={int(r['signals'])}")

    print("\nAdditional low-winrate, high-volume candidates:")
    for _, r in extra_low.iterrows():
        print(f"  lowN (dow={int(r['dow'])}, hour={int(r['hour'])}) wr={r['winrate']:.2f}% signals={int(r['signals'])}")

if __name__ == "__main__":
    main()
