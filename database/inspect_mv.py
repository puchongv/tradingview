#!/usr/bin/env python3
"""
Inspect mv_strategy_metrics_hourly structure and data
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

conn = psycopg2.connect(**DB_CONFIG)

print("=" * 100)
print("🔍 Inspecting mv_strategy_metrics_hourly")
print("=" * 100)

# Get columns
print("\n📊 Column Structure:")
print("-" * 100)
df_cols = pd.read_sql_query("""
    SELECT 
        column_name, 
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_name = 'mv_strategy_metrics_hourly'
    ORDER BY ordinal_position;
""", conn)
print(df_cols.to_string(index=False))

# Get sample data
print("\n\n📈 Sample Data (TOP 10):")
print("-" * 100)
df_sample = pd.read_sql_query("""
    SELECT * FROM mv_strategy_metrics_hourly LIMIT 10;
""", conn)
print(df_sample.to_string(index=False))

# Get row count
print("\n\n📊 Statistics:")
print("-" * 100)
df_stats = pd.read_sql_query("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT strategy) as unique_strategies,
        COUNT(DISTINCT action) as unique_actions
    FROM mv_strategy_metrics_hourly;
""", conn)
print(df_stats.to_string(index=False))

conn.close()

print("\n" + "=" * 100)

