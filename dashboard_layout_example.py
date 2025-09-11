import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np

def create_dashboard_layout_example():
    """สร้างตัวอย่าง Dashboard Layout สำหรับ Metabase"""
    
    # สร้าง figure ใหญ่
    fig, ax = plt.subplots(figsize=(20, 12))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # กำหนดสี
    colors = {
        'table': '#E8F4FD',
        'bar_chart': '#B8E6B8', 
        'line_chart': '#FFE4B5',
        'heatmap': '#FFB6C1',
        'number': '#DDA0DD',
        'border': '#2C3E50'
    }
    
    # กำหนดขนาดและตำแหน่งของ charts
    chart_configs = [
        # แถวที่ 1 (บนสุด)
        {'name': 'Strategy Performance\n(Table)', 'pos': (0.5, 9.5), 'size': (6, 2.5), 'type': 'table', 'color': colors['table']},
        {'name': 'Win Rate by Strategy\n(Bar Chart)', 'pos': (7, 9.5), 'size': (6, 2.5), 'type': 'bar_chart', 'color': colors['bar_chart']},
        {'name': 'Total Trades Today\n(Number)', 'pos': (13.5, 9.5), 'size': (6, 2.5), 'type': 'number', 'color': colors['number']},
        
        # แถวที่ 2 (กลางบน)
        {'name': 'Time Pattern Analysis\n(Line Chart)', 'pos': (0.5, 6.5), 'size': (6, 2.5), 'type': 'line_chart', 'color': colors['line_chart']},
        {'name': 'Risk Assessment\n(Table)', 'pos': (7, 6.5), 'size': (6, 2.5), 'type': 'table', 'color': colors['table']},
        {'name': 'Recent Performance\n(Line Chart)', 'pos': (13.5, 6.5), 'size': (6, 2.5), 'type': 'line_chart', 'color': colors['line_chart']},
        
        # แถวที่ 3 (กลางล่าง)
        {'name': 'Strategy + Time\nHeatmap', 'pos': (0.5, 3.5), 'size': (6, 2.5), 'type': 'heatmap', 'color': colors['heatmap']},
        {'name': 'Action + Time\nHeatmap', 'pos': (7, 3.5), 'size': (6, 2.5), 'type': 'heatmap', 'color': colors['heatmap']},
        {'name': 'Best Combinations\n(Table)', 'pos': (13.5, 3.5), 'size': (6, 2.5), 'type': 'table', 'color': colors['table']},
        
        # แถวที่ 4 (ล่างสุด)
        {'name': 'Pre-Loss Streak\nAnalysis (Bar)', 'pos': (0.5, 0.5), 'size': (6, 2.5), 'type': 'bar_chart', 'color': colors['bar_chart']},
        {'name': 'Price Movement\nAnalysis (Bar)', 'pos': (7, 0.5), 'size': (6, 2.5), 'type': 'bar_chart', 'color': colors['bar_chart']},
        {'name': 'Daily Performance\nTrend (Line)', 'pos': (13.5, 0.5), 'size': (6, 2.5), 'type': 'line_chart', 'color': colors['line_chart']}
    ]
    
    # วาด charts
    for config in chart_configs:
        x, y = config['pos']
        width, height = config['size']
        
        # สร้าง rectangle
        rect = Rectangle((x, y), width, height, 
                        facecolor=config['color'], 
                        edgecolor=colors['border'], 
                        linewidth=2,
                        alpha=0.8)
        ax.add_patch(rect)
        
        # เพิ่มข้อความ
        ax.text(x + width/2, y + height/2, config['name'], 
                ha='center', va='center', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # เพิ่ม icon ตามประเภท
        icon_x = x + width - 0.8
        icon_y = y + height - 0.3
        
        if config['type'] == 'table':
            ax.text(icon_x, icon_y, '📊', fontsize=16)
        elif config['type'] == 'bar_chart':
            ax.text(icon_x, icon_y, '📊', fontsize=16)
        elif config['type'] == 'line_chart':
            ax.text(icon_x, icon_y, '📈', fontsize=16)
        elif config['type'] == 'heatmap':
            ax.text(icon_x, icon_y, '🔥', fontsize=16)
        elif config['type'] == 'number':
            ax.text(icon_x, icon_y, '🔢', fontsize=16)
    
    # เพิ่ม title
    ax.text(10, 11.5, 'Metabase Dashboard Layout Example', 
            ha='center', va='center', fontsize=20, fontweight='bold')
    
    # เพิ่ม subtitle
    ax.text(10, 11, 'Trading Signal Analysis Dashboard', 
            ha='center', va='center', fontsize=14, style='italic')
    
    # เพิ่ม legend
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, facecolor=colors['table'], label='Table Charts'),
        plt.Rectangle((0, 0), 1, 1, facecolor=colors['bar_chart'], label='Bar Charts'),
        plt.Rectangle((0, 0), 1, 1, facecolor=colors['line_chart'], label='Line Charts'),
        plt.Rectangle((0, 0), 1, 1, facecolor=colors['heatmap'], label='Heatmaps'),
        plt.Rectangle((0, 0), 1, 1, facecolor=colors['number'], label='Number Cards')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    # เพิ่ม grid lines
    for i in range(0, 21, 5):
        ax.axvline(x=i, color='gray', linestyle='--', alpha=0.3)
    for i in range(0, 13, 3):
        ax.axhline(y=i, color='gray', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    return fig

def create_compact_dashboard_layout():
    """สร้างตัวอย่าง Dashboard Layout แบบกะทัดรัด"""
    
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    colors = {
        'primary': '#3498DB',
        'secondary': '#2ECC71', 
        'accent': '#E74C3C',
        'neutral': '#95A5A6',
        'background': '#ECF0F1'
    }
    
    # Layout แบบ 2x4
    chart_configs = [
        # แถวที่ 1
        {'name': 'Strategy Performance\n(Table)', 'pos': (0.5, 7.5), 'size': (7, 2), 'type': 'table'},
        {'name': 'Win Rate Analysis\n(Bar Chart)', 'pos': (8.5, 7.5), 'size': (7, 2), 'type': 'bar'},
        
        # แถวที่ 2  
        {'name': 'Time Pattern\n(Line Chart)', 'pos': (0.5, 5), 'size': (7, 2), 'type': 'line'},
        {'name': 'Risk Assessment\n(Table)', 'pos': (8.5, 5), 'size': (7, 2), 'type': 'table'},
        
        # แถวที่ 3
        {'name': 'Strategy Heatmap\n(Heatmap)', 'pos': (0.5, 2.5), 'size': (7, 2), 'type': 'heatmap'},
        {'name': 'Action Heatmap\n(Heatmap)', 'pos': (8.5, 2.5), 'size': (7, 2), 'type': 'heatmap'},
        
        # แถวที่ 4
        {'name': 'Best Combinations\n(Table)', 'pos': (0.5, 0.5), 'size': (7, 1.5), 'type': 'table'},
        {'name': 'Recent Performance\n(Line Chart)', 'pos': (8.5, 0.5), 'size': (7, 1.5), 'type': 'line'}
    ]
    
    for i, config in enumerate(chart_configs):
        x, y = config['pos']
        width, height = config['size']
        
        # เลือกสีตามลำดับ
        if i % 4 == 0:
            color = colors['primary']
        elif i % 4 == 1:
            color = colors['secondary']
        elif i % 4 == 2:
            color = colors['accent']
        else:
            color = colors['neutral']
        
        rect = Rectangle((x, y), width, height, 
                        facecolor=color, 
                        edgecolor='white', 
                        linewidth=2,
                        alpha=0.7)
        ax.add_patch(rect)
        
        ax.text(x + width/2, y + height/2, config['name'], 
                ha='center', va='center', fontsize=9, fontweight='bold',
                color='white')
    
    ax.text(8, 9.5, 'Compact Dashboard Layout', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_mobile_dashboard_layout():
    """สร้างตัวอย่าง Dashboard Layout สำหรับ Mobile"""
    
    fig, ax = plt.subplots(figsize=(8, 12))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    colors = ['#3498DB', '#2ECC71', '#E74C3C', '#F39C12', '#9B59B6', '#1ABC9C']
    
    # Layout แบบ 1 column
    chart_configs = [
        {'name': 'Strategy Performance', 'pos': (0.5, 10.5), 'size': (7, 1.5), 'color': colors[0]},
        {'name': 'Win Rate Chart', 'pos': (0.5, 8.5), 'size': (7, 1.5), 'color': colors[1]},
        {'name': 'Time Pattern', 'pos': (0.5, 6.5), 'size': (7, 1.5), 'color': colors[2]},
        {'name': 'Risk Assessment', 'pos': (0.5, 4.5), 'size': (7, 1.5), 'color': colors[3]},
        {'name': 'Strategy Heatmap', 'pos': (0.5, 2.5), 'size': (7, 1.5), 'color': colors[4]},
        {'name': 'Best Combinations', 'pos': (0.5, 0.5), 'size': (7, 1.5), 'color': colors[5]}
    ]
    
    for config in chart_configs:
        x, y = config['pos']
        width, height = config['size']
        
        rect = Rectangle((x, y), width, height, 
                        facecolor=config['color'], 
                        edgecolor='white', 
                        linewidth=2,
                        alpha=0.8)
        ax.add_patch(rect)
        
        ax.text(x + width/2, y + height/2, config['name'], 
                ha='center', va='center', fontsize=10, fontweight='bold',
                color='white')
    
    ax.text(4, 11.5, 'Mobile Dashboard Layout', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    print("Creating Dashboard Layout Examples...")
    
    # สร้าง layout ต่างๆ
    fig1 = create_dashboard_layout_example()
    fig1.savefig('/Users/puchong/tradingview/dashboard_layout_full.png', dpi=300, bbox_inches='tight')
    print("✓ Full Dashboard Layout saved")
    
    fig2 = create_compact_dashboard_layout()
    fig2.savefig('/Users/puchong/tradingview/dashboard_layout_compact.png', dpi=300, bbox_inches='tight')
    print("✓ Compact Dashboard Layout saved")
    
    fig3 = create_mobile_dashboard_layout()
    fig3.savefig('/Users/puchong/tradingview/dashboard_layout_mobile.png', dpi=300, bbox_inches='tight')
    print("✓ Mobile Dashboard Layout saved")
    
    # แสดง charts
    plt.show()
