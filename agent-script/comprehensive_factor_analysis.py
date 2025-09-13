#!/usr/bin/env python3
"""
Comprehensive Factor Analysis for Binary Options Trading
วิเคราะห์ปัจจัยที่ส่งผลต่อ win rate แบบละเอียดและครบถ้วน
รวมข้อมูลหลายชุดและสร้างระบบที่ agent เครื่องอื่นสามารถ resume งานต่อได้
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import json
import os
warnings.filterwarnings('ignore')

class ComprehensiveFactorAnalyzer:
    def __init__(self, data_files):
        """เริ่มต้นการวิเคราะห์ปัจจัยแบบครบถ้วน"""
        self.data_files = data_files
        self.df = None
        self.factors = {}
        self.significant_patterns = {}
        self.analysis_results = {}
        self.dashboard_config = {}
        self.load_all_data()
    
    def load_all_data(self):
        """โหลดข้อมูลจากไฟล์ทั้งหมด"""
        print("กำลังโหลดข้อมูลจากไฟล์ทั้งหมด...")
        
        all_dataframes = []
        
        for file_path in self.data_files:
            if os.path.exists(file_path):
                print(f"โหลดข้อมูลจาก: {file_path}")
                df = pd.read_csv(file_path)
                df['source_file'] = file_path
                all_dataframes.append(df)
                print(f"  - {len(df)} records")
            else:
                print(f"ไม่พบไฟล์: {file_path}")
        
        if all_dataframes:
            self.df = pd.concat(all_dataframes, ignore_index=True)
            print(f"รวมข้อมูลทั้งหมด: {len(self.df)} records")
        else:
            raise ValueError("ไม่พบข้อมูลใดๆ")
        
        # ประมวลผลข้อมูล
        self.process_data()
    
    def process_data(self):
        """ประมวลผลข้อมูลให้พร้อมสำหรับการวิเคราะห์"""
        print("กำลังประมวลผลข้อมูล...")
        
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
        self.df['day_of_month'] = self.df['entry_time'].dt.day
        self.df['week_of_year'] = self.df['entry_time'].dt.isocalendar().week
        
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
        
        # คำนวณ price momentum
        self.df['momentum_10min'] = np.where(self.df['price_change_10min'] > 0, 'Positive', 
                                           np.where(self.df['price_change_10min'] < 0, 'Negative', 'Neutral'))
        self.df['momentum_30min'] = np.where(self.df['price_change_30min'] > 0, 'Positive', 
                                           np.where(self.df['price_change_30min'] < 0, 'Negative', 'Neutral'))
        self.df['momentum_60min'] = np.where(self.df['price_change_60min'] > 0, 'Positive', 
                                           np.where(self.df['price_change_60min'] < 0, 'Negative', 'Neutral'))
        
        # คำนวณ price direction
        self.df['price_direction_10min'] = np.where(self.df['price_change_10min'] > 0, 'Up', 'Down')
        self.df['price_direction_30min'] = np.where(self.df['price_change_30min'] > 0, 'Up', 'Down')
        self.df['price_direction_60min'] = np.where(self.df['price_change_60min'] > 0, 'Up', 'Down')
        
        # คำนวณ market trend (ใช้ price change 60min)
        trend_ranges = pd.cut(self.df['price_change_60min'], bins=4, labels=['Strong Down', 'Down', 'Sideways', 'Strong Up'])
        self.df['market_trend'] = trend_ranges
        
        # คำนวณ volatility level
        vol_ranges = pd.cut(self.df['volatility_60min'], bins=3, labels=['Low', 'Medium', 'High'])
        self.df['volatility_level'] = vol_ranges
        
        # คำนวณ price range
        price_ranges = pd.cut(self.df['entry_price'], bins=10, labels=False)
        self.df['price_range'] = price_ranges
        
        print(f"ข้อมูลครอบคลุม: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        print(f"Total Records: {len(self.df)}")
    
    def analyze_time_factors(self):
        """วิเคราะห์ Time Factors แบบละเอียด"""
        print("\n=== TIME FACTORS ANALYSIS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        print(f"Overall Win Rate: {overall_winrate:.1%}")
        
        # 1. Hour Factor Analysis
        hour_analysis = self.df.groupby('hour').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        hour_analysis.columns = ['win_rate', 'count', 'std']
        hour_analysis = hour_analysis[hour_analysis['count'] >= 10]
        
        hour_analysis['difference'] = hour_analysis['win_rate'] - overall_winrate
        hour_analysis['abs_difference'] = abs(hour_analysis['difference'])
        
        # หา significant hours
        significant_hours = hour_analysis[hour_analysis['abs_difference'] >= 0.2]
        very_significant_hours = hour_analysis[hour_analysis['abs_difference'] >= 0.5]
        
        print(f"Significant Hours (≥20% difference): {len(significant_hours)} hours")
        print(f"Very Significant Hours (≥50% difference): {len(very_significant_hours)} hours")
        
        # 2. Day of Week Factor Analysis
        day_analysis = self.df.groupby('day_of_week').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        day_analysis.columns = ['win_rate', 'count', 'std']
        day_analysis = day_analysis[day_analysis['count'] >= 10]
        
        day_analysis['difference'] = day_analysis['win_rate'] - overall_winrate
        day_analysis['abs_difference'] = abs(day_analysis['difference'])
        
        significant_days = day_analysis[day_analysis['abs_difference'] >= 0.2]
        
        print(f"Significant Days (≥20% difference): {len(significant_days)} days")
        
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
        
        print(f"Significant Time Ranges (≥30% difference): {len(significant_time_ranges)} ranges")
        
        # 4. Week of Year Analysis
        week_analysis = self.df.groupby('week_of_year').agg({
            'win_60min': ['mean', 'count']
        }).round(3)
        week_analysis.columns = ['win_rate', 'count']
        week_analysis = week_analysis[week_analysis['count'] >= 20]
        
        week_analysis['difference'] = week_analysis['win_rate'] - overall_winrate
        week_analysis['abs_difference'] = abs(week_analysis['difference'])
        
        significant_weeks = week_analysis[week_analysis['abs_difference'] >= 0.2]
        
        print(f"Significant Weeks (≥20% difference): {len(significant_weeks)} weeks")
        
        self.factors['time'] = {
            'overall_winrate': overall_winrate,
            'significant_hours': significant_hours.to_dict('index'),
            'very_significant_hours': very_significant_hours.to_dict('index'),
            'significant_days': significant_days.to_dict('index'),
            'significant_time_ranges': significant_time_ranges.to_dict('index'),
            'significant_weeks': significant_weeks.to_dict('index')
        }
    
    def analyze_strategy_factors(self):
        """วิเคราะห์ Strategy Factors แบบละเอียด"""
        print("\n=== STRATEGY FACTORS ANALYSIS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        
        # 1. Strategy Performance Analysis
        strategy_analysis = self.df.groupby('strategy').agg({
            'win_10min': ['mean', 'count', 'std'],
            'win_30min': ['mean', 'count', 'std'],
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        
        strategy_analysis.columns = ['win_rate_10min', 'count_10min', 'std_10min', 
                                   'win_rate_30min', 'count_30min', 'std_30min',
                                   'win_rate_60min', 'count_60min', 'std_60min']
        
        # หา strategies ที่มี win rate แตกต่างกันมาก
        strategy_analysis['difference_60min'] = strategy_analysis['win_rate_60min'] - overall_winrate
        strategy_analysis['abs_difference_60min'] = abs(strategy_analysis['difference_60min'])
        
        significant_strategies = strategy_analysis[strategy_analysis['abs_difference_60min'] >= 0.15]
        very_significant_strategies = strategy_analysis[strategy_analysis['abs_difference_60min'] >= 0.3]
        
        print(f"Significant Strategies (≥15% difference): {len(significant_strategies)} strategies")
        print(f"Very Significant Strategies (≥30% difference): {len(very_significant_strategies)} strategies")
        
        # 2. Strategy Consistency Analysis
        strategy_analysis['consistency_60min'] = 1 - (strategy_analysis['std_60min'] / strategy_analysis['win_rate_60min'])
        consistent_strategies = strategy_analysis[strategy_analysis['consistency_60min'] >= 0.8]
        
        print(f"Consistent Strategies (≥80% consistency): {len(consistent_strategies)} strategies")
        
        # 3. Strategy + Time Analysis
        strategy_time = self.df.groupby(['strategy', 'hour'])['win_60min'].agg(['mean', 'count']).reset_index()
        strategy_time = strategy_time[strategy_time['count'] >= 5]
        
        strategy_time['difference'] = strategy_time['mean'] - overall_winrate
        strategy_time['abs_difference'] = abs(strategy_time['difference'])
        
        significant_strategy_time = strategy_time[strategy_time['abs_difference'] >= 0.4]
        
        print(f"Significant Strategy+Time combinations (≥40% difference): {len(significant_strategy_time)} combinations")
        
        self.factors['strategy'] = {
            'overall_winrate': overall_winrate,
            'significant_strategies': significant_strategies.to_dict('index'),
            'very_significant_strategies': very_significant_strategies.to_dict('index'),
            'consistent_strategies': consistent_strategies.to_dict('index'),
            'significant_strategy_time': significant_strategy_time.to_dict('records')
        }
    
    def analyze_action_factors(self):
        """วิเคราะห์ Action Factors แบบละเอียด"""
        print("\n=== ACTION FACTORS ANALYSIS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        
        # 1. Action Performance Analysis
        action_analysis = self.df.groupby('action').agg({
            'win_10min': ['mean', 'count', 'std'],
            'win_30min': ['mean', 'count', 'std'],
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        
        action_analysis.columns = ['win_rate_10min', 'count_10min', 'std_10min', 
                                 'win_rate_30min', 'count_30min', 'std_30min',
                                 'win_rate_60min', 'count_60min', 'std_60min']
        
        # หา actions ที่มี win rate แตกต่างกันมาก
        action_analysis['difference_60min'] = action_analysis['win_rate_60min'] - overall_winrate
        action_analysis['abs_difference_60min'] = abs(action_analysis['difference_60min'])
        
        significant_actions = action_analysis[action_analysis['abs_difference_60min'] >= 0.15]
        very_significant_actions = action_analysis[action_analysis['abs_difference_60min'] >= 0.3]
        
        print(f"Significant Actions (≥15% difference): {len(significant_actions)} actions")
        print(f"Very Significant Actions (≥30% difference): {len(very_significant_actions)} actions")
        
        # 2. Action + Time Analysis
        action_time = self.df.groupby(['action', 'hour'])['win_60min'].agg(['mean', 'count']).reset_index()
        action_time = action_time[action_time['count'] >= 5]
        
        action_time['difference'] = action_time['mean'] - overall_winrate
        action_time['abs_difference'] = abs(action_time['difference'])
        
        significant_action_time = action_time[action_time['abs_difference'] >= 0.4]
        
        print(f"Significant Action+Time combinations (≥40% difference): {len(significant_action_time)} combinations")
        
        # 3. Action Sequence Analysis
        self.df = self.df.sort_values(['strategy', 'entry_time'])
        self.df['prev_action'] = self.df.groupby('strategy')['action'].shift(1)
        self.df['prev_result'] = self.df.groupby('strategy')['win_60min'].shift(1)
        
        # วิเคราะห์ action sequence
        sequence_data = self.df[self.df['prev_action'].notna()].copy()
        if len(sequence_data) > 0:
            sequence_analysis = sequence_data.groupby(['prev_action', 'action'])['win_60min'].mean().reset_index()
            sequence_analysis = sequence_analysis.merge(
                sequence_data.groupby(['prev_action', 'action'])['win_60min'].count().reset_index(),
                on=['prev_action', 'action'],
                suffixes=('_mean', '_count')
            )
            sequence_analysis = sequence_analysis[sequence_analysis['win_60min_count'] >= 5]
            
            sequence_analysis['difference'] = sequence_analysis['win_60min_mean'] - overall_winrate
            sequence_analysis['abs_difference'] = abs(sequence_analysis['difference'])
            
            significant_sequences = sequence_analysis[sequence_analysis['abs_difference'] >= 0.3]
            
            print(f"Significant Action Sequences (≥30% difference): {len(significant_sequences)} sequences")
        else:
            significant_sequences = pd.DataFrame()
        
        self.factors['action'] = {
            'overall_winrate': overall_winrate,
            'significant_actions': significant_actions.to_dict('index'),
            'very_significant_actions': very_significant_actions.to_dict('index'),
            'significant_action_time': significant_action_time.to_dict('records'),
            'significant_sequences': significant_sequences.to_dict('records') if len(significant_sequences) > 0 else []
        }
    
    def analyze_price_factors(self):
        """วิเคราะห์ Price Factors แบบละเอียด"""
        print("\n=== PRICE FACTORS ANALYSIS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        
        # 1. Price Range Analysis
        price_analysis = self.df.groupby('price_range').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        price_analysis.columns = ['win_rate', 'count', 'std']
        price_analysis = price_analysis[price_analysis['count'] >= 10]
        
        price_analysis['difference'] = price_analysis['win_rate'] - overall_winrate
        price_analysis['abs_difference'] = abs(price_analysis['difference'])
        
        significant_price_ranges = price_analysis[price_analysis['abs_difference'] >= 0.2]
        
        print(f"Significant Price Ranges (≥20% difference): {len(significant_price_ranges)} ranges")
        
        # 2. Volatility Analysis
        vol_analysis = self.df.groupby('volatility_level').agg({
            'win_60min': ['mean', 'count', 'std']
        }).round(3)
        vol_analysis.columns = ['win_rate', 'count', 'std']
        vol_analysis = vol_analysis[vol_analysis['count'] >= 10]
        
        vol_analysis['difference'] = vol_analysis['win_rate'] - overall_winrate
        vol_analysis['abs_difference'] = abs(vol_analysis['difference'])
        
        significant_vol_ranges = vol_analysis[vol_analysis['abs_difference'] >= 0.2]
        
        print(f"Significant Volatility Ranges (≥20% difference): {len(significant_vol_ranges)} ranges")
        
        # 3. Price Direction Analysis
        direction_analysis = self.df.groupby('price_direction_60min')['win_60min'].agg(['mean', 'count']).round(3)
        direction_analysis.columns = ['win_rate', 'count']
        
        direction_analysis['difference'] = direction_analysis['win_rate'] - overall_winrate
        direction_analysis['abs_difference'] = abs(direction_analysis['difference'])
        
        significant_directions = direction_analysis[direction_analysis['abs_difference'] >= 0.1]
        
        print(f"Significant Price Directions (≥10% difference): {len(significant_directions)} directions")
        
        # 4. Market Trend Analysis
        trend_analysis = self.df.groupby('market_trend')['win_60min'].agg(['mean', 'count']).round(3)
        trend_analysis.columns = ['win_rate', 'count']
        trend_analysis = trend_analysis[trend_analysis['count'] >= 10]
        
        trend_analysis['difference'] = trend_analysis['win_rate'] - overall_winrate
        trend_analysis['abs_difference'] = abs(trend_analysis['difference'])
        
        significant_trends = trend_analysis[trend_analysis['abs_difference'] >= 0.2]
        
        print(f"Significant Market Trends (≥20% difference): {len(significant_trends)} trends")
        
        self.factors['price'] = {
            'overall_winrate': overall_winrate,
            'significant_price_ranges': significant_price_ranges.to_dict('index'),
            'significant_vol_ranges': significant_vol_ranges.to_dict('index'),
            'significant_directions': significant_directions.to_dict('index'),
            'significant_trends': significant_trends.to_dict('index')
        }
    
    def analyze_combination_factors(self):
        """วิเคราะห์ Combination Factors แบบละเอียด"""
        print("\n=== COMBINATION FACTORS ANALYSIS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        
        # 1. Strategy + Action + Time Analysis
        combo_analysis = self.df.groupby(['strategy', 'action', 'hour'])['win_60min'].agg(['mean', 'count']).reset_index()
        combo_analysis = combo_analysis[combo_analysis['count'] >= 3]
        
        combo_analysis['difference'] = combo_analysis['mean'] - overall_winrate
        combo_analysis['abs_difference'] = abs(combo_analysis['difference'])
        
        significant_combos = combo_analysis[combo_analysis['abs_difference'] >= 0.4]
        very_significant_combos = combo_analysis[combo_analysis['abs_difference'] >= 0.6]
        
        print(f"Significant Strategy+Action+Time combinations (≥40% difference): {len(significant_combos)} combinations")
        print(f"Very Significant Strategy+Action+Time combinations (≥60% difference): {len(very_significant_combos)} combinations")
        
        # 2. Strategy + Price Range Analysis
        price_strategy = self.df.groupby(['strategy', 'price_range'])['win_60min'].agg(['mean', 'count']).reset_index()
        price_strategy = price_strategy[price_strategy['count'] >= 5]
        
        price_strategy['difference'] = price_strategy['mean'] - overall_winrate
        price_strategy['abs_difference'] = abs(price_strategy['difference'])
        
        significant_price_strategy = price_strategy[price_strategy['abs_difference'] >= 0.3]
        
        print(f"Significant Strategy+Price combinations (≥30% difference): {len(significant_price_strategy)} combinations")
        
        # 3. Action + Volatility Analysis
        vol_action = self.df.groupby(['action', 'volatility_level'])['win_60min'].agg(['mean', 'count']).reset_index()
        vol_action = vol_action[vol_action['count'] >= 5]
        
        vol_action['difference'] = vol_action['mean'] - overall_winrate
        vol_action['abs_difference'] = abs(vol_action['difference'])
        
        significant_vol_action = vol_action[vol_action['abs_difference'] >= 0.3]
        
        print(f"Significant Action+Volatility combinations (≥30% difference): {len(significant_vol_action)} combinations")
        
        # 4. Strategy + Action + Day Analysis
        day_combo = self.df.groupby(['strategy', 'action', 'day_of_week'])['win_60min'].agg(['mean', 'count']).reset_index()
        day_combo = day_combo[day_combo['count'] >= 3]
        
        day_combo['difference'] = day_combo['mean'] - overall_winrate
        day_combo['abs_difference'] = abs(day_combo['difference'])
        
        significant_day_combo = day_combo[day_combo['abs_difference'] >= 0.4]
        
        print(f"Significant Strategy+Action+Day combinations (≥40% difference): {len(significant_day_combo)} combinations")
        
        self.factors['combination'] = {
            'overall_winrate': overall_winrate,
            'significant_combos': significant_combos.to_dict('records'),
            'very_significant_combos': very_significant_combos.to_dict('records'),
            'significant_price_strategy': significant_price_strategy.to_dict('records'),
            'significant_vol_action': significant_vol_action.to_dict('records'),
            'significant_day_combo': significant_day_combo.to_dict('records')
        }
    
    def analyze_trend_changes(self):
        """วิเคราะห์ Trend Changes - การเปลี่ยนแปลงของประสิทธิภาพตามเวลา"""
        print("\n=== TREND CHANGES ANALYSIS ===")
        
        # วิเคราะห์การเปลี่ยนแปลงของ win rate ตามเวลา
        self.df['time_window'] = self.df['entry_time'].dt.floor('6H')  # 6 ชั่วโมง window
        
        trend_analysis = self.df.groupby(['strategy', 'time_window'])['win_60min'].agg(['mean', 'count']).reset_index()
        trend_analysis = trend_analysis[trend_analysis['count'] >= 5]
        
        # คำนวณการเปลี่ยนแปลงของ win rate
        trend_changes = []
        for strategy in trend_analysis['strategy'].unique():
            strategy_data = trend_analysis[trend_analysis['strategy'] == strategy].sort_values('time_window')
            if len(strategy_data) > 1:
                for i in range(1, len(strategy_data)):
                    prev_winrate = strategy_data.iloc[i-1]['mean']
                    curr_winrate = strategy_data.iloc[i]['mean']
                    change = curr_winrate - prev_winrate
                    
                    if abs(change) >= 0.3:  # 30% change
                        trend_changes.append({
                            'strategy': strategy,
                            'time_window': strategy_data.iloc[i]['time_window'],
                            'prev_winrate': prev_winrate,
                            'curr_winrate': curr_winrate,
                            'change': change,
                            'count': strategy_data.iloc[i]['count']
                        })
        
        trend_changes_df = pd.DataFrame(trend_changes)
        
        if len(trend_changes_df) > 0:
            print(f"Significant Trend Changes (≥30% change): {len(trend_changes_df)} changes")
            
            # หา strategies ที่มีการเปลี่ยนแปลงมากที่สุด
            strategy_changes = trend_changes_df.groupby('strategy')['change'].agg(['mean', 'std', 'count']).round(3)
            strategy_changes.columns = ['avg_change', 'change_std', 'change_count']
            
            volatile_strategies = strategy_changes[strategy_changes['change_std'] >= 0.2]
            print(f"Volatile Strategies (high change std): {len(volatile_strategies)} strategies")
            
            for strategy in volatile_strategies.index:
                avg_change = strategy_changes.loc[strategy, 'avg_change']
                change_std = strategy_changes.loc[strategy, 'change_std']
                change_count = strategy_changes.loc[strategy, 'change_count']
                print(f"  {strategy}: avg change {avg_change:+.1%}, std {change_std:.1%}, count {change_count}")
        else:
            print("ไม่พบ Significant Trend Changes")
        
        self.factors['trend_changes'] = {
            'trend_changes': trend_changes_df.to_dict('records') if len(trend_changes_df) > 0 else [],
            'volatile_strategies': volatile_strategies.to_dict('index') if len(trend_changes_df) > 0 else {}
        }
    
    def identify_significant_patterns(self):
        """ระบุ Significant Patterns ที่ชัดเจน (ความแตกต่าง > 70%)"""
        print("\n=== IDENTIFYING SIGNIFICANT PATTERNS ===")
        
        significant_patterns = []
        
        # 1. Time Patterns
        if 'time' in self.factors:
            time_factors = self.factors['time']
            
            # Very Significant Hours
            for hour, data in time_factors['very_significant_hours'].items():
                significant_patterns.append({
                    'type': 'Time',
                    'factor': 'Hour',
                    'value': f"{hour:02d}:00",
                    'win_rate': data['win_rate'],
                    'difference': data['difference'],
                    'count': data['count'],
                    'significance': 'Very High'
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
                        'significance': 'Very High'
                    })
        
        # 2. Strategy Patterns
        if 'strategy' in self.factors:
            strategy_factors = self.factors['strategy']
            
            for strategy, data in strategy_factors['very_significant_strategies'].items():
                significant_patterns.append({
                    'type': 'Strategy',
                    'factor': 'Strategy Type',
                    'value': strategy,
                    'win_rate': data['win_rate_60min'],
                    'difference': data['difference_60min'],
                    'count': data['count_60min'],
                    'significance': 'Very High'
                })
        
        # 3. Action Patterns
        if 'action' in self.factors:
            action_factors = self.factors['action']
            
            for action, data in action_factors['very_significant_actions'].items():
                significant_patterns.append({
                    'type': 'Action',
                    'factor': 'Action Type',
                    'value': action,
                    'win_rate': data['win_rate_60min'],
                    'difference': data['difference_60min'],
                    'count': data['count_60min'],
                    'significance': 'Very High'
                })
        
        # 4. Combination Patterns
        if 'combination' in self.factors:
            combo_factors = self.factors['combination']
            
            for combo in combo_factors['very_significant_combos']:
                significant_patterns.append({
                    'type': 'Combination',
                    'factor': 'Strategy+Action+Time',
                    'value': f"{combo['strategy']} + {combo['action']} at {combo['hour']:02d}:00",
                    'win_rate': combo['mean'],
                    'difference': combo['difference'],
                    'count': combo['count'],
                    'significance': 'Very High'
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
            print("ต้องวิเคราะห์เพิ่มเติมหรือลดเกณฑ์การตัดสิน")
        
        self.significant_patterns = significant_patterns
        return significant_patterns
    
    def create_dashboard_config(self):
        """สร้าง Dashboard Configuration สำหรับ Metabase"""
        print("\n=== CREATING DASHBOARD CONFIGURATION ===")
        
        dashboard_config = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_records': len(self.df),
                'date_range': {
                    'start': self.df['entry_time'].min().isoformat(),
                    'end': self.df['entry_time'].max().isoformat()
                },
                'strategies': self.df['strategy'].nunique(),
                'actions': self.df['action'].nunique()
            },
            'charts': []
        }
        
        # 1. Time Pattern Charts
        if 'time' in self.factors:
            time_factors = self.factors['time']
            
            # Hour Heatmap
            dashboard_config['charts'].append({
                'type': 'heatmap',
                'title': 'Win Rate by Hour',
                'description': 'แสดง win rate ตามชั่วโมง',
                'data_source': 'time_factors.significant_hours',
                'x_axis': 'hour',
                'y_axis': 'win_rate',
                'color_scale': 'RdYlGn'
            })
            
            # Day of Week Bar Chart
            dashboard_config['charts'].append({
                'type': 'bar_chart',
                'title': 'Win Rate by Day of Week',
                'description': 'แสดง win rate ตามวันในสัปดาห์',
                'data_source': 'time_factors.significant_days',
                'x_axis': 'day_of_week',
                'y_axis': 'win_rate'
            })
        
        # 2. Strategy Pattern Charts
        if 'strategy' in self.factors:
            strategy_factors = self.factors['strategy']
            
            # Strategy Performance Bar Chart
            dashboard_config['charts'].append({
                'type': 'bar_chart',
                'title': 'Strategy Performance',
                'description': 'แสดง win rate ตาม strategy',
                'data_source': 'strategy_factors.significant_strategies',
                'x_axis': 'strategy',
                'y_axis': 'win_rate_60min'
            })
            
            # Strategy Consistency Scatter Plot
            dashboard_config['charts'].append({
                'type': 'scatter_plot',
                'title': 'Strategy Consistency',
                'description': 'แสดงความสม่ำเสมอของ strategy',
                'data_source': 'strategy_factors.consistent_strategies',
                'x_axis': 'win_rate_60min',
                'y_axis': 'consistency_60min'
            })
        
        # 3. Action Pattern Charts
        if 'action' in self.factors:
            action_factors = self.factors['action']
            
            # Action Performance Bar Chart
            dashboard_config['charts'].append({
                'type': 'bar_chart',
                'title': 'Action Performance',
                'description': 'แสดง win rate ตาม action',
                'data_source': 'action_factors.significant_actions',
                'x_axis': 'action',
                'y_axis': 'win_rate_60min'
            })
        
        # 4. Combination Pattern Charts
        if 'combination' in self.factors:
            combo_factors = self.factors['combination']
            
            # Strategy+Action+Time Heatmap
            dashboard_config['charts'].append({
                'type': 'heatmap',
                'title': 'Strategy+Action+Time Combinations',
                'description': 'แสดง win rate ตามการรวมกันของ strategy, action และเวลา',
                'data_source': 'combination_factors.significant_combos',
                'x_axis': 'strategy',
                'y_axis': 'action',
                'color_scale': 'RdYlGn'
            })
        
        # 5. Trend Change Charts
        if 'trend_changes' in self.factors:
            trend_factors = self.factors['trend_changes']
            
            # Trend Changes Line Chart
            dashboard_config['charts'].append({
                'type': 'line_chart',
                'title': 'Trend Changes Over Time',
                'description': 'แสดงการเปลี่ยนแปลงของ win rate ตามเวลา',
                'data_source': 'trend_changes.trend_changes',
                'x_axis': 'time_window',
                'y_axis': 'curr_winrate'
            })
        
        self.dashboard_config = dashboard_config
        
        # บันทึก dashboard config
        with open('dashboard_config.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard_config, f, indent=2, ensure_ascii=False)
        
        print(f"Dashboard Configuration สร้างเสร็จ: {len(dashboard_config['charts'])} charts")
        print("บันทึกใน: dashboard_config.json")
    
    def save_analysis_results(self):
        """บันทึกผลการวิเคราะห์ทั้งหมด"""
        print("\n=== SAVING ANALYSIS RESULTS ===")
        
        # บันทึก factors
        with open('factors_analysis.json', 'w', encoding='utf-8') as f:
            # แปลง keys ที่ไม่ใช่ string เป็น string
            def convert_keys(obj):
                if isinstance(obj, dict):
                    return {str(k): convert_keys(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_keys(item) for item in obj]
                else:
                    return obj
            
            factors_serializable = convert_keys(self.factors)
            json.dump(factors_serializable, f, indent=2, ensure_ascii=False, default=str)
        
        # บันทึก significant patterns
        with open('significant_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(self.significant_patterns, f, indent=2, ensure_ascii=False, default=str)
        
        # บันทึก analysis summary
        analysis_summary = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_records': len(self.df),
                'date_range': {
                    'start': self.df['entry_time'].min().isoformat(),
                    'end': self.df['entry_time'].max().isoformat()
                },
                'strategies': self.df['strategy'].nunique(),
                'actions': self.df['action'].nunique()
            },
            'significant_patterns_count': len(self.significant_patterns),
            'factors_analyzed': list(self.factors.keys()),
            'dashboard_charts': len(self.dashboard_config['charts']) if self.dashboard_config else 0
        }
        
        with open('analysis_summary.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_summary, f, indent=2, ensure_ascii=False, default=str)
        
        print("ผลการวิเคราะห์บันทึกเสร็จ:")
        print("- factors_analysis.json")
        print("- significant_patterns.json")
        print("- analysis_summary.json")
        print("- dashboard_config.json")
    
    def generate_comprehensive_report(self):
        """สร้างรายงานแบบครบถ้วน"""
        print("\n" + "="*100)
        print("COMPREHENSIVE FACTOR ANALYSIS REPORT")
        print("="*100)
        
        print(f"ข้อมูลที่วิเคราะห์: {len(self.df)} records")
        print(f"ช่วงเวลา: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        print(f"Source Files: {len(self.data_files)} ไฟล์")
        
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
        
        print(f"\nDashboard Charts: {len(self.dashboard_config['charts'])} charts")
        for i, chart in enumerate(self.dashboard_config['charts'], 1):
            print(f"{i}. {chart['title']} ({chart['type']})")
            print(f"   Description: {chart['description']}")
            print()
        
        print("\n" + "="*100)
    
    def run_comprehensive_analysis(self):
        """รันการวิเคราะห์แบบครบถ้วน"""
        print("เริ่มต้น Comprehensive Factor Analysis...")
        print("="*100)
        
        # วิเคราะห์ปัจจัยต่างๆ
        self.analyze_time_factors()
        self.analyze_strategy_factors()
        self.analyze_action_factors()
        self.analyze_price_factors()
        self.analyze_combination_factors()
        self.analyze_trend_changes()
        
        # ระบุ significant patterns
        self.identify_significant_patterns()
        
        # สร้าง dashboard config
        self.create_dashboard_config()
        
        # บันทึกผลการวิเคราะห์
        self.save_analysis_results()
        
        # สร้างรายงาน
        self.generate_comprehensive_report()
        
        print("Comprehensive Factor Analysis เสร็จสิ้น!")
        return self.factors, self.significant_patterns, self.dashboard_config

if __name__ == "__main__":
    # กำหนดไฟล์ข้อมูล
    data_files = [
        "Result Last 120HR.csv",
        "Result 2568-09-11 22-54-00.csv"
    ]
    
    # เริ่มต้น Comprehensive Factor Analyzer
    analyzer = ComprehensiveFactorAnalyzer(data_files)
    
    # รันการวิเคราะห์แบบครบถ้วน
    factors, significant_patterns, dashboard_config = analyzer.run_comprehensive_analysis()
