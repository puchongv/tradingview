import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

def calculate_profit(wins, losses, bet_amount=250):
    """Calculate profit using Binary Options formula"""
    return (wins * 0.8 * bet_amount) - (losses * 1.0 * bet_amount)

def convert_numpy(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

try:
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Query all data with time components
    query = """
    SELECT 
        strategy,
        action,
        EXTRACT(DOW FROM entry_time) as day_of_week,
        EXTRACT(HOUR FROM entry_time) as hour,
        result_10min,
        result_30min,
        result_60min,
        entry_time
    FROM tradingviewdata 
    WHERE result_10min IS NOT NULL 
    AND result_30min IS NOT NULL 
    AND result_60min IS NOT NULL
    ORDER BY entry_time
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f'✅ Loaded {len(df)} records with complete results')
    print(f'📅 Date range: {df["entry_time"].min()} to {df["entry_time"].max()}')
    
    # Convert day of week to readable format
    day_map = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    df['day_name'] = df['day_of_week'].map(day_map)
    
    results = {}
    
    # Analyze each timeframe
    for timeframe in ['10min', '30min', '60min']:
        result_col = f'result_{timeframe}'
        
        # Calculate profit for each strategy+action+day+hour combination
        analysis = df.groupby(['strategy', 'action', 'day_name', 'hour']).agg({
            result_col: ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSE').sum()]
        }).round(2)
        
        analysis.columns = ['total_trades', 'wins', 'losses']
        analysis['win_rate'] = (analysis['wins'] / analysis['total_trades'] * 100).round(2)
        analysis['profit_usd'] = analysis.apply(lambda row: calculate_profit(row['wins'], row['losses']), axis=1)
        analysis['profit_per_trade'] = (analysis['profit_usd'] / analysis['total_trades']).round(2)
        
        # Filter out noise (minimum 10 trades)
        analysis_filtered = analysis[analysis['total_trades'] >= 10].copy()
        
        # Sort by profit
        analysis_sorted = analysis_filtered.sort_values('profit_usd', ascending=False)
        
        results[timeframe] = {
            'total_combinations': len(analysis),
            'filtered_combinations': len(analysis_filtered),
            'top_10_profitable': analysis_sorted.head(10).to_dict('index'),
            'bottom_10_profitable': analysis_sorted.tail(10).to_dict('index')
        }
        
        print(f'\n🎯 {timeframe.upper()} ANALYSIS:')
        print(f'Total combinations: {len(analysis)}')
        print(f'After filtering (≥10 trades): {len(analysis_filtered)}')
        
        if len(analysis_filtered) > 0:
            print(f'\n💰 TOP 5 MOST PROFITABLE:')
            for i, (combo, data) in enumerate(analysis_sorted.head(5).iterrows(), 1):
                strategy, action, day, hour = combo
                profit = data["profit_usd"]
                win_rate = data["win_rate"]
                trades = data["total_trades"]
                print(f'{i}. {strategy} + {action} @ {day} {hour:02d}h: ${profit:,.0f} ({win_rate:.1f}% WR, {trades} trades)')
            
            print(f'\n📉 TOP 5 LEAST PROFITABLE:')
            for i, (combo, data) in enumerate(analysis_sorted.tail(5).iterrows(), 1):
                strategy, action, day, hour = combo
                profit = data["profit_usd"]
                win_rate = data["win_rate"]
                trades = data["total_trades"]
                print(f'{i}. {strategy} + {action} @ {day} {hour:02d}h: ${profit:,.0f} ({win_rate:.1f}% WR, {trades} trades)')
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'report/profit_analysis_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=convert_numpy)
    
    print(f'\n💾 Detailed results saved to: report/profit_analysis_{timestamp}.json')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
