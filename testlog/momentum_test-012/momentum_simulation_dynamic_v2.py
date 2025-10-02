#!/usr/bin/env python3
"""Test: 012 - Rate of Growth (Option E)"""
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
    """Option E: Rate of Growth"""
    p1, p2, p3, p4, p5, p6 = pnls
    r1 = (p1 - p2) / max(abs(p2), 1) if p2 != 0 else (p1 - p2)
    r2 = (p2 - p3) / max(abs(p3), 1) if p3 != 0 else (p2 - p3)
    r3 = (p3 - p4) / max(abs(p4), 1) if p4 != 0 else (p3 - p4)
    r4 = (p4 - p5) / max(abs(p5), 1) if p5 != 0 else (p4 - p5)
    r5 = (p5 - p6) / max(abs(p6), 1) if p6 != 0 else (p5 - p6)
    return (5 * max(r1, 0) * 100 + 4 * max(r2, 0) * 100 + 3 * max(r3, 0) * 100 + 2 * max(r4, 0) * 100 + 1 * max(r5, 0) * 100)

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
            ps = []
            for i in range(6):
                li = hi - i
                if li >= 0: ps.append(hp[ah[li]].get(st, 0))
                else: ps.append(0)
            rr = calculate_momentum_score(ps)
            rrs.append(rr)
            scs[st] = {'pnl': ps[0], 'recent_raw': rr, 'score': 0}
        rk = np.mean(rrs) + np.std(rrs) if np.std(rrs) > 0 else 1
        for st in scs:
            raw = scs[st]['recent_raw']
            scs[st]['score'] = min((raw / rk) * 30, 30) if rk > 0 else 0
        ss = sorted(scs.items(), key=lambda x: x[1]['score'], reverse=True)
        t6 = [s[0] for s in ss[:TOP_N]]
        bs = t6[0]
        if v and hi % 24 == 0: print(f"⏰ {hs} PNL=${tp:.0f} TOP: {bs.split('|')[0].strip()}")
        if cs != bs:
            if cs is not None: sc.append({'time': h, 'from': cs, 'to': bs})
            cs = bs
        ct = df[(df['strategy_action'] == bs) & (df['hour'] == h)]
        for _, t in ct.iterrows():
            pc = WIN_PROFIT if t['result_10min'] == 'WIN' else LOSE_LOSS
            tp += pc
            tr.append({'time': t['entry_time'], 'strategy': bs, 'result': t['result_10min'], 'pnl': pc, 'total_pnl': tp})
    if v: print(f"\n{'='*120}\n💰 FINAL: ${tp:.0f} | Trades: {len(tr)} | Changes: {len(sc)}\n{'='*120}")
    return {'total_pnl': tp, 'trades': tr, 'strategy_changes': sc, 'all_strategies': fs}

if __name__ == "__main__":
    print("="*120 + "\n🚀 Test 012: Rate of Growth (Option E)\n" + "="*120)
    r = run_simulation('2025-09-01 00:00:00', '2025-09-30 23:59:59', True)
    print(f"✅ Test 012 Complete! Final PNL: ${r['total_pnl']:.0f}")
