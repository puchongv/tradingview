import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta
import json

# ตั้งค่า style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# อ่านข้อมูลจาก metabase_data.json
with open('/Users/puchong/tradingview/metabase_data.json', 'r') as f:
    data = json.load(f)

# สร้างข้อมูล dummy สำหรับแสดงตัวอย่าง
def create_dummy_data():
    # Strategy Performance Data
    strategies = ['MWP-20', 'MWP-25', 'MWP-27', 'MWP-30', 'Range FRAMA3', 'Range FRAMA3-99', 'Range Filter5', 'UT-BOT2-10']
    actions = ['Buy', 'Sell', 'FlowTrend Bullish + Buy', 'FlowTrend Bearish + Sell+']
    
    # สร้างข้อมูล performance
    performance_data = []
    for strategy in strategies:
        for action in actions[:2]:  # ใช้แค่ Buy, Sell
            win_rate_10min = np.random.uniform(45, 75)
            win_rate_30min = win_rate_10min + np.random.uniform(-10, 5)
            total_trades = np.random.randint(50, 400)
            
            performance_data.append({
                'strategy': strategy,
                'action': action,
                'total_trades': total_trades,
                'win_rate_10min': round(win_rate_10min, 2),
                'win_rate_30min': round(win_rate_30min, 2),
                'avg_pnl': round(np.random.uniform(-50, 100), 2)
            })
    
    return pd.DataFrame(performance_data)

# สร้างข้อมูล time pattern
def create_time_pattern_data():
    hours = list(range(24))
    win_rates = []
    
    for hour in hours:
        # สร้าง pattern ที่สมจริง
        if hour in [0, 8, 11, 16, 22]:  # ชั่วโมงที่ดี
            base_rate = np.random.uniform(60, 80)
        elif hour in [3, 12, 17, 19]:  # ชั่วโมงที่แย่
            base_rate = np.random.uniform(30, 50)
        else:  # ชั่วโมงปกติ
            base_rate = np.random.uniform(45, 65)
        
        win_rates.append(round(base_rate, 2))
    
    return pd.DataFrame({
        'hour': hours,
        'win_rate_10min': win_rates,
        'total_trades': [np.random.randint(20, 100) for _ in range(24)]
    })

# สร้างข้อมูล heatmap
def create_heatmap_data():
    strategies = ['MWP-20', 'MWP-25', 'MWP-27', 'MWP-30', 'Range FRAMA3']
    hours = list(range(24))
    
    heatmap_data = []
    for strategy in strategies:
        for hour in hours:
            # สร้าง pattern ที่แตกต่างกันตาม strategy
            if strategy == 'Range FRAMA3':
                base_rate = np.random.uniform(55, 75)
            elif strategy == 'MWP-20':
                base_rate = np.random.uniform(50, 70)
            else:
                base_rate = np.random.uniform(45, 65)
            
            heatmap_data.append({
                'strategy': strategy,
                'hour': hour,
                'win_rate': round(base_rate, 2)
            })
    
    return pd.DataFrame(heatmap_data)

