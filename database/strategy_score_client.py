#!/usr/bin/env python3
"""
Strategy Score Client
Description: Python client for querying strategy scores
Author: AI Assistant
Created: 2025-10-02
"""

import psycopg2
import pandas as pd
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class StrategyScoreClient:
    """Client for querying strategy scores from database"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or DB_CONFIG
    
    def get_current_scores(self, top_n=10):
        """Get current hour's top N strategy scores"""
        conn = psycopg2.connect(**self.db_config)
        
        query = f"""
        SELECT 
            ROW_NUMBER() OVER (ORDER BY score DESC) as rank,
            strategy_action,
            strategy,
            action,
            current_pnl,
            momentum,
            acceleration,
            recent_raw,
            score,
            trade_count,
            win_count,
            win_rate,
            current_hour
        FROM strategy_score_acceleration
        WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
        ORDER BY score DESC
        LIMIT {top_n};
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_strategy_history(self, strategy_action, hours=24):
        """Get historical scores for a specific strategy"""
        conn = psycopg2.connect(**self.db_config)
        
        query = f"""
        SELECT 
            current_hour,
            current_pnl,
            momentum,
            acceleration,
            score,
            trade_count,
            win_count,
            win_rate
        FROM strategy_score_acceleration
        WHERE strategy_action = '{strategy_action}'
            AND current_hour >= NOW() - INTERVAL '{hours} hours'
        ORDER BY current_hour DESC;
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_summary_stats(self):
        """Get summary statistics for current hour"""
        conn = psycopg2.connect(**self.db_config)
        
        query = """
        SELECT 
            current_hour,
            COUNT(*) as total_strategies,
            ROUND(AVG(score), 2) as avg_score,
            ROUND(MAX(score), 2) as max_score,
            ROUND(MIN(score), 2) as min_score,
            SUM(trade_count) as total_trades,
            SUM(win_count) as total_wins,
            ROUND((SUM(win_count)::numeric / NULLIF(SUM(trade_count), 0)) * 100, 2) as overall_win_rate
        FROM strategy_score_acceleration
        WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
        GROUP BY current_hour;
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def refresh_view(self):
        """Manually refresh the materialized view"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute("REFRESH MATERIALIZED VIEW strategy_score_acceleration;")
            conn.commit()
            print(f"✅ View refreshed successfully at {datetime.now()}")
            return True
        except Exception as e:
            print(f"❌ Error refreshing view: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_top_strategy(self):
        """Get the single best strategy right now"""
        df = self.get_current_scores(top_n=1)
        if len(df) > 0:
            return df.iloc[0].to_dict()
        return None


# Example usage
if __name__ == "__main__":
    client = StrategyScoreClient()
    
    print("=" * 80)
    print("🎯 Strategy Score Client - Example Usage")
    print("=" * 80)
    
    # Get TOP 10 scores
    print("\n📊 TOP 10 Current Scores:")
    scores = client.get_current_scores(top_n=10)
    print(scores.to_string(index=False))
    
    # Get summary stats
    print("\n📈 Summary Statistics:")
    stats = client.get_summary_stats()
    print(stats.to_string(index=False))
    
    # Get best strategy
    print("\n🏆 Best Strategy:")
    best = client.get_top_strategy()
    if best:
        print(f"  Strategy: {best['strategy_action']}")
        print(f"  Score: {best['score']:.2f}")
        print(f"  PNL: ${best['current_pnl']:.0f}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
    
    print("\n" + "=" * 80)

