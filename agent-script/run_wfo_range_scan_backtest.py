#!/usr/bin/env python3
import psycopg2
import pandas as pd
import re
import datetime as dt
from typing import List, Dict, Tuple
from database_connection import DB_CONFIG

SQL_PATH = '/Users/puchong/tradingview/agent-script/strategy_range_scanner_v1_0_0.sql'


def load_sql(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def fill_params(sql: str, *, timeframes_csv: str, start_date: str, end_date: str,
                min_trades: int, payout: float, investment: float,
                quality_mode: str, min_signal_quality: float, min_stability: float) -> str:
    replacements = {
        r"\{\{timeframes_csv\}\}": f"'{timeframes_csv}'",
        r"\{\{start_date\}\}": f"'{start_date}'",
        r"\{\{end_date\}\}": f"'{end_date}'",
        r"\{\{min_trades_per_strategy\}\}": f"'{min_trades}'",
        r"\{\{payout_rate\}\}": f"'{payout}'",
        r"\{\{investment_amount\}\}": f"'{investment}'",
        r"\{\{quality_mode\}\}": f"'{quality_mode}'",
        r"\{\{min_signal_quality\}\}": f"'{min_signal_quality}'",
        r"\{\{min_stability\}\}": f"'{min_stability}'",
    }
    for pattern, value in replacements.items():
        sql = re.sub(pattern, value, sql)
    return sql


def run_scan(start_date: str, end_date: str,
             *, timeframes_csv='10,30,60', min_trades=5, payout=0.8, investment=250,
             quality_mode='balanced', min_signal_quality=7.5, min_stability=6.0) -> pd.DataFrame:
    sql_tpl = load_sql(SQL_PATH)
    sql = fill_params(sql_tpl,
                      timeframes_csv=timeframes_csv,
                      start_date=start_date,
                      end_date=end_date,
                      min_trades=min_trades,
                      payout=payout,
                      investment=investment,
                      quality_mode=quality_mode,
                      min_signal_quality=min_signal_quality,
                      min_stability=min_stability)
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df


def freeze_buckets(df: pd.DataFrame) -> List[Dict]:
    if df.empty:
        return []
    cols = ['timeframe', 'day_of_week', 'hour_of_day', 'strategy_action']
    frozen = df[cols].drop_duplicates().to_dict('records')
    return frozen


def refine_frozen(train_df: pd.DataFrame, frozen: List[Dict]) -> List[Dict]:
    if train_df.empty or not frozen:
        return frozen
    payout = 0.8
    breakeven_pct = 100.0/(1.0+payout)
    df = train_df.copy()
    df['trade'] = pd.to_numeric(df['trade'], errors='coerce').fillna(0).astype(int)
    df['trade_win'] = pd.to_numeric(df['trade_win'], errors='coerce').fillna(0).astype(int)
    df['stability'] = pd.to_numeric(df['stability'], errors='coerce').fillna(0.0)
    df['bucket_winrate'] = pd.to_numeric(df['bucket_winrate'], errors='coerce').fillna(0.0)
    # compute Wilson LB on train
    df['p_hat'] = df.apply(lambda r: (r['trade_win']/r['trade']) if r['trade']>0 else 0.0, axis=1)
    df['wilson_lb'] = df.apply(lambda r: wilson_lower_bound(r['trade_win'], r['trade']), axis=1)
    # keep only frozen keys
    keycols = ['timeframe','day_of_week','hour_of_day','strategy_action']
    frozen_df = pd.DataFrame(frozen)
    merged = df.merge(frozen_df, on=keycols, how='inner')
    # Broad refinement across all strategies/timeframes (Train-only):
    # trades>=20, Wilson LB>=0.74, stability>=8.0, bucket_winrate>breakeven, EV/trade>=35 (stake=100)
    refined = merged[
        (merged['trade'] >= 20) &
        (merged['wilson_lb'] >= 0.74) &
        (merged['stability'] >= 8.0) &
        (merged['bucket_winrate'] > breakeven_pct)
    ].copy()
    # Open timeframe '10' to all strategies (remove UT-BOT2-10 restriction)
    # Keep only timeframe '10' to match coverage goal while avoiding overlap across TFs
    if not refined.empty:
        refined = refined[(refined['timeframe'].astype(str) == '10')].copy()
        # require bucket winrate advantage ≥ 3 percentage points over breakeven
        refined = refined[(pd.to_numeric(refined['bucket_winrate'], errors='coerce').fillna(0.0) >= (breakeven_pct + 3.0))]
        # require signal_quality ≥ 7.5 when available
        if 'signal_quality' in refined.columns:
            refined['signal_quality'] = pd.to_numeric(refined['signal_quality'], errors='coerce').fillna(0.0)
            refined = refined[refined['signal_quality'] >= 7.5]
    if not refined.empty:
        payout = 0.8
        stake = 100.0
        refined['p_hat'] = refined.apply(lambda r: (r['trade_win']/r['trade']) if r['trade']>0 else 0.0, axis=1)
        refined['ev_per_trade'] = refined['p_hat'].apply(lambda p: stake * (p*payout - (1.0-p)))
        refined = refined[refined['ev_per_trade'] >= 35.0].copy()
    if refined.empty:
        return frozen
    # score: prioritize Wilson LB, then sample size, then signal_quality if present
    if 'signal_quality' in refined.columns:
        refined['signal_quality'] = pd.to_numeric(refined['signal_quality'], errors='coerce').fillna(0.0)
        refined = refined.sort_values(['wilson_lb','trade','signal_quality'], ascending=[False, False, False])
    else:
        refined = refined.sort_values(['wilson_lb','trade'], ascending=[False, False])
    return refined[keycols].drop_duplicates().head(20).to_dict('records')


def filter_to_buckets(df: pd.DataFrame, buckets: List[Dict]) -> pd.DataFrame:
    if df.empty or not buckets:
        return df.iloc[0:0].copy()
    mask = False
    for b in buckets:
        m = (
            (df['timeframe'].astype(str) == str(b['timeframe'])) &
            (df['day_of_week'] == b['day_of_week']) &
            (df['hour_of_day'] == b['hour_of_day']) &
            (df['strategy_action'] == b['strategy_action'])
        )
        mask = m if isinstance(mask, bool) and mask is False else (mask | m)
    return df[mask].copy()


def summarize(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    if df.empty:
        per_bucket = pd.DataFrame(columns=['timeframe','day_of_week','hour_of_day','strategy_action','trade','trade_win','pnl','winrate_pct'])
        overall = {'trades': 0, 'wins': 0, 'winrate_pct': 0.0, 'pnl': 0.0}
        return per_bucket, overall
    group_cols = ['timeframe', 'day_of_week', 'hour_of_day', 'strategy_action']
    gb = df.groupby(group_cols, as_index=False).agg(
        trade=('trade','sum'),
        trade_win=('trade_win','sum'),
        pnl=('pnl','sum'),
    )
    gb['winrate_pct'] = (gb['trade_win'] / gb['trade']).where(gb['trade'] > 0, 0) * 100.0
    totals = {
        'trades': int(gb['trade'].sum()),
        'wins': int(gb['trade_win'].sum()),
        'winrate_pct': (float(gb['trade_win'].sum()) / float(gb['trade'].sum()) * 100.0) if gb['trade'].sum() > 0 else 0.0,
        'pnl': float(gb['pnl'].sum()),
    }
    return gb, totals


def daterange(start: dt.date, end: dt.date) -> List[dt.date]:
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += dt.timedelta(days=1)
    return days


def wilson_lower_bound(wins: int, n: int, z: float = 1.96) -> float:
    if n <= 0:
        return 0.0
    p_hat = wins / n
    denom = 1.0 + (z*z)/n
    centre = p_hat + (z*z)/(2*n)
    radicand = (p_hat*(1.0-p_hat) + (z*z)/(4*n)) / n
    margin = z * (radicand ** 0.5)
    return max(0.0, (centre - margin) / denom)


def fetch_raw_trades(start_date: str, end_date: str) -> pd.DataFrame:
    sql = """
    WITH base AS (
      SELECT
        t.entry_time,
        EXTRACT(DOW FROM t.entry_time)::int AS dow,
        EXTRACT(HOUR FROM t.entry_time)::int AS hr,
        t.strategy || ' | ' || t.action AS strategy_action,
        '10' AS timeframe,
        CASE WHEN t.result_10min = 'WIN' THEN 'WIN'
             WHEN t.result_10min IN ('LOSE','LOST') THEN 'LOSE' END AS result
      FROM tradingviewdata t
      WHERE t.entry_time >= %s::timestamp
        AND t.entry_time <  %s::timestamp + interval '1 day'
        AND t.result_10min IN ('WIN','LOSE')
      UNION ALL
      SELECT
        t.entry_time,
        EXTRACT(DOW FROM t.entry_time)::int AS dow,
        EXTRACT(HOUR FROM t.entry_time)::int AS hr,
        t.strategy || ' | ' || t.action AS strategy_action,
        '30' AS timeframe,
        CASE WHEN t.result_30min = 'WIN' THEN 'WIN'
             WHEN t.result_30min IN ('LOSE','LOST') THEN 'LOSE' END AS result
      FROM tradingviewdata t
      WHERE t.entry_time >= %s::timestamp
        AND t.entry_time <  %s::timestamp + interval '1 day'
        AND t.result_30min IN ('WIN','LOSE')
      UNION ALL
      SELECT
        t.entry_time,
        EXTRACT(DOW FROM t.entry_time)::int AS dow,
        EXTRACT(HOUR FROM t.entry_time)::int AS hr,
        t.strategy || ' | ' || t.action AS strategy_action,
        '60' AS timeframe,
        CASE WHEN t.result_60min = 'WIN' THEN 'WIN'
             WHEN t.result_60min IN ('LOSE','LOST') THEN 'LOSE' END AS result
      FROM tradingviewdata t
      WHERE t.entry_time >= %s::timestamp
        AND t.entry_time <  %s::timestamp + interval '1 day'
        AND t.result_60min IN ('WIN','LOSE')
    )
    SELECT * FROM base
    """
    params = (start_date, end_date, start_date, end_date, start_date, end_date)
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()


def simulate_daily(
    frozen: List[Dict],
    raw_df: pd.DataFrame,
    payout: float,
    initial_bankroll: float,
    base_stake: float,
    daily_cap: int = 3,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    if not frozen or raw_df.empty:
        return pd.DataFrame(columns=['date','trades','wins','pnl','bankroll_end']), {'daily_avg': 0.0, 'days': 0, 'pnl': 0.0, 'final_bankroll': initial_bankroll}

    # Filter to frozen membership
    frozen_set = set((str(b['timeframe']), b['day_of_week'], b['hour_of_day'], b['strategy_action']) for b in frozen)
    df = raw_df.copy()
    df['date'] = pd.to_datetime(df['entry_time']).dt.date
    df['key'] = list(zip(df['timeframe'].astype(str), df['dow'], df['hr'], df['strategy_action']))
    df = df[df['key'].isin(frozen_set)]
    if df.empty:
        return pd.DataFrame(columns=['date','trades','wins','pnl','bankroll_end']), {'daily_avg': 0.0, 'days': 0, 'pnl': 0.0, 'final_bankroll': initial_bankroll}

    # Duration per timeframe in minutes
    tf_to_min = {'10': 10, '30': 30, '60': 60}

    bankroll = float(initial_bankroll)
    results = []
    for date_val, day_df in df.sort_values('entry_time').groupby('date'):
        day_df = day_df.sort_values('entry_time').copy()
        picked_rows = []
        last_end = None
        taken = 0
        pnl = 0.0
        wins = 0
        for _, row in day_df.iterrows():
            if taken >= daily_cap:
                break
            if bankroll < 5.0:
                break
            tf = str(row['timeframe'])
            dur_min = tf_to_min.get(tf, 10)
            entry_ts = pd.to_datetime(row['entry_time'])
            end_ts = entry_ts + pd.Timedelta(minutes=dur_min)
            if last_end is not None and entry_ts < last_end:
                continue  # avoid overlapping positions
            # place trade
            stake = min(base_stake, bankroll)
            change = (stake * payout) if row['result'] == 'WIN' else (-stake)
            bankroll += change
            pnl += change
            wins += 1 if row['result'] == 'WIN' else 0
            taken += 1
            last_end = end_ts
            picked_rows.append(row)
        results.append({'date': date_val, 'trades': taken, 'wins': wins, 'pnl': pnl, 'bankroll_end': bankroll})

    res_df = pd.DataFrame(results).sort_values('date')
    days = len(res_df)
    total_pnl = float(res_df['pnl'].sum()) if days > 0 else 0.0
    daily_avg = total_pnl / days if days > 0 else 0.0
    return res_df, {'daily_avg': daily_avg, 'days': days, 'pnl': total_pnl, 'final_bankroll': bankroll}


def main():
    # Config per user (50/50 split; train strictly before test; no peeking)
    train_start = dt.date(2025, 8, 28)
    train_end   = dt.date(2025, 9, 7)   # inclusive (~11 days, ~50%)
    embargo_days = 1
    final_test_end = dt.date(2025, 9, 18)

    train_len = len(daterange(train_start, train_end))

    # Adaptive threshold grid (train-only), stop at first that yields enough buckets
    threshold_grid = [
        # (quality_mode, min_quality, min_stability, min_trades)
        ('strict',    8.5, 7.0, 10),
        ('balanced',  7.5, 6.5,  8),
        ('balanced',  7.0, 6.0,  5),
        ('practical', 7.0, 5.5,  5),
        ('practical', 6.5, 5.0,  3),
        ('practical', 0.0, 0.0,  1),
    ]

    chosen = None
    frozen = []
    last_train_df = pd.DataFrame()
    for (qm, qmin, smin, tmin) in threshold_grid:
        train_df = run_scan(
            train_start.strftime('%Y-%m-%d'), train_end.strftime('%Y-%m-%d'),
            min_trades=tmin, quality_mode=qm,
            min_signal_quality=qmin, min_stability=smin,
            timeframes_csv='10,30,60', payout=0.8, investment=250,
        )
        cand = freeze_buckets(train_df)
        print(f'Train try -> mode={qm}, q>={qmin}, s>={smin}, min_trades>={tmin} | buckets={len(cand)}')
        if len(cand) >= 1:  # accept at least 1 bucket-strategy to prioritize quality
            frozen = cand
            chosen = {'quality_mode': qm, 'min_quality': qmin, 'min_stability': smin, 'min_trades': tmin}
            last_train_df = train_df
            break

    print(f'\nTrain window: {train_start} to {train_end}')
    if chosen:
        print(f"Chosen thresholds: {chosen}")
        # refine using train-only metrics to target 300+/day feasibility
        frozen = refine_frozen(last_train_df, frozen)
        # Remove top-K truncation to use all refined buckets
        print(pd.DataFrame(frozen).to_string(index=False))
    else:
        print('No thresholds produced enough frozen buckets; fallback: UT-BOT2-10 only, trade≥10, Wilson LB≥0.70, bucket_winrate>breakeven, stability≥7.5, EV/trade≥30.')
        # Fallback: build from permissive train scan
        fallback_df = run_scan(
            train_start.strftime('%Y-%m-%d'), train_end.strftime('%Y-%m-%d'),
            min_trades=1, quality_mode='practical',
            min_signal_quality=0.0, min_stability=0.0,
            timeframes_csv='10,30,60', payout=0.8, investment=250,
        )
        if not fallback_df.empty:
            payout = 0.8
            investment = 250.0
            breakeven_pct = 100.0/(1.0+payout)
            df = fallback_df.copy()
            df['trade'] = pd.to_numeric(df['trade'], errors='coerce').fillna(0).astype(int)
            df['trade_win'] = pd.to_numeric(df['trade_win'], errors='coerce').fillna(0).astype(int)
            df['stability'] = pd.to_numeric(df['stability'], errors='coerce').fillna(0.0)
            df['signal_quality'] = pd.to_numeric(df['signal_quality'], errors='coerce').fillna(0.0)
            df['bucket_winrate'] = pd.to_numeric(df['bucket_winrate'], errors='coerce').fillna(0.0)
            df['p_hat'] = df.apply(lambda r: (r['trade_win']/r['trade']) if r['trade']>0 else 0.0, axis=1)
            df['wilson_lb'] = df.apply(lambda r: wilson_lower_bound(r['trade_win'], r['trade']), axis=1)
            df['ev_per_trade'] = df['p_hat'].apply(lambda p: investment * (p*payout - (1.0-p)))
            # Restrict to UT-BOT2-10 only
            df = df[(df['strategy_action'].astype(str).str.startswith('UT-BOT2-10')) & (df['timeframe'].astype(str) == '10')]
            sel = df[(df['trade']>=10) & (df['wilson_lb']>=0.70) & (df['bucket_winrate']>breakeven_pct) & (df['stability']>=7.5) & (df['ev_per_trade']>=30.0)]
            # score: EV then Wilson LB then sample
            sel = sel.sort_values(['ev_per_trade','wilson_lb','trade'], ascending=[False, False, False])
            cols = ['timeframe','day_of_week','hour_of_day','strategy_action']
            frozen = sel[cols].drop_duplicates().head(4).to_dict('records')
            if frozen:
                chosen = {'quality_mode': 'practical', 'min_quality': 0.0, 'min_stability': 0.0, 'min_trades': 1}
                print(pd.DataFrame(frozen).to_string(index=False))
            else:
                frozen = []
                print('Fallback also found no suitable buckets.')
        else:
            print('Fallback scan returned empty.')

    # Test windows (equal to train length where possible) with embargo
    # Single test window starting after embargo (per user example: train_end + 1 day)
    test_windows = []
    first_test_start = train_end + dt.timedelta(days=embargo_days)
    cur_start = first_test_start
    cur_end = final_test_end
    if cur_start <= cur_end:
        test_windows.append((cur_start, cur_end))

    # Execute tests using raw trades with real trading rules
    print('\nTest windows:')
    for (ts, te) in test_windows:
        print(f'  {ts} to {te}')

    daily_frames = []
    initial_bankroll = 1000.0
    base_stake = 100.0
    for (ts, te) in test_windows:
        raw = fetch_raw_trades(ts.strftime('%Y-%m-%d'), te.strftime('%Y-%m-%d'))
        daily_df, daily_summary = simulate_daily(
            frozen, raw, payout=0.8,
            initial_bankroll=initial_bankroll,
            base_stake=base_stake,
            daily_cap=5,
        )
        initial_bankroll = daily_summary.get('final_bankroll', initial_bankroll)
        if not daily_df.empty:
            daily_df['window_start'] = ts.strftime('%Y-%m-%d')
            daily_df['window_end'] = te.strftime('%Y-%m-%d')
            daily_frames.append(daily_df)

    if daily_frames:
        combined_daily = pd.concat(daily_frames, ignore_index=True)
        days = int(combined_daily.shape[0])
        total_pnl = float(combined_daily['pnl'].sum()) if days > 0 else 0.0
        daily_avg = total_pnl / days if days > 0 else 0.0
        print('\nDaily results (sample):')
        print(combined_daily.head(20).to_string(index=False))
        print('\nOverall test:')
        print(f'  days={days}, total_pnl={total_pnl:.2f}, daily_avg={daily_avg:.2f}, final_bankroll={initial_bankroll:.2f}')
    else:
        print('\nOverall test: days=0 (no trades)')


if __name__ == '__main__':
    main()


