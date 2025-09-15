import pandas as pd
import psycopg2
import json
from datetime import datetime
import os

# --- Database Connection Configuration ---
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

def fetch_trading_data(conn):
    """Fetches trading data from the tradingviewdata table for the 10-minute timeframe."""
    if not conn:
        return None
    
    # Query specifically for the 10-minute result, aliased as 'result' for compatibility
    query = "SELECT strategy, entry_time, result_10min AS result FROM tradingviewdata WHERE result_10min IS NOT NULL ORDER BY entry_time ASC;"
    try:
        df = pd.read_sql_query(query, conn)
        print(f"Successfully fetched {len(df)} records for 10-minute timeframe from the database.")
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_stability(df, window_size=30):
    """
    Calculates the stability of win rates for each strategy.
    
    Stability is defined by the standard deviation of the rolling win rate.
    A lower standard deviation indicates higher stability.
    """
    if df is None or df.empty:
        return None

    # Convert result to a numerical format (1 for WIN, 0 for LOSE)
    df['win'] = df['result'].apply(lambda x: 1 if x == 'WIN' else 0)
    
    # Ensure entry_time is in datetime format and sort
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df = df.sort_values('entry_time')

    results = []
    strategies = df['strategy'].unique()

    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy].copy()
        
        if len(strategy_df) < window_size:
            print(f"Skipping strategy '{strategy}': Not enough data for rolling window (needs {window_size}, has {len(strategy_df)}).")
            continue

        # Calculate rolling win rate
        strategy_df['rolling_win_rate'] = strategy_df['win'].rolling(window=window_size, min_periods=window_size).mean() * 100
        
        # Drop initial NaN values where the window was not full
        strategy_df.dropna(subset=['rolling_win_rate'], inplace=True)

        if strategy_df.empty:
            print(f"Skipping strategy '{strategy}': No valid rolling win rate data after dropping NaNs.")
            continue
            
        # Calculate stability metrics
        stability_score = strategy_df['rolling_win_rate'].std()
        overall_win_rate = (strategy_df['win'].mean()) * 100
        total_trades = len(strategy_df)
        
        results.append({
            'strategy': strategy,
            'total_trades': total_trades,
            'overall_win_rate': round(overall_win_rate, 2),
            'win_rate_stability_score': round(stability_score, 2), # Lower is more stable
            'comment': 'Lower score indicates higher stability (less fluctuation in win rate).'
        })

    # Sort results by stability score (most stable first)
    sorted_results = sorted(results, key=lambda x: x['win_rate_stability_score'])
    
    return sorted_results

def main():
    """Main function to run the stability analysis."""
    conn = get_db_connection()
    if conn:
        trading_data_df = fetch_trading_data(conn)
        conn.close()

        if trading_data_df is not None:
            analysis_results = calculate_stability(trading_data_df)
            
            if analysis_results:
                # Get the absolute path for the report directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                report_dir = os.path.join(script_dir, '..', 'report')
                os.makedirs(report_dir, exist_ok=True)

                # Save results to a JSON file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = os.path.join(report_dir, f'winrate_stability_analysis_10min_{timestamp}.json')
                
                with open(output_filename, 'w') as f:
                    json.dump(analysis_results, f, indent=4)
                
                print(f"\nAnalysis complete. Results saved to '{output_filename}'")
                print("\n--- Win Rate Stability Report (10-minute Timeframe, Most Stable First) ---")
                for res in analysis_results:
                    print(f"  - Strategy: {res['strategy']:<15} | Stability Score: {res['win_rate_stability_score']:<6} | Overall Win Rate: {res['overall_win_rate']}% ({res['total_trades']} trades)")
            else:
                print("Could not generate analysis results for the 10-minute timeframe.")
    else:
        print("Failed to get database connection. Aborting.")

if __name__ == "__main__":
    main()
