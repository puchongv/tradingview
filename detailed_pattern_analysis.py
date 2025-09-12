#!/usr/bin/env python3
"""
Detailed Pattern Analysis - วิเคราะห์แบบละเอียดเหมือน agent เก่า
ใช้ข้อมูลชุดเดียวกันแต่วิเคราะห์ใหม่
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class DetailedPatternAnalyzer:
    def __init__(self, csv_file):
        """เริ่มต้นการวิเคราะห์แบบละเอียด"""
        self.csv_file = csv_file
        self.df = None
        self.patterns = {}
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
    
    def analyze_pre_loss_streak_pattern(self):
        """วิเคราะห์ Pre-Loss Streak Pattern"""
        print("\n=== PRE-LOSS STREAK PATTERN ANALYSIS ===")
        
        # เรียงข้อมูลตาม strategy และเวลา
        self.df = self.df.sort_values(['strategy', 'entry_time']).reset_index(drop=True)
        
        # คำนวณ previous result
        self.df['prev_result'] = self.df.groupby('strategy')['win_60min'].shift(1)
        self.df['prev_result_10min'] = self.df.groupby('strategy')['win_10min'].shift(1)
        self.df['prev_result_30min'] = self.df.groupby('strategy')['win_30min'].shift(1)
        
        # วิเคราะห์ win rate หลังจากแพ้
        after_loss = self.df[self.df['prev_result'] == 0].copy()
        after_win = self.df[self.df['prev_result'] == 1].copy()
        
        if len(after_loss) > 0 and len(after_win) > 0:
            # Win rate หลังจากแพ้
            loss_winrate = after_loss.groupby('strategy')['win_60min'].agg(['mean', 'count']).round(3)
            loss_winrate.columns = ['win_rate_after_loss', 'count_after_loss']
            
            # Win rate หลังจากชนะ
            win_winrate = after_win.groupby('strategy')['win_60min'].agg(['mean', 'count']).round(3)
            win_winrate.columns = ['win_rate_after_win', 'count_after_win']
            
            # รวมผลลัพธ์
            comparison = pd.merge(loss_winrate, win_winrate, left_index=True, right_index=True, how='outer')
            comparison = comparison.fillna(0)
            
            # คำนวณความแตกต่าง
            comparison['difference'] = comparison['win_rate_after_win'] - comparison['win_rate_after_loss']
            comparison = comparison[comparison['count_after_loss'] >= 5]  # Filter strategies with enough data
            
            print("Win Rate หลังจากแพ้ vs หลังจากชนะ:")
            for strategy in comparison.index:
                win_after_win = comparison.loc[strategy, 'win_rate_after_win']
                win_after_loss = comparison.loc[strategy, 'win_rate_after_loss']
                diff = comparison.loc[strategy, 'difference']
                print(f"{strategy}: หลังชนะ {win_after_win:.1%} vs หลังแพ้ {win_after_loss:.1%} (ต่าง {diff:.1%})")
            
            # หา strategies ที่มีผลกระทบมาก
            significant_impact = comparison[abs(comparison['difference']) >= 0.2]
            print(f"\nStrategies ที่มีผลกระทบมาก (≥20%): {len(significant_impact)} strategies")
            
            self.patterns['pre_loss_streak'] = comparison.to_dict('index')
        else:
            print("ข้อมูลไม่เพียงพอสำหรับการวิเคราะห์ Pre-Loss Streak")
            self.patterns['pre_loss_streak'] = {}
    
    def analyze_time_zone_pattern(self):
        """วิเคราะห์ Time Zone Pattern"""
        print("\n=== TIME ZONE PATTERN ANALYSIS ===")
        
        # วิเคราะห์ win rate ตามชั่วโมง
        hour_analysis = self.df.groupby('hour')['win_60min'].agg(['mean', 'count']).round(3)
        hour_analysis.columns = ['win_rate', 'count']
        hour_analysis = hour_analysis[hour_analysis['count'] >= 10]  # Filter hours with enough data
        
        # หาโซนดีและโซนแย่
        good_hours = hour_analysis[hour_analysis['win_rate'] >= 0.6].index.tolist()
        bad_hours = hour_analysis[hour_analysis['win_rate'] <= 0.4].index.tolist()
        
        print(f"โซนดี (≥60% win rate): {good_hours}")
        print(f"โซนแย่ (≤40% win rate): {bad_hours}")
        
        # วิเคราะห์ตามวัน
        day_analysis = self.df.groupby('day_of_week')['win_60min'].agg(['mean', 'count']).round(3)
        day_analysis.columns = ['win_rate', 'count']
        day_analysis = day_analysis[day_analysis['count'] >= 10]
        
        good_days = day_analysis[day_analysis['win_rate'] >= 0.6].index.tolist()
        bad_days = day_analysis[day_analysis['win_rate'] <= 0.4].index.tolist()
        
        print(f"วันดี (≥60% win rate): {good_days}")
        print(f"วันแย่ (≤40% win rate): {bad_days}")
        
        self.patterns['time_zone'] = {
            'good_hours': good_hours,
            'bad_hours': bad_hours,
            'good_days': good_days,
            'bad_days': bad_days,
            'hour_analysis': hour_analysis.to_dict('index'),
            'day_analysis': day_analysis.to_dict('index')
        }
    
    def analyze_winning_streak_pattern(self):
        """วิเคราะห์ Winning Streak Pattern"""
        print("\n=== WINNING STREAK PATTERN ANALYSIS ===")
        
        # คำนวณ winning streak
        self.df['winning_streak'] = 0
        for strategy in self.df['strategy'].unique():
            strategy_mask = self.df['strategy'] == strategy
            strategy_data = self.df[strategy_mask].copy()
            
            current_streak = 0
            for i, row in strategy_data.iterrows():
                if row['win_60min'] == 1:
                    current_streak += 1
                else:
                    current_streak = 0
                self.df.loc[i, 'winning_streak'] = current_streak
        
        # วิเคราะห์ win rate ตาม winning streak
        streak_analysis = self.df.groupby('winning_streak')['win_60min'].agg(['mean', 'count']).round(3)
        streak_analysis.columns = ['win_rate', 'count']
        streak_analysis = streak_analysis[streak_analysis['count'] >= 5]
        
        print("Win Rate ตาม Winning Streak:")
        for streak in streak_analysis.index:
            win_rate = streak_analysis.loc[streak, 'win_rate']
            count = streak_analysis.loc[streak, 'count']
            print(f"Streak {streak}: {win_rate:.1%} (n={count})")
        
        # หา streak ที่ดี
        good_streaks = streak_analysis[streak_analysis['win_rate'] >= 0.8].index.tolist()
        bad_streaks = streak_analysis[streak_analysis['win_rate'] <= 0.5].index.tolist()
        
        print(f"Streak ที่ดี (≥80% win rate): {good_streaks}")
        print(f"Streak ที่แย่ (≤50% win rate): {bad_streaks}")
        
        self.patterns['winning_streak'] = {
            'good_streaks': good_streaks,
            'bad_streaks': bad_streaks,
            'streak_analysis': streak_analysis.to_dict('index')
        }
    
    def analyze_strategy_rotation_pattern(self):
        """วิเคราะห์ Strategy Rotation Pattern"""
        print("\n=== STRATEGY ROTATION PATTERN ANALYSIS ===")
        
        # วิเคราะห์ win rate ตาม strategy และ timeframe
        strategy_analysis = self.df.groupby('strategy').agg({
            'win_10min': ['mean', 'count'],
            'win_30min': ['mean', 'count'],
            'win_60min': ['mean', 'count']
        }).round(3)
        
        strategy_analysis.columns = ['win_rate_10min', 'count_10min', 'win_rate_30min', 'count_30min', 'win_rate_60min', 'count_60min']
        
        print("Win Rate ตาม Strategy และ Timeframe:")
        for strategy in strategy_analysis.index:
            win_10min = strategy_analysis.loc[strategy, 'win_rate_10min']
            win_30min = strategy_analysis.loc[strategy, 'win_rate_30min']
            win_60min = strategy_analysis.loc[strategy, 'win_rate_60min']
            count_10min = strategy_analysis.loc[strategy, 'count_10min']
            count_30min = strategy_analysis.loc[strategy, 'count_30min']
            count_60min = strategy_analysis.loc[strategy, 'count_60min']
            
            print(f"{strategy}:")
            print(f"  10min: {win_10min:.1%} (n={count_10min})")
            print(f"  30min: {win_30min:.1%} (n={count_30min})")
            print(f"  60min: {win_60min:.1%} (n={count_60min})")
            print()
        
        # หา best strategies ตาม timeframe
        best_10min = strategy_analysis.nlargest(3, 'win_rate_10min')
        best_30min = strategy_analysis.nlargest(3, 'win_rate_30min')
        best_60min = strategy_analysis.nlargest(3, 'win_rate_60min')
        
        print(f"Best strategies 10min: {best_10min.index.tolist()}")
        print(f"Best strategies 30min: {best_30min.index.tolist()}")
        print(f"Best strategies 60min: {best_60min.index.tolist()}")
        
        self.patterns['strategy_rotation'] = {
            'strategy_analysis': strategy_analysis.to_dict('index'),
            'best_10min': best_10min.index.tolist(),
            'best_30min': best_30min.index.tolist(),
            'best_60min': best_60min.index.tolist()
        }
    
    def analyze_price_momentum_pattern(self):
        """วิเคราะห์ Price Momentum Pattern"""
        print("\n=== PRICE MOMENTUM PATTERN ANALYSIS ===")
        
        # คำนวณ momentum
        self.df['momentum_10min'] = np.where(self.df['price_change_10min'] > 0, 'Positive', 
                                           np.where(self.df['price_change_10min'] < 0, 'Negative', 'Neutral'))
        self.df['momentum_30min'] = np.where(self.df['price_change_30min'] > 0, 'Positive', 
                                           np.where(self.df['price_change_30min'] < 0, 'Negative', 'Neutral'))
        self.df['momentum_60min'] = np.where(self.df['price_change_60min'] > 0, 'Positive', 
                                           np.where(self.df['price_change_60min'] < 0, 'Negative', 'Neutral'))
        
        # วิเคราะห์ win rate ตาม momentum
        momentum_analysis = self.df.groupby('momentum_10min')['win_10min'].agg(['mean', 'count']).round(3)
        momentum_analysis.columns = ['win_rate', 'count']
        
        print("Win Rate ตาม Price Momentum (10min):")
        for momentum in momentum_analysis.index:
            win_rate = momentum_analysis.loc[momentum, 'win_rate']
            count = momentum_analysis.loc[momentum, 'count']
            print(f"{momentum}: {win_rate:.1%} (n={count})")
        
        # วิเคราะห์ volatility
        vol_ranges = pd.cut(self.df['volatility_10min'], bins=3, labels=['Low', 'Medium', 'High'])
        self.df['volatility_level'] = vol_ranges
        
        vol_analysis = self.df.groupby('volatility_level')['win_10min'].agg(['mean', 'count']).round(3)
        vol_analysis.columns = ['win_rate', 'count']
        
        print("\nWin Rate ตาม Volatility (10min):")
        for vol in vol_analysis.index:
            win_rate = vol_analysis.loc[vol, 'win_rate']
            count = vol_analysis.loc[vol, 'count']
            print(f"{vol} Volatility: {win_rate:.1%} (n={count})")
        
        self.patterns['price_momentum'] = {
            'momentum_analysis': momentum_analysis.to_dict('index'),
            'volatility_analysis': vol_analysis.to_dict('index')
        }
    
    def analyze_action_pattern(self):
        """วิเคราะห์ Action Pattern"""
        print("\n=== ACTION PATTERN ANALYSIS ===")
        
        # วิเคราะห์ win rate ตาม action
        action_analysis = self.df.groupby('action')['win_60min'].agg(['mean', 'count']).round(3)
        action_analysis.columns = ['win_rate', 'count']
        
        print("Win Rate ตาม Action:")
        for action in action_analysis.index:
            win_rate = action_analysis.loc[action, 'win_rate']
            count = action_analysis.loc[action, 'count']
            print(f"{action}: {win_rate:.1%} (n={count})")
        
        # วิเคราะห์ action + time
        action_time = self.df.groupby(['action', 'hour'])['win_60min'].mean().reset_index()
        action_time_pivot = action_time.pivot(index='hour', columns='action', values='win_60min')
        
        # หา best action per hour
        best_actions_per_hour = {}
        for hour in action_time_pivot.index:
            hour_data = action_time_pivot.loc[hour].dropna()
            if len(hour_data) > 0:
                best_action = hour_data.idxmax()
                best_winrate = hour_data.max()
                if best_winrate >= 0.6:  # Filter only good win rates
                    best_actions_per_hour[hour] = {'action': best_action, 'win_rate': best_winrate}
        
        print(f"\nBest Action per Hour (≥60% win rate): {len(best_actions_per_hour)} combinations")
        for hour, data in best_actions_per_hour.items():
            print(f"Hour {hour:02d}: {data['action']} ({data['win_rate']:.1%})")
        
        self.patterns['action'] = {
            'action_analysis': action_analysis.to_dict('index'),
            'best_actions_per_hour': best_actions_per_hour
        }
    
    def analyze_market_condition_pattern(self):
        """วิเคราะห์ Market Condition Pattern"""
        print("\n=== MARKET CONDITION PATTERN ANALYSIS ===")
        
        # คำนวณ market trend (ใช้ price change 60min)
        trend_ranges = pd.cut(self.df['price_change_60min'], bins=4, labels=['Strong Down', 'Down', 'Sideways', 'Strong Up'])
        self.df['market_trend'] = trend_ranges
        
        # วิเคราะห์ win rate ตาม market trend
        trend_analysis = self.df.groupby('market_trend')['win_60min'].agg(['mean', 'count']).round(3)
        trend_analysis.columns = ['win_rate', 'count']
        
        print("Win Rate ตาม Market Trend:")
        for trend in trend_analysis.index:
            win_rate = trend_analysis.loc[trend, 'win_rate']
            count = trend_analysis.loc[trend, 'count']
            print(f"{trend}: {win_rate:.1%} (n={count})")
        
        # วิเคราะห์ strategy + market condition
        strategy_trend = self.df.groupby(['strategy', 'market_trend'])['win_60min'].mean().reset_index()
        strategy_trend_pivot = strategy_trend.pivot(index='strategy', columns='market_trend', values='win_60min')
        
        # หา best strategy per market condition
        best_strategies_per_trend = {}
        for trend in strategy_trend_pivot.columns:
            trend_data = strategy_trend_pivot[trend].dropna()
            if len(trend_data) > 0:
                best_strategy = trend_data.idxmax()
                best_winrate = trend_data.max()
                if best_winrate >= 0.6:  # Filter only good win rates
                    best_strategies_per_trend[trend] = {'strategy': best_strategy, 'win_rate': best_winrate}
        
        print(f"\nBest Strategy per Market Trend (≥60% win rate): {len(best_strategies_per_trend)} combinations")
        for trend, data in best_strategies_per_trend.items():
            print(f"{trend}: {data['strategy']} ({data['win_rate']:.1%})")
        
        self.patterns['market_condition'] = {
            'trend_analysis': trend_analysis.to_dict('index'),
            'best_strategies_per_trend': best_strategies_per_trend
        }
    
    def generate_detailed_report(self):
        """สร้างรายงานแบบละเอียด"""
        print("\n" + "="*80)
        print("DETAILED PATTERN ANALYSIS REPORT")
        print("="*80)
        
        print(f"ข้อมูลที่วิเคราะห์: {len(self.df)} records")
        print(f"ช่วงเวลา: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        
        # สรุป patterns ที่สำคัญ
        print("\nPATTERNS ที่สำคัญที่สุด:")
        
        if 'time_zone' in self.patterns:
            time_patterns = self.patterns['time_zone']
            print(f"1. Time Zone Pattern:")
            print(f"   - โซนดี: {time_patterns['good_hours']}")
            print(f"   - โซนแย่: {time_patterns['bad_hours']}")
        
        if 'strategy_rotation' in self.patterns:
            strategy_patterns = self.patterns['strategy_rotation']
            print(f"2. Strategy Rotation Pattern:")
            print(f"   - Best 10min: {strategy_patterns['best_10min']}")
            print(f"   - Best 30min: {strategy_patterns['best_30min']}")
            print(f"   - Best 60min: {strategy_patterns['best_60min']}")
        
        if 'action' in self.patterns:
            action_patterns = self.patterns['action']
            print(f"3. Action Pattern:")
            print(f"   - Best actions per hour: {len(action_patterns['best_actions_per_hour'])} combinations")
        
        if 'market_condition' in self.patterns:
            market_patterns = self.patterns['market_condition']
            print(f"4. Market Condition Pattern:")
            print(f"   - Best strategies per trend: {len(market_patterns['best_strategies_per_trend'])} combinations")
        
        print("\n" + "="*80)
    
    def run_detailed_analysis(self):
        """รันการวิเคราะห์แบบละเอียด"""
        print("เริ่มต้น Detailed Pattern Analysis...")
        print("="*80)
        
        self.analyze_pre_loss_streak_pattern()
        self.analyze_time_zone_pattern()
        self.analyze_winning_streak_pattern()
        self.analyze_strategy_rotation_pattern()
        self.analyze_price_momentum_pattern()
        self.analyze_action_pattern()
        self.analyze_market_condition_pattern()
        self.generate_detailed_report()
        
        print("Detailed Pattern Analysis เสร็จสิ้น!")
        return self.patterns

if __name__ == "__main__":
    # เริ่มต้น Detailed Pattern Analyzer
    analyzer = DetailedPatternAnalyzer("Result Last 120HR.csv")
    
    # รันการวิเคราะห์แบบละเอียด
    patterns = analyzer.run_detailed_analysis()
