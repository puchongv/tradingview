#!/usr/bin/env python3
"""
Advanced Pattern Analysis for Binary Options
วิเคราะห์ pattern ในหลายๆ มุม หลายๆ สมมุติฐาน
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AdvancedPatternAnalyzer:
    def __init__(self, csv_file):
        """เริ่มต้นการวิเคราะห์ pattern ขั้นสูง"""
        self.csv_file = csv_file
        self.df = None
        self.patterns = {}
        self.hypotheses = {}
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
            self.df['minute'] = self.df['entry_time'].dt.minute
            
            # เรียงลำดับตามเวลา
            self.df = self.df.sort_values('entry_time').reset_index(drop=True)
            
            print("แปลงข้อมูลเวลาเสร็จสิ้น")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    
    def analyze_market_cycles(self):
        """วิเคราะห์ market cycles และ patterns"""
        print("\n" + "="*60)
        print("วิเคราะห์ MARKET CYCLES และ PATTERNS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} MARKET CYCLE ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # วิเคราะห์ performance ตามช่วงเวลา
                valid_data['time_period'] = valid_data['entry_time'].dt.floor('6H')
                period_performance = valid_data.groupby('time_period').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                period_performance.columns = ['total_trades', 'wins']
                period_performance['win_rate'] = (period_performance['wins'] / period_performance['total_trades'] * 100).round(2)
                
                print(f"\nPerformance ตามช่วงเวลา 6 ชั่วโมง ({tf}):")
                for period, row in period_performance.iterrows():
                    print(f"  {period.strftime('%Y-%m-%d %H:%M')}: {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                # วิเคราะห์ trend ของ performance
                period_performance['win_rate_ma'] = period_performance['win_rate'].rolling(window=3, center=True).mean()
                period_performance['trend'] = period_performance['win_rate_ma'].diff()
                
                print(f"\nTrend Analysis ({tf}):")
                for period, row in period_performance.iterrows():
                    if not pd.isna(row['trend']):
                        trend_direction = "ขึ้น" if row['trend'] > 0 else "ลง" if row['trend'] < 0 else "คงที่"
                        print(f"  {period.strftime('%Y-%m-%d %H:%M')}: {trend_direction} ({row['trend']:+.1f}%)")
    
    def analyze_strategy_rotation(self):
        """วิเคราะห์การหมุนเวียนของ strategy performance"""
        print("\n" + "="*60)
        print("วิเคราะห์ STRATEGY ROTATION")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} STRATEGY ROTATION ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # วิเคราะห์ performance ตาม strategy ในช่วงเวลา
                valid_data['time_period'] = valid_data['entry_time'].dt.floor('12H')
                
                strategy_rotation = valid_data.groupby(['time_period', 'strategy']).agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                strategy_rotation.columns = ['total_trades', 'wins']
                strategy_rotation['win_rate'] = (strategy_rotation['wins'] / strategy_rotation['total_trades'] * 100).round(2)
                strategy_rotation = strategy_rotation.reset_index()
                
                # หา strategy ที่ดีที่สุดในแต่ละช่วงเวลา
                best_strategies = strategy_rotation.loc[strategy_rotation.groupby('time_period')['win_rate'].idxmax()]
                
                print(f"\nStrategy ที่ดีที่สุดในแต่ละช่วงเวลา ({tf}):")
                for _, row in best_strategies.iterrows():
                    if row['total_trades'] >= 5:  # ต้องมีข้อมูลอย่างน้อย 5 ครั้ง
                        print(f"  {row['time_period'].strftime('%Y-%m-%d %H:%M')}: {row['strategy']} = {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                # วิเคราะห์การเปลี่ยนแปลงของ strategy performance
                strategy_changes = best_strategies['strategy'].value_counts()
                print(f"\nStrategy ที่เป็นที่ 1 บ่อยที่สุด ({tf}):")
                for strategy, count in strategy_changes.items():
                    print(f"  {strategy}: {count} ครั้ง")
    
    def analyze_price_momentum(self):
        """วิเคราะห์ price momentum และ patterns"""
        print("\n" + "="*60)
        print("วิเคราะห์ PRICE MOMENTUM และ PATTERNS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} PRICE MOMENTUM ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # วิเคราะห์ price movement patterns
                if tf == '10min' and 'price_10min' in valid_data.columns:
                    price_col = 'price_10min'
                elif tf == '30min' and 'price_30min' in valid_data.columns:
                    price_col = 'price_30min'
                elif tf == '60min' and 'price_60min' in valid_data.columns:
                    price_col = 'price_60min'
                else:
                    continue
                
                # คำนวณ price change
                valid_data['price_change'] = ((valid_data[price_col] - valid_data['entry_price']) / valid_data['entry_price'] * 100)
                
                # วิเคราะห์ price momentum
                valid_data['price_momentum'] = valid_data['price_change'].rolling(window=5, center=True).mean()
                valid_data['price_volatility'] = valid_data['price_change'].rolling(window=5, center=True).std()
                
                # แบ่งกลุ่มตาม price momentum
                valid_data['momentum_group'] = pd.cut(
                    valid_data['price_momentum'], 
                    bins=[-np.inf, -0.1, 0.1, np.inf], 
                    labels=['Negative', 'Neutral', 'Positive']
                )
                
                # วิเคราะห์ผลกระทบของ price momentum
                momentum_analysis = valid_data.groupby('momentum_group').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                momentum_analysis.columns = ['total_trades', 'wins']
                momentum_analysis['win_rate'] = (momentum_analysis['wins'] / momentum_analysis['total_trades'] * 100).round(2)
                
                print(f"\nPrice Momentum Analysis ({tf}):")
                for group, row in momentum_analysis.iterrows():
                    print(f"  {group} Momentum: {row['win_rate']:.1f}% win rate ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                # วิเคราะห์ price volatility
                valid_data['volatility_group'] = pd.cut(
                    valid_data['price_volatility'], 
                    bins=[0, 0.05, 0.1, np.inf], 
                    labels=['Low', 'Medium', 'High']
                )
                
                volatility_analysis = valid_data.groupby('volatility_group').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                volatility_analysis.columns = ['total_trades', 'wins']
                volatility_analysis['win_rate'] = (volatility_analysis['wins'] / volatility_analysis['total_trades'] * 100).round(2)
                
                print(f"\nPrice Volatility Analysis ({tf}):")
                for group, row in volatility_analysis.iterrows():
                    print(f"  {group} Volatility: {row['win_rate']:.1f}% win rate ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def analyze_action_patterns(self):
        """วิเคราะห์ action patterns และ sequences"""
        print("\n" + "="*60)
        print("วิเคราะห์ ACTION PATTERNS และ SEQUENCES")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} ACTION PATTERN ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # วิเคราะห์ action sequences
                valid_data['action_sequence'] = valid_data['action'].shift(1) + ' -> ' + valid_data['action']
                action_sequences = valid_data.groupby('action_sequence').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                action_sequences.columns = ['total_trades', 'wins']
                action_sequences['win_rate'] = (action_sequences['wins'] / action_sequences['total_trades'] * 100).round(2)
                action_sequences = action_sequences[action_sequences['total_trades'] >= 5].sort_values('win_rate', ascending=False)
                
                print(f"\nAction Sequence Analysis ({tf}):")
                for sequence, row in action_sequences.head(10).iterrows():
                    print(f"  {sequence}: {row['win_rate']:.1f}% win rate ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                # วิเคราะห์ action performance ตามเวลา
                hourly_action = valid_data.groupby(['hour', 'action']).agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                hourly_action.columns = ['total_trades', 'wins']
                hourly_action['win_rate'] = (hourly_action['wins'] / hourly_action['total_trades'] * 100).round(2)
                hourly_action = hourly_action[hourly_action['total_trades'] >= 3].reset_index()
                
                # หา action ที่ดีที่สุดในแต่ละชั่วโมง
                best_actions = hourly_action.loc[hourly_action.groupby('hour')['win_rate'].idxmax()]
                
                print(f"\nBest Action per Hour ({tf}):")
                for _, row in best_actions.iterrows():
                    print(f"  {row['hour']:02d}:00 - {row['action']}: {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def analyze_winning_streaks(self):
        """วิเคราะห์ winning streaks และ patterns"""
        print("\n" + "="*60)
        print("วิเคราะห์ WINNING STREAKS และ PATTERNS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} WINNING STREAK ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # วิเคราะห์ winning streaks
                valid_data['is_win'] = (valid_data[result_col] == 'WIN').astype(int)
                valid_data['streak_group'] = (valid_data['is_win'] != valid_data['is_win'].shift()).cumsum()
                
                winning_streaks = valid_data[valid_data['is_win'] == 1].groupby('streak_group').agg({
                    'strategy': 'first',
                    'action': 'first',
                    'entry_time': ['min', 'max'],
                    'is_win': 'count'
                }).round(2)
                winning_streaks.columns = ['strategy', 'action', 'start_time', 'end_time', 'streak_length']
                winning_streaks = winning_streaks[winning_streaks['streak_length'] >= 3].sort_values('streak_length', ascending=False)
                
                print(f"\nWinning Streaks (≥3 consecutive wins) ({tf}):")
                for _, row in winning_streaks.head(10).iterrows():
                    print(f"  {row['strategy']} + {row['action']}: {row['streak_length']} wins "
                          f"({row['start_time'].strftime('%m-%d %H:%M')} - {row['end_time'].strftime('%m-%d %H:%M')})")
                
                # วิเคราะห์ pattern หลัง winning streak
                valid_data['winning_streak'] = 0
                for i in range(1, len(valid_data)):
                    if valid_data.iloc[i-1]['is_win'] == 1:
                        valid_data.iloc[i, valid_data.columns.get_loc('winning_streak')] = \
                            valid_data.iloc[i-1]['winning_streak'] + 1
                    else:
                        valid_data.iloc[i, valid_data.columns.get_loc('winning_streak')] = 0
                
                # วิเคราะห์ผลกระทบของ winning streak
                streak_analysis = valid_data.groupby('winning_streak').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                streak_analysis.columns = ['total_trades', 'wins']
                streak_analysis['win_rate'] = (streak_analysis['wins'] / streak_analysis['total_trades'] * 100).round(2)
                streak_analysis = streak_analysis[streak_analysis['total_trades'] >= 5]
                
                print(f"\nWinning Streak Impact Analysis ({tf}):")
                for streak, row in streak_analysis.iterrows():
                    print(f"  After {streak} wins: {row['win_rate']:.1f}% win rate ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def analyze_market_conditions(self):
        """วิเคราะห์ market conditions และ patterns"""
        print("\n" + "="*60)
        print("วิเคราะห์ MARKET CONDITIONS และ PATTERNS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} MARKET CONDITION ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # วิเคราะห์ market condition ตาม price movement
                if tf == '10min' and 'price_10min' in valid_data.columns:
                    price_col = 'price_10min'
                elif tf == '30min' and 'price_30min' in valid_data.columns:
                    price_col = 'price_30min'
                elif tf == '60min' and 'price_60min' in valid_data.columns:
                    price_col = 'price_60min'
                else:
                    continue
                
                # คำนวณ price change
                valid_data['price_change'] = ((valid_data[price_col] - valid_data['entry_price']) / valid_data['entry_price'] * 100)
                
                # วิเคราะห์ market condition
                valid_data['market_condition'] = pd.cut(
                    valid_data['price_change'], 
                    bins=[-np.inf, -0.2, -0.05, 0.05, 0.2, np.inf], 
                    labels=['Strong Down', 'Down', 'Sideways', 'Up', 'Strong Up']
                )
                
                # วิเคราะห์ performance ตาม market condition
                condition_analysis = valid_data.groupby('market_condition').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                condition_analysis.columns = ['total_trades', 'wins']
                condition_analysis['win_rate'] = (condition_analysis['wins'] / condition_analysis['total_trades'] * 100).round(2)
                
                print(f"\nMarket Condition Analysis ({tf}):")
                for condition, row in condition_analysis.iterrows():
                    print(f"  {condition}: {row['win_rate']:.1f}% win rate ({row['wins']:.0f}/{row['total_trades']:.0f})")
                
                # วิเคราะห์ strategy performance ตาม market condition
                strategy_condition = valid_data.groupby(['strategy', 'market_condition']).agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                strategy_condition.columns = ['total_trades', 'wins']
                strategy_condition['win_rate'] = (strategy_condition['wins'] / strategy_condition['total_trades'] * 100).round(2)
                strategy_condition = strategy_condition[strategy_condition['total_trades'] >= 5].reset_index()
                
                # หา strategy ที่ดีที่สุดในแต่ละ market condition
                best_strategies = strategy_condition.loc[strategy_condition.groupby('market_condition')['win_rate'].idxmax()]
                
                print(f"\nBest Strategy per Market Condition ({tf}):")
                for _, row in best_strategies.iterrows():
                    print(f"  {row['market_condition']}: {row['strategy']} = {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def analyze_correlation_patterns(self):
        """วิเคราะห์ correlation patterns ระหว่างตัวแปรต่างๆ"""
        print("\n" + "="*60)
        print("วิเคราะห์ CORRELATION PATTERNS")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} CORRELATION ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # สร้างตัวแปรสำหรับ correlation analysis
                valid_data['is_win'] = (valid_data[result_col] == 'WIN').astype(int)
                valid_data['hour_sin'] = np.sin(2 * np.pi * valid_data['hour'] / 24)
                valid_data['hour_cos'] = np.cos(2 * np.pi * valid_data['hour'] / 24)
                valid_data['day_of_week_num'] = valid_data['day_of_week'].map({
                    'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 
                    'Friday': 5, 'Saturday': 6, 'Sunday': 7
                })
                
                # วิเคราะห์ correlation
                correlation_vars = ['hour', 'hour_sin', 'hour_cos', 'day_of_week_num', 'is_win']
                correlation_matrix = valid_data[correlation_vars].corr()
                
                print(f"\nCorrelation Matrix ({tf}):")
                print(correlation_matrix.round(3))
                
                # วิเคราะห์ correlation กับ win rate
                win_correlations = correlation_matrix['is_win'].drop('is_win').sort_values(key=abs, ascending=False)
                print(f"\nCorrelation with Win Rate ({tf}):")
                for var, corr in win_correlations.items():
                    print(f"  {var}: {corr:.3f}")
    
    def run_advanced_analysis(self):
        """รันการวิเคราะห์ขั้นสูงทั้งหมด"""
        print("Advanced Pattern Analysis for Binary Options")
        print("=" * 60)
        
        self.analyze_market_cycles()
        self.analyze_strategy_rotation()
        self.analyze_price_momentum()
        self.analyze_action_patterns()
        self.analyze_winning_streaks()
        self.analyze_market_conditions()
        self.analyze_correlation_patterns()
        
        print("\n" + "="*60)
        print("การวิเคราะห์ขั้นสูงเสร็จสิ้น")
        print("="*60)

def main():
    """ฟังก์ชันหลัก"""
    analyzer = AdvancedPatternAnalyzer('/Users/puchong/tradingview/Result Last 120HR.csv')
    analyzer.run_advanced_analysis()

if __name__ == "__main__":
    main()
