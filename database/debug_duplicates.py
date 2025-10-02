#!/usr/bin/env python3
"""
Debug why duplicates still exist
"""
import psycopg2

DB_CONFIG = {
    'host': '45.77.46.180',
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("\n" + "="*80)
print("🔍 Debugging Duplicate Issue")
print("="*80 + "\n")

# Check: How many distinct hours do we have for SuperTrend9 | Sell?
print("1️⃣ Checking hours for SuperTrend9 | Sell:\n")
cur.execute("""
    SELECT 
        SPLIT_PART(strategy_action, ' | ', 1) as strategy,
        SPLIT_PART(strategy_action, ' | ', 2) as action,
        current_hour,
        p1, p2, p3,
        recent_raw
    FROM (
        WITH 
        hourly_trades AS (
            SELECT 
                strategy,
                action,
                strategy || ' | ' || action as strategy_action,
                DATE_TRUNC('hour', entry_time) as hour,
                CASE 
                    WHEN result_10min = 'WIN' THEN 50 
                    ELSE -50 
                END as pnl_value
            FROM tradingviewdata
            WHERE 
                action IN ('Buy', 'Sell')
                AND result_10min IS NOT NULL
                AND entry_time >= NOW() - INTERVAL '30 days'
        ),
        cumulative_pnl AS (
            SELECT 
                strategy_action,
                hour,
                SUM(pnl_value) OVER (
                    PARTITION BY strategy_action 
                    ORDER BY hour 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) as cumulative_pnl
            FROM hourly_trades
        ),
        hourly_pnl_latest AS (
            SELECT DISTINCT ON (strategy_action, hour)
                strategy_action,
                hour,
                cumulative_pnl
            FROM cumulative_pnl
            ORDER BY strategy_action, hour, cumulative_pnl DESC
        ),
        pnl_windows AS (
            SELECT 
                a.strategy_action,
                a.hour as current_hour,
                COALESCE(a.cumulative_pnl, 0) as p1,
                COALESCE(LAG(a.cumulative_pnl, 1) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p2,
                COALESCE(LAG(a.cumulative_pnl, 2) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p3
            FROM hourly_pnl_latest a
        ),
        momentum_calc AS (
            SELECT 
                strategy_action,
                current_hour,
                p1, p2, p3,
                (p1 - p2) as m1,
                (p2 - p3) as m2,
                ((p1 - p2) - (p2 - p3)) as acceleration
            FROM pnl_windows
        ),
        raw_scores AS (
            SELECT 
                strategy_action,
                current_hour,
                p1, p2, p3,
                (5.0 * GREATEST(m1, 0) + 3.0 * GREATEST(acceleration, 0)) as recent_raw
            FROM momentum_calc
        )
        SELECT * FROM raw_scores
    ) t
    WHERE t.strategy_action = 'SuperTrend9 | Sell'
    ORDER BY current_hour DESC
    LIMIT 10;
""")

for row in cur.fetchall():
    print(f"  {row[0]:<20} {row[1]:<10} {row[2]} P1={row[3]:>6.0f} P2={row[4]:>6.0f} P3={row[5]:>6.0f} Raw={row[6]:>6.0f}")

# Check what's the MAX hour
print("\n2️⃣ What's the MAX current_hour in raw_scores?\n")
cur.execute("""
    WITH 
    hourly_trades AS (
        SELECT 
            strategy,
            action,
            strategy || ' | ' || action as strategy_action,
            DATE_TRUNC('hour', entry_time) as hour,
            CASE 
                WHEN result_10min = 'WIN' THEN 50 
                ELSE -50 
            END as pnl_value
        FROM tradingviewdata
        WHERE 
            action IN ('Buy', 'Sell')
            AND result_10min IS NOT NULL
            AND entry_time >= NOW() - INTERVAL '30 days'
    ),
    cumulative_pnl AS (
        SELECT 
            strategy_action,
            hour,
            SUM(pnl_value) OVER (
                PARTITION BY strategy_action 
                ORDER BY hour 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) as cumulative_pnl
        FROM hourly_trades
    ),
    hourly_pnl_latest AS (
        SELECT DISTINCT ON (strategy_action, hour)
            strategy_action,
            hour,
            cumulative_pnl
        FROM cumulative_pnl
        ORDER BY strategy_action, hour, cumulative_pnl DESC
    ),
    pnl_windows AS (
        SELECT 
            a.strategy_action,
            a.hour as current_hour,
            COALESCE(a.cumulative_pnl, 0) as p1,
            COALESCE(LAG(a.cumulative_pnl, 1) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p2,
            COALESCE(LAG(a.cumulative_pnl, 2) OVER (PARTITION BY a.strategy_action ORDER BY a.hour), 0) as p3
        FROM hourly_pnl_latest a
    ),
    momentum_calc AS (
        SELECT 
            strategy_action,
            current_hour,
            p1, p2, p3,
            (p1 - p2) as m1,
            (p2 - p3) as m2,
            ((p1 - p2) - (p2 - p3)) as acceleration
        FROM pnl_windows
    ),
    raw_scores AS (
        SELECT 
            strategy_action,
            current_hour,
            p1, p2, p3,
            (5.0 * GREATEST(m1, 0) + 3.0 * GREATEST(acceleration, 0)) as recent_raw
        FROM momentum_calc
    )
    SELECT MAX(current_hour) FROM raw_scores;
""")

max_hour = cur.fetchone()[0]
print(f"  MAX hour: {max_hour}")

print("\n3️⃣ How many rows in the final view?\n")
cur.execute("SELECT COUNT(*) FROM strategy_acceleration_score;")
total = cur.fetchone()[0]
print(f"  Total rows: {total}")

print("\n" + "="*80 + "\n")

cur.close()
conn.close()

