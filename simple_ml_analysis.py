#!/usr/bin/env python3
"""
Simple Machine Learning Analysis for Binary Options Trading
ใช้ libraries ที่มีอยู่แล้วเพื่อหาจุดบ่งชี้ที่ส่งผลต่อ win rate
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
import json

class SimpleMLAnalyzer:
    def __init__(self, data_files):
        """เริ่มต้นการวิเคราะห์ด้วย Simple ML"""
        self.data_files = data_files
        self.df = None
        self.feature_importance = {}
        self.patterns = {}
        self.load_all_data()
    
    def load_all_data(self):
        """โหลดข้อมูลจากไฟล์ทั้งหมด"""
        print("กำลังโหลดข้อมูลจากไฟล์ทั้งหมด...")
        
        all_dataframes = []
        
        for file_path in self.data_files:
            try:
                print(f"โหลดข้อมูลจาก: {file_path}")
                df = pd.read_csv(file_path)
                df['source_file'] = file_path
                all_dataframes.append(df)
                print(f"  - {len(df)} records")
            except Exception as e:
                print(f"ไม่สามารถโหลดไฟล์ {file_path}: {e}")
        
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
        self.df['momentum_10min'] = np.where(self.df['price_change_10min'] > 0, 1, 
                                           np.where(self.df['price_change_10min'] < 0, -1, 0))
        self.df['momentum_30min'] = np.where(self.df['price_change_30min'] > 0, 1, 
                                           np.where(self.df['price_change_30min'] < 0, -1, 0))
        self.df['momentum_60min'] = np.where(self.df['price_change_60min'] > 0, 1, 
                                           np.where(self.df['price_change_60min'] < 0, -1, 0))
        
        # คำนวณ price direction
        self.df['price_direction_10min'] = np.where(self.df['price_change_10min'] > 0, 1, 0)
        self.df['price_direction_30min'] = np.where(self.df['price_change_30min'] > 0, 1, 0)
        self.df['price_direction_60min'] = np.where(self.df['price_change_60min'] > 0, 1, 0)
        
        # คำนวณ market trend
        trend_ranges = pd.cut(self.df['price_change_60min'], bins=4, labels=[0, 1, 2, 3])
        self.df['market_trend'] = trend_ranges.astype(int)
        
        # คำนวณ volatility level
        vol_ranges = pd.cut(self.df['volatility_60min'], bins=3, labels=[0, 1, 2])
        self.df['volatility_level'] = vol_ranges.astype(int)
        
        # คำนวณ price range
        price_ranges = pd.cut(self.df['entry_price'], bins=10, labels=False)
        self.df['price_range'] = price_ranges
        
        # สร้าง features เพิ่มเติม
        self.create_advanced_features()
        
        print(f"ข้อมูลครอบคลุม: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        print(f"Total Records: {len(self.df)}")
    
    def create_advanced_features(self):
        """สร้าง features ขั้นสูง"""
        print("สร้าง advanced features...")
        
        # เรียงข้อมูลตามเวลา
        self.df = self.df.sort_values(['strategy', 'entry_time']).reset_index(drop=True)
        
        # สร้าง rolling features
        for strategy in self.df['strategy'].unique():
            strategy_mask = self.df['strategy'] == strategy
            strategy_data = self.df[strategy_mask].copy()
            
            # Rolling win rate
            self.df.loc[strategy_mask, 'rolling_win_rate_10'] = strategy_data['win_60min'].rolling(window=10, min_periods=1).mean()
            self.df.loc[strategy_mask, 'rolling_win_rate_20'] = strategy_data['win_60min'].rolling(window=20, min_periods=1).mean()
            
            # Rolling volatility
            self.df.loc[strategy_mask, 'rolling_volatility_10'] = strategy_data['volatility_60min'].rolling(window=10, min_periods=1).mean()
            self.df.loc[strategy_mask, 'rolling_volatility_20'] = strategy_data['volatility_60min'].rolling(window=20, min_periods=1).mean()
            
            # Previous results
            self.df.loc[strategy_mask, 'prev_win_60min'] = strategy_data['win_60min'].shift(1)
            self.df.loc[strategy_mask, 'prev_2_win_60min'] = strategy_data['win_60min'].shift(2)
            self.df.loc[strategy_mask, 'prev_3_win_60min'] = strategy_data['win_60min'].shift(3)
            
            # Win streak
            self.df.loc[strategy_mask, 'win_streak'] = (strategy_data['win_60min'] * (strategy_data['win_60min'].groupby((strategy_data['win_60min'] != strategy_data['win_60min'].shift()).cumsum()).cumcount() + 1)).where(strategy_data['win_60min'] == 1, 0)
            
            # Loss streak
            self.df.loc[strategy_mask, 'loss_streak'] = ((1 - strategy_data['win_60min']) * ((1 - strategy_data['win_60min']).groupby(((1 - strategy_data['win_60min']) != (1 - strategy_data['win_60min']).shift()).cumsum()).cumcount() + 1)).where(strategy_data['win_60min'] == 0, 0)
        
        # สร้าง time-based features
        self.df['is_weekend'] = self.df['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)
        self.df['is_morning'] = ((self.df['hour'] >= 6) & (self.df['hour'] < 12)).astype(int)
        self.df['is_afternoon'] = ((self.df['hour'] >= 12) & (self.df['hour'] < 18)).astype(int)
        self.df['is_evening'] = ((self.df['hour'] >= 18) & (self.df['hour'] < 24)).astype(int)
        self.df['is_night'] = ((self.df['hour'] >= 0) & (self.df['hour'] < 6)).astype(int)
        
        # สร้าง interaction features
        self.df['strategy_action_interaction'] = self.df['strategy'].astype(str) + '_' + self.df['action'].astype(str)
        self.df['hour_strategy_interaction'] = self.df['hour'].astype(str) + '_' + self.df['strategy'].astype(str)
        
        print("Advanced features created successfully")
    
    def analyze_correlation_patterns(self):
        """วิเคราะห์ correlation patterns"""
        print("\n=== ANALYZING CORRELATION PATTERNS ===")
        
        # เลือก features ที่สำคัญ
        feature_columns = [
            'hour', 'day_of_month', 'week_of_year', 'minute',
            'entry_price', 'price_change_10min', 'price_change_30min', 'price_change_60min',
            'volatility_10min', 'volatility_30min', 'volatility_60min',
            'momentum_10min', 'momentum_30min', 'momentum_60min',
            'price_direction_10min', 'price_direction_30min', 'price_direction_60min',
            'market_trend', 'volatility_level', 'price_range',
            'rolling_win_rate_10', 'rolling_win_rate_20',
            'rolling_volatility_10', 'rolling_volatility_20',
            'prev_win_60min', 'prev_2_win_60min', 'prev_3_win_60min',
            'win_streak', 'loss_streak',
            'is_weekend', 'is_morning', 'is_afternoon', 'is_evening', 'is_night'
        ]
        
        # สร้าง categorical features
        categorical_columns = ['strategy', 'action', 'day_of_week']
        
        # Encode categorical features (simple mapping)
        for col in categorical_columns:
            unique_values = self.df[col].unique()
            mapping = {val: i for i, val in enumerate(unique_values)}
            self.df[f'{col}_encoded'] = self.df[col].map(mapping)
            feature_columns.append(f'{col}_encoded')
        
        # เลือก features
        X = self.df[feature_columns].fillna(0)
        
        # เลือก target variables
        y_10min = self.df['win_10min'].values
        y_30min = self.df['win_30min'].values
        y_60min = self.df['win_60min'].values
        
        # คำนวณ correlation กับ target variables
        correlations = {}
        for target_name, target in [('win_10min', y_10min), ('win_30min', y_30min), ('win_60min', y_60min)]:
            correlations[target_name] = {}
            for i, feature in enumerate(feature_columns):
                if i < len(X.columns):
                    corr = np.corrcoef(X.iloc[:, i], target)[0, 1]
                    correlations[target_name][feature] = corr if not np.isnan(corr) else 0
        
        # หา features ที่มีความสัมพันธ์สูง
        high_correlation_features = {}
        for target_name, corrs in correlations.items():
            sorted_corrs = sorted(corrs.items(), key=lambda x: abs(x[1]), reverse=True)
            high_correlation_features[target_name] = sorted_corrs[:10]
        
        print("Top 10 Features with Highest Correlation:")
        for target_name, features in high_correlation_features.items():
            print(f"\n{target_name}:")
            for i, (feature, corr) in enumerate(features, 1):
                print(f"  {i:2d}. {feature}: {corr:.4f}")
        
        return high_correlation_features
    
    def analyze_pattern_strength(self):
        """วิเคราะห์ความแข็งแกร่งของ patterns"""
        print("\n=== ANALYZING PATTERN STRENGTH ===")
        
        patterns = {}
        
        # 1. Time Patterns
        time_patterns = {}
        for hour in range(24):
            hour_data = self.df[self.df['hour'] == hour]
            if len(hour_data) >= 10:
                win_rate = hour_data['win_60min'].mean()
                count = len(hour_data)
                time_patterns[hour] = {'win_rate': win_rate, 'count': count}
        
        patterns['time'] = time_patterns
        
        # 2. Strategy Patterns
        strategy_patterns = {}
        for strategy in self.df['strategy'].unique():
            strategy_data = self.df[self.df['strategy'] == strategy]
            if len(strategy_data) >= 10:
                win_rate = strategy_data['win_60min'].mean()
                count = len(strategy_data)
                strategy_patterns[strategy] = {'win_rate': win_rate, 'count': count}
        
        patterns['strategy'] = strategy_patterns
        
        # 3. Action Patterns
        action_patterns = {}
        for action in self.df['action'].unique():
            action_data = self.df[self.df['action'] == action]
            if len(action_data) >= 10:
                win_rate = action_data['win_60min'].mean()
                count = len(action_data)
                action_patterns[action] = {'win_rate': win_rate, 'count': count}
        
        patterns['action'] = action_patterns
        
        # 4. Combination Patterns
        combination_patterns = {}
        for strategy in self.df['strategy'].unique():
            for action in self.df['action'].unique():
                combo_data = self.df[(self.df['strategy'] == strategy) & (self.df['action'] == action)]
                if len(combo_data) >= 5:
                    win_rate = combo_data['win_60min'].mean()
                    count = len(combo_data)
                    combination_patterns[f"{strategy}_{action}"] = {'win_rate': win_rate, 'count': count}
        
        patterns['combination'] = combination_patterns
        
        # 5. Volatility Patterns
        volatility_patterns = {}
        for vol_level in [0, 1, 2]:
            vol_data = self.df[self.df['volatility_level'] == vol_level]
            if len(vol_data) >= 10:
                win_rate = vol_data['win_60min'].mean()
                count = len(vol_data)
                volatility_patterns[vol_level] = {'win_rate': win_rate, 'count': count}
        
        patterns['volatility'] = volatility_patterns
        
        return patterns
    
    def identify_significant_patterns(self, patterns):
        """ระบุ patterns ที่มีความสำคัญ"""
        print("\n=== IDENTIFYING SIGNIFICANT PATTERNS ===")
        
        overall_winrate = self.df['win_60min'].mean()
        significant_patterns = {}
        
        for pattern_type, pattern_data in patterns.items():
            significant_patterns[pattern_type] = {}
            
            for pattern_name, data in pattern_data.items():
                win_rate = data['win_rate']
                count = data['count']
                difference = win_rate - overall_winrate
                abs_difference = abs(difference)
                
                # เกณฑ์ความสำคัญ
                if abs_difference >= 0.2 and count >= 10:  # 20% difference และข้อมูลเพียงพอ
                    significant_patterns[pattern_type][pattern_name] = {
                        'win_rate': win_rate,
                        'count': count,
                        'difference': difference,
                        'abs_difference': abs_difference,
                        'significance': 'High' if abs_difference >= 0.3 else 'Medium'
                    }
        
        # แสดงผล patterns ที่สำคัญ
        for pattern_type, sig_patterns in significant_patterns.items():
            if sig_patterns:
                print(f"\n{pattern_type.upper()} Patterns:")
                sorted_patterns = sorted(sig_patterns.items(), key=lambda x: x[1]['abs_difference'], reverse=True)
                for pattern_name, data in sorted_patterns:
                    print(f"  {pattern_name}: {data['win_rate']:.1%} (diff: {data['difference']:+.1%}, n={data['count']}, {data['significance']})")
        
        return significant_patterns
    
    def create_prediction_rules(self, significant_patterns):
        """สร้างกฎการทำนาย"""
        print("\n=== CREATING PREDICTION RULES ===")
        
        prediction_rules = []
        
        for pattern_type, patterns in significant_patterns.items():
            for pattern_name, data in patterns.items():
                if data['significance'] == 'High':
                    if data['difference'] > 0:
                        rule = f"IF {pattern_type} = {pattern_name} THEN PREDICT WIN (Confidence: {data['win_rate']:.1%})"
                    else:
                        rule = f"IF {pattern_type} = {pattern_name} THEN PREDICT LOSE (Confidence: {1-data['win_rate']:.1%})"
                    
                    prediction_rules.append({
                        'rule': rule,
                        'pattern_type': pattern_type,
                        'pattern_name': pattern_name,
                        'confidence': data['win_rate'] if data['difference'] > 0 else 1-data['win_rate'],
                        'support': data['count']
                    })
        
        # เรียงตาม confidence
        prediction_rules.sort(key=lambda x: x['confidence'], reverse=True)
        
        print("Top 10 Prediction Rules:")
        for i, rule in enumerate(prediction_rules[:10], 1):
            print(f"{i:2d}. {rule['rule']} (Support: {rule['support']})")
        
        return prediction_rules
    
    def generate_insights(self, high_correlation_features, significant_patterns, prediction_rules):
        """สร้าง insights จากผลการวิเคราะห์"""
        print("\n=== GENERATING INSIGHTS ===")
        
        insights = {
            'correlation_features': high_correlation_features,
            'significant_patterns': significant_patterns,
            'prediction_rules': prediction_rules,
            'key_findings': [],
            'recommendations': []
        }
        
        # สร้าง key findings
        total_patterns = sum(len(patterns) for patterns in significant_patterns.values())
        high_significance_patterns = sum(
            len([p for p in patterns.values() if p['significance'] == 'High'])
            for patterns in significant_patterns.values()
        )
        
        insights['key_findings'] = [
            f"Total significant patterns found: {total_patterns}",
            f"High significance patterns: {high_significance_patterns}",
            f"Prediction rules created: {len(prediction_rules)}",
            f"Overall win rate: {self.df['win_60min'].mean():.1%}",
            f"Total records analyzed: {len(self.df)}"
        ]
        
        # สร้างคำแนะนำ
        insights['recommendations'] = [
            "Use prediction rules for decision making",
            "Monitor high significance patterns regularly",
            "Focus on patterns with high confidence and support",
            "Update patterns with new data",
            "Combine multiple patterns for better accuracy"
        ]
        
        return insights
    
    def save_results(self, insights):
        """บันทึกผลการวิเคราะห์"""
        print("\n=== SAVING RESULTS ===")
        
        # บันทึก insights
        with open('simple_ml_insights.json', 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False, default=str)
        
        print("ผลการวิเคราะห์บันทึกเสร็จ:")
        print("- simple_ml_insights.json")
    
    def run_simple_ml_analysis(self):
        """รันการวิเคราะห์ Simple ML แบบครบถ้วน"""
        print("เริ่มต้น Simple Machine Learning Analysis...")
        print("="*80)
        
        # วิเคราะห์ correlation patterns
        high_correlation_features = self.analyze_correlation_patterns()
        
        # วิเคราะห์ pattern strength
        patterns = self.analyze_pattern_strength()
        
        # ระบุ significant patterns
        significant_patterns = self.identify_significant_patterns(patterns)
        
        # สร้าง prediction rules
        prediction_rules = self.create_prediction_rules(significant_patterns)
        
        # สร้าง insights
        insights = self.generate_insights(high_correlation_features, significant_patterns, prediction_rules)
        
        # บันทึกผลลัพธ์
        self.save_results(insights)
        
        print("\n" + "="*80)
        print("SIMPLE MACHINE LEARNING ANALYSIS COMPLETE")
        print("="*80)
        
        return insights

if __name__ == "__main__":
    # กำหนดไฟล์ข้อมูล
    data_files = [
        "Result Last 120HR.csv",
        "Result 2568-09-11 22-54-00.csv"
    ]
    
    # เริ่มต้น Simple ML Analyzer
    analyzer = SimpleMLAnalyzer(data_files)
    
    # รันการวิเคราะห์ Simple ML
    insights = analyzer.run_simple_ml_analysis()
