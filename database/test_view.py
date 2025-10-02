#!/usr/bin/env python3
"""
Test Strategy Score View
"""
import psycopg2
import pandas as pd

DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

print("=" * 100)
print("📊 Testing Strategy Score View")
print("=" * 100)

conn = psycopg2.connect(**DB_CONFIG)

# Get TOP 10 scores
print("\n🏆 TOP 10 Current Scores:")
print("-" * 100)

query = """
SELECT 
    ROW_NUMBER() OVER (ORDER BY score DESC) as rank,
    strategy_action,
    ROUND(current_pnl::numeric, 0) as pnl,
    ROUND(momentum::numeric, 0) as momentum,
    ROUND(acceleration::numeric, 0) as accel,
    ROUND(score::numeric, 2) as score,
    trade_count,
    win_count,
    ROUND(win_rate::numeric, 1) as win_rate,
    current_hour
FROM strategy_score_acceleration
WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
ORDER BY score DESC
LIMIT 10;
"""

df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))

# Get summary stats
print("\n\n📈 Summary Statistics:")
print("-" * 100)

query2 = """
SELECT 
    current_hour,
    COUNT(*) as total_strategies,
    ROUND(AVG(score)::numeric, 2) as avg_score,
    ROUND(MAX(score)::numeric, 2) as max_score,
    ROUND(MIN(score)::numeric, 2) as min_score,
    SUM(trade_count) as total_trades,
    SUM(win_count) as total_wins,
    ROUND((SUM(win_count)::numeric / NULLIF(SUM(trade_count), 0)) * 100, 2) as overall_win_rate
FROM strategy_score_acceleration
WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
GROUP BY current_hour;
"""

df2 = pd.read_sql_query(query2, conn)
print(df2.to_string(index=False))

conn.close()

print("\n" + "=" * 100)
print("✅ Test Complete!")
print("=" * 100)

