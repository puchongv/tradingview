#!/usr/bin/env python3
"""
ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลัง
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def verify_12hour_data():
    """ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลัง"""
    
    # โหลดข้อมูล
    df = pd.read_csv('/Users/puchong/tradingview/Result Last 120HR.csv')
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df = df.sort_values('entry_time').reset_index(drop=True)
    
    print("ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลัง")
    print("=" * 50)
    
    # ตรวจสอบข้อมูลทั้งหมด
    print(f"ข้อมูลทั้งหมด: {len(df)} รายการ")
    print(f"วันที่เริ่มต้น: {df['entry_time'].min()}")
    print(f"วันที่สิ้นสุด: {df['entry_time'].max()}")
    print(f"ระยะเวลา: {(df['entry_time'].max() - df['entry_time'].min()).days} วัน")
    
    # ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลัง
    timeframes = ['10min', '30min', '60min']
    
    for tf in timeframes:
        result_col = f'result_{tf}'
        if result_col in df.columns:
            print(f"\n--- {tf.upper()} 12-HOUR DATA VERIFICATION ---")
            
            valid_data = df[df[result_col].notna() & (df[result_col] != '')].copy()
            valid_data = valid_data.sort_values('entry_time')
            
            # ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลัง
            lookback_data = []
            
            for i in range(len(valid_data)):
                current_time = valid_data.iloc[i]['entry_time']
                window_start = current_time - timedelta(hours=12)
                
                # ข้อมูลในหน้าต่าง 12 ชั่วโมง
                window_data = valid_data[
                    (valid_data['entry_time'] >= window_start) & 
                    (valid_data['entry_time'] < current_time)
                ]
                
                lookback_data.append({
                    'current_time': current_time,
                    'lookback_count': len(window_data),
                    'has_12hour_data': len(window_data) >= 5
                })
            
            lookback_df = pd.DataFrame(lookback_data)
            
            # สถิติข้อมูล 12 ชั่วโมงย้อนหลัง
            total_trades = len(lookback_df)
            has_12hour_data = len(lookback_df[lookback_df['has_12hour_data'] == True])
            no_12hour_data = len(lookback_df[lookback_df['has_12hour_data'] == False])
            
            print(f"การเทรดทั้งหมด: {total_trades}")
            print(f"มีข้อมูล 12 ชั่วโมงย้อนหลัง: {has_12hour_data} ({has_12hour_data/total_trades*100:.1f}%)")
            print(f"ไม่มีข้อมูล 12 ชั่วโมงย้อนหลัง: {no_12hour_data} ({no_12hour_data/total_trades*100:.1f}%)")
            
            # ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลังเฉลี่ย
            avg_lookback = lookback_df['lookback_count'].mean()
            print(f"ข้อมูล 12 ชั่วโมงย้อนหลังเฉลี่ย: {avg_lookback:.1f} รายการ")
            
            # ตรวจสอบช่วงเวลาที่ไม่มีข้อมูล 12 ชั่วโมงย้อนหลัง
            no_data_periods = lookback_df[lookback_df['has_12hour_data'] == False]
            if len(no_data_periods) > 0:
                print(f"\nช่วงเวลาที่ไม่มีข้อมูล 12 ชั่วโมงย้อนหลัง:")
                for _, row in no_data_periods.head(10).iterrows():
                    print(f"  {row['current_time'].strftime('%Y-%m-%d %H:%M:%S')}: {row['lookback_count']} รายการ")
            
            # ตรวจสอบข้อมูล 12 ชั่วโมงย้อนหลังตามเวลา
            lookback_df['hour'] = lookback_df['current_time'].dt.hour
            hourly_lookback = lookback_df.groupby('hour').agg({
                'lookback_count': ['mean', 'min', 'max'],
                'has_12hour_data': 'sum'
            }).round(2)
            hourly_lookback.columns = ['avg_lookback', 'min_lookback', 'max_lookback', 'has_12hour_data']
            
            print(f"\nข้อมูล 12 ชั่วโมงย้อนหลังตามชั่วโมง:")
            for hour, row in hourly_lookback.iterrows():
                print(f"  {hour:02d}:00 - เฉลี่ย: {row['avg_lookback']:.1f}, "
                      f"ต่ำสุด: {row['min_lookback']:.0f}, สูงสุด: {row['max_lookback']:.0f}, "
                      f"มีข้อมูล: {row['has_12hour_data']:.0f}")

if __name__ == "__main__":
    verify_12hour_data()
