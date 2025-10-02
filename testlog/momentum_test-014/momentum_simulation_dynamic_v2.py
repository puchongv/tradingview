#!/usr/bin/env python3
"""Test: 014 - Penalty (Option G)"""
import psycopg2
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DB_CONFIG = {'host': '45.77.46.180', 'port': 5432, 'database': 'TradingView', 'user': 'postgres', 'password': 'pwd@root99'}
BET_SIZE, PAYOUT, WIN_PROFIT, LOSE_LOSS, TOP_N = 250, 0.8, 200, -250, 6

def fetch_all_strategy_actions(s, e):
    c = psycopg2.connect(**DB_CONFIG)
    d = pd.read_sql_query(f"SELECT DISTINCT strategy, action, strategy || ' | ' || action as fn FROM tradingviewdata WHERE entry_time >= '{s}' AND entry_time < '{e}' AND result_10min IS NOT NULL ORDER BY strategy, action;", c)
    c.close()
    return d['fn'].tolist(), d['strategy'].unique(), d['action'].unique()

def fetch_trading_data(s, e):
    c = psycopg2.connect(**DB_CONFIG)
    d = pd.read_sql_query(f"SELECT strategy, action, entry_time, result_10min, CASE WHEN result_10min = 'WIN' THEN 50 ELSE -50 END as pnl_value FROM tradingviewdata WHERE entry_time >= '{s}' AND entry_time < '{e}' AND result_10min IS NOT NULL ORDER BY entry_time;", c)
    c.close()
    return d

def calculate_hourly_pnl(df, fs):
    df['strategy_action'], df['hour'] = df['strategy'] + ' | ' + df['action'], df['entry_time'].dt.floor('H')
    hp = {}
    for s in fs:
        ds = df[df['strategy_action'] == s].copy()
        if len(ds) > 0:
            ds['cumulative_pnl'] = ds['pnl_value'].cumsum()
            for h, g in ds.groupby('hour'):
                if h not in hp: hp[h] = {}
                hp[h][s] = g['cumulative_pnl'].iloc[-1]
    ah = sorted(hp.keys())
    for s in fs:
        pp = 0
        for h in ah:
            if s not in hp[h]: hp[h][s] = pp
            else: pp = hp[h][s]
    return hp, ah

def calculate_momentum_score(pnls):
    """Option G: Penalty"""
    p1, p2, p3, p4, p5, p6 = pnls
    m1, m2, m3, m4, m5 = p1 - p2, p2 - p3, p3 - p4, p4 - p5, p5 - p6
    return (5 * max(m1, 0) - 2.0 * max(-m1, 0) + 4 * max(m2, 0) - 1.5 * max(-m2, 0) + 3 * max(m3, 0) - 1.0 * max(-m3, 0) + 2 * max(m4, 0) + 1 * max(m5, 0))

def run_simulation(s, e, v=True):
    fs, bs, a = fetch_all_strategy_actions(s, e)
    if v: print(f"📊 {len(bs)} strategies, {len(a)} actions, {len(fs)} combinations\n")
    df = fetch_trading_data(s, e)
    hp, ah = calculate_hourly_pnl(df, fs)
    cs, tp, tr, sc = None, 0, [], []
    for hi, h in enumerate(ah):
        hs = h.strftime('%d/%m %H:%M')
        scs, rrs = {}, []
        for st in fs:
            ps = [hp[ah[hi - i]].get(st, 0) if hi - i >= 0 else 0 for i in range(6)]
            rr = calculate_momentum_score(ps)
            rrs.append(rr)
            scs[st] = {'pnl': ps[0], 'recent_raw': rr, 'score': 0}
        rk = np.mean(rrs) + np.std(rrs) if np.std(rrs) > 0 else 1
        for st in scs: scs[st]['score'] = min((scs[st]['recent_raw'] / rk) * 30, 30) if rk > 0 else 0
        ss = sorted(scs.items(), key=lambda x: x[1]['score'], reverse=True)
        bs = ss[0][0]
        if v and hi % 24 == 0: print(f"⏰ {hs} PNL=${tp:.0f}")
        if cs != bs:
            if cs: sc.append({'time': h, 'from': cs, 'to': bs})
            cs = bs
        for _, t in df[(df['strategy_action'] == bs) & (df['hour'] == h)].iterrows():
            pc = WIN_PROFIT if t['result_10min'] == 'WIN' else LOSE_LOSS
            tp += pc
            tr.append({})
    if v: print(f"\n{'='*120}\n💰 FINAL: ${tp:.0f} | Trades: {len(tr)} | Changes: {len(sc)}\n{'='*120}")
    return {'total_pnl': tp, 'trades': tr, 'strategy_changes': sc}

if __name__ == "__main__":
    print("="*120 + "\n🚀 Test 014: Penalty (Option G)\n" + "="*120)
    r = run_simulation('2025-09-01 00:00:00', '2025-09-30 23:59:59', True)
    print(f"✅ Test 014 Complete! Final PNL: ${r['total_pnl']:.0f}")
