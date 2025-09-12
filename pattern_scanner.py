#!/usr/bin/env python3
"""
Pattern Scanner for Binary Options Trading
วิเคราะห์ข้อมูลดิบเพื่อหาจุดบ่งชี้ที่ส่งผลต่อ win rate อย่างมีนัยสำคัญ
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PatternScanner:
    def __init__(self, csv_file):
        """เริ่มต้นการ scan pattern"""
        self.csv_file = csv_file
        self.df = None
        self.patterns = {}
        self.indicators = {}
        self.load_data()
    
    def load_data(self):
        """โหลดและประมวลผลข้อมูล"""
        print("กำลังโหลดข้อมูล...")
        self.df = pd.read_csv(self.csv_file)
        print(f"โหลดข้อมูลสำเร็จ: {len(self.df)} records")
        
        # แปลงคอลัมน์เวลา
        self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])
        self.df['price_10min_ts'] = pd.to_datetime(self.df['price_10min_ts'])
        self.df['price_30min_ts'] = pd.to_datetime(self.df['price_30min_ts'])
        self.df['price_60min_ts'] = pd.to_datetime(self.df['price_60min_ts'])
        
        # สร้าง features ใหม่
        self.df['hour'] = self.df['entry_time'].dt.hour
        self.df['day_of_week'] = self.df['entry_time'].dt.day_name()
        self.df['date'] = self.df['entry_time'].dt.date
        
        # คำนวณ win rate
        self.df['win_10min'] = (self.df['result_10min'] == 'WIN').astype(int)
        self.df['win_30min'] = (self.df['result_30min'] == 'WIN').astype(int)
        self.df['win_60min'] = (self.df['result_60min'] == 'WIN').astype(int)
        
        # คำนวณ price changes
        self.df['price_change_10min'] = ((self.df['price_10min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        self.df['price_change_30min'] = ((self.df['price_30min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        self.df['price_change_60min'] = ((self.df['price_60min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        
        # คำนวณ volatility
        self.df['volatility_10min'] = abs(self.df['price_change_10min'])
        self.df['volatility_30min'] = abs(self.df['price_change_30min'])
        self.df['volatility_60min'] = abs(self.df['price_change_60min'])
        
        print(f"ข้อมูลครอบคลุม: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
    
    def scan_time_patterns(self):
        """Scan Time Patterns - ช่วงเวลาไหนที่ส่งผลต่อ win rate"""
        print("\n=== SCANNING TIME PATTERNS ===")
        
        # 1. Hour Pattern Analysis
        hour_analysis = self.df.groupby('hour').agg({
            'win_10min': ['mean', 'count'],
            'win_30min': ['mean', 'count'],
            'win_60min': ['mean', 'count']
        }).round(3)
        
        hour_analysis.columns = ['win_rate_10min', 'count_10min', 'win_rate_30min', 'count_30min', 'win_rate_60min', 'count_60min']
        hour_analysis = hour_analysis[hour_analysis['count_10min'] >= 10]  # Filter hours with enough data
        
        # หา hours ที่มี win rate สูง/ต่ำ
        high_win_hours = hour_analysis[hour_analysis['win_rate_60min'] >= 0.6].index.tolist()
        low_win_hours = hour_analysis[hour_analysis['win_rate_60min'] <= 0.4].index.tolist()
        
        print(f"ชั่วโมงที่มี win rate สูง (≥60%): {high_win_hours}")
        print(f"ชั่วโมงที่มี win rate ต่ำ (≤40%): {low_win_hours}")
        
        # 2. Day of Week Pattern
        day_analysis = self.df.groupby('day_of_week').agg({
            'win_60min': ['mean', 'count']
        }).round(3)
        day_analysis.columns = ['win_rate', 'count']
        day_analysis = day_analysis[day_analysis['count'] >= 10]
        
        print(f"วันที่มี win rate สูง: {day_analysis[day_analysis['win_rate'] >= 0.6].index.tolist()}")
        print(f"วันที่มี win rate ต่ำ: {day_analysis[day_analysis['win_rate'] <= 0.4].index.tolist()}")
        
        # 3. Time + Strategy Pattern
        time_strategy = self.df.groupby(['hour', 'strategy'])['win_60min'].mean().reset_index()
        time_strategy_pivot = time_strategy.pivot(index='hour', columns='strategy', values='win_60min')
        
        # หา combination ที่ดี
        best_combinations = time_strategy[time_strategy['win_60min'] >= 0.7]
        print(f"Best Time+Strategy combinations (≥70% win rate): {len(best_combinations)} combinations")
        
        self.patterns['time'] = {
            'high_win_hours': high_win_hours,
            'low_win_hours': low_win_hours,
            'best_combinations': best_combinations.to_dict('records')
        }
    
    def scan_price_patterns(self):
        """Scan Price Patterns - ราคาแบบไหนที่ส่งผลต่อ win rate"""
        print("\n=== SCANNING PRICE PATTERNS ===")
        
        # 1. Price Range Analysis
        price_ranges = pd.cut(self.df['entry_price'], bins=10, labels=False)
        self.df['price_range'] = price_ranges
        
        price_analysis = self.df.groupby('price_range').agg({
            'win_60min': ['mean', 'count'],
            'entry_price': ['min', 'max']
        }).round(3)
        price_analysis.columns = ['win_rate', 'count', 'min_price', 'max_price']
        price_analysis = price_analysis[price_analysis['count'] >= 10]
        
        best_price_ranges = price_analysis[price_analysis['win_rate'] >= 0.6]
        print(f"Price ranges ที่มี win rate สูง: {len(best_price_ranges)} ranges")
        
        # 2. Volatility Analysis
        vol_ranges = pd.cut(self.df['volatility_60min'], bins=5, labels=False)
        self.df['volatility_range'] = vol_ranges
        
        vol_analysis = self.df.groupby('volatility_range').agg({
            'win_60min': ['mean', 'count'],
            'volatility_60min': ['min', 'max']
        }).round(3)
        vol_analysis.columns = ['win_rate', 'count', 'min_vol', 'max_vol']
        vol_analysis = vol_analysis[vol_analysis['count'] >= 10]
        
        best_vol_ranges = vol_analysis[vol_analysis['win_rate'] >= 0.6]
        print(f"Volatility ranges ที่มี win rate สูง: {len(best_vol_ranges)} ranges")
        
        # 3. Price Change Direction Analysis
        self.df['price_direction_10min'] = np.where(self.df['price_change_10min'] > 0, 'Up', 'Down')
        self.df['price_direction_30min'] = np.where(self.df['price_change_30min'] > 0, 'Up', 'Down')
        self.df['price_direction_60min'] = np.where(self.df['price_change_60min'] > 0, 'Up', 'Down')
        
        direction_analysis = self.df.groupby('price_direction_60min')['win_60min'].agg(['mean', 'count']).round(3)
        print(f"Price direction win rates: {direction_analysis.to_dict()}")
        
        self.patterns['price'] = {
            'best_price_ranges': best_price_ranges.to_dict('records'),
            'best_vol_ranges': best_vol_ranges.to_dict('records'),
            'direction_analysis': direction_analysis.to_dict()
        }
    
    def scan_strategy_patterns(self):
        """Scan Strategy Patterns - strategy ไหนมีจุดบ่งชี้ชัดเจน"""
        print("\n=== SCANNING STRATEGY PATTERNS ===")
        
        # 1. Strategy Performance Analysis
        strategy_analysis = self.df.groupby('strategy').agg({
            'win_10min': ['mean', 'count', 'std'],
            'win_30min': ['mean', 'count', 'std'],
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        
        strategy_analysis.columns = ['win_rate_10min', 'count_10min', 'std_10min', 
                                   'win_rate_30min', 'count_30min', 'std_30min',
                                   'win_rate_60min', 'count_60min', 'std_60min']
        
        # หา strategies ที่ดี
        best_strategies = strategy_analysis[strategy_analysis['win_rate_60min'] >= 0.55]
        worst_strategies = strategy_analysis[strategy_analysis['win_rate_60min'] <= 0.45]
        
        print(f"Best strategies (≥55% win rate): {best_strategies.index.tolist()}")
        print(f"Worst strategies (≤45% win rate): {worst_strategies.index.tolist()}")
        
        # 2. Strategy Consistency Analysis
        strategy_consistency = strategy_analysis.copy()
        strategy_consistency['consistency_10min'] = 1 - (strategy_consistency['std_10min'] / strategy_consistency['win_rate_10min'])
        strategy_consistency['consistency_30min'] = 1 - (strategy_consistency['std_30min'] / strategy_consistency['win_rate_30min'])
        strategy_consistency['consistency_60min'] = 1 - (strategy_consistency['std_60min'] / strategy_consistency['win_rate_60min'])
        
        consistent_strategies = strategy_consistency[strategy_consistency['consistency_60min'] >= 0.8]
        print(f"Consistent strategies (≥80% consistency): {consistent_strategies.index.tolist()}")
        
        # 3. Strategy + Action Analysis
        strategy_action = self.df.groupby(['strategy', 'action'])['win_60min'].mean().reset_index()
        best_combinations = strategy_action[strategy_action['win_60min'] >= 0.7]
        print(f"Best Strategy+Action combinations (≥70% win rate): {len(best_combinations)} combinations")
        
        self.patterns['strategy'] = {
            'best_strategies': best_strategies.to_dict('index'),
            'worst_strategies': worst_strategies.to_dict('index'),
            'consistent_strategies': consistent_strategies.to_dict('index'),
            'best_combinations': best_combinations.to_dict('records')
        }
    
    def scan_action_patterns(self):
        """Scan Action Patterns - action ไหนมีจุดบ่งชี้ชัดเจน"""
        print("\n=== SCANNING ACTION PATTERNS ===")
        
        # 1. Action Performance Analysis
        action_analysis = self.df.groupby('action').agg({
            'win_10min': ['mean', 'count'],
            'win_30min': ['mean', 'count'],
            'win_60min': ['mean', 'count']
        }).round(3)
        
        action_analysis.columns = ['win_rate_10min', 'count_10min', 'win_rate_30min', 'count_30min', 'win_rate_60min', 'count_60min']
        
        best_actions = action_analysis[action_analysis['win_rate_60min'] >= 0.6]
        worst_actions = action_analysis[action_analysis['win_rate_60min'] <= 0.4]
        
        print(f"Best actions (≥60% win rate): {best_actions.index.tolist()}")
        print(f"Worst actions (≤40% win rate): {worst_actions.index.tolist()}")
        
        # 2. Action + Time Analysis
        action_time = self.df.groupby(['action', 'hour'])['win_60min'].mean().reset_index()
        best_action_time = action_time[action_time['win_60min'] >= 0.7]
        print(f"Best Action+Time combinations (≥70% win rate): {len(best_action_time)} combinations")
        
        # 3. Action Sequence Analysis
        self.df = self.df.sort_values(['strategy', 'entry_time'])
        self.df['prev_action'] = self.df.groupby('strategy')['action'].shift(1)
        self.df['prev_result'] = self.df.groupby('strategy')['win_60min'].shift(1)
        
        # วิเคราะห์ action sequence
        sequence_data = self.df[self.df['prev_action'].notna()].copy()
        if len(sequence_data) > 0:
            sequence_analysis = sequence_data.groupby(['prev_action', 'action'])['win_60min'].mean().reset_index()
            best_sequences = sequence_analysis[sequence_analysis['win_60min'] >= 0.7]
            print(f"Best action sequences (≥70% win rate): {len(best_sequences)} sequences")
        
        self.patterns['action'] = {
            'best_actions': best_actions.to_dict('index'),
            'worst_actions': worst_actions.to_dict('index'),
            'best_action_time': best_action_time.to_dict('records'),
            'best_sequences': best_sequences.to_dict('records') if len(sequence_data) > 0 else []
        }
    
    def scan_combination_patterns(self):
        """Scan Combination Patterns - การรวมกันของปัจจัยต่างๆ"""
        print("\n=== SCANNING COMBINATION PATTERNS ===")
        
        # 1. Time + Strategy + Action Analysis
        combo_analysis = self.df.groupby(['hour', 'strategy', 'action'])['win_60min'].agg(['mean', 'count']).reset_index()
        combo_analysis = combo_analysis[combo_analysis['count'] >= 5]  # Filter combinations with enough data
        
        best_combos = combo_analysis[combo_analysis['mean'] >= 0.8]
        print(f"Best Time+Strategy+Action combinations (≥80% win rate): {len(best_combos)} combinations")
        
        # 2. Price + Strategy Analysis
        price_strategy = self.df.groupby(['price_range', 'strategy'])['win_60min'].agg(['mean', 'count']).reset_index()
        price_strategy = price_strategy[price_strategy['count'] >= 5]
        
        best_price_strategy = price_strategy[price_strategy['mean'] >= 0.7]
        print(f"Best Price+Strategy combinations (≥70% win rate): {len(best_price_strategy)} combinations")
        
        # 3. Volatility + Action Analysis
        vol_action = self.df.groupby(['volatility_range', 'action'])['win_60min'].agg(['mean', 'count']).reset_index()
        vol_action = vol_action[vol_action['count'] >= 5]
        
        best_vol_action = vol_action[vol_action['mean'] >= 0.7]
        print(f"Best Volatility+Action combinations (≥70% win rate): {len(best_vol_action)} combinations")
        
        self.patterns['combination'] = {
            'best_combos': best_combos.to_dict('records'),
            'best_price_strategy': best_price_strategy.to_dict('records'),
            'best_vol_action': best_vol_action.to_dict('records')
        }
    
    def identify_key_indicators(self):
        """ระบุ Key Indicators ที่ส่งผลต่อ win rate อย่างมีนัยสำคัญ"""
        print("\n=== IDENTIFYING KEY INDICATORS ===")
        
        key_indicators = []
        
        # 1. Time Indicators
        if 'time' in self.patterns:
            time_patterns = self.patterns['time']
            if time_patterns['high_win_hours']:
                key_indicators.append({
                    'type': 'Time',
                    'indicator': 'Hour',
                    'pattern': f"Hours {time_patterns['high_win_hours']} have high win rate",
                    'significance': 'High'
                })
        
        # 2. Strategy Indicators
        if 'strategy' in self.patterns:
            strategy_patterns = self.patterns['strategy']
            if strategy_patterns['best_strategies']:
                best_strategies = list(strategy_patterns['best_strategies'].keys())
                key_indicators.append({
                    'type': 'Strategy',
                    'indicator': 'Strategy Type',
                    'pattern': f"Strategies {best_strategies} have high win rate",
                    'significance': 'High'
                })
        
        # 3. Action Indicators
        if 'action' in self.patterns:
            action_patterns = self.patterns['action']
            if action_patterns['best_actions']:
                best_actions = list(action_patterns['best_actions'].keys())
                key_indicators.append({
                    'type': 'Action',
                    'indicator': 'Action Type',
                    'pattern': f"Actions {best_actions} have high win rate",
                    'significance': 'High'
                })
        
        # 4. Price Indicators
        if 'price' in self.patterns:
            price_patterns = self.patterns['price']
            if price_patterns['best_vol_ranges']:
                key_indicators.append({
                    'type': 'Price',
                    'indicator': 'Volatility',
                    'pattern': f"Low volatility ranges have high win rate",
                    'significance': 'Medium'
                })
        
        # 5. Combination Indicators
        if 'combination' in self.patterns:
            combo_patterns = self.patterns['combination']
            if combo_patterns['best_combos']:
                key_indicators.append({
                    'type': 'Combination',
                    'indicator': 'Time+Strategy+Action',
                    'pattern': f"{len(combo_patterns['best_combos'])} combinations have ≥80% win rate",
                    'significance': 'Very High'
                })
        
        print(f"พบ Key Indicators: {len(key_indicators)} ตัว")
        for indicator in key_indicators:
            print(f"- {indicator['type']}: {indicator['pattern']} ({indicator['significance']})")
        
        self.indicators = key_indicators
        return key_indicators
    
    def generate_summary_report(self):
        """สร้างรายงานสรุป"""
        print("\n" + "="*60)
        print("PATTERN SCAN SUMMARY REPORT")
        print("="*60)
        
        print(f"ข้อมูลที่วิเคราะห์: {len(self.df)} records")
        print(f"ช่วงเวลา: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        
        print(f"\nKey Indicators ที่พบ: {len(self.indicators)} ตัว")
        for i, indicator in enumerate(self.indicators, 1):
            print(f"{i}. {indicator['type']} - {indicator['indicator']}")
            print(f"   Pattern: {indicator['pattern']}")
            print(f"   Significance: {indicator['significance']}")
            print()
        
        # สรุป patterns ที่สำคัญ
        print("PATTERNS ที่สำคัญที่สุด:")
        if 'time' in self.patterns and self.patterns['time']['high_win_hours']:
            print(f"- Time Pattern: Hours {self.patterns['time']['high_win_hours']} มี win rate สูง")
        
        if 'strategy' in self.patterns and self.patterns['strategy']['best_strategies']:
            best_strategies = list(self.patterns['strategy']['best_strategies'].keys())
            print(f"- Strategy Pattern: {best_strategies} มี win rate สูง")
        
        if 'combination' in self.patterns and self.patterns['combination']['best_combos']:
            print(f"- Combination Pattern: {len(self.patterns['combination']['best_combos'])} combinations มี win rate ≥80%")
        
        print("\n" + "="*60)
    
    def run_full_scan(self):
        """รันการ scan แบบครบถ้วน"""
        print("เริ่มต้น Pattern Scanning...")
        print("="*60)
        
        self.scan_time_patterns()
        self.scan_price_patterns()
        self.scan_strategy_patterns()
        self.scan_action_patterns()
        self.scan_combination_patterns()
        self.identify_key_indicators()
        self.generate_summary_report()
        
        print("Pattern Scanning เสร็จสิ้น!")
        return self.patterns, self.indicators

if __name__ == "__main__":
    # เริ่มต้น Pattern Scanner
    scanner = PatternScanner("Result Last 120HR.csv")
    
    # รันการ scan แบบครบถ้วน
    patterns, indicators = scanner.run_full_scan()
