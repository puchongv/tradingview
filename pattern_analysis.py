#!/usr/bin/env python3
"""
Binary Options Pattern Analysis
วิเคราะห์ pattern การชนะ/แพ้สำหรับ Binary Options
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BinaryOptionsAnalyzer:
    def __init__(self, csv_file):
        """เริ่มต้นการวิเคราะห์ Binary Options"""
        self.csv_file = csv_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """โหลดข้อมูลจาก CSV file"""
        try:
            print("กำลังโหลดข้อมูล...")
            self.df = pd.read_csv(self.csv_file)
            print(f"โหลดข้อมูลสำเร็จ: {len(self.df)} รายการ")
            
            # แปลงคอลัมน์เวลา
            self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])
            self.df['created_at'] = pd.to_datetime(self.df['created_at'])
            self.df['updated_at'] = pd.to_datetime(self.df['updated_at'])
            
            # แปลงคอลัมน์ timestamp
            for col in ['price_10min_ts', 'price_30min_ts', 'price_60min_ts', 'price_1day_ts']:
                if col in self.df.columns:
                    self.df[col] = pd.to_datetime(self.df[col])
            
            # เพิ่มคอลัมน์สำหรับการวิเคราะห์
            self.df['hour'] = self.df['entry_time'].dt.hour
            self.df['day_of_week'] = self.df['entry_time'].dt.day_name()
            self.df['date'] = self.df['entry_time'].dt.date
            
            print("แปลงข้อมูลเวลาเสร็จสิ้น")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    
    def analyze_winning_patterns(self):
        """วิเคราะห์ pattern การชนะ"""
        print("\n" + "="*60)
        print("วิเคราะห์ PATTERN การชนะ")
        print("="*60)
        
        # วิเคราะห์แต่ละ timeframe
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} ANALYSIS ---")
                
                # กรองข้อมูลที่มีผลลัพธ์
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                if len(valid_data) > 0:
                    # วิเคราะห์ตาม strategy
                    strategy_analysis = valid_data.groupby('strategy')[result_col].agg(['count', lambda x: (x == 'WIN').sum()]).round(2)
                    strategy_analysis.columns = ['total_trades', 'wins']
                    strategy_analysis['win_rate'] = (strategy_analysis['wins'] / strategy_analysis['total_trades'] * 100).round(2)
                    strategy_analysis = strategy_analysis.sort_values('win_rate', ascending=False)
                    
                    print(f"\nStrategy Performance ({tf}):")
                    print(strategy_analysis.head(10))
                    
                    # วิเคราะห์ตาม action
                    action_analysis = valid_data.groupby('action')[result_col].agg(['count', lambda x: (x == 'WIN').sum()]).round(2)
                    action_analysis.columns = ['total_trades', 'wins']
                    action_analysis['win_rate'] = (action_analysis['wins'] / action_analysis['total_trades'] * 100).round(2)
                    
                    print(f"\nAction Performance ({tf}):")
                    print(action_analysis)
                    
                    # วิเคราะห์ตามชั่วโมง
                    hourly_analysis = valid_data.groupby('hour')[result_col].agg(['count', lambda x: (x == 'WIN').sum()]).round(2)
                    hourly_analysis.columns = ['total_trades', 'wins']
                    hourly_analysis['win_rate'] = (hourly_analysis['wins'] / hourly_analysis['total_trades'] * 100).round(2)
                    hourly_analysis = hourly_analysis.sort_values('win_rate', ascending=False)
                    
                    print(f"\nBest Hours ({tf}):")
                    print(hourly_analysis.head(5))
                    
                    print(f"\nWorst Hours ({tf}):")
                    print(hourly_analysis.tail(5))
    
    def analyze_losing_streaks(self):
        """วิเคราะห์ lost streaks"""
        print("\n" + "="*60)
        print("วิเคราะห์ LOST STREAKS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} LOST STREAKS ---")
                
                # สร้าง lost streak analysis
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # คำนวณ lost streaks
                valid_data['is_loss'] = (valid_data[result_col] == 'LOSE').astype(int)
                valid_data['streak_group'] = (valid_data['is_loss'] != valid_data['is_loss'].shift()).cumsum()
                
                # หา lost streaks
                loss_streaks = valid_data[valid_data['is_loss'] == 1].groupby('streak_group').agg({
                    'strategy': 'first',
                    'action': 'first',
                    'entry_time': ['min', 'max'],
                    'is_loss': 'count'
                }).round(2)
                
                loss_streaks.columns = ['strategy', 'action', 'start_time', 'end_time', 'streak_length']
                loss_streaks = loss_streaks[loss_streaks['streak_length'] >= 2].sort_values('streak_length', ascending=False)
                
                print(f"Lost Streaks (≥2 consecutive losses):")
                print(loss_streaks.head(10))
                
                # วิเคราะห์ strategy ที่มี lost streak มากที่สุด
                strategy_streaks = loss_streaks.groupby('strategy').agg({
                    'streak_length': ['count', 'max', 'mean']
                }).round(2)
                strategy_streaks.columns = ['streak_count', 'max_streak', 'avg_streak']
                strategy_streaks = strategy_streaks.sort_values('max_streak', ascending=False)
                
                print(f"\nStrategy Lost Streak Analysis:")
                print(strategy_streaks.head(10))
    
    def analyze_price_patterns(self):
        """วิเคราะห์ pattern ราคา"""
        print("\n" + "="*60)
        print("วิเคราะห์ PRICE PATTERNS")
        print("="*60)
        
        # วิเคราะห์การเปลี่ยนแปลงราคา
        if 'price_10min' in self.df.columns and 'entry_price' in self.df.columns:
            self.df['price_change_10min'] = ((self.df['price_10min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
            
            # วิเคราะห์ตาม price change ranges
            price_ranges = [
                (-np.inf, -0.1, "Strong Down"),
                (-0.1, -0.05, "Down"),
                (-0.05, 0.05, "Sideways"),
                (0.05, 0.1, "Up"),
                (0.1, np.inf, "Strong Up")
            ]
            
            for tf in ['10min', '30min', '60min']:
                result_col = f'result_{tf}'
                if result_col in self.df.columns:
                    print(f"\n--- {tf.upper()} PRICE PATTERN ANALYSIS ---")
                    
                    valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                    
                    if tf == '10min' and 'price_change_10min' in valid_data.columns:
                        price_col = 'price_change_10min'
                    elif tf == '30min' and 'price_30min' in valid_data.columns:
                        valid_data['price_change_30min'] = ((valid_data['price_30min'] - valid_data['entry_price']) / valid_data['entry_price'] * 100)
                        price_col = 'price_change_30min'
                    elif tf == '60min' and 'price_60min' in valid_data.columns:
                        valid_data['price_change_60min'] = ((valid_data['price_60min'] - valid_data['entry_price']) / valid_data['entry_price'] * 100)
                        price_col = 'price_change_60min'
                    else:
                        continue
                    
                    # วิเคราะห์ตาม price movement
                    for min_val, max_val, label in price_ranges:
                        range_data = valid_data[(valid_data[price_col] >= min_val) & (valid_data[price_col] < max_val)]
                        if len(range_data) > 0:
                            wins = len(range_data[range_data[result_col] == 'WIN'])
                            total = len(range_data)
                            win_rate = wins / total * 100 if total > 0 else 0
                            print(f"{label}: {win_rate:.1f}% win rate ({wins}/{total})")
    
    def analyze_time_patterns(self):
        """วิเคราะห์ pattern ตามเวลา"""
        print("\n" + "="*60)
        print("วิเคราะห์ TIME PATTERNS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} TIME PATTERN ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # วิเคราะห์ตามชั่วโมง
                hourly_performance = valid_data.groupby('hour').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                hourly_performance.columns = ['total_trades', 'wins']
                hourly_performance['win_rate'] = (hourly_performance['wins'] / hourly_performance['total_trades'] * 100).round(2)
                hourly_performance = hourly_performance.sort_values('win_rate', ascending=False)
                
                print(f"\nBest Performing Hours ({tf}):")
                best_hours = hourly_performance[hourly_performance['total_trades'] >= 10].head(5)
                for hour, row in best_hours.iterrows():
                    print(f"  {hour:02d}:00 - {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                print(f"\nWorst Performing Hours ({tf}):")
                worst_hours = hourly_performance[hourly_performance['total_trades'] >= 10].tail(5)
                for hour, row in worst_hours.iterrows():
                    print(f"  {hour:02d}:00 - {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                # วิเคราะห์ตามวันในสัปดาห์
                daily_performance = valid_data.groupby('day_of_week').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                daily_performance.columns = ['total_trades', 'wins']
                daily_performance['win_rate'] = (daily_performance['wins'] / daily_performance['total_trades'] * 100).round(2)
                daily_performance = daily_performance.sort_values('win_rate', ascending=False)
                
                print(f"\nDaily Performance ({tf}):")
                for day, row in daily_performance.iterrows():
                    print(f"  {day}: {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def find_winning_conditions(self):
        """หาเงื่อนไขที่ทำให้ชนะ"""
        print("\n" + "="*60)
        print("เงื่อนไขที่ทำให้ชนะ")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} WINNING CONDITIONS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # หา combination ที่ชนะบ่อย
                winning_combinations = valid_data[valid_data[result_col] == 'WIN'].groupby(['strategy', 'action', 'hour']).size().reset_index(name='wins')
                total_combinations = valid_data.groupby(['strategy', 'action', 'hour']).size().reset_index(name='total')
                
                combo_analysis = pd.merge(winning_combinations, total_combinations, on=['strategy', 'action', 'hour'])
                combo_analysis['win_rate'] = (combo_analysis['wins'] / combo_analysis['total'] * 100).round(2)
                combo_analysis = combo_analysis[combo_analysis['total'] >= 5].sort_values('win_rate', ascending=False)
                
                print(f"Top Winning Combinations ({tf}):")
                print(combo_analysis.head(10))
                
                # หา strategy + action ที่ชนะบ่อย
                strategy_action = valid_data.groupby(['strategy', 'action']).agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                strategy_action.columns = ['total', 'wins']
                strategy_action['win_rate'] = (strategy_action['wins'] / strategy_action['total'] * 100).round(2)
                strategy_action = strategy_action[strategy_action['total'] >= 10].sort_values('win_rate', ascending=False)
                
                print(f"\nBest Strategy+Action ({tf}):")
                print(strategy_action.head(10))
    
    def generate_recommendations(self):
        """สร้างคำแนะนำ"""
        print("\n" + "="*60)
        print("คำแนะนำสำหรับ Binary Options Trading")
        print("="*60)
        
        # วิเคราะห์ strategy ที่ดีที่สุด
        best_strategies = {}
        
        for tf in ['10min', '30min', '60min']:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                strategy_performance = valid_data.groupby('strategy').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                strategy_performance.columns = ['total', 'wins']
                strategy_performance['win_rate'] = (strategy_performance['wins'] / strategy_performance['total'] * 100).round(2)
                strategy_performance = strategy_performance[strategy_performance['total'] >= 20].sort_values('win_rate', ascending=False)
                
                best_strategies[tf] = strategy_performance.head(3)
        
        print("\nกลยุทธ์ที่แนะนำ (ตาม Win Rate):")
        for tf, strategies in best_strategies.items():
            print(f"\n{tf.upper()}:")
            for strategy, row in strategies.iterrows():
                print(f"  {strategy}: {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total']:.0f})")
        
        # วิเคราะห์ risk
        print(f"\nการวิเคราะห์ความเสี่ยง:")
        print(f"- ข้อมูลทั้งหมด: {len(self.df):,} การเทรด")
        print(f"- ระยะเวลา: {(self.df['entry_time'].max() - self.df['entry_time'].min()).days} วัน")
        print(f"- การเทรดเฉลี่ยต่อวัน: {len(self.df) / (self.df['entry_time'].max() - self.df['entry_time'].min()).days:.1f} ครั้ง")
        
        # คำนวณ potential profit
        print(f"\nการคำนวณกำไรที่คาดหวัง:")
        print(f"- ลงทุนไม้ละ: $100")
        print(f"- ชนะได้: 80-85%")
        print(f"- แพ้เสีย: 100%")
        
        for tf in ['10min', '30min', '60min']:
            if tf in best_strategies and len(best_strategies[tf]) > 0:
                best_strategy = best_strategies[tf].iloc[0]
                win_rate = best_strategy['win_rate'] / 100
                avg_trades_per_day = len(self.df) / (self.df['entry_time'].max() - self.df['entry_time'].min()).days
                
                # คำนวณกำไรต่อวัน (สมมติใช้ strategy ที่ดีที่สุด)
                daily_profit = avg_trades_per_day * win_rate * 0.825 * 100 - avg_trades_per_day * (1 - win_rate) * 100
                
                print(f"\n{tf.upper()} - {best_strategies[tf].index[0]}:")
                print(f"  Win Rate: {best_strategy['win_rate']:.1f}%")
                print(f"  การเทรดต่อวัน: {avg_trades_per_day:.1f} ครั้ง")
                print(f"  กำไรที่คาดหวังต่อวัน: ${daily_profit:.2f}")
    
    def run_full_analysis(self):
        """รันการวิเคราะห์ทั้งหมด"""
        print("Binary Options Pattern Analysis")
        print("=" * 60)
        
        self.analyze_winning_patterns()
        self.analyze_losing_streaks()
        self.analyze_price_patterns()
        self.analyze_time_patterns()
        self.find_winning_conditions()
        self.generate_recommendations()

def main():
    """ฟังก์ชันหลัก"""
    analyzer = BinaryOptionsAnalyzer('/Users/puchong/tradingview/Result Last 120HR.csv')
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
