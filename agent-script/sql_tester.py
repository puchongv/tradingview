#!/usr/bin/env python3
import psycopg2, sys, re
from database_connection import DB_CONFIG

def load_and_fill(path: str) -> str:
    sql = open(path, 'r', encoding='utf-8').read()
    # Replace Metabase params with values that satisfy CASE expressions
    repl = {
        r"\{\{target_interval\}\}": "'10min'",
        r"\{\{target_day_of_week\}\}": "'0'",
        r"\{\{target_hour\}\}": "'0'",
        r"\{\{weeks_back\}\}": "'all'",
        r"\{\{min_trades_per_strategy\}\}": "'1'",
        r"\{\{payout_rate\}\}": "'0.8'",
        r"\{\{investment_amount\}\}": "'250'",
        r"\{\{quality_mode\}\}": "'balanced'",
    }
    for k,v in repl.items():
        sql = re.sub(k, v, sql)
    return sql

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'agent-script/dna_scan_v1708.sql'
    q = load_and_fill(path)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(q)
        rows = cur.fetchmany(5)
        print(f"OK, got {len(rows)} rows")
        for r in rows:
            print(r[:5])
    except Exception as e:
        print("ERROR:", e)
        m = re.search(r"Position: (\d+)", str(e))
        if m:
            pos = int(m.group(1))
            start = max(0, pos-200)
            end = min(len(q), pos+200)
            print("Context:\n", q[start:end])
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass
