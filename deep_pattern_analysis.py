#!/usr/bin/env python3
"""
Deep Pattern Analysis for Binary Options
วิเคราะห์ pattern ลึกๆ จากข้อมูล 120 ชั่วโมง
ตามกฎ 7 ข้อที่กำหนด
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DeepPatternAnalyzer:
    def __init__(self, csv_file):
        """เริ่มต้นการวิเคราะห์ pattern ลึกๆ"""
        self.csv_file = csv_file
        self.df = None
        self.patterns = {}
        self.signals = {}
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
    
    def analyze_pre_loss_streak_pattern(self):
        """วิเคราะห์ pattern ของ pre-loss streak (กฎข้อ 1)"""
        print("\n" + "="*60)
        print("วิเคราะห์ PRE-LOSS STREAK PATTERN (กฎข้อ 1)")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} PRE-LOSS STREAK ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # วิเคราะห์ pre-loss streak pattern
                pre_loss_patterns = {}
                
                for strategy in valid_data['strategy'].unique():
                    strategy_data = valid_data[valid_data['strategy'] == strategy].copy()
                    strategy_data = strategy_data.sort_values('entry_time')
                    
                    # คำนวณ pre-loss streak
                    strategy_data['is_loss'] = (strategy_data[result_col] == 'LOSE').astype(int)
                    strategy_data['pre_loss_streak'] = 0
                    
                    for i in range(1, len(strategy_data)):
                        if strategy_data.iloc[i-1]['is_loss'] == 1:
                            strategy_data.iloc[i, strategy_data.columns.get_loc('pre_loss_streak')] = \
                                strategy_data.iloc[i-1]['pre_loss_streak'] + 1
                        else:
                            strategy_data.iloc[i, strategy_data.columns.get_loc('pre_loss_streak')] = 0
                    
                    # วิเคราะห์ผลกระทบของ pre-loss streak
                    pre_loss_analysis = strategy_data.groupby('pre_loss_streak').agg({
                        result_col: ['count', lambda x: (x == 'WIN').sum()]
                    }).round(2)
                    pre_loss_analysis.columns = ['total_trades', 'wins']
                    pre_loss_analysis['win_rate'] = (pre_loss_analysis['wins'] / pre_loss_analysis['total_trades'] * 100).round(2)
                    
                    # เก็บเฉพาะข้อมูลที่มีการเทรดมากกว่า 5 ครั้ง
                    pre_loss_analysis = pre_loss_analysis[pre_loss_analysis['total_trades'] >= 5]
                    
                    if len(pre_loss_analysis) > 0:
                        pre_loss_patterns[strategy] = pre_loss_analysis.to_dict('index')
                
                # สรุปผลกระทบของ pre-loss streak
                print(f"\nผลกระทบของ Pre-Loss Streak ({tf}):")
                for strategy, patterns in pre_loss_patterns.items():
                    print(f"\n{strategy}:")
                    for streak, data in patterns.items():
                        print(f"  Pre-loss streak {streak}: {data['win_rate']:.1f}% win rate ({data['wins']:.0f}/{data['total_trades']:.0f})")
                
                # หา pattern ที่สำคัญ
                print(f"\nPattern ที่สำคัญ ({tf}):")
                for strategy, patterns in pre_loss_patterns.items():
                    if 0 in patterns and 1 in patterns:
                        win_rate_0 = patterns[0]['win_rate']
                        win_rate_1 = patterns[1]['win_rate']
                        if win_rate_1 < win_rate_0 - 10:  # ถ้า win rate ตกลงมากกว่า 10%
                            print(f"  {strategy}: Pre-loss streak 1 ทำให้ win rate ตกลง {win_rate_0 - win_rate_1:.1f}%")
    
    def analyze_time_of_day_pattern(self):
        """วิเคราะห์ pattern ของช่วงเวลา (กฎข้อ 2)"""
        print("\n" + "="*60)
        print("วิเคราะห์ TIME-OF-DAY PATTERN (กฎข้อ 2)")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} TIME-OF-DAY ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # วิเคราะห์ performance ตามชั่วโมง
                hourly_performance = valid_data.groupby('hour').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                hourly_performance.columns = ['total_trades', 'wins']
                hourly_performance['win_rate'] = (hourly_performance['wins'] / hourly_performance['total_trades'] * 100).round(2)
                hourly_performance = hourly_performance[hourly_performance['total_trades'] >= 10]
                
                # แบ่งเป็นโซนดี/แย่
                good_hours = hourly_performance[hourly_performance['win_rate'] >= 60].index.tolist()
                bad_hours = hourly_performance[hourly_performance['win_rate'] <= 40].index.tolist()
                neutral_hours = hourly_performance[
                    (hourly_performance['win_rate'] > 40) & 
                    (hourly_performance['win_rate'] < 60)
                ].index.tolist()
                
                print(f"\nโซนดี (Win Rate ≥ 60%): {sorted(good_hours)}")
                print(f"โซนแย่ (Win Rate ≤ 40%): {sorted(bad_hours)}")
                print(f"โซนกลาง (40% < Win Rate < 60%): {sorted(neutral_hours)}")
                
                # วิเคราะห์ pattern ตามวันในสัปดาห์
                daily_performance = valid_data.groupby('day_of_week').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                daily_performance.columns = ['total_trades', 'wins']
                daily_performance['win_rate'] = (daily_performance['wins'] / daily_performance['total_trades'] * 100).round(2)
                daily_performance = daily_performance.sort_values('win_rate', ascending=False)
                
                print(f"\nPerformance ตามวันในสัปดาห์ ({tf}):")
                for day, row in daily_performance.iterrows():
                    print(f"  {day}: {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def analyze_horizon_pattern(self):
        """วิเคราะห์ pattern ของ horizon (กฎข้อ 3)"""
        print("\n" + "="*60)
        print("วิเคราะห์ HORIZON PATTERN (กฎข้อ 3)")
        print("="*60)
        
        # เปรียบเทียบ performance ระหว่าง timeframes
        timeframe_comparison = {}
        
        for tf in ['10min', '30min', '60min']:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # คำนวณ win rate โดยรวม
                total_trades = len(valid_data)
                total_wins = len(valid_data[valid_data[result_col] == 'WIN'])
                win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
                
                # คำนวณ risk score (lost streak)
                valid_data = valid_data.sort_values('entry_time')
                valid_data['is_loss'] = (valid_data[result_col] == 'LOSE').astype(int)
                valid_data['streak_group'] = (valid_data['is_loss'] != valid_data['is_loss'].shift()).cumsum()
                
                loss_streaks = valid_data[valid_data['is_loss'] == 1].groupby('streak_group')['is_loss'].count()
                max_streak = loss_streaks.max() if len(loss_streaks) > 0 else 0
                avg_streak = loss_streaks.mean() if len(loss_streaks) > 0 else 0
                
                timeframe_comparison[tf] = {
                    'win_rate': round(win_rate, 2),
                    'total_trades': total_trades,
                    'max_streak': max_streak,
                    'avg_streak': round(avg_streak, 2)
                }
        
        print("\nเปรียบเทียบ Timeframe Performance:")
        for tf, data in timeframe_comparison.items():
            print(f"  {tf}: {data['win_rate']:.1f}% win rate, Max streak: {data['max_streak']}, Avg streak: {data['avg_streak']:.1f}")
        
        # วิเคราะห์ strategy ที่เหมาะกับแต่ละ timeframe
        print(f"\nStrategy ที่เหมาะกับแต่ละ Timeframe:")
        for tf in ['10min', '30min', '60min']:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                strategy_performance = valid_data.groupby('strategy').agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                strategy_performance.columns = ['total_trades', 'wins']
                strategy_performance['win_rate'] = (strategy_performance['wins'] / strategy_performance['total_trades'] * 100).round(2)
                strategy_performance = strategy_performance[strategy_performance['total_trades'] >= 20].sort_values('win_rate', ascending=False)
                
                print(f"\n{tf.upper()}:")
                for strategy, row in strategy_performance.head(3).iterrows():
                    print(f"  {strategy}: {row['win_rate']:.1f}% ({row['wins']:.0f}/{row['total_trades']:.0f})")
    
    def analyze_lookback_performance(self):
        """วิเคราะห์ lookback performance (กฎข้อ 4)"""
        print("\n" + "="*60)
        print("วิเคราะห์ LOOKBACK PERFORMANCE (กฎข้อ 4)")
        print("="*60)
        
        # วิเคราะห์ performance ในหน้าต่าง 12 ชั่วโมง
        window_hours = 12
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} LOOKBACK PERFORMANCE ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # สร้างหน้าต่าง 12 ชั่วโมง
                lookback_performance = []
                
                for i in range(len(valid_data)):
                    current_time = valid_data.iloc[i]['entry_time']
                    window_start = current_time - timedelta(hours=window_hours)
                    
                    # ข้อมูลในหน้าต่าง 12 ชั่วโมง
                    window_data = valid_data[
                        (valid_data['entry_time'] >= window_start) & 
                        (valid_data['entry_time'] < current_time)
                    ]
                    
                    if len(window_data) >= 5:  # ต้องมีข้อมูลอย่างน้อย 5 ครั้ง
                        # คำนวณ performance
                        total_trades = len(window_data)
                        wins = len(window_data[window_data[result_col] == 'WIN'])
                        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                        
                        # คำนวณ pnl_performance = (best + worst) / 2
                        # สมมติว่า best = win_rate, worst = 100 - win_rate
                        pnl_performance = (win_rate + (100 - win_rate)) / 2
                        
                        lookback_performance.append({
                            'current_time': current_time,
                            'strategy': valid_data.iloc[i]['strategy'],
                            'action': valid_data.iloc[i]['action'],
                            'lookback_win_rate': win_rate,
                            'pnl_performance': pnl_performance,
                            'lookback_trades': total_trades,
                            'current_result': valid_data.iloc[i][result_col]
                        })
                
                # วิเคราะห์ผลกระทบของ lookback performance
                lookback_df = pd.DataFrame(lookback_performance)
                
                if len(lookback_df) > 0:
                    # แบ่งกลุ่มตาม lookback performance
                    lookback_df['performance_group'] = pd.cut(
                        lookback_df['lookback_win_rate'], 
                        bins=[0, 40, 60, 100], 
                        labels=['Low', 'Medium', 'High']
                    )
                    
                    # วิเคราะห์ผลกระทบ
                    performance_impact = lookback_df.groupby('performance_group').agg({
                        'current_result': ['count', lambda x: (x == 'WIN').sum()]
                    }).round(2)
                    performance_impact.columns = ['total_trades', 'wins']
                    performance_impact['win_rate'] = (performance_impact['wins'] / performance_impact['total_trades'] * 100).round(2)
                    
                    print(f"\nผลกระทบของ Lookback Performance ({tf}):")
                    for group, row in performance_impact.iterrows():
                        print(f"  {group} Performance: {row['win_rate']:.1f}% win rate ({row['wins']:.0f}/{row['total_trades']:.0f})")
                    
                    # วิเคราะห์ correlation
                    correlation = lookback_df['lookback_win_rate'].corr(
                        (lookback_df['current_result'] == 'WIN').astype(int)
                    )
                    print(f"\nCorrelation ระหว่าง Lookback Performance และ Current Result: {correlation:.3f}")
    
    def analyze_max_loss_streak(self):
        """วิเคราะห์ max loss streak (กฎข้อ 5)"""
        print("\n" + "="*60)
        print("วิเคราะห์ MAX LOSS STREAK (กฎข้อ 5)")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} MAX LOSS STREAK ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                valid_data = valid_data.sort_values('entry_time')
                
                # วิเคราะห์ loss streak pattern
                loss_streak_analysis = {}
                
                for strategy in valid_data['strategy'].unique():
                    strategy_data = valid_data[valid_data['strategy'] == strategy].copy()
                    strategy_data = strategy_data.sort_values('entry_time')
                    
                    # คำนวณ loss streak
                    strategy_data['is_loss'] = (strategy_data[result_col] == 'LOSE').astype(int)
                    strategy_data['streak_group'] = (strategy_data['is_loss'] != strategy_data['is_loss'].shift()).cumsum()
                    
                    loss_streaks = strategy_data[strategy_data['is_loss'] == 1].groupby('streak_group')['is_loss'].count()
                    
                    if len(loss_streaks) > 0:
                        max_streak = loss_streaks.max()
                        avg_streak = loss_streaks.mean()
                        streak_count = len(loss_streaks)
                        
                        loss_streak_analysis[strategy] = {
                            'max_streak': max_streak,
                            'avg_streak': round(avg_streak, 2),
                            'streak_count': streak_count,
                            'total_trades': len(strategy_data)
                        }
                
                # แสดงผลการวิเคราะห์
                print(f"\nLoss Streak Analysis ({tf}):")
                for strategy, data in loss_streak_analysis.items():
                    print(f"  {strategy}: Max {data['max_streak']}, Avg {data['avg_streak']:.1f}, Count {data['streak_count']}")
                
                # หา strategy ที่เสี่ยงมาก (max streak > 3)
                risky_strategies = [s for s, d in loss_streak_analysis.items() if d['max_streak'] > 3]
                safe_strategies = [s for s, d in loss_streak_analysis.items() if d['max_streak'] <= 3]
                
                print(f"\nStrategy ที่เสี่ยงมาก (Max Streak > 3): {risky_strategies}")
                print(f"Strategy ที่ปลอดภัย (Max Streak ≤ 3): {safe_strategies}")
    
    def analyze_statistical_reliability(self):
        """วิเคราะห์ความน่าเชื่อถือของสถิติ (กฎข้อ 6)"""
        print("\n" + "="*60)
        print("วิเคราะห์ STATISTICAL RELIABILITY (กฎข้อ 6)")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} STATISTICAL RELIABILITY ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # วิเคราะห์ความน่าเชื่อถือของแต่ละ strategy
                reliability_analysis = {}
                
                for strategy in valid_data['strategy'].unique():
                    strategy_data = valid_data[valid_data['strategy'] == strategy]
                    
                    # วิเคราะห์ตาม action
                    action_analysis = strategy_data.groupby('action').agg({
                        result_col: ['count', lambda x: (x == 'WIN').sum()]
                    }).round(2)
                    action_analysis.columns = ['total_trades', 'wins']
                    action_analysis['win_rate'] = (action_analysis['wins'] / action_analysis['total_trades'] * 100).round(2)
                    
                    # ตรวจสอบว่ามีข้อมูลเพียงพอหรือไม่ (≥ 12)
                    sufficient_data = action_analysis[action_analysis['total_trades'] >= 12]
                    
                    if len(sufficient_data) > 0:
                        reliability_analysis[strategy] = {
                            'total_actions': len(sufficient_data),
                            'total_trades': sufficient_data['total_trades'].sum(),
                            'avg_win_rate': sufficient_data['win_rate'].mean(),
                            'min_win_rate': sufficient_data['win_rate'].min(),
                            'max_win_rate': sufficient_data['win_rate'].max()
                        }
                
                # แสดงผลการวิเคราะห์
                print(f"\nStatistical Reliability Analysis ({tf}):")
                for strategy, data in reliability_analysis.items():
                    print(f"  {strategy}: {data['total_actions']} actions, {data['total_trades']} trades, "
                          f"Win Rate {data['min_win_rate']:.1f}%-{data['max_win_rate']:.1f}%")
                
                # หา strategy ที่น่าเชื่อถือ
                reliable_strategies = [s for s, d in reliability_analysis.items() 
                                     if d['total_actions'] >= 2 and d['total_trades'] >= 50]
                
                print(f"\nStrategy ที่น่าเชื่อถือ (≥2 actions, ≥50 trades): {reliable_strategies}")
    
    def analyze_daily_stability(self):
        """วิเคราะห์เสถียรภาพรายวัน (กฎข้อ 7)"""
        print("\n" + "="*60)
        print("วิเคราะห์ DAILY STABILITY (กฎข้อ 7)")
        print("="*60)
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\n--- {tf.upper()} DAILY STABILITY ANALYSIS ---")
                
                valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
                
                # วิเคราะห์เสถียรภาพรายวัน
                daily_performance = valid_data.groupby(['date', 'strategy']).agg({
                    result_col: ['count', lambda x: (x == 'WIN').sum()]
                }).round(2)
                daily_performance.columns = ['total_trades', 'wins']
                daily_performance['win_rate'] = (daily_performance['wins'] / daily_performance['total_trades'] * 100).round(2)
                daily_performance = daily_performance.reset_index()
                
                # คำนวณ variance และ standard deviation
                stability_analysis = daily_performance.groupby('strategy').agg({
                    'win_rate': ['mean', 'std', 'var', 'min', 'max']
                }).round(2)
                stability_analysis.columns = ['mean_win_rate', 'std_win_rate', 'var_win_rate', 'min_win_rate', 'max_win_rate']
                stability_analysis = stability_analysis[stability_analysis['mean_win_rate'].notna()]
                
                # คำนวณ coefficient of variation (CV = std/mean)
                stability_analysis['cv'] = (stability_analysis['std_win_rate'] / stability_analysis['mean_win_rate'] * 100).round(2)
                
                # แสดงผลการวิเคราะห์
                print(f"\nDaily Stability Analysis ({tf}):")
                for strategy, row in stability_analysis.iterrows():
                    print(f"  {strategy}: Mean {row['mean_win_rate']:.1f}%, "
                          f"Std {row['std_win_rate']:.1f}%, CV {row['cv']:.1f}%")
                
                # หา strategy ที่เสถียร (CV ต่ำ)
                stable_strategies = stability_analysis[stability_analysis['cv'] <= 20].index.tolist()
                unstable_strategies = stability_analysis[stability_analysis['cv'] > 20].index.tolist()
                
                print(f"\nStrategy ที่เสถียร (CV ≤ 20%): {stable_strategies}")
                print(f"Strategy ที่ไม่เสถียร (CV > 20%): {unstable_strategies}")
    
    def run_deep_analysis(self):
        """รันการวิเคราะห์ pattern ลึกๆ ทั้งหมด"""
        print("Deep Pattern Analysis for Binary Options")
        print("=" * 60)
        
        self.analyze_pre_loss_streak_pattern()
        self.analyze_time_of_day_pattern()
        self.analyze_horizon_pattern()
        self.analyze_lookback_performance()
        self.analyze_max_loss_streak()
        self.analyze_statistical_reliability()
        self.analyze_daily_stability()
        
        print("\n" + "="*60)
        print("การวิเคราะห์เสร็จสิ้น")
        print("="*60)

def main():
    """ฟังก์ชันหลัก"""
    analyzer = DeepPatternAnalyzer('/Users/puchong/tradingview/Result Last 120HR.csv')
    analyzer.run_deep_analysis()

if __name__ == "__main__":
    main()
