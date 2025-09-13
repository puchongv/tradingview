#!/usr/bin/env python3
"""
Additional Pattern Analysis - หาปัจจัยเพิ่มเติมที่อาจจะพลาดไป
วิเคราะห์ปัจจัยอื่นๆ ที่ยังไม่ได้ดู เช่น day of week, price levels, sequences, etc.
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Statistical testing
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class AdditionalPatternAnalyzer:
    def __init__(self):
        """Initialize additional pattern analyzer"""
        self.connection = None
        self.data = None
        self.results = {
            'day_of_week_patterns': [],
            'day_of_month_patterns': [],
            'price_level_patterns': [],
            'sequential_patterns': [],
            'interval_comparison_patterns': [],
            'market_trend_patterns': [],
            'strategy_combination_patterns': [],
            'pnl_patterns': [],
            'price_movement_patterns': [],
            'time_decay_patterns': [],
            'additional_insights': []
        }
        
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            print("🔗 Connecting to database...")
            self.connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_data(self):
        """Load and prepare data"""
        try:
            print("📊 Loading data...")
            
            query = """
            SELECT 
                id, action, symbol, strategy, tf, entry_time, entry_price,
                price_10min, price_30min, price_60min, price_1day,
                result_10min, result_30min, result_60min, result_1day,
                pnl, created_at, updated_at, trade, martingale,
                EXTRACT(HOUR FROM entry_time) as hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(DAY FROM entry_time) as day_of_month,
                EXTRACT(WEEK FROM entry_time) as week,
                EXTRACT(MONTH FROM entry_time) as month,
                EXTRACT(DOW FROM entry_time) as dow_num,
                CASE 
                    WHEN EXTRACT(DOW FROM entry_time) = 0 THEN 'Sunday'
                    WHEN EXTRACT(DOW FROM entry_time) = 1 THEN 'Monday'
                    WHEN EXTRACT(DOW FROM entry_time) = 2 THEN 'Tuesday'
                    WHEN EXTRACT(DOW FROM entry_time) = 3 THEN 'Wednesday'
                    WHEN EXTRACT(DOW FROM entry_time) = 4 THEN 'Thursday'
                    WHEN EXTRACT(DOW FROM entry_time) = 5 THEN 'Friday'
                    WHEN EXTRACT(DOW FROM entry_time) = 6 THEN 'Saturday'
                END as day_name
            FROM tradingviewdata 
            WHERE entry_time IS NOT NULL
              AND entry_price IS NOT NULL
            ORDER BY entry_time;
            """
            
            self.data = pd.read_sql_query(query, self.connection)
            
            # Create additional features
            self.preprocess_additional_features()
            
            print(f"✅ Loaded {len(self.data)} records!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def preprocess_additional_features(self):
        """Create additional features for analysis"""
        print("🔧 Creating additional features...")
        
        # Win/loss binary columns
        for timeframe in ['10min', '30min', '60min', '1day']:
            col = f'result_{timeframe}'
            if col in self.data.columns:
                self.data[f'win_{timeframe}'] = (self.data[col] == 'WIN').astype(int)
        
        # Price change calculations
        for timeframe in ['10min', '30min', '60min', '1day']:
            price_col = f'price_{timeframe}'
            if price_col in self.data.columns and self.data[price_col].notna().sum() > 0:
                self.data[f'price_change_{timeframe}'] = ((self.data[price_col] - self.data['entry_price']) / self.data['entry_price'] * 100)
                self.data[f'abs_price_change_{timeframe}'] = abs(self.data[f'price_change_{timeframe}'])
        
        # Price level categories
        self.data['entry_price_rounded'] = self.data['entry_price'].round(-2)  # Round to nearest 100
        price_quartiles = self.data['entry_price'].quantile([0.25, 0.5, 0.75]).values
        self.data['price_quartile'] = pd.cut(self.data['entry_price'], 
                                           bins=[0] + list(price_quartiles) + [float('inf')], 
                                           labels=['Q1_Low', 'Q2_Mid_Low', 'Q3_Mid_High', 'Q4_High'])
        
        # Market trend direction
        self.data = self.data.sort_values('entry_time').reset_index(drop=True)
        self.data['price_sma_5'] = self.data['entry_price'].rolling(window=5, min_periods=1).mean()
        self.data['price_sma_20'] = self.data['entry_price'].rolling(window=20, min_periods=1).mean()
        self.data['trend_bullish'] = (self.data['price_sma_5'] > self.data['price_sma_20']).astype(int)
        
        # Sequential patterns
        self.data['prev_result'] = self.data['win_60min'].shift(1)
        self.data['next_result'] = self.data['win_60min'].shift(-1)
        self.data['prev_strategy'] = self.data['strategy'].shift(1)
        self.data['same_strategy_consecutive'] = (self.data['strategy'] == self.data['prev_strategy']).astype(int)
        
        # Time-based features
        self.data['is_weekend'] = (self.data['day_of_week'].isin([0, 6])).astype(int)
        self.data['is_month_start'] = (self.data['day_of_month'] <= 7).astype(int)
        self.data['is_month_middle'] = ((self.data['day_of_month'] > 7) & (self.data['day_of_month'] <= 21)).astype(int)
        self.data['is_month_end'] = (self.data['day_of_month'] > 21).astype(int)
        
        print(f"✅ Created additional features. Total columns: {len(self.data.columns)}")
    
    def analyze_day_of_week_patterns(self):
        """Analyze day of week patterns"""
        print("📅 Analyzing day of week patterns...")
        
        overall_win_rate = self.data['win_60min'].mean()
        dow_patterns = []
        
        for dow in range(7):
            day_data = self.data[self.data['day_of_week'] == dow]
            if len(day_data) >= 10:
                wins = day_data['win_60min'].sum()
                total = len(day_data)
                win_rate = wins / total
                
                # Statistical significance
                expected_wins = total * overall_win_rate
                if expected_wins > 5:
                    chi2, p_value = stats.chisquare([wins, total-wins], [expected_wins, total-expected_wins])
                    
                    # Strategy breakdown for this day
                    strategy_breakdown = day_data.groupby('strategy')['win_60min'].agg(['count', 'mean']).reset_index()
                    strategy_breakdown = strategy_breakdown[strategy_breakdown['count'] >= 5]  # Minimum 5 signals
                    
                    dow_patterns.append({
                        'day_of_week': dow,
                        'day_name': day_data['day_name'].iloc[0] if len(day_data) > 0 else f'Day_{dow}',
                        'win_rate': win_rate,
                        'total_signals': total,
                        'difference_from_overall': win_rate - overall_win_rate,
                        'p_value': p_value,
                        'significance': 'High' if p_value < 0.01 else 'Medium' if p_value < 0.05 else 'Low',
                        'strategy_breakdown': strategy_breakdown.to_dict('records') if len(strategy_breakdown) > 0 else []
                    })
        
        self.results['day_of_week_patterns'] = sorted(dow_patterns, 
                                                     key=lambda x: abs(x['difference_from_overall']), 
                                                     reverse=True)
    
    def analyze_price_level_patterns(self):
        """Analyze price level patterns"""
        print("💰 Analyzing price level patterns...")
        
        overall_win_rate = self.data['win_60min'].mean()
        price_patterns = []
        
        # Quartile analysis
        for quartile in ['Q1_Low', 'Q2_Mid_Low', 'Q3_Mid_High', 'Q4_High']:
            quartile_data = self.data[self.data['price_quartile'] == quartile]
            if len(quartile_data) >= 10:
                win_rate = quartile_data['win_60min'].mean()
                total = len(quartile_data)
                
                price_patterns.append({
                    'price_level': quartile,
                    'win_rate': win_rate,
                    'total_signals': total,
                    'difference_from_overall': win_rate - overall_win_rate,
                    'price_range': f"{quartile_data['entry_price'].min():.0f} - {quartile_data['entry_price'].max():.0f}"
                })
        
        # Specific price level analysis (rounded to nearest 1000)
        self.data['price_k'] = (self.data['entry_price'] / 1000).round() * 1000
        price_level_analysis = []
        
        price_groups = self.data.groupby('price_k').agg({
            'win_60min': ['count', 'mean'],
            'entry_price': ['min', 'max']
        }).round(3)
        
        price_groups.columns = ['total_signals', 'win_rate', 'min_price', 'max_price']
        price_groups = price_groups[price_groups['total_signals'] >= 20].reset_index()  # Minimum 20 signals
        
        for _, row in price_groups.iterrows():
            price_level_analysis.append({
                'price_level_k': int(row['price_k']),
                'win_rate': row['win_rate'],
                'total_signals': int(row['total_signals']),
                'difference_from_overall': row['win_rate'] - overall_win_rate,
                'price_range': f"{row['min_price']:.0f} - {row['max_price']:.0f}"
            })
        
        self.results['price_level_patterns'] = {
            'quartile_analysis': price_patterns,
            'price_level_analysis': sorted(price_level_analysis, 
                                         key=lambda x: abs(x['difference_from_overall']), 
                                         reverse=True)
        }
    
    def analyze_sequential_patterns(self):
        """Analyze sequential patterns (what happens after win/loss)"""
        print("🔄 Analyzing sequential patterns...")
        
        sequential_patterns = []
        
        # Win after win, loss after loss patterns by strategy
        for strategy in self.data['strategy'].unique():
            strategy_data = self.data[self.data['strategy'] == strategy].copy()
            if len(strategy_data) >= 20:
                
                # Patterns after win
                after_win = strategy_data[strategy_data['prev_result'] == 1]
                after_loss = strategy_data[strategy_data['prev_result'] == 0]
                
                if len(after_win) >= 5 and len(after_loss) >= 5:
                    win_after_win_rate = after_win['win_60min'].mean()
                    win_after_loss_rate = after_loss['win_60min'].mean()
                    
                    sequential_patterns.append({
                        'strategy': strategy,
                        'win_after_win_rate': win_after_win_rate,
                        'win_after_loss_rate': win_after_loss_rate,
                        'after_win_count': len(after_win),
                        'after_loss_count': len(after_loss),
                        'pattern_strength': abs(win_after_win_rate - win_after_loss_rate),
                        'momentum_effect': win_after_win_rate - win_after_loss_rate  # Positive = momentum, Negative = mean reversion
                    })
        
        # Same strategy consecutive analysis
        consecutive_analysis = []
        consecutive_data = self.data[self.data['same_strategy_consecutive'] == 1]
        non_consecutive_data = self.data[self.data['same_strategy_consecutive'] == 0]
        
        if len(consecutive_data) >= 10 and len(non_consecutive_data) >= 10:
            consecutive_win_rate = consecutive_data['win_60min'].mean()
            non_consecutive_win_rate = non_consecutive_data['win_60min'].mean()
            
            consecutive_analysis.append({
                'pattern_type': 'same_strategy_consecutive',
                'consecutive_win_rate': consecutive_win_rate,
                'non_consecutive_win_rate': non_consecutive_win_rate,
                'difference': consecutive_win_rate - non_consecutive_win_rate,
                'consecutive_count': len(consecutive_data),
                'non_consecutive_count': len(non_consecutive_data)
            })
        
        self.results['sequential_patterns'] = {
            'strategy_sequential': sorted(sequential_patterns, key=lambda x: x['pattern_strength'], reverse=True),
            'consecutive_analysis': consecutive_analysis
        }
    
    def analyze_interval_comparison(self):
        """Analyze performance across different intervals (10min vs 30min vs 60min)"""
        print("⏰ Analyzing interval comparison patterns...")
        
        interval_analysis = []
        
        # Overall interval comparison
        intervals = ['10min', '30min', '60min']
        overall_comparison = []
        
        for interval in intervals:
            win_col = f'win_{interval}'
            if win_col in self.data.columns:
                valid_data = self.data[self.data[win_col].notna()]
                if len(valid_data) > 0:
                    win_rate = valid_data[win_col].mean()
                    total_signals = len(valid_data)
                    overall_comparison.append({
                        'interval': interval,
                        'win_rate': win_rate,
                        'total_signals': total_signals
                    })
        
        # Strategy-specific interval comparison
        strategy_interval_comparison = []
        for strategy in self.data['strategy'].unique():
            strategy_data = self.data[self.data['strategy'] == strategy]
            strategy_intervals = []
            
            for interval in intervals:
                win_col = f'win_{interval}'
                if win_col in strategy_data.columns:
                    valid_data = strategy_data[strategy_data[win_col].notna()]
                    if len(valid_data) >= 10:
                        win_rate = valid_data[win_col].mean()
                        total_signals = len(valid_data)
                        strategy_intervals.append({
                            'interval': interval,
                            'win_rate': win_rate,
                            'total_signals': total_signals
                        })
            
            if len(strategy_intervals) >= 2:  # At least 2 intervals to compare
                # Find best and worst intervals
                best_interval = max(strategy_intervals, key=lambda x: x['win_rate'])
                worst_interval = min(strategy_intervals, key=lambda x: x['win_rate'])
                
                strategy_interval_comparison.append({
                    'strategy': strategy,
                    'intervals': strategy_intervals,
                    'best_interval': best_interval,
                    'worst_interval': worst_interval,
                    'interval_spread': best_interval['win_rate'] - worst_interval['win_rate']
                })
        
        self.results['interval_comparison_patterns'] = {
            'overall_comparison': overall_comparison,
            'strategy_comparison': sorted(strategy_interval_comparison, 
                                        key=lambda x: x['interval_spread'], 
                                        reverse=True)
        }
    
    def analyze_market_trend_patterns(self):
        """Analyze performance in bullish vs bearish market conditions"""
        print("📈 Analyzing market trend patterns...")
        
        overall_win_rate = self.data['win_60min'].mean()
        trend_patterns = []
        
        # Bullish vs Bearish overall
        bullish_data = self.data[self.data['trend_bullish'] == 1]
        bearish_data = self.data[self.data['trend_bullish'] == 0]
        
        if len(bullish_data) >= 10 and len(bearish_data) >= 10:
            bullish_win_rate = bullish_data['win_60min'].mean()
            bearish_win_rate = bearish_data['win_60min'].mean()
            
            trend_patterns.append({
                'market_condition': 'Overall',
                'bullish_win_rate': bullish_win_rate,
                'bearish_win_rate': bearish_win_rate,
                'bullish_count': len(bullish_data),
                'bearish_count': len(bearish_data),
                'trend_effect': bullish_win_rate - bearish_win_rate
            })
        
        # Strategy-specific trend analysis
        strategy_trend_analysis = []
        for strategy in self.data['strategy'].unique():
            strategy_data = self.data[self.data['strategy'] == strategy]
            
            bullish_strategy = strategy_data[strategy_data['trend_bullish'] == 1]
            bearish_strategy = strategy_data[strategy_data['trend_bullish'] == 0]
            
            if len(bullish_strategy) >= 5 and len(bearish_strategy) >= 5:
                bullish_win_rate = bullish_strategy['win_60min'].mean()
                bearish_win_rate = bearish_strategy['win_60min'].mean()
                
                strategy_trend_analysis.append({
                    'strategy': strategy,
                    'bullish_win_rate': bullish_win_rate,
                    'bearish_win_rate': bearish_win_rate,
                    'bullish_count': len(bullish_strategy),
                    'bearish_count': len(bearish_strategy),
                    'trend_effect': bullish_win_rate - bearish_win_rate,
                    'trend_preference': 'Bullish' if bullish_win_rate > bearish_win_rate else 'Bearish'
                })
        
        self.results['market_trend_patterns'] = {
            'overall_trend': trend_patterns,
            'strategy_trend': sorted(strategy_trend_analysis, 
                                   key=lambda x: abs(x['trend_effect']), 
                                   reverse=True)
        }
    
    def analyze_pnl_patterns(self):
        """Analyze PnL patterns if available"""
        print("💵 Analyzing PnL patterns...")
        
        pnl_patterns = []
        
        # Check if PnL data exists and is meaningful
        valid_pnl = self.data[self.data['pnl'].notna() & (self.data['pnl'] != 0)]
        
        if len(valid_pnl) > 10:
            # PnL distribution analysis
            pnl_quartiles = valid_pnl['pnl'].quantile([0.25, 0.5, 0.75]).values
            
            # Categorize PnL
            valid_pnl = valid_pnl.copy()
            valid_pnl['pnl_category'] = pd.cut(valid_pnl['pnl'], 
                                             bins=[-float('inf')] + list(pnl_quartiles) + [float('inf')], 
                                             labels=['Loss_High', 'Loss_Low', 'Profit_Low', 'Profit_High'])
            
            for category in ['Loss_High', 'Loss_Low', 'Profit_Low', 'Profit_High']:
                cat_data = valid_pnl[valid_pnl['pnl_category'] == category]
                if len(cat_data) >= 5:
                    pnl_patterns.append({
                        'pnl_category': category,
                        'win_rate': cat_data['win_60min'].mean(),
                        'count': len(cat_data),
                        'avg_pnl': cat_data['pnl'].mean(),
                        'pnl_range': f"{cat_data['pnl'].min():.2f} to {cat_data['pnl'].max():.2f}"
                    })
        else:
            pnl_patterns.append({
                'note': 'Insufficient PnL data for meaningful analysis',
                'valid_pnl_records': len(valid_pnl),
                'total_records': len(self.data)
            })
        
        self.results['pnl_patterns'] = pnl_patterns
    
    def generate_additional_insights(self):
        """Generate insights from additional patterns"""
        print("💡 Generating additional insights...")
        
        insights = []
        
        # Day of week insights
        if self.results['day_of_week_patterns']:
            best_day = max(self.results['day_of_week_patterns'], key=lambda x: x['win_rate'])
            worst_day = min(self.results['day_of_week_patterns'], key=lambda x: x['win_rate'])
            
            if best_day['total_signals'] >= 20:
                insights.append({
                    'type': 'Best Trading Day',
                    'pattern': f"{best_day['day_name']} (Day {best_day['day_of_week']})",
                    'win_rate': f"{best_day['win_rate']:.1%}",
                    'improvement': f"+{best_day['difference_from_overall']:.1%} vs overall",
                    'sample_size': best_day['total_signals'],
                    'significance': best_day['significance'],
                    'recommendation': f"Increase trading activity on {best_day['day_name']}",
                    'confidence': 'High' if best_day['significance'] in ['High', 'Medium'] else 'Low'
                })
            
            if worst_day['total_signals'] >= 20:
                insights.append({
                    'type': 'Worst Trading Day',
                    'pattern': f"{worst_day['day_name']} (Day {worst_day['day_of_week']})",
                    'win_rate': f"{worst_day['win_rate']:.1%}",
                    'decline': f"{worst_day['difference_from_overall']:.1%} vs overall",
                    'sample_size': worst_day['total_signals'],
                    'significance': worst_day['significance'],
                    'recommendation': f"Reduce or avoid trading on {worst_day['day_name']}",
                    'confidence': 'High' if worst_day['significance'] in ['High', 'Medium'] else 'Low'
                })
        
        # Price level insights
        if 'price_level_analysis' in self.results['price_level_patterns']:
            price_analysis = self.results['price_level_patterns']['price_level_analysis']
            if price_analysis:
                best_price_level = price_analysis[0]  # Already sorted by difference
                
                insights.append({
                    'type': 'Optimal Price Level',
                    'pattern': f"Price around {best_price_level['price_level_k']:.0f}K",
                    'win_rate': f"{best_price_level['win_rate']:.1%}",
                    'improvement': f"{best_price_level['difference_from_overall']:+.1%} vs overall",
                    'sample_size': best_price_level['total_signals'],
                    'price_range': best_price_level['price_range'],
                    'recommendation': f"Focus on trades when price is around {best_price_level['price_level_k']:.0f}K level",
                    'confidence': 'High' if best_price_level['total_signals'] >= 50 else 'Medium'
                })
        
        # Sequential pattern insights
        if 'strategy_sequential' in self.results['sequential_patterns']:
            seq_patterns = self.results['sequential_patterns']['strategy_sequential']
            if seq_patterns:
                strongest_momentum = max(seq_patterns, key=lambda x: x['momentum_effect'])
                
                if strongest_momentum['momentum_effect'] > 0.1:  # 10% momentum effect
                    insights.append({
                        'type': 'Momentum Strategy',
                        'pattern': f"{strongest_momentum['strategy']} shows momentum effect",
                        'win_after_win': f"{strongest_momentum['win_after_win_rate']:.1%}",
                        'win_after_loss': f"{strongest_momentum['win_after_loss_rate']:.1%}",
                        'momentum_effect': f"+{strongest_momentum['momentum_effect']:.1%}",
                        'recommendation': f"Increase confidence in {strongest_momentum['strategy']} after wins",
                        'confidence': 'High' if strongest_momentum['after_win_count'] >= 20 else 'Medium'
                    })
        
        # Market trend insights
        if 'strategy_trend' in self.results['market_trend_patterns']:
            trend_strategies = self.results['market_trend_patterns']['strategy_trend']
            if trend_strategies:
                strongest_trend_strategy = trend_strategies[0]  # Already sorted
                
                if abs(strongest_trend_strategy['trend_effect']) > 0.1:
                    insights.append({
                        'type': 'Market Trend Strategy',
                        'pattern': f"{strongest_trend_strategy['strategy']} - {strongest_trend_strategy['trend_preference']} market preference",
                        'bullish_win_rate': f"{strongest_trend_strategy['bullish_win_rate']:.1%}",
                        'bearish_win_rate': f"{strongest_trend_strategy['bearish_win_rate']:.1%}",
                        'trend_effect': f"{strongest_trend_strategy['trend_effect']:+.1%}",
                        'recommendation': f"Use {strongest_trend_strategy['strategy']} more in {strongest_trend_strategy['trend_preference']} markets",
                        'confidence': 'High' if min(strongest_trend_strategy['bullish_count'], strongest_trend_strategy['bearish_count']) >= 10 else 'Medium'
                    })
        
        self.results['additional_insights'] = sorted(insights, key=lambda x: x.get('sample_size', 0), reverse=True)
    
    def save_results(self):
        """Save additional analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'/Users/puchong/tradingview/report/additional_patterns_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate report
        report = self.generate_report()
        with open(f'/Users/puchong/tradingview/report/ADDITIONAL_PATTERNS_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Additional analysis results saved!")
    
    def generate_report(self):
        """Generate comprehensive additional patterns report"""
        report = f"""# 🔍 Additional Pattern Analysis Report
## ปัจจัยเพิ่มเติมที่อาจจะพลาดไป - วิเคราะห์เพิ่มเติม

**วันที่วิเคราะห์**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**ข้อมูลที่ใช้**: {len(self.data):,} records  
**วิธีการ**: Day of Week + Price Levels + Sequential + Market Trend + Interval Comparison

---

## 📅 **DAY OF WEEK PATTERNS**

"""
        
        if self.results['day_of_week_patterns']:
            report += "### **📊 วันที่มีผลต่อ Win Rate**\n\n"
            
            for i, day_data in enumerate(self.results['day_of_week_patterns'][:5], 1):
                trend_emoji = "📈" if day_data['difference_from_overall'] > 0 else "📉"
                sig_emoji = "🔥" if day_data['significance'] == 'High' else "⚡" if day_data['significance'] == 'Medium' else "💫"
                
                report += f"""**{sig_emoji} #{i} {day_data['day_name']}** {trend_emoji}
- **Win Rate**: {day_data['win_rate']:.1%} ({day_data['difference_from_overall']:+.1%} จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: {day_data['total_signals']} ครั้ง
- **P-value**: {day_data['p_value']:.6f}
- **ระดับนัยสำคัญ**: {day_data['significance']}

"""
        
        # Price Level Patterns
        if 'price_level_analysis' in self.results['price_level_patterns']:
            report += "\n## 💰 **PRICE LEVEL PATTERNS**\n\n"
            
            price_analysis = self.results['price_level_patterns']['price_level_analysis']
            for i, price_data in enumerate(price_analysis[:5], 1):
                trend_emoji = "📈" if price_data['difference_from_overall'] > 0 else "📉"
                
                report += f"""**#{i} Price Level {price_data['price_level_k']:.0f}K** {trend_emoji}
- **Win Rate**: {price_data['win_rate']:.1%} ({price_data['difference_from_overall']:+.1%} vs overall)
- **จำนวนสัญญาณ**: {price_data['total_signals']} ครั้ง
- **Price Range**: {price_data['price_range']}

"""
        
        # Additional Insights
        if self.results['additional_insights']:
            report += "\n## 💡 **ข้อค้นพบใหม่ที่น่าสนใจ**\n\n"
            
            for i, insight in enumerate(self.results['additional_insights'], 1):
                confidence_emoji = "🟢" if insight['confidence'] == 'High' else "🟡" if insight['confidence'] == 'Medium' else "🟠"
                
                report += f"""**{confidence_emoji} #{i} {insight['type']}**
- **Pattern**: {insight['pattern']}
"""
                
                for key, value in insight.items():
                    if key not in ['type', 'pattern', 'confidence']:
                        report += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                report += "\n"
        
        # Sequential Patterns
        if 'strategy_sequential' in self.results['sequential_patterns']:
            report += "\n## 🔄 **SEQUENTIAL PATTERNS (ลำดับ Win/Loss)**\n\n"
            
            seq_patterns = self.results['sequential_patterns']['strategy_sequential']
            for i, seq in enumerate(seq_patterns[:3], 1):
                momentum_emoji = "🚀" if seq['momentum_effect'] > 0 else "🔄"
                
                report += f"""**{momentum_emoji} #{i} {seq['strategy']}**
- **Win After Win**: {seq['win_after_win_rate']:.1%} ({seq['after_win_count']} cases)
- **Win After Loss**: {seq['win_after_loss_rate']:.1%} ({seq['after_loss_count']} cases)
- **Momentum Effect**: {seq['momentum_effect']:+.1%}
- **Pattern Type**: {"Momentum" if seq['momentum_effect'] > 0 else "Mean Reversion"}

"""
        
        # Market Trend Patterns
        if 'strategy_trend' in self.results['market_trend_patterns']:
            report += "\n## 📈 **MARKET TREND PATTERNS**\n\n"
            
            trend_strategies = self.results['market_trend_patterns']['strategy_trend']
            for i, trend in enumerate(trend_strategies[:3], 1):
                pref_emoji = "🐂" if trend['trend_preference'] == 'Bullish' else "🐻"
                
                report += f"""**{pref_emoji} #{i} {trend['strategy']} - {trend['trend_preference']} Preference**
- **Bullish Market**: {trend['bullish_win_rate']:.1%} ({trend['bullish_count']} trades)
- **Bearish Market**: {trend['bearish_win_rate']:.1%} ({trend['bearish_count']} trades)
- **Trend Effect**: {trend['trend_effect']:+.1%}

"""
        
        report += f"""
---

## 📊 **สถิติการวิเคราะห์เพิ่มเติม**

- **Day of Week Patterns**: {len(self.results['day_of_week_patterns'])} วัน
- **Price Level Patterns**: {len(self.results['price_level_patterns'].get('price_level_analysis', []))} ระดับราคา
- **Sequential Patterns**: {len(self.results['sequential_patterns'].get('strategy_sequential', []))} strategies
- **Market Trend Patterns**: {len(self.results['market_trend_patterns'].get('strategy_trend', []))} strategies
- **Additional Insights**: {len(self.results['additional_insights'])} ข้อค้นพบ

---

**รายงานนี้เป็นการวิเคราะห์ปัจจัยเพิ่มเติมที่อาจจะพลาดไปในการวิเคราะห์ครั้งแรก**
"""
        
        return report
    
    def run_complete_additional_analysis(self):
        """Run complete additional pattern analysis"""
        print("🔍 Starting Additional Pattern Analysis...")
        print("=" * 60)
        
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_data():
            return False
        
        # Run additional analyses
        self.analyze_day_of_week_patterns()
        self.analyze_price_level_patterns()
        self.analyze_sequential_patterns()
        self.analyze_interval_comparison()
        self.analyze_market_trend_patterns()
        self.analyze_pnl_patterns()
        self.generate_additional_insights()
        
        # Save results
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 Additional Pattern Analysis COMPLETE!")
        print(f"⏱️ Duration: {duration}")
        print(f"📊 Records Analyzed: {len(self.data):,}")
        print(f"💡 Additional Insights: {len(self.results['additional_insights'])}")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    analyzer = AdditionalPatternAnalyzer()
    analyzer.run_complete_additional_analysis()
