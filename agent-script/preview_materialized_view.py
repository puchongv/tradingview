#!/usr/bin/env python3
"""
Preview MATERIALIZED VIEW Data
Simulates what mv_strategy_metrics_hourly will contain
"""

import psycopg2
import pandas as pd
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

def preview_materialized_view():
    """
    Preview what the MATERIALIZED VIEW will contain
    by running the same logic but returning results directly
    """
    print("=" * 100)
    print("📊 Preview: MATERIALIZED VIEW - mv_strategy_metrics_hourly")
    print("=" * 100)
    print()
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected!")
        print()
        
        # Query to simulate MATERIALIZED VIEW
        query = """
        WITH config AS (
            SELECT 
                250.0 AS default_investment,
                0.8 AS default_payout
        ),
        time_windows AS (
            SELECT unnest(ARRAY[1, 2, 3, 4, 5, 6, 12, 24, 48, 72]) AS window_hours
        ),
        strategy_list AS (
            SELECT DISTINCT
                strategy,
                action,
                symbol,
                tf
            FROM tradingviewdata
            WHERE entry_time >= NOW() - INTERVAL '72 hours'
              AND result_10min IN ('WIN', 'LOSE')
            LIMIT 5  -- Limit to 5 strategies for preview
        ),
        metrics_calc AS (
            SELECT
                sl.strategy,
                sl.action,
                sl.symbol,
                sl.tf,
                tw.window_hours,
                COUNT(*) FILTER (WHERE t.result_10min IN ('WIN', 'LOSE')) AS total_trades,
                COUNT(*) FILTER (WHERE t.result_10min = 'WIN') AS wins,
                COUNT(*) FILTER (WHERE t.result_10min = 'LOSE') AS losses,
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE t.result_10min = 'WIN')::numeric
                    / NULLIF(COUNT(*) FILTER (WHERE t.result_10min IN ('WIN', 'LOSE')), 0),
                    2
                ) AS winrate,
                -- PNL Calculation: (#WIN × investment × payout) - (#LOSE × investment)
                (
                    (COUNT(*) FILTER (WHERE t.result_10min = 'WIN')::numeric * c.default_investment * c.default_payout)
                    -
                    (COUNT(*) FILTER (WHERE t.result_10min = 'LOSE')::numeric * c.default_investment)
                ) AS pnl,
                NOW() AS last_updated
            FROM strategy_list sl
            CROSS JOIN time_windows tw
            CROSS JOIN config c
            LEFT JOIN tradingviewdata t
                ON t.strategy = sl.strategy
               AND t.action = sl.action
               AND t.symbol = sl.symbol
               AND t.tf = sl.tf
               AND t.entry_time >= NOW() - (tw.window_hours || ' hours')::INTERVAL
               AND t.result_10min IN ('WIN', 'LOSE')
            GROUP BY
                sl.strategy,
                sl.action,
                sl.symbol,
                sl.tf,
                tw.window_hours,
                c.default_investment,
                c.default_payout
        )
        SELECT
            strategy,
            action,
            symbol,
            tf,
            window_hours,
            total_trades,
            wins,
            losses,
            COALESCE(winrate, 0) AS winrate,
            pnl,
            last_updated
        FROM metrics_calc
        WHERE total_trades > 0
        ORDER BY strategy, action, window_hours;
        """
        
        print("📊 Fetching preview data...")
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("⚠️  No data found in last 72 hours")
            print("   Please check if tradingviewdata table has recent data")
            conn.close()
            return
        
        print(f"✅ Found {len(df)} records")
        print()
        
        # Show summary
        print("=" * 100)
        print("📈 SUMMARY")
        print("=" * 100)
        unique_strategies = df.groupby(['strategy', 'action']).size().reset_index(name='windows')
        print(f"Total Unique Strategies: {len(unique_strategies)}")
        print(f"Total Records: {len(df)}")
        print()
        
        # Show strategy breakdown
        print("Strategy Breakdown:")
        print("-" * 100)
        for idx, row in unique_strategies.iterrows():
            print(f"  {idx+1}. {row['strategy']} - {row['action'][:50]} ({row['windows']} time windows)")
        print()
        
        # Show sample data for first strategy
        print("=" * 100)
        print("📋 SAMPLE DATA - First Strategy (All Time Windows)")
        print("=" * 100)
        first_strategy = df.head(10)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        print(first_strategy.to_string(index=False))
        print()
        
        # Show detailed view for one strategy
        if len(df) > 0:
            sample_strategy = df['strategy'].iloc[0]
            sample_action = df['action'].iloc[0]
            strategy_data = df[
                (df['strategy'] == sample_strategy) & 
                (df['action'] == sample_action)
            ].copy()
            
            print("=" * 100)
            print(f"🔍 DETAILED VIEW: {sample_strategy} - {sample_action[:50]}")
            print("=" * 100)
            print()
            
            # Format for better visualization
            print(f"{'Window':<10} {'Trades':<10} {'Wins':<10} {'Losses':<10} {'Winrate':<12} {'PNL':<15}")
            print("-" * 100)
            for _, row in strategy_data.iterrows():
                print(f"{row['window_hours']:>3}h      "
                      f"{row['total_trades']:>6}    "
                      f"{row['wins']:>6}    "
                      f"{row['losses']:>6}    "
                      f"{row['winrate']:>6.2f}%     "
                      f"{row['pnl']:>12.2f}")
            print()
            
            # Show PNL trend
            print("PNL Trend (for Recent Performance calculation):")
            print("-" * 100)
            recent_windows = strategy_data[strategy_data['window_hours'] <= 6].sort_values('window_hours')
            if len(recent_windows) > 0:
                for _, row in recent_windows.iterrows():
                    print(f"  PNL_{row['window_hours']}h = {row['pnl']:.2f}")
                print()
                print("  This data will be used for:")
                print("  RecentScore_raw = 5×max(PNL₁−PNL₂,0) + 4×max(PNL₁−PNL₃,0) + ...")
            print()
        
        # Show how this will be used in V1.8
        print("=" * 100)
        print("💡 HOW V1.8 WILL USE THIS DATA")
        print("=" * 100)
        print()
        print("1. PNL Window Score (40 points):")
        print("   → Uses: pnl from window_hours IN (72, 48, 24, 12)")
        print()
        print("2. Winrate Consistency Score (30 points):")
        print("   → Uses: winrate from window_hours IN (72, 48, 24)")
        print()
        print("3. Recent Performance Score (30 points):")
        print("   → Uses: pnl from window_hours IN (1, 2, 3, 4, 5, 6)")
        print()
        
        # Save to CSV for reference
        output_file = "tmp/mv_preview_sample.csv"
        df.to_csv(output_file, index=False)
        print(f"💾 Full data saved to: {output_file}")
        print()
        
        # Close connection
        conn.close()
        print("✅ Preview completed!")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection Error: {e}")
        print()
        print("Please check:")
        print("  1. Database server is running")
        print("  2. Network connection to 45.77.46.180:5432")
        print("  3. Credentials are correct")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    preview_materialized_view()