# 1. Strategy Performance Bar Chart
def create_strategy_performance_chart():
    df = create_dummy_data()
    
    # กรองข้อมูลเฉพาะ Buy action และรวมทุก strategy
    buy_data = df[df['action'] == 'Buy'].groupby('strategy')['win_rate_10min'].mean().reset_index()
    buy_data = buy_data.sort_values('win_rate_10min', ascending=True)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(buy_data['strategy'], buy_data['win_rate_10min'], 
                   color=plt.cm.viridis(np.linspace(0, 1, len(buy_data))))
    
    # เพิ่มค่า win rate บน bar
    for i, (idx, row) in enumerate(buy_data.iterrows()):
        ax.text(row['win_rate_10min'] + 1, i, f"{row['win_rate_10min']:.1f}%", 
                va='center', fontweight='bold')
    
    ax.set_xlabel('Win Rate (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Strategy', fontsize=12, fontweight='bold')
    ax.set_title('Strategy Performance - Win Rate (10min)', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # เพิ่มเส้น 50% win rate
    ax.axvline(x=50, color='red', linestyle='--', alpha=0.7, label='50% Win Rate')
    ax.legend()
    
    plt.tight_layout()
    return fig

# 2. Time Pattern Line Chart
def create_time_pattern_chart():
    df = create_time_pattern_data()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # สร้างเส้น win rate
    ax.plot(df['hour'], df['win_rate_10min'], marker='o', linewidth=3, 
            markersize=8, color='#2E86AB', label='Win Rate 10min')
    
    # สร้าง bar chart สำหรับ total trades (secondary y-axis)
    ax2 = ax.twinx()
    bars = ax2.bar(df['hour'], df['total_trades'], alpha=0.3, color='#A23B72', 
                   label='Total Trades')
    
    # ตั้งค่า axes
    ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
    ax.set_ylabel('Win Rate (%)', fontsize=12, fontweight='bold', color='#2E86AB')
    ax2.set_ylabel('Total Trades', fontsize=12, fontweight='bold', color='#A23B72')
    ax.set_title('Trading Performance by Hour', fontsize=14, fontweight='bold')
    
    # ตั้งค่า x-axis
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlim(-0.5, 23.5)
    
    # เพิ่มเส้น 50% win rate
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% Win Rate')
    
    # สี highlight ชั่วโมงที่ดี
    for hour in [0, 8, 11, 16, 22]:
        ax.axvspan(hour-0.4, hour+0.4, alpha=0.2, color='green', label='Best Hours' if hour == 0 else "")
    
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# 3. Strategy + Time Heatmap
def create_strategy_time_heatmap():
    df = create_heatmap_data()
    
    # สร้าง pivot table
    pivot_df = df.pivot(index='strategy', columns='hour', values='win_rate')
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # สร้าง heatmap
    sns.heatmap(pivot_df, annot=True, fmt='.1f', cmap='RdYlGn', 
                center=50, vmin=30, vmax=80, ax=ax,
                cbar_kws={'label': 'Win Rate (%)'})
    
    ax.set_title('Strategy Performance by Hour (Heatmap)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
    ax.set_ylabel('Strategy', fontsize=12, fontweight='bold')
    
    # ตั้งค่า x-axis labels
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels(range(0, 24, 2))
    
    plt.tight_layout()
    return fig

# 4. Risk Assessment Table
def create_risk_assessment_table():
    strategies = ['MWP-20', 'MWP-25', 'MWP-27', 'MWP-30', 'Range FRAMA3', 'Range FRAMA3-99', 'Range Filter5', 'UT-BOT2-10']
    
    risk_data = []
    for strategy in strategies:
        win_rate = np.random.uniform(45, 70)
        max_losses = np.random.randint(2, 8)
        
        if max_losses <= 3:
            risk_level = 'Low Risk'
            risk_color = 'green'
        elif max_losses <= 5:
            risk_level = 'Medium Risk'
            risk_color = 'orange'
        else:
            risk_level = 'High Risk'
            risk_color = 'red'
        
        risk_data.append({
            'Strategy': strategy,
            'Win Rate (%)': f"{win_rate:.1f}",
            'Max Consecutive Losses': max_losses,
            'Risk Level': risk_level,
            'Risk Color': risk_color
        })
    
    return pd.DataFrame(risk_data)

# 5. Recent Performance Line Chart
def create_recent_performance_chart():
    # สร้างข้อมูล 7 วันล่าสุด
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    strategies = ['MWP-20', 'MWP-25', 'Range FRAMA3']
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    
    for i, strategy in enumerate(strategies):
        # สร้างข้อมูล performance แบบสุ่ม
        win_rates = [np.random.uniform(40, 80) for _ in range(7)]
        
        ax.plot(dates, win_rates, marker='o', linewidth=3, 
                markersize=8, color=colors[i], label=strategy)
    
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Win Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Recent Performance (Last 7 Days)', fontsize=14, fontweight='bold')
    
    # หมุน x-axis labels
    plt.xticks(rotation=45)
    
    # เพิ่มเส้น 50% win rate
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% Win Rate')
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# 6. Best Combinations Table
def create_best_combinations_table():
    combinations = [
        {'Strategy': 'Range FRAMA3', 'Action': 'Buy', 'Hour': 16, 'Win Rate': 75.3, 'Trades': 15},
        {'Strategy': 'MWP-20', 'Action': 'Sell', 'Hour': 11, 'Win Rate': 73.4, 'Trades': 12},
        {'Strategy': 'MWP-25', 'Action': 'Buy', 'Hour': 8, 'Win Rate': 69.2, 'Trades': 8},
        {'Strategy': 'Range FRAMA3-99', 'Action': 'Sell', 'Hour': 22, 'Win Rate': 68.5, 'Trades': 10},
        {'Strategy': 'UT-BOT2-10', 'Action': 'Buy', 'Hour': 14, 'Win Rate': 66.7, 'Trades': 9},
        {'Strategy': 'MWP-27', 'Action': 'Sell', 'Hour': 9, 'Win Rate': 65.2, 'Trades': 7},
        {'Strategy': 'Range Filter5', 'Action': 'Buy', 'Hour': 15, 'Win Rate': 63.8, 'Trades': 6},
        {'Strategy': 'MWP-30', 'Action': 'Sell', 'Hour': 13, 'Win Rate': 62.1, 'Trades': 5}
    ]
    
    return pd.DataFrame(combinations)

# สร้างและแสดง charts ทั้งหมด
def create_all_charts():
    print("Creating dummy charts for Metabase Dashboard example...")
    
    # 1. Strategy Performance Bar Chart
    fig1 = create_strategy_performance_chart()
    fig1.savefig('/Users/puchong/tradingview/strategy_performance_chart.png', dpi=300, bbox_inches='tight')
    print("✓ Strategy Performance Chart saved")
    
    # 2. Time Pattern Line Chart
    fig2 = create_time_pattern_chart()
    fig2.savefig('/Users/puchong/tradingview/time_pattern_chart.png', dpi=300, bbox_inches='tight')
    print("✓ Time Pattern Chart saved")
    
    # 3. Strategy + Time Heatmap
    fig3 = create_strategy_time_heatmap()
    fig3.savefig('/Users/puchong/tradingview/strategy_time_heatmap.png', dpi=300, bbox_inches='tight')
    print("✓ Strategy + Time Heatmap saved")
    
    # 4. Recent Performance Line Chart
    fig4 = create_recent_performance_chart()
    fig4.savefig('/Users/puchong/tradingview/recent_performance_chart.png', dpi=300, bbox_inches='tight')
    print("✓ Recent Performance Chart saved")
    
    # 5. สร้าง tables
    risk_table = create_risk_assessment_table()
    risk_table.to_csv('/Users/puchong/tradingview/risk_assessment_table.csv', index=False)
    print("✓ Risk Assessment Table saved")
    
    best_combinations = create_best_combinations_table()
    best_combinations.to_csv('/Users/puchong/tradingview/best_combinations_table.csv', index=False)
    print("✓ Best Combinations Table saved")
    
    # แสดงตัวอย่าง tables
    print("\n" + "="*50)
    print("RISK ASSESSMENT TABLE")
    print("="*50)
    print(risk_table.to_string(index=False))
    
    print("\n" + "="*50)
    print("BEST COMBINATIONS TABLE")
    print("="*50)
    print(best_combinations.to_string(index=False))
    
    return fig1, fig2, fig3, fig4

if __name__ == "__main__":
    # สร้าง charts ทั้งหมด
    charts = create_all_charts()
    
    # แสดง charts
    plt.show()
