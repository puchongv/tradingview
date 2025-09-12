#!/usr/bin/env python3
"""
Factor Analysis for Binary Options Trading
วิเคราะห์ปัจจัยที่ส่งผลต่อ win rate (ไม่ใช่ผลลัพธ์ในอดีต)
หาจุดบ่งชี้ที่ชัดเจน (ความแตกต่างต้องมากกว่า 70%)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class FactorAnalyzer:
    def __init__(self, csv_file):
        """เริ่มต้นการวิเคราะห์ปัจจัย"""
        self.csv_file = csv_file
        self.df = None
        self.factors = {}
        self.significant_patterns = {}
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
        self.df['minute'] = self.df['entry_time'].dt.minute
        
        # คำนวณ win rate
        self.df['win_10min'] = (self.df['result_10min'] == 'WIN').astype(int)
        self.df['win_30min'] = (self.df['result_30min'] == 'WIN').astype(int)
        self.df['win_60min'] = (self.df['result_60min'] == 'WIN').astype(int)
        
        # คำนวณ price changes และ volatility
        self.df['price_change_10min'] = ((self.df['price_10min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        self.df['price_change_30min'] = ((self.df['price_30min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        self.df['price_change_60min'] = ((self.df['price_60min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        
        self.df['volatility_10min'] = abs(self.df['price_change_10min'])
        self.df['volatility_30min'] = abs(self.df['price_change_30min'])
        self.df['volatility_60min'] = abs(self.df['price_change_60min'])
        
        print(f"ข้อมูลครอบคลุม: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
    
    def analyze_time_factors(self):
        """วิเคราะห์ Time Factors - ช่วงเวลาไหนส่งผลต่อ win rate"""
        print("\n=== TIME FACTORS ANALYSIS ===")
        
        # 1. Hour Factor Analysis
        hour_analysis = self.df.groupby('hour').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        hour_analysis.columns = ['win_rate', 'count', 'std']
        hour_analysis = hour_analysis[hour_analysis['count'] >= 10]  # Filter hours with enough data
        
        # หา hours ที่มี win rate แตกต่างกันมาก
        overall_winrate = self.df['win_60min'].mean()
        hour_analysis['difference'] = hour_analysis['win_rate'] - overall_winrate
        hour_analysis['abs_difference'] = abs(hour_analysis['difference'])
        
        # หา significant hours (ความแตกต่าง > 20%)
        significant_hours = hour_analysis[hour_analysis['abs_difference'] >= 0.2]
        
        print(f"Overall Win Rate: {overall_winrate:.1%}")
        print(f"Significant Hours (≥20% difference): {len(significant_hours)} hours")
        
        for hour in significant_hours.index:
            win_rate = hour_analysis.loc[hour, 'win_rate']
            diff = hour_analysis.loc[hour, 'difference']
            count = hour_analysis.loc[hour, 'count']
            print(f"  Hour {hour:02d}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        # 2. Day of Week Factor Analysis
        day_analysis = self.df.groupby('day_of_week').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        day_analysis.columns = ['win_rate', 'count', 'std']
        day_analysis = day_analysis[day_analysis['count'] >= 10]
        
        day_analysis['difference'] = day_analysis['win_rate'] - overall_winrate
        day_analysis['abs_difference'] = abs(day_analysis['difference'])
        
        significant_days = day_analysis[day_analysis['abs_difference'] >= 0.2]
        
        print(f"\nSignificant Days (≥20% difference): {len(significant_days)} days")
        for day in significant_days.index:
            win_rate = day_analysis.loc[day, 'win_rate']
            diff = day_analysis.loc[day, 'difference']
            count = day_analysis.loc[day, 'count']
            print(f"  {day}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        # 3. Time Range Analysis (15-minute intervals)
        self.df['time_range'] = self.df['entry_time'].dt.floor('15min').dt.time
        time_range_analysis = self.df.groupby('time_range').agg({
            'win_60min': ['mean', 'count']
        }).round(3)
        time_range_analysis.columns = ['win_rate', 'count']
        time_range_analysis = time_range_analysis[time_range_analysis['count'] >= 5]
        
        time_range_analysis['difference'] = time_range_analysis['win_rate'] - overall_winrate
        time_range_analysis['abs_difference'] = abs(time_range_analysis['difference'])
        
        significant_time_ranges = time_range_analysis[time_range_analysis['abs_difference'] >= 0.3]
        
        print(f"\nSignificant Time Ranges (≥30% difference): {len(significant_time_ranges)} ranges")
        for time_range in significant_time_ranges.index:
            win_rate = time_range_analysis.loc[time_range, 'win_rate']
            diff = time_range_analysis.loc[time_range, 'difference']
            count = time_range_analysis.loc[time_range, 'count']
            print(f"  {time_range}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        self.factors['time'] = {
            'overall_winrate': overall_winrate,
            'significant_hours': significant_hours.to_dict('index'),
            'significant_days': significant_days.to_dict('index'),
            'significant_time_ranges': significant_time_ranges.to_dict('index')
        }
    
    def analyze_strategy_factors(self):
        """วิเคราะห์ Strategy Factors - strategy ไหนส่งผลต่อ win rate"""
        print("\n=== STRATEGY FACTORS ANALYSIS ===")
        
        # 1. Strategy Performance Analysis
        strategy_analysis = self.df.groupby('strategy').agg({
            'win_10min': ['mean', 'count', 'std'],
            'win_30min': ['mean', 'count', 'std'],
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        
        strategy_analysis.columns = ['win_rate_10min', 'count_10min', 'std_10min', 
                                   'win_rate_30min', 'count_30min', 'std_30min',
                                   'win_rate_60min', 'count_60min', 'std_60min']
        
        overall_winrate = self.df['win_60min'].mean()
        
        # หา strategies ที่มี win rate แตกต่างกันมาก
        strategy_analysis['difference_60min'] = strategy_analysis['win_rate_60min'] - overall_winrate
        strategy_analysis['abs_difference_60min'] = abs(strategy_analysis['difference_60min'])
        
        significant_strategies = strategy_analysis[strategy_analysis['abs_difference_60min'] >= 0.15]
        
        print(f"Overall Win Rate: {overall_winrate:.1%}")
        print(f"Significant Strategies (≥15% difference): {len(significant_strategies)} strategies")
        
        for strategy in significant_strategies.index:
            win_rate = strategy_analysis.loc[strategy, 'win_rate_60min']
            diff = strategy_analysis.loc[strategy, 'difference_60min']
            count = strategy_analysis.loc[strategy, 'count_60min']
            print(f"  {strategy}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        # 2. Strategy Consistency Analysis
        strategy_analysis['consistency_60min'] = 1 - (strategy_analysis['std_60min'] / strategy_analysis['win_rate_60min'])
        consistent_strategies = strategy_analysis[strategy_analysis['consistency_60min'] >= 0.8]
        
        print(f"\nConsistent Strategies (≥80% consistency): {len(consistent_strategies)} strategies")
        for strategy in consistent_strategies.index:
            consistency = strategy_analysis.loc[strategy, 'consistency_60min']
            win_rate = strategy_analysis.loc[strategy, 'win_rate_60min']
            print(f"  {strategy}: {consistency:.1%} consistency, {win_rate:.1%} win rate")
        
        self.factors['strategy'] = {
            'overall_winrate': overall_winrate,
            'significant_strategies': significant_strategies.to_dict('index'),
            'consistent_strategies': consistent_strategies.to_dict('index')
        }
    
    def analyze_action_factors(self):
        """วิเคราะห์ Action Factors - action ไหนส่งผลต่อ win rate"""
        print("\n=== ACTION FACTORS ANALYSIS ===")
        
        # 1. Action Performance Analysis
        action_analysis = self.df.groupby('action').agg({
            'win_10min': ['mean', 'count', 'std'],
            'win_30min': ['mean', 'count', 'std'],
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        
        action_analysis.columns = ['win_rate_10min', 'count_10min', 'std_10min', 
                                 'win_rate_30min', 'count_30min', 'std_30min',
                                 'win_rate_60min', 'count_60min', 'std_60min']
        
        overall_winrate = self.df['win_60min'].mean()
        
        # หา actions ที่มี win rate แตกต่างกันมาก
        action_analysis['difference_60min'] = action_analysis['win_rate_60min'] - overall_winrate
        action_analysis['abs_difference_60min'] = abs(action_analysis['difference_60min'])
        
        significant_actions = action_analysis[action_analysis['abs_difference_60min'] >= 0.15]
        
        print(f"Overall Win Rate: {overall_winrate:.1%}")
        print(f"Significant Actions (≥15% difference): {len(significant_actions)} actions")
        
        for action in significant_actions.index:
            win_rate = action_analysis.loc[action, 'win_rate_60min']
            diff = action_analysis.loc[action, 'difference_60min']
            count = action_analysis.loc[action, 'count_60min']
            print(f"  {action}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        # 2. Action + Time Factor Analysis
        action_time = self.df.groupby(['action', 'hour'])['win_60min'].agg(['mean', 'count']).reset_index()
        action_time = action_time[action_time['count'] >= 5]  # Filter combinations with enough data
        
        action_time['difference'] = action_time['mean'] - overall_winrate
        action_time['abs_difference'] = abs(action_time['difference'])
        
        significant_action_time = action_time[action_time['abs_difference'] >= 0.3]
        
        print(f"\nSignificant Action+Time combinations (≥30% difference): {len(significant_action_time)} combinations")
        for _, row in significant_action_time.iterrows():
            print(f"  {row['action']} at {row['hour']:02d}:00: {row['mean']:.1%} (diff: {row['difference']:+.1%}, n={row['count']})")
        
        self.factors['action'] = {
            'overall_winrate': overall_winrate,
            'significant_actions': significant_actions.to_dict('index'),
            'significant_action_time': significant_action_time.to_dict('records')
        }
    
    def analyze_price_factors(self):
        """วิเคราะห์ Price Factors - ราคาแบบไหนส่งผลต่อ win rate"""
        print("\n=== PRICE FACTORS ANALYSIS ===")
        
        # 1. Price Range Analysis
        price_ranges = pd.cut(self.df['entry_price'], bins=10, labels=False)
        self.df['price_range'] = price_ranges
        
        price_analysis = self.df.groupby('price_range').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        price_analysis.columns = ['win_rate', 'count', 'std']
        price_analysis = price_analysis[price_analysis['count'] >= 10]
        
        overall_winrate = self.df['win_60min'].mean()
        price_analysis['difference'] = price_analysis['win_rate'] - overall_winrate
        price_analysis['abs_difference'] = abs(price_analysis['difference'])
        
        significant_price_ranges = price_analysis[price_analysis['abs_difference'] >= 0.2]
        
        print(f"Overall Win Rate: {overall_winrate:.1%}")
        print(f"Significant Price Ranges (≥20% difference): {len(significant_price_ranges)} ranges")
        
        for price_range in significant_price_ranges.index:
            win_rate = price_analysis.loc[price_range, 'win_rate']
            diff = price_analysis.loc[price_range, 'difference']
            count = price_analysis.loc[price_range, 'count']
            print(f"  Price Range {price_range}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        # 2. Volatility Analysis
        vol_ranges = pd.cut(self.df['volatility_60min'], bins=5, labels=False)
        self.df['volatility_range'] = vol_ranges
        
        vol_analysis = self.df.groupby('volatility_range').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        vol_analysis.columns = ['win_rate', 'count', 'std']
        vol_analysis = vol_analysis[vol_analysis['count'] >= 10]
        
        vol_analysis['difference'] = vol_analysis['win_rate'] - overall_winrate
        vol_analysis['abs_difference'] = abs(vol_analysis['difference'])
        
        significant_vol_ranges = vol_analysis[vol_analysis['abs_difference'] >= 0.2]
        
        print(f"\nSignificant Volatility Ranges (≥20% difference): {len(significant_vol_ranges)} ranges")
        for vol_range in significant_vol_ranges.index:
            win_rate = vol_analysis.loc[vol_range, 'win_rate']
            diff = vol_analysis.loc[vol_range, 'difference']
            count = vol_analysis.loc[vol_range, 'count']
            print(f"  Volatility Range {vol_range}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        # 3. Price Direction Analysis
        self.df['price_direction_60min'] = np.where(self.df['price_change_60min'] > 0, 'Up', 'Down')
        direction_analysis = self.df.groupby('price_direction_60min')['win_60min'].agg(['mean', 'count']).round(3)
        direction_analysis.columns = ['win_rate', 'count']
        
        direction_analysis['difference'] = direction_analysis['win_rate'] - overall_winrate
        direction_analysis['abs_difference'] = abs(direction_analysis['difference'])
        
        significant_directions = direction_analysis[direction_analysis['abs_difference'] >= 0.1]
        
        print(f"\nSignificant Price Directions (≥10% difference): {len(significant_directions)} directions")
        for direction in significant_directions.index:
            win_rate = direction_analysis.loc[direction, 'win_rate']
            diff = direction_analysis.loc[direction, 'difference']
            count = direction_analysis.loc[direction, 'count']
            print(f"  {direction}: {win_rate:.1%} (diff: {diff:+.1%}, n={count})")
        
        self.factors['price'] = {
            'overall_winrate': overall_winrate,
            'significant_price_ranges': significant_price_ranges.to_dict('index'),
            'significant_vol_ranges': significant_vol_ranges.to_dict('index'),
            'significant_directions': significant_directions.to_dict('index')
        }
    
    def analyze_combination_factors(self):
        """วิเคราะห์ Combination Factors - การรวมกันของปัจจัยต่างๆ"""
        print("\n=== COMBINATION FACTORS ANALYSIS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        
        # 1. Strategy + Action + Time Analysis
        combo_analysis = self.df.groupby(['strategy', 'action', 'hour'])['win_60min'].agg(['mean', 'count']).reset_index()
        combo_analysis = combo_analysis[combo_analysis['count'] >= 3]  # Filter combinations with enough data
        
        combo_analysis['difference'] = combo_analysis['mean'] - overall_winrate
        combo_analysis['abs_difference'] = abs(combo_analysis['difference'])
        
        significant_combos = combo_analysis[combo_analysis['abs_difference'] >= 0.4]
        
        print(f"Overall Win Rate: {overall_winrate:.1%}")
        print(f"Significant Strategy+Action+Time combinations (≥40% difference): {len(significant_combos)} combinations")
        
        for _, row in significant_combos.iterrows():
            print(f"  {row['strategy']} + {row['action']} at {row['hour']:02d}:00: {row['mean']:.1%} (diff: {row['difference']:+.1%}, n={row['count']})")
        
        # 2. Strategy + Price Range Analysis
        price_strategy = self.df.groupby(['strategy', 'price_range'])['win_60min'].agg(['mean', 'count']).reset_index()
        price_strategy = price_strategy[price_strategy['count'] >= 5]
        
        price_strategy['difference'] = price_strategy['mean'] - overall_winrate
        price_strategy['abs_difference'] = abs(price_strategy['difference'])
        
        significant_price_strategy = price_strategy[price_strategy['abs_difference'] >= 0.3]
        
        print(f"\nSignificant Strategy+Price combinations (≥30% difference): {len(significant_price_strategy)} combinations")
        for _, row in significant_price_strategy.iterrows():
            print(f"  {row['strategy']} + Price Range {row['price_range']}: {row['mean']:.1%} (diff: {row['difference']:+.1%}, n={row['count']})")
        
        # 3. Action + Volatility Analysis
        vol_action = self.df.groupby(['action', 'volatility_range'])['win_60min'].agg(['mean', 'count']).reset_index()
        vol_action = vol_action[vol_action['count'] >= 5]
        
        vol_action['difference'] = vol_action['mean'] - overall_winrate
        vol_action['abs_difference'] = abs(vol_action['difference'])
        
        significant_vol_action = vol_action[vol_action['abs_difference'] >= 0.3]
        
        print(f"\nSignificant Action+Volatility combinations (≥30% difference): {len(significant_vol_action)} combinations")
        for _, row in significant_vol_action.iterrows():
            print(f"  {row['action']} + Volatility Range {row['volatility_range']}: {row['mean']:.1%} (diff: {row['difference']:+.1%}, n={row['count']})")
        
        self.factors['combination'] = {
            'overall_winrate': overall_winrate,
            'significant_combos': significant_combos.to_dict('records'),
            'significant_price_strategy': significant_price_strategy.to_dict('records'),
            'significant_vol_action': significant_vol_action.to_dict('records')
        }
    
    def identify_significant_patterns(self):
        """ระบุ Significant Patterns ที่ชัดเจน (ความแตกต่าง > 70%)"""
        print("\n=== IDENTIFYING SIGNIFICANT PATTERNS ===")
        
        significant_patterns = []
        
        # 1. Time Patterns
        if 'time' in self.factors:
            time_factors = self.factors['time']
            
            # Significant Hours
            for hour, data in time_factors['significant_hours'].items():
                if abs(data['difference']) >= 0.7:  # 70% difference
                    significant_patterns.append({
                        'type': 'Time',
                        'factor': 'Hour',
                        'value': f"{hour:02d}:00",
                        'win_rate': data['win_rate'],
                        'difference': data['difference'],
                        'count': data['count'],
                        'significance': 'Very High' if abs(data['difference']) >= 0.7 else 'High'
                    })
            
            # Significant Time Ranges
            for time_range, data in time_factors['significant_time_ranges'].items():
                if abs(data['difference']) >= 0.7:
                    significant_patterns.append({
                        'type': 'Time',
                        'factor': 'Time Range',
                        'value': str(time_range),
                        'win_rate': data['win_rate'],
                        'difference': data['difference'],
                        'count': data['count'],
                        'significance': 'Very High' if abs(data['difference']) >= 0.7 else 'High'
                    })
        
        # 2. Strategy Patterns
        if 'strategy' in self.factors:
            strategy_factors = self.factors['strategy']
            
            for strategy, data in strategy_factors['significant_strategies'].items():
                if abs(data['difference_60min']) >= 0.7:
                    significant_patterns.append({
                        'type': 'Strategy',
                        'factor': 'Strategy Type',
                        'value': strategy,
                        'win_rate': data['win_rate_60min'],
                        'difference': data['difference_60min'],
                        'count': data['count_60min'],
                        'significance': 'Very High' if abs(data['difference_60min']) >= 0.7 else 'High'
                    })
        
        # 3. Action Patterns
        if 'action' in self.factors:
            action_factors = self.factors['action']
            
            for action, data in action_factors['significant_actions'].items():
                if abs(data['difference_60min']) >= 0.7:
                    significant_patterns.append({
                        'type': 'Action',
                        'factor': 'Action Type',
                        'value': action,
                        'win_rate': data['win_rate_60min'],
                        'difference': data['difference_60min'],
                        'count': data['count_60min'],
                        'significance': 'Very High' if abs(data['difference_60min']) >= 0.7 else 'High'
                    })
        
        # 4. Combination Patterns
        if 'combination' in self.factors:
            combo_factors = self.factors['combination']
            
            for combo in combo_factors['significant_combos']:
                if abs(combo['difference']) >= 0.7:
                    significant_patterns.append({
                        'type': 'Combination',
                        'factor': 'Strategy+Action+Time',
                        'value': f"{combo['strategy']} + {combo['action']} at {combo['hour']:02d}:00",
                        'win_rate': combo['mean'],
                        'difference': combo['difference'],
                        'count': combo['count'],
                        'significance': 'Very High' if abs(combo['difference']) >= 0.7 else 'High'
                    })
        
        print(f"พบ Significant Patterns: {len(significant_patterns)} patterns")
        
        if significant_patterns:
            print("\nSignificant Patterns (≥70% difference):")
            for i, pattern in enumerate(significant_patterns, 1):
                print(f"{i}. {pattern['type']} - {pattern['factor']}")
                print(f"   Value: {pattern['value']}")
                print(f"   Win Rate: {pattern['win_rate']:.1%}")
                print(f"   Difference: {pattern['difference']:+.1%}")
                print(f"   Count: {pattern['count']}")
                print(f"   Significance: {pattern['significance']}")
                print()
        else:
            print("ไม่พบ Significant Patterns ที่มีความแตกต่าง ≥70%")
            print("Patterns ที่มีความแตกต่างมากที่สุด:")
            
            # หา patterns ที่มีความแตกต่างมากที่สุด
            all_patterns = []
            
            # Time patterns
            if 'time' in self.factors:
                for hour, data in self.factors['time']['significant_hours'].items():
                    all_patterns.append({
                        'type': 'Time',
                        'factor': 'Hour',
                        'value': f"{hour:02d}:00",
                        'difference': abs(data['difference']),
                        'data': data
                    })
            
            # Strategy patterns
            if 'strategy' in self.factors:
                for strategy, data in self.factors['strategy']['significant_strategies'].items():
                    all_patterns.append({
                        'type': 'Strategy',
                        'factor': 'Strategy Type',
                        'value': strategy,
                        'difference': abs(data['difference_60min']),
                        'data': data
                    })
            
            # Action patterns
            if 'action' in self.factors:
                for action, data in self.factors['action']['significant_actions'].items():
                    all_patterns.append({
                        'type': 'Action',
                        'factor': 'Action Type',
                        'value': action,
                        'difference': abs(data['difference_60min']),
                        'data': data
                    })
            
            # เรียงตามความแตกต่าง
            all_patterns.sort(key=lambda x: x['difference'], reverse=True)
            
            print("Top 5 Patterns with highest difference:")
            for i, pattern in enumerate(all_patterns[:5], 1):
                data = pattern['data']
                if 'win_rate' in data:
                    win_rate = data['win_rate']
                    count = data['count']
                elif 'win_rate_60min' in data:
                    win_rate = data['win_rate_60min']
                    count = data['count_60min']
                else:
                    win_rate = data['mean']
                    count = data['count']
                
                print(f"{i}. {pattern['type']} - {pattern['factor']}: {pattern['value']}")
                print(f"   Win Rate: {win_rate:.1%}")
                print(f"   Difference: {pattern['difference']:.1%}")
                print(f"   Count: {count}")
                print()
        
        self.significant_patterns = significant_patterns
        return significant_patterns
    
    def generate_factor_report(self):
        """สร้างรายงานปัจจัยที่ส่งผลต่อ win rate"""
        print("\n" + "="*80)
        print("FACTOR ANALYSIS REPORT")
        print("="*80)
        
        print(f"ข้อมูลที่วิเคราะห์: {len(self.df)} records")
        print(f"ช่วงเวลา: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        
        print(f"\nSignificant Patterns ที่พบ: {len(self.significant_patterns)} patterns")
        
        if self.significant_patterns:
            print("\nSignificant Patterns (≥70% difference):")
            for i, pattern in enumerate(self.significant_patterns, 1):
                print(f"{i}. {pattern['type']} - {pattern['factor']}")
                print(f"   Value: {pattern['value']}")
                print(f"   Win Rate: {pattern['win_rate']:.1%}")
                print(f"   Difference: {pattern['difference']:+.1%}")
                print(f"   Count: {pattern['count']}")
                print(f"   Significance: {pattern['significance']}")
                print()
        else:
            print("ไม่พบ Significant Patterns ที่มีความแตกต่าง ≥70%")
            print("ต้องวิเคราะห์เพิ่มเติมหรือลดเกณฑ์การตัดสิน")
        
        print("\n" + "="*80)
    
    def run_factor_analysis(self):
        """รันการวิเคราะห์ปัจจัยแบบครบถ้วน"""
        print("เริ่มต้น Factor Analysis...")
        print("="*80)
        
        self.analyze_time_factors()
        self.analyze_strategy_factors()
        self.analyze_action_factors()
        self.analyze_price_factors()
        self.analyze_combination_factors()
        self.identify_significant_patterns()
        self.generate_factor_report()
        
        print("Factor Analysis เสร็จสิ้น!")
        return self.factors, self.significant_patterns

if __name__ == "__main__":
    # เริ่มต้น Factor Analyzer
    analyzer = FactorAnalyzer("Result Last 120HR.csv")
    
    # รันการวิเคราะห์ปัจจัย
    factors, significant_patterns = analyzer.run_factor_analysis()
