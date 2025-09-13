#!/usr/bin/env python3
"""
PURE MARKET PATTERN ANALYSIS - ไม่แคร์สัญญาน แค่มองตลาด
วิเคราะห์ว่าตลาดเอง มี pattern ไหนบ้างที่ชัดเจน โดยไม่พึ่งพา signal quality
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class PureMarketPatternAnalyzer:
    def __init__(self):
        self.connection = None
        self.data = None
        self.results = {
            'pure_time_patterns': {},
            'price_movement_patterns': {},
            'market_microstructure': {},
            'volatility_patterns': {},
            'sequential_patterns': {},
            'randomness_test': {},
            'final_verdict': {}
        }
    
    def connect_database(self):
        """Connect to database"""
        try:
            print("🔗 Connecting to database...")
            self.connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_pure_market_data(self):
        """Load data focusing on pure market behavior"""
        try:
            print("📊 Loading PURE market data (ignoring signal quality)...")
            
            query = """
            SELECT 
                id,
                entry_time,
                entry_price,
                result_60min,
                EXTRACT(HOUR FROM entry_time) as hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(MINUTE FROM entry_time) as minute,
                DATE(entry_time) as trade_date,
                entry_time::time as time_only,
                CASE 
                    WHEN result_60min = 'WIN' THEN 1 
                    ELSE 0 
                END as market_win
            FROM tradingviewdata 
            WHERE entry_time IS NOT NULL
              AND result_60min IS NOT NULL
              AND entry_price IS NOT NULL
            ORDER BY entry_time;
            """
            
            self.data = pd.read_sql_query(query, self.connection)
            self.data['trade_date'] = pd.to_datetime(self.data['trade_date'])
            self.data['entry_time'] = pd.to_datetime(self.data['entry_time'])
            
            # Add additional pure market features
            self.data['hour_minute'] = self.data['hour'] * 100 + self.data['minute']
            self.data['time_block'] = self.data['hour'] // 4  # 6-hour blocks
            self.data['is_weekend'] = self.data['day_of_week'].isin([0, 6])  # Sunday=0, Saturday=6
            
            print(f"✅ Loaded {len(self.data)} pure market records!")
            print(f"📈 Overall market win rate: {self.data['market_win'].mean():.3f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading pure market data: {e}")
            return False
    
    def analyze_pure_time_patterns(self):
        """วิเคราะห์ pure time patterns - ไม่ใส่ใจสัญญาน"""
        print("⏰ Analyzing PURE TIME PATTERNS (market-only)...")
        
        time_patterns = {}
        
        # 1. Hour-by-hour analysis
        hourly_stats = []
        for hour in range(24):
            hour_data = self.data[self.data['hour'] == hour]
            if len(hour_data) >= 10:  # Minimum sample
                win_rate = hour_data['market_win'].mean()
                count = len(hour_data)
                
                # Statistical significance test
                p_value = stats.binomtest(hour_data['market_win'].sum(), count, 0.5).pvalue
                
                hourly_stats.append({
                    'hour': hour,
                    'win_rate': win_rate,
                    'sample_size': count,
                    'deviation_from_50%': abs(win_rate - 0.5),
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'pattern_strength': abs(win_rate - 0.5) * count  # Size + effect
                })
        
        hourly_df = pd.DataFrame(hourly_stats)
        time_patterns['hourly'] = hourly_df.to_dict('records')
        
        # 2. Day of week analysis
        dow_stats = []
        for dow in range(7):  # 0=Sunday, 1=Monday, ..., 6=Saturday
            dow_data = self.data[self.data['day_of_week'] == dow]
            if len(dow_data) >= 20:
                win_rate = dow_data['market_win'].mean()
                count = len(dow_data)
                
                p_value = stats.binomtest(dow_data['market_win'].sum(), count, 0.5).pvalue
                
                dow_stats.append({
                    'day_of_week': dow,
                    'day_name': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][dow],
                    'win_rate': win_rate,
                    'sample_size': count,
                    'deviation_from_50%': abs(win_rate - 0.5),
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'pattern_strength': abs(win_rate - 0.5) * count
                })
        
        dow_df = pd.DataFrame(dow_stats)
        time_patterns['daily'] = dow_df.to_dict('records')
        
        # 3. Time block analysis (6-hour blocks)
        block_stats = []
        block_names = ['00:00-05:59', '06:00-11:59', '12:00-17:59', '18:00-23:59']
        for block in range(4):
            block_data = self.data[self.data['time_block'] == block]
            if len(block_data) >= 50:
                win_rate = block_data['market_win'].mean()
                count = len(block_data)
                
                p_value = stats.binomtest(block_data['market_win'].sum(), count, 0.5).pvalue
                
                block_stats.append({
                    'time_block': block,
                    'time_range': block_names[block],
                    'win_rate': win_rate,
                    'sample_size': count,
                    'deviation_from_50%': abs(win_rate - 0.5),
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'pattern_strength': abs(win_rate - 0.5) * count
                })
        
        time_patterns['time_blocks'] = block_stats
        
        self.results['pure_time_patterns'] = time_patterns
    
    def analyze_price_movement_patterns(self):
        """วิเคราะห์ pure price movement patterns"""
        print("💰 Analyzing PURE PRICE MOVEMENT PATTERNS...")
        
        price_patterns = {}
        
        # 1. Price level analysis (binning)
        price_bins = pd.qcut(self.data['entry_price'], q=10, labels=False, duplicates='drop')
        self.data['price_decile'] = price_bins
        
        price_stats = []
        for decile in range(10):
            decile_data = self.data[self.data['price_decile'] == decile]
            if len(decile_data) >= 20:
                win_rate = decile_data['market_win'].mean()
                count = len(decile_data)
                price_range = f"{decile_data['entry_price'].min():.0f}-{decile_data['entry_price'].max():.0f}"
                
                p_value = stats.binomtest(decile_data['market_win'].sum(), count, 0.5).pvalue
                
                price_stats.append({
                    'price_decile': decile,
                    'price_range': price_range,
                    'win_rate': win_rate,
                    'sample_size': count,
                    'deviation_from_50%': abs(win_rate - 0.5),
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'pattern_strength': abs(win_rate - 0.5) * count
                })
        
        price_patterns['price_levels'] = price_stats
        
        # 2. Price momentum (previous result impact)
        if len(self.data) > 1:
            self.data['prev_result'] = self.data['market_win'].shift(1)
            
            momentum_stats = []
            for prev_result in [0, 1]:
                momentum_data = self.data[self.data['prev_result'] == prev_result]
                if len(momentum_data) >= 50:
                    win_rate = momentum_data['market_win'].mean()
                    count = len(momentum_data)
                    
                    p_value = stats.binomtest(momentum_data['market_win'].sum(), count, 0.5).pvalue
                    
                    momentum_stats.append({
                        'previous_result': 'WIN' if prev_result == 1 else 'LOSS',
                        'subsequent_win_rate': win_rate,
                        'sample_size': count,
                        'deviation_from_50%': abs(win_rate - 0.5),
                        'p_value': p_value,
                        'is_significant': p_value < 0.05,
                        'pattern_strength': abs(win_rate - 0.5) * count
                    })
            
            price_patterns['momentum'] = momentum_stats
        
        self.results['price_movement_patterns'] = price_patterns
    
    def analyze_sequential_patterns(self):
        """วิเคราะห์ sequential patterns - streaks, cycles"""
        print("🔄 Analyzing SEQUENTIAL PATTERNS...")
        
        sequential = {}
        
        # 1. Win/Loss streak analysis
        def get_streaks(series):
            streaks = []
            current_streak = 1
            current_value = series.iloc[0]
            
            for i in range(1, len(series)):
                if series.iloc[i] == current_value:
                    current_streak += 1
                else:
                    streaks.append((current_value, current_streak))
                    current_value = series.iloc[i]
                    current_streak = 1
            
            streaks.append((current_value, current_streak))
            return streaks
        
        streaks = get_streaks(self.data['market_win'])
        
        # Analyze streak lengths
        win_streaks = [length for result, length in streaks if result == 1]
        loss_streaks = [length for result, length in streaks if result == 0]
        
        sequential['streaks'] = {
            'win_streaks': {
                'average_length': np.mean(win_streaks) if win_streaks else 0,
                'max_length': max(win_streaks) if win_streaks else 0,
                'count': len(win_streaks)
            },
            'loss_streaks': {
                'average_length': np.mean(loss_streaks) if loss_streaks else 0,
                'max_length': max(loss_streaks) if loss_streaks else 0,
                'count': len(loss_streaks)
            }
        }
        
        # 2. Cycle analysis - หา patterns ที่ repeat
        if len(self.data) >= 100:
            # Look for 3-step patterns
            patterns_3 = {}
            for i in range(len(self.data) - 2):
                pattern = tuple(self.data['market_win'].iloc[i:i+3])
                if pattern in patterns_3:
                    patterns_3[pattern] += 1
                else:
                    patterns_3[pattern] = 1
            
            # Find most common patterns
            common_patterns = sorted(patterns_3.items(), key=lambda x: x[1], reverse=True)[:5]
            
            sequential['common_3_patterns'] = [
                {
                    'pattern': list(pattern),
                    'count': count,
                    'frequency': count / (len(self.data) - 2)
                }
                for pattern, count in common_patterns
            ]
        
        self.results['sequential_patterns'] = sequential
    
    def test_randomness(self):
        """ทดสอบว่าข้อมูลเป็น random หรือมี pattern จริง"""
        print("🎲 Testing RANDOMNESS vs PATTERNS...")
        
        randomness = {}
        
        # 1. Manual Runs test implementation - ทดสอบว่า sequence เป็น random หรือไม่
        def manual_runs_test(sequence):
            """Manual implementation of runs test"""
            n1 = np.sum(sequence)  # number of 1s
            n2 = len(sequence) - n1  # number of 0s
            
            # Count runs
            runs = 1
            for i in range(1, len(sequence)):
                if sequence[i] != sequence[i-1]:
                    runs += 1
            
            # Expected runs and variance
            expected_runs = (2 * n1 * n2) / (n1 + n2) + 1
            variance = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2)**2 * (n1 + n2 - 1))
            
            # Z-score
            if variance > 0:
                z_score = (runs - expected_runs) / np.sqrt(variance)
                p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed test
                return runs, expected_runs, p_value
            else:
                return runs, expected_runs, 1.0
        
        # Convert to binary sequence (above/below median)
        median_win_rate = self.data['market_win'].median()
        binary_sequence = (self.data['market_win'] > median_win_rate).astype(int)
        
        # Manual runs test
        try:
            runs, expected_runs, runs_p_value = manual_runs_test(binary_sequence.values)
            randomness['runs_test'] = {
                'runs_observed': int(runs),
                'runs_expected': float(expected_runs),
                'p_value': float(runs_p_value),
                'is_random': runs_p_value > 0.05,
                'interpretation': 'Random' if runs_p_value > 0.05 else 'Has Pattern'
            }
        except Exception as e:
            randomness['runs_test'] = {'error': f'Could not perform runs test: {str(e)}'}
        
        # 2. Chi-square test for uniform distribution across hours
        hour_counts = self.data['hour'].value_counts().sort_index()
        expected_per_hour = len(self.data) / 24
        
        chi2_stat, chi2_p = stats.chisquare(hour_counts.values)
        randomness['hour_distribution_test'] = {
            'chi2_statistic': chi2_stat,
            'p_value': chi2_p,
            'is_uniform': chi2_p > 0.05,
            'interpretation': 'Uniform distribution' if chi2_p > 0.05 else 'Non-uniform (has pattern)'
        }
        
        # 3. Simple Autocorrelation test (manual implementation)
        def manual_autocorrelation(series, max_lags=10):
            """Manual autocorrelation calculation"""
            n = len(series)
            mean_val = np.mean(series)
            variance = np.var(series)
            
            autocorrs = []
            for lag in range(1, max_lags + 1):
                if lag >= n:
                    break
                    
                numerator = np.sum((series[:-lag] - mean_val) * (series[lag:] - mean_val))
                autocorr = numerator / ((n - lag) * variance) if variance > 0 else 0
                autocorrs.append(autocorr)
            
            return np.array(autocorrs)
        
        try:
            autocorr = manual_autocorrelation(self.data['market_win'].values, max_lags=10)
            significant_lags = np.where(np.abs(autocorr) > 0.1)[0] + 1  # More lenient threshold
            
            randomness['autocorrelation'] = {
                'has_significant_autocorr': len(significant_lags) > 0,
                'significant_lags': significant_lags.tolist(),
                'max_autocorr': float(np.max(np.abs(autocorr))) if len(autocorr) > 0 else 0.0,
                'interpretation': 'Has memory/pattern' if len(significant_lags) > 0 else 'No memory (random)'
            }
        except Exception as e:
            randomness['autocorrelation'] = {'error': f'Could not perform autocorrelation: {str(e)}'}
        
        self.results['randomness_test'] = randomness
    
    def generate_final_verdict(self):
        """สรุปผลลัพธ์สุดท้าย - มี pattern หรือไม่"""
        print("⚖️ Generating FINAL VERDICT...")
        
        verdict = {
            'has_significant_patterns': False,
            'pattern_count': 0,
            'strongest_patterns': [],
            'randomness_verdict': '',
            'recommendation': '',
            'confidence_level': ''
        }
        
        # Count significant patterns
        pattern_count = 0
        all_patterns = []
        
        # Time patterns
        if 'pure_time_patterns' in self.results:
            for category, patterns in self.results['pure_time_patterns'].items():
                if isinstance(patterns, list):
                    for pattern in patterns:
                        if pattern.get('is_significant', False):
                            pattern_count += 1
                            all_patterns.append({
                                'type': f'Time ({category})',
                                'description': pattern,
                                'strength': pattern.get('pattern_strength', 0)
                            })
        
        # Price patterns
        if 'price_movement_patterns' in self.results:
            for category, patterns in self.results['price_movement_patterns'].items():
                if isinstance(patterns, list):
                    for pattern in patterns:
                        if pattern.get('is_significant', False):
                            pattern_count += 1
                            all_patterns.append({
                                'type': f'Price ({category})',
                                'description': pattern,
                                'strength': pattern.get('pattern_strength', 0)
                            })
        
        # Sort by strength
        all_patterns.sort(key=lambda x: x['strength'], reverse=True)
        
        verdict['pattern_count'] = pattern_count
        verdict['strongest_patterns'] = all_patterns[:5]  # Top 5
        
        # Randomness assessment
        randomness = self.results.get('randomness_test', {})
        random_indicators = 0
        total_tests = 0
        
        if 'runs_test' in randomness and 'is_random' in randomness['runs_test']:
            total_tests += 1
            if randomness['runs_test']['is_random']:
                random_indicators += 1
        
        if 'hour_distribution_test' in randomness:
            total_tests += 1
            if randomness['hour_distribution_test']['is_uniform']:
                random_indicators += 1
        
        if 'autocorrelation' in randomness:
            total_tests += 1
            if not randomness['autocorrelation']['has_significant_autocorr']:
                random_indicators += 1
        
        # Final decision
        if pattern_count >= 3:
            verdict['has_significant_patterns'] = True
            verdict['recommendation'] = 'USE PATTERNS - มี patterns ที่ชัดเจนพอใช้ได้'
            verdict['confidence_level'] = 'HIGH' if pattern_count >= 5 else 'MEDIUM'
        elif pattern_count >= 1:
            verdict['has_significant_patterns'] = True
            verdict['recommendation'] = 'USE PATTERNS WITH CAUTION - มี patterns บ้าง แต่น้อย'
            verdict['confidence_level'] = 'LOW'
        else:
            verdict['has_significant_patterns'] = False
            verdict['recommendation'] = 'RELY ON SIGNALS - ไม่มี patterns ที่ชัดเจน ต้องพึ่งสัญญาน'
            verdict['confidence_level'] = 'NONE'
        
        if total_tests > 0:
            randomness_score = random_indicators / total_tests
            if randomness_score >= 0.67:
                verdict['randomness_verdict'] = 'HIGHLY RANDOM - ตลาดนี้เป็น random มาก'
            elif randomness_score >= 0.33:
                verdict['randomness_verdict'] = 'PARTIALLY RANDOM - มี pattern บ้าง แต่ยังมี randomness เยอะ'
            else:
                verdict['randomness_verdict'] = 'HAS PATTERNS - มี patterns ชัดเจน ไม่ใช่ random'
        
        self.results['final_verdict'] = verdict
    
    def save_results(self):
        """Save pure market analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'/Users/puchong/tradingview/report/pure_market_patterns_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate report
        report = self.generate_pure_market_report()
        with open(f'/Users/puchong/tradingview/report/PURE_MARKET_PATTERN_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Pure market pattern analysis saved!")
    
    def generate_pure_market_report(self):
        """Generate pure market pattern report"""
        verdict = self.results.get('final_verdict', {})
        
        overall_win_rate = self.data['market_win'].mean() if self.data is not None else 0
        total_records = len(self.data) if self.data is not None else 0
        
        return f"""# 🎲 PURE MARKET PATTERN ANALYSIS
## ไม่แคร์สัญญาน - มองเฉพาะตลาด

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Market Records**: {total_records}  
**Overall Market Win Rate**: {overall_win_rate:.1%}

---

## 🎯 **FINAL VERDICT**

### **Has Significant Patterns?** 
**{verdict.get('has_significant_patterns', 'Unknown')}**

### **Pattern Count Found:** 
**{verdict.get('pattern_count', 0)}** statistically significant patterns

### **Randomness Assessment:**
**{verdict.get('randomness_verdict', 'Unknown')}**

### **RECOMMENDATION:**
**{verdict.get('recommendation', 'Unknown')}**

### **Confidence Level:**
**{verdict.get('confidence_level', 'Unknown')}**

---

## ⏰ **PURE TIME PATTERNS**

{self.format_time_patterns()}

---

## 💰 **PURE PRICE MOVEMENT PATTERNS**

{self.format_price_patterns()}

---

## 🔄 **SEQUENTIAL PATTERNS**

{self.format_sequential_patterns()}

---

## 🎲 **RANDOMNESS TESTS**

{self.format_randomness_tests()}

---

## 🏆 **STRONGEST PATTERNS FOUND**

{self.format_strongest_patterns()}

---

## 💡 **EXECUTIVE SUMMARY**

{self.generate_executive_summary()}
"""
    
    def format_time_patterns(self):
        if 'pure_time_patterns' not in self.results:
            return "ไม่มีข้อมูล"
        
        output = ""
        
        # Hourly patterns
        if 'hourly' in self.results['pure_time_patterns']:
            significant_hours = [p for p in self.results['pure_time_patterns']['hourly'] if p.get('is_significant', False)]
            
            if significant_hours:
                output += "### 📅 **Significant Hours:**\n"
                for hour in sorted(significant_hours, key=lambda x: x['pattern_strength'], reverse=True):
                    output += f"- **Hour {hour['hour']:02d}:00**: {hour['win_rate']:.1%} win rate ({hour['sample_size']} samples, p={hour['p_value']:.4f})\n"
            else:
                output += "### 📅 **Hours**: ไม่มี hour ไหนที่มี pattern ชัดเจน\n"
        
        output += "\n"
        
        # Daily patterns
        if 'daily' in self.results['pure_time_patterns']:
            significant_days = [p for p in self.results['pure_time_patterns']['daily'] if p.get('is_significant', False)]
            
            if significant_days:
                output += "### 📆 **Significant Days:**\n"
                for day in sorted(significant_days, key=lambda x: x['pattern_strength'], reverse=True):
                    output += f"- **{day['day_name']}**: {day['win_rate']:.1%} win rate ({day['sample_size']} samples, p={day['p_value']:.4f})\n"
            else:
                output += "### 📆 **Days**: ไม่มีวันไหนที่มี pattern ชัดเจน\n"
        
        return output
    
    def format_price_patterns(self):
        if 'price_movement_patterns' not in self.results:
            return "ไม่มีข้อมูล"
        
        output = ""
        
        # Price level patterns
        if 'price_levels' in self.results['price_movement_patterns']:
            significant_prices = [p for p in self.results['price_movement_patterns']['price_levels'] if p.get('is_significant', False)]
            
            if significant_prices:
                output += "### 💲 **Significant Price Levels:**\n"
                for price in sorted(significant_prices, key=lambda x: x['pattern_strength'], reverse=True):
                    output += f"- **{price['price_range']}**: {price['win_rate']:.1%} win rate ({price['sample_size']} samples, p={price['p_value']:.4f})\n"
            else:
                output += "### 💲 **Price Levels**: ไม่มี price level ไหนที่มี pattern ชัดเจน\n"
        
        output += "\n"
        
        # Momentum patterns
        if 'momentum' in self.results['price_movement_patterns']:
            output += "### 📈 **Momentum Patterns:**\n"
            for momentum in self.results['price_movement_patterns']['momentum']:
                significance = "✅" if momentum.get('is_significant', False) else "❌"
                output += f"- **After {momentum['previous_result']}**: {momentum['subsequent_win_rate']:.1%} win rate ({momentum['sample_size']} samples, p={momentum['p_value']:.4f}) {significance}\n"
        
        return output
    
    def format_sequential_patterns(self):
        if 'sequential_patterns' not in self.results:
            return "ไม่มีข้อมูล"
        
        output = ""
        sequential = self.results['sequential_patterns']
        
        if 'streaks' in sequential:
            streaks = sequential['streaks']
            output += "### 🔥 **Win/Loss Streaks:**\n"
            output += f"- **Win Streaks**: Average {streaks['win_streaks']['average_length']:.1f}, Max {streaks['win_streaks']['max_length']}, Count {streaks['win_streaks']['count']}\n"
            output += f"- **Loss Streaks**: Average {streaks['loss_streaks']['average_length']:.1f}, Max {streaks['loss_streaks']['max_length']}, Count {streaks['loss_streaks']['count']}\n"
        
        if 'common_3_patterns' in sequential:
            output += "\n### 🔄 **Common 3-Step Patterns:**\n"
            for pattern in sequential['common_3_patterns']:
                pattern_str = ''.join(['W' if x == 1 else 'L' for x in pattern['pattern']])
                output += f"- **{pattern_str}**: {pattern['frequency']:.1%} frequency ({pattern['count']} occurrences)\n"
        
        return output
    
    def format_randomness_tests(self):
        if 'randomness_test' not in self.results:
            return "ไม่มีข้อมูล"
        
        output = ""
        randomness = self.results['randomness_test']
        
        if 'runs_test' in randomness:
            runs = randomness['runs_test']
            if 'error' not in runs:
                result = "✅ Random" if runs['is_random'] else "❌ Has Pattern"
                output += f"- **Runs Test**: {result} (p={runs['p_value']:.4f})\n"
        
        if 'hour_distribution_test' in randomness:
            hour_test = randomness['hour_distribution_test']
            result = "✅ Uniform" if hour_test['is_uniform'] else "❌ Non-uniform"
            output += f"- **Hour Distribution**: {result} (p={hour_test['p_value']:.4f})\n"
        
        if 'autocorrelation' in randomness:
            autocorr = randomness['autocorrelation']
            result = "❌ Has Memory" if autocorr['has_significant_autocorr'] else "✅ No Memory"
            output += f"- **Autocorrelation**: {result} (max={autocorr['max_autocorr']:.3f})\n"
        
        return output
    
    def format_strongest_patterns(self):
        verdict = self.results.get('final_verdict', {})
        patterns = verdict.get('strongest_patterns', [])
        
        if not patterns:
            return "❌ **ไม่พบ patterns ที่แข็งแกร่งพอ**"
        
        output = ""
        for i, pattern in enumerate(patterns, 1):
            desc = pattern['description']
            if isinstance(desc, dict):
                if 'hour' in desc:
                    detail = f"Hour {desc['hour']:02d}:00 - {desc['win_rate']:.1%} win rate"
                elif 'day_name' in desc:
                    detail = f"{desc['day_name']} - {desc['win_rate']:.1%} win rate"
                elif 'price_range' in desc:
                    detail = f"Price {desc['price_range']} - {desc['win_rate']:.1%} win rate"
                else:
                    detail = str(desc)
                
                output += f"**#{i} {pattern['type']}**: {detail} (strength: {pattern['strength']:.1f})\n"
        
        return output
    
    def generate_executive_summary(self):
        verdict = self.results.get('final_verdict', {})
        
        if verdict.get('has_significant_patterns', False):
            return f"""
✅ **FOUND PATTERNS!**

มีการค้นพบ {verdict.get('pattern_count', 0)} patterns ที่มีนัยสำคัญทางสถิติ

**แนะนำ**: {verdict.get('recommendation', 'Unknown')}

**ความมั่นใจ**: {verdict.get('confidence_level', 'Unknown')}

**คำแนะนำในการใช้งาน**:
1. ใช้ patterns ที่แข็งแกร่งที่สุดเป็นหลัก
2. Combine กับสัญญานที่ดีเพื่อเพิ่มความแม่นยำ
3. ทดสอบในระยะสั้นก่อนนำไปใช้จริง
4. Monitor ผลลัพธ์และปรับปรุงอย่างต่อเนื่อง
"""
        else:
            return f"""
❌ **NO SIGNIFICANT PATTERNS FOUND**

{verdict.get('randomness_verdict', 'ตลาดแสดงลักษณะ random')}

**แนะนำ**: {verdict.get('recommendation', 'พึ่งสัญญานเป็นหลัก')}

**เหตุผล**:
- ไม่พบ patterns ที่มีนัยสำคัญทางสถิติ
- ตลาดมีลักษณะ random มากกว่า predictable
- การพึ่งพา historical signal performance น่าจะดีกว่า

**คำแนะนำ**:
1. Focus ที่คุณภาพของสัญญาน
2. ใช้ risk management ที่เข้มงวด
3. Diversify กับหลาย signals
4. ไม่ต้องหา patterns เพิ่ม
"""

    def run_complete_pure_analysis(self):
        """Run complete pure market pattern analysis"""
        print("🎲 Starting PURE MARKET Pattern Analysis...")
        print("🎯 GOAL: หา patterns ของตลาด (ไม่แคร์สัญญาน)")
        print("=" * 60)
        
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_pure_market_data():
            return False
        
        # Run pure analyses
        self.analyze_pure_time_patterns()
        self.analyze_price_movement_patterns()
        self.analyze_sequential_patterns()
        self.test_randomness()
        self.generate_final_verdict()
        
        # Save results
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 PURE MARKET Analysis COMPLETE!")
        print(f"⏱️ Duration: {duration}")
        
        # Show quick verdict
        verdict = self.results.get('final_verdict', {})
        print(f"🎯 VERDICT: {verdict.get('recommendation', 'Unknown')}")
        print(f"📊 Patterns Found: {verdict.get('pattern_count', 0)}")
        print(f"🎲 Randomness: {verdict.get('randomness_verdict', 'Unknown')}")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    analyzer = PureMarketPatternAnalyzer()
    analyzer.run_complete_pure_analysis()
