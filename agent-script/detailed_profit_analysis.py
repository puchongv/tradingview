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
    return (wins * 0.8 * bet_amount) - (losses * 1.0 * bet_amount)

try:
    conn = psycopg2.connect(**DB_CONFIG)

    # Check distribution of trades per combination
    query = '''
    SELECT 
        strategy,
        action,
        EXTRACT(DOW FROM entry_time) as day_of_week,
        EXTRACT(HOUR FROM entry_time) as hour,
        result_10min,
        result_30min,
        result_60min
    FROM tradingviewdata 
    WHERE result_10min IS NOT NULL 
    AND result_30min IS NOT NULL 
    AND result_60min IS NOT NULL
    '''

    df = pd.read_sql(query, conn)
    conn.close()

    # Convert day of week
    day_map = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    df['day_name'] = df['day_of_week'].map(day_map)

    # Check trade distribution
    trade_counts = df.groupby(['strategy', 'action', 'day_name', 'hour']).size()
    print(f'📊 Trade count distribution:')
    print(f'Min trades per combination: {trade_counts.min()}')
    print(f'Max trades per combination: {trade_counts.max()}')
    print(f'Mean trades per combination: {trade_counts.mean():.1f}')
    print(f'Median trades per combination: {trade_counts.median():.1f}')

    # Show distribution
    print(f'\n📈 Combinations with different trade counts:')
    for min_trades in [1, 2, 3, 5, 8]:
        count = (trade_counts >= min_trades).sum()
        print(f'≥{min_trades} trades: {count} combinations')

    # Analyze with lower threshold (≥3 trades) for 60min
    print(f'\n🎯 ANALYSIS WITH ≥3 TRADES THRESHOLD (60MIN):')

    analysis = df.groupby(['strategy', 'action', 'day_name', 'hour']).agg({
        'result_60min': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSE').sum()]
    }).round(2)

    analysis.columns = ['total_trades', 'wins', 'losses']
    analysis['win_rate'] = (analysis['wins'] / analysis['total_trades'] * 100).round(2)
    analysis['profit_usd'] = analysis.apply(lambda row: calculate_profit(row['wins'], row['losses']), axis=1)

    # Filter with ≥3 trades
    analysis_filtered = analysis[analysis['total_trades'] >= 3].copy()
    analysis_sorted = analysis_filtered.sort_values('profit_usd', ascending=False)

    print(f'Total combinations: {len(analysis)}')
    print(f'After filtering (≥3 trades): {len(analysis_filtered)}')

    if len(analysis_filtered) > 0:
        print(f'\n💰 TOP 10 MOST PROFITABLE (60min):')
        for i, (combo, data) in enumerate(analysis_sorted.head(10).iterrows(), 1):
            strategy, action, day, hour = combo
            profit = int(float(data['profit_usd']))
            win_rate = float(data['win_rate'])
            trades = int(float(data['total_trades']))
            hour_int = int(float(hour))
            print(f'{i:2d}. {strategy:<15} + {action:<25} @ {day:<9} {hour_int:02d}h: ${profit:6d} ({win_rate:5.1f}% WR, {trades:2d} trades)')
        
        print(f'\n📉 TOP 10 LEAST PROFITABLE (60min):')
        for i, (combo, data) in enumerate(analysis_sorted.tail(10).iterrows(), 1):
            strategy, action, day, hour = combo
            profit = int(float(data['profit_usd']))
            win_rate = float(data['win_rate'])
            trades = int(float(data['total_trades']))
            hour_int = int(float(hour))
            print(f'{i:2d}. {strategy:<15} + {action:<25} @ {day:<9} {hour_int:02d}h: ${profit:6d} ({win_rate:5.1f}% WR, {trades:2d} trades)')
    
    # Now analyze by hour only (aggregated)
    print(f'\n🕐 HOUR-ONLY ANALYSIS (≥20 trades):')
    hour_analysis = df.groupby('hour').agg({
        'result_60min': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSE').sum()]
    })
    hour_analysis.columns = ['total_trades', 'wins', 'losses']
    hour_analysis['win_rate'] = (hour_analysis['wins'] / hour_analysis['total_trades'] * 100).round(2)
    hour_analysis['profit_usd'] = hour_analysis.apply(lambda row: calculate_profit(row['wins'], row['losses']), axis=1)
    
    hour_filtered = hour_analysis[hour_analysis['total_trades'] >= 20].copy()
    hour_sorted = hour_filtered.sort_values('profit_usd', ascending=False)
    
    print(f'Hours with ≥20 trades: {len(hour_filtered)}')
    if len(hour_filtered) > 0:
        print(f'\n⏰ TOP 5 MOST PROFITABLE HOURS:')
        for hour, data in hour_sorted.head(5).iterrows():
            profit = int(float(data['profit_usd']))
            win_rate = float(data['win_rate'])
            trades = int(float(data['total_trades']))
            hour_int = int(float(hour))
            print(f'Hour {hour_int:02d}: ${profit:6d} ({win_rate:5.1f}% WR, {trades:3d} trades)')
    
    # Strategy-only analysis
    print(f'\n🎯 STRATEGY-ONLY ANALYSIS (≥50 trades):')
    strategy_analysis = df.groupby(['strategy', 'action']).agg({
        'result_60min': ['count', lambda x: (x == 'WIN').sum(), lambda x: (x == 'LOSE').sum()]
    })
    strategy_analysis.columns = ['total_trades', 'wins', 'losses']
    strategy_analysis['win_rate'] = (strategy_analysis['wins'] / strategy_analysis['total_trades'] * 100).round(2)
    strategy_analysis['profit_usd'] = strategy_analysis.apply(lambda row: calculate_profit(row['wins'], row['losses']), axis=1)
    
    strategy_filtered = strategy_analysis[strategy_analysis['total_trades'] >= 50].copy()
    strategy_sorted = strategy_filtered.sort_values('profit_usd', ascending=False)
    
    if len(strategy_filtered) > 0:
        print(f'\n🏆 TOP STRATEGIES (≥50 trades):')
        for (strategy, action), data in strategy_sorted.iterrows():
            profit = int(float(data['profit_usd']))
            win_rate = float(data['win_rate'])
            trades = int(float(data['total_trades']))
            print(f'{strategy:<15} + {action:<25}: ${profit:6d} ({win_rate:5.1f}% WR, {trades:3d} trades)')
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results = {
        'detailed_combinations': analysis_sorted.head(20).to_dict('index'),
        'hour_analysis': hour_sorted.to_dict('index'),
        'strategy_analysis': strategy_sorted.to_dict('index'),
        'summary': {
            'total_records': len(df),
            'total_combinations': len(analysis),
            'filtered_combinations_3plus': len(analysis_filtered),
            'profitable_hours': len(hour_filtered),
            'profitable_strategies': len(strategy_filtered)
        }
    }
    
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    with open(f'report/detailed_profit_analysis_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=convert_numpy)
    
    print(f'\n💾 Results saved to: report/detailed_profit_analysis_{timestamp}.json')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
