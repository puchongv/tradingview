#!/usr/bin/env python3
"""
Trading Data Analysis Tool
วิเคราะห์ข้อมูลการเทรดจาก CSV file
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ตั้งค่า matplotlib สำหรับแสดงผลภาษาไทย
plt.rcParams['font.family'] = ['Tahoma', 'DejaVu Sans', 'Liberation Sans']

class TradingAnalyzer:
    def __init__(self, csv_file):
        """เริ่มต้นการวิเคราะห์ข้อมูล"""
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
            
            print("แปลงข้อมูลเวลาเสร็จสิ้น")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    
    def basic_statistics(self):
        """สถิติพื้นฐาน"""
        print("\n" + "="*50)
        print("สถิติพื้นฐาน")
        print("="*50)
        
        print(f"จำนวนการเทรดทั้งหมด: {len(self.df):,}")
        print(f"วันที่เริ่มต้น: {self.df['entry_time'].min()}")
        print(f"วันที่สิ้นสุด: {self.df['entry_time'].max()}")
        print(f"ระยะเวลา: {(self.df['entry_time'].max() - self.df['entry_time'].min()).days} วัน")
        
        # สถิติการเทรด
        buy_trades = self.df[self.df['action'] == 'Buy']
        sell_trades = self.df[self.df['action'] == 'Sell']
        
        print(f"\nการเทรด Buy: {len(buy_trades):,} ({len(buy_trades)/len(self.df)*100:.1f}%)")
        print(f"การเทรด Sell: {len(sell_trades):,} ({len(sell_trades)/len(self.df)*100:.1f}%)")
        
        # กลยุทธ์ที่ใช้
        strategies = self.df['strategy'].value_counts()
        print(f"\nกลยุทธ์ที่ใช้ (Top 10):")
        for strategy, count in strategies.head(10).items():
            print(f"  {strategy}: {count:,} ({count/len(self.df)*100:.1f}%)")
    
    def win_loss_analysis(self):
        """วิเคราะห์ผลการเทรด"""
        print("\n" + "="*50)
        print("วิเคราะห์ผลการเทรด")
        print("="*50)
        
        # วิเคราะห์แต่ละ timeframe
        timeframes = ['10min', '30min', '60min', '1day']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                # กรองข้อมูลที่มีผลลัพธ์
                valid_results = self.df[self.df[result_col].notna() & (self.df[result_col] != '')]
                
                if len(valid_results) > 0:
                    wins = len(valid_results[valid_results[result_col] == 'WIN'])
                    losses = len(valid_results[valid_results[result_col] == 'LOSE'])
                    total = wins + losses
                    
                    if total > 0:
                        win_rate = wins / total * 100
                        print(f"\n{tf.upper()}:")
                        print(f"  ชนะ: {wins:,} ({win_rate:.1f}%)")
                        print(f"  แพ้: {losses:,} ({100-win_rate:.1f}%)")
                        print(f"  รวม: {total:,}")
    
    def strategy_performance(self):
        """ประสิทธิภาพของแต่ละกลยุทธ์"""
        print("\n" + "="*50)
        print("ประสิทธิภาพกลยุทธ์")
        print("="*50)
        
        # วิเคราะห์กลยุทธ์ที่ใช้บ่อย
        top_strategies = self.df['strategy'].value_counts().head(10)
        
        for strategy in top_strategies.index:
            strategy_data = self.df[self.df['strategy'] == strategy]
            
            print(f"\n{strategy} ({len(strategy_data):,} การเทรด):")
            
            # วิเคราะห์ผลลัพธ์ 30min (ถ้ามี)
            if 'result_30min' in strategy_data.columns:
                valid_30min = strategy_data[strategy_data['result_30min'].notna() & (strategy_data['result_30min'] != '')]
                if len(valid_30min) > 0:
                    wins_30 = len(valid_30min[valid_30min['result_30min'] == 'WIN'])
                    total_30 = len(valid_30min)
                    win_rate_30 = wins_30 / total_30 * 100 if total_30 > 0 else 0
                    print(f"  30min Win Rate: {win_rate_30:.1f}% ({wins_30}/{total_30})")
            
            # วิเคราะห์ผลลัพธ์ 60min (ถ้ามี)
            if 'result_60min' in strategy_data.columns:
                valid_60min = strategy_data[strategy_data['result_60min'].notna() & (strategy_data['result_60min'] != '')]
                if len(valid_60min) > 0:
                    wins_60 = len(valid_60min[valid_60min['result_60min'] == 'WIN'])
                    total_60 = len(valid_60min)
                    win_rate_60 = wins_60 / total_60 * 100 if total_60 > 0 else 0
                    print(f"  60min Win Rate: {win_rate_60:.1f}% ({wins_60}/{total_60})")
    
    def price_analysis(self):
        """วิเคราะห์ราคา"""
        print("\n" + "="*50)
        print("วิเคราะห์ราคา")
        print("="*50)
        
        # ราคาเข้าเฉลี่ย
        avg_entry_price = self.df['entry_price'].mean()
        print(f"ราคาเข้าเฉลี่ย: ${avg_entry_price:,.2f}")
        
        # ราคาสูงสุด-ต่ำสุด
        print(f"ราคาเข้าสูงสุด: ${self.df['entry_price'].max():,.2f}")
        print(f"ราคาเข้าต่ำสุด: ${self.df['entry_price'].min():,.2f}")
        
        # วิเคราะห์การเปลี่ยนแปลงราคา
        if 'price_10min' in self.df.columns and 'entry_price' in self.df.columns:
            self.df['price_change_10min'] = ((self.df['price_10min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
            avg_change_10min = self.df['price_change_10min'].mean()
            print(f"การเปลี่ยนแปลงราคาเฉลี่ย 10min: {avg_change_10min:.3f}%")
    
    def time_analysis(self):
        """วิเคราะห์ตามเวลา"""
        print("\n" + "="*50)
        print("วิเคราะห์ตามเวลา")
        print("="*50)
        
        # แยกชั่วโมง
        self.df['hour'] = self.df['entry_time'].dt.hour
        
        # การเทรดในแต่ละชั่วโมง
        hourly_trades = self.df['hour'].value_counts().sort_index()
        print("\nการเทรดในแต่ละชั่วโมง:")
        for hour, count in hourly_trades.items():
            print(f"  {hour:02d}:00 - {count:,} การเทรด")
        
        # ชั่วโมงที่มีการเทรดมากที่สุด
        peak_hour = hourly_trades.idxmax()
        print(f"\nชั่วโมงที่มีการเทรดมากที่สุด: {peak_hour:02d}:00 ({hourly_trades[peak_hour]:,} การเทรด)")
    
    def generate_report(self):
        """สร้างรายงานสรุป"""
        print("\n" + "="*50)
        print("รายงานสรุป")
        print("="*50)
        
        self.basic_statistics()
        self.win_loss_analysis()
        self.strategy_performance()
        self.price_analysis()
        self.time_analysis()
    
    def create_visualizations(self):
        """สร้างกราฟ"""
        print("\nกำลังสร้างกราฟ...")
        
        # ตั้งค่า subplot
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Trading Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. การเทรดตามเวลา
        hourly_trades = self.df['hour'].value_counts().sort_index()
        axes[0, 0].bar(hourly_trades.index, hourly_trades.values, color='skyblue', alpha=0.7)
        axes[0, 0].set_title('การเทรดในแต่ละชั่วโมง')
        axes[0, 0].set_xlabel('ชั่วโมง')
        axes[0, 0].set_ylabel('จำนวนการเทรด')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. กลยุทธ์ที่ใช้บ่อย
        top_strategies = self.df['strategy'].value_counts().head(8)
        axes[0, 1].pie(top_strategies.values, labels=top_strategies.index, autopct='%1.1f%%')
        axes[0, 1].set_title('กลยุทธ์ที่ใช้บ่อย (Top 8)')
        
        # 3. Buy vs Sell
        action_counts = self.df['action'].value_counts()
        axes[1, 0].bar(action_counts.index, action_counts.values, color=['green', 'red'], alpha=0.7)
        axes[1, 0].set_title('Buy vs Sell')
        axes[1, 0].set_ylabel('จำนวนการเทรด')
        
        # 4. ราคาเข้า
        axes[1, 1].hist(self.df['entry_price'], bins=50, color='orange', alpha=0.7)
        axes[1, 1].set_title('การกระจายของราคาเข้า')
        axes[1, 1].set_xlabel('ราคาเข้า (USD)')
        axes[1, 1].set_ylabel('ความถี่')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/Users/puchong/tradingview/trading_analysis.png', dpi=300, bbox_inches='tight')
        print("บันทึกกราฟเป็น trading_analysis.png")
        
        return fig

def main():
    """ฟังก์ชันหลัก"""
    print("Trading Data Analysis Tool")
    print("=" * 50)
    
    # เริ่มต้นการวิเคราะห์
    analyzer = TradingAnalyzer('/Users/puchong/tradingview/Result Last 120HR.csv')
    
    # สร้างรายงาน
    analyzer.generate_report()
    
    # สร้างกราฟ
    try:
        analyzer.create_visualizations()
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการสร้างกราฟ: {e}")
    
    print("\nการวิเคราะห์เสร็จสิ้น!")

if __name__ == "__main__":
    main()
