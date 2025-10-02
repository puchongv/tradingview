#!/usr/bin/env python3
import psycopg2
import pandas as pd
import re
from database_connection import DB_CONFIG

SQL_PATH = '/Users/puchong/tradingview/agent-script/strategy_scanner_v1_0_0.sql'

def load_sql(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def fill_params(sql, *, timeframes_csv='10,30,60', weeks_back='all', min_trades=1, payout=0.8, investment=250, quality_mode='strict', min_signal_quality=8, min_stability=5):
    repl = {
        r"\{\{timeframes_csv\}\}": f"'{timeframes_csv}'",
        r"\{\{weeks_back\}\}": f"'{weeks_back}'",
        r"\{\{min_trades_per_strategy\}\}": f"'{min_trades}'",
        r"\{\{payout_rate\}\}": f"'{payout}'",
        r"\{\{investment_amount\}\}": f"'{investment}'",
        r"\{\{quality_mode\}\}": f"'{quality_mode}'",
        r"\{\{min_signal_quality\}\}": f"'{min_signal_quality}'",
        r"\{\{min_stability\}\}": f"'{min_stability}'",
    }
    for k,v in repl.items():
        sql = re.sub(k, v, sql)
    return sql

def main():
    sql = load_sql(SQL_PATH)
    # Use requested parameters
    sql = fill_params(sql,
                      timeframes_csv='10,30,60',
                      weeks_back='1',
                      min_trades=3,
                      payout=0.8,
                      investment=250,
                      quality_mode='practical',
                      min_signal_quality=6.5,
                      min_stability=5)
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql_query(sql, conn)
        print(f"Rows: {len(df)}")
        print(df.head(20).to_string(index=False))
    finally:
        conn.close()

if __name__ == '__main__':
    main()
