#!/usr/bin/env python3
"""
Bucket Rating Calculator (V17.0.5 principles)
- Reads per-bucket DNA CSV files created by dna_scan_v1705.py under report/
- Computes bucket-level performance_rating_10 and stability_10
  * performance = 10 * (0.60*normExp + 0.25*normRel + 0.15*sample)
    - normExp = clamp(weighted_expectancy / (investment*payout), 0..1)
    - normRel = clamp((weighted_reliability_margin + 10)/10, 0..1)
    - sample   = clamp(ln(1+trade_sum)/ln(51), 0..1)
    - mild calibration by agreement = 1 - losing_volume_share (±10% scale)
  * stability = clamp(10 - weighted_stddev/3, 1..10)

Outputs a concise table of ratings per bucket.
"""
import os
import re
import math
import pandas as pd

INVESTMENT = 250.0
PAYOUT = 0.8
MAX_NORM = INVESTMENT * PAYOUT  # 200

REPORT_DIR = "report"

BUCKET_FILE_RE = re.compile(r"dna_v1705_dow(\d+)_hour(\d+)\.csv$")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def load_buckets():
    buckets = []
    for fn in os.listdir(REPORT_DIR):
        m = BUCKET_FILE_RE.match(fn)
        if not m:
            continue
        dow = int(m.group(1)); hour = int(m.group(2))
        path = os.path.join(REPORT_DIR, fn)
        df = pd.read_csv(path)
        if df.empty:
            continue
        buckets.append(((dow, hour), df))
    return buckets


def compute_bucket_rating(df: pd.DataFrame):
    # trade-weighted aggregates
    trade_sum = float(df["trade"].sum())
    if trade_sum <= 0:
        return None
    w = df["trade"] / trade_sum
    exp_w = float((df["expectancy_per_trade"] * w).sum())
    rel_w = float((df["reliability_margin_pct"] * w).sum())
    # stability from stddev if present (weight by trade)
    if "consistency_stddev_pct" in df.columns:
        std_w = float((df["consistency_stddev_pct"].fillna(30) * w).sum())
    else:
        std_w = 20.0
    # agreement proxy
    losing_share = float(df.loc[df["expectancy_per_trade"] <= 0, "trade"].sum() / trade_sum)
    agreement = 1.0 - losing_share

    normExp = clamp(exp_w / MAX_NORM, 0.0, 1.0)
    normRel = clamp((rel_w + 10.0) / 10.0, 0.0, 1.0)
    sample  = clamp(math.log(1.0 + trade_sum) / math.log(51.0), 0.0, 1.0)

    base_score = 10.0 * (0.60 * normExp + 0.25 * normRel + 0.15 * sample)

    # mild calibration by agreement (±10%)
    adj = clamp(0.9 + 0.2 * (agreement - 0.5), 0.8, 1.1)
    perf = round(base_score * adj, 2)

    stability = round(clamp(10.0 - (std_w / 3.0), 1.0, 10.0), 2)

    return dict(
        trade_sum=int(trade_sum), exp_w=round(exp_w,2), rel_w=round(rel_w,2), std_w=round(std_w,2),
        losing_share=round(losing_share,2), performance_rating_10=perf, stability_10=stability
    )


def main():
    rows = []
    for (dow,hour), df in load_buckets():
        m = compute_bucket_rating(df)
        if m is None:
            continue
        rows.append({"dow":dow, "hour":hour, **m})
    if not rows:
        print("No bucket files found.")
        return
    out = pd.DataFrame(rows).sort_values(["performance_rating_10","stability_10","trade_sum"], ascending=[False, False, False])
    print("Bucket ratings (dow,hour ⇒ perf/stability/trade/losing_share, exp_w, rel_w):")
    for _, r in out.iterrows():
        print(f"  (dow={int(r['dow'])}, hour={int(r['hour'])}) perf={r['performance_rating_10']:.2f} stability={r['stability_10']:.2f} trade={int(r['trade_sum'])} losing={r['losing_share']:.2f} expW={r['exp_w']:.2f} relW={r['rel_w']:.2f}")

if __name__ == "__main__":
    main()
