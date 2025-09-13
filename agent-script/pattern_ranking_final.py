#!/usr/bin/env python3
"""
FINAL PATTERN RANKING - สรุปทุก patterns เรียงตาม win rate
ตัด noise ออก แสดงแค่ที่เทพที่สุด สำหรับทำ dashboard
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
import json
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class FinalPatternRanking:
    def __init__(self):
        self.connection = None
        self.data = None
        self.min_sample_size = 50  # ตัด noise: ต้องมีข้อมูลอย่างน้อย 50 samples
        self.min_win_rate_deviation = 0.05  # ต้องต่างจาก 50% อย่างน้อย 5%
        
        self.final_patterns = []
    
    def connect_database(self):
        """Connect to database"""
        try:
            print("🔗 Connecting to database...")
            self.connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_clean_data(self):
        """Load data and filter out noise signals"""
        try:
            print("📊 Loading data and filtering noise...")
            
            query = """
            SELECT 
                id,
                strategy,
                action,
                entry_time,
                entry_price,
                result_60min,
                EXTRACT(HOUR FROM entry_time) as hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(MINUTE FROM entry_time) as minute,
                DATE(entry_time) as trade_date,
                CASE 
                    WHEN result_60min = 'WIN' THEN 1 
                    ELSE 0 
                END as win
            FROM tradingviewdata 
            WHERE entry_time IS NOT NULL
              AND result_60min IS NOT NULL
              AND strategy IS NOT NULL
              AND strategy != ''
            ORDER BY entry_time;
            """
            
            self.data = pd.read_sql_query(query, self.connection)
            
            # Filter out noise signals (เก็บแค่ที่มี sample size พอ)
            strategy_counts = self.data['strategy'].value_counts()
            good_strategies = strategy_counts[strategy_counts >= self.min_sample_size].index.tolist()
            
            print(f"🗑️ Original strategies: {self.data['strategy'].nunique()}")
            print(f"✅ After noise filtering: {len(good_strategies)} strategies")
            print(f"🔍 Removed noise strategies: {set(self.data['strategy'].unique()) - set(good_strategies)}")
            
            # Filter data
            self.data = self.data[self.data['strategy'].isin(good_strategies)].copy()
            self.data = self.data.reset_index(drop=True)
            
            # Add previous result for momentum
            self.data['prev_win'] = self.data['win'].shift(1)
            
            print(f"✅ Clean data: {len(self.data)} records with reliable signals only!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def analyze_all_patterns(self):
        """Analyze all possible patterns and rank them"""
        print("🎯 Analyzing ALL patterns and ranking by win rate...")
        
        patterns = []
        
        # 1. MOMENTUM PATTERNS (แข็งแกร่งที่สุด)
        print("  🔄 Analyzing Momentum Patterns...")
        
        # After WIN pattern
        after_win = self.data[self.data['prev_win'] == 1].dropna()
        if len(after_win) >= self.min_sample_size:
            win_rate = after_win['win'].mean()
            if abs(win_rate - 0.5) >= self.min_win_rate_deviation:
                p_value = stats.binomtest(after_win['win'].sum(), len(after_win), 0.5).pvalue
                patterns.append({
                    'category': 'MOMENTUM',
                    'pattern_name': 'After WIN',
                    'description': 'หลังจากชนะ 1 ไม้ → ไม้ต่อไป',
                    'condition': 'prev_result = WIN',
                    'win_rate': win_rate,
                    'sample_size': len(after_win),
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'pattern_strength': abs(win_rate - 0.5) * len(after_win),
                    'actionable': 'เพิ่มความมั่นใจ' if win_rate > 0.5 else 'ระวัง/หลีกเลี่ยง',
                    'dashboard_filter': "previous_trade_result = 'WIN'"
                })
        
        # After LOSS pattern
        after_loss = self.data[self.data['prev_win'] == 0].dropna()
        if len(after_loss) >= self.min_sample_size:
            win_rate = after_loss['win'].mean()
            if abs(win_rate - 0.5) >= self.min_win_rate_deviation:
                p_value = stats.binomtest(after_loss['win'].sum(), len(after_loss), 0.5).pvalue
                patterns.append({
                    'category': 'MOMENTUM',
                    'pattern_name': 'After LOSS',
                    'description': 'หลังจากแพ้ 1 ไม้ → ไม้ต่อไป',
                    'condition': 'prev_result = LOSS',
                    'win_rate': win_rate,
                    'sample_size': len(after_loss),
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'pattern_strength': abs(win_rate - 0.5) * len(after_loss),
                    'actionable': 'เพิ่มความมั่นใจ' if win_rate > 0.5 else 'ระวัง/หลีกเลี่ยง',
                    'dashboard_filter': "previous_trade_result = 'LOSS'"
                })
        
        # 2. TIME PATTERNS
        print("  ⏰ Analyzing Time Patterns...")
        
        # Hourly patterns
        for hour in range(24):
            hour_data = self.data[self.data['hour'] == hour]
            if len(hour_data) >= self.min_sample_size:
                win_rate = hour_data['win'].mean()
                if abs(win_rate - 0.5) >= self.min_win_rate_deviation:
                    p_value = stats.binomtest(hour_data['win'].sum(), len(hour_data), 0.5).pvalue
                    patterns.append({
                        'category': 'TIME_HOUR',
                        'pattern_name': f'Hour {hour:02d}:00',
                        'description': f'เทรดในชั่วโมง {hour:02d}:00-{hour:02d}:59',
                        'condition': f'hour = {hour}',
                        'win_rate': win_rate,
                        'sample_size': len(hour_data),
                        'p_value': p_value,
                        'is_significant': p_value < 0.05,
                        'pattern_strength': abs(win_rate - 0.5) * len(hour_data),
                        'actionable': 'เทรดในชั่วโมงนี้' if win_rate > 0.5 else 'หลีกเลี่ยงชั่วโมงนี้',
                        'dashboard_filter': f"EXTRACT(HOUR FROM entry_time) = {hour}"
                    })
        
        # Day of week patterns
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for dow in range(7):
            dow_data = self.data[self.data['day_of_week'] == dow]
            if len(dow_data) >= self.min_sample_size:
                win_rate = dow_data['win'].mean()
                if abs(win_rate - 0.5) >= self.min_win_rate_deviation:
                    p_value = stats.binomtest(dow_data['win'].sum(), len(dow_data), 0.5).pvalue
                    patterns.append({
                        'category': 'TIME_DAY',
                        'pattern_name': f'{day_names[dow]}',
                        'description': f'เทรดในวัน{day_names[dow]}',
                        'condition': f'day_of_week = {dow}',
                        'win_rate': win_rate,
                        'sample_size': len(dow_data),
                        'p_value': p_value,
                        'is_significant': p_value < 0.05,
                        'pattern_strength': abs(win_rate - 0.5) * len(dow_data),
                        'actionable': f'เทรดในวัน{day_names[dow]}' if win_rate > 0.5 else f'หลีกเลี่ยงวัน{day_names[dow]}',
                        'dashboard_filter': f"EXTRACT(DOW FROM entry_time) = {dow}"
                    })
        
        # 3. TIME BLOCK PATTERNS (ช่วงเวลา)
        print("  🕐 Analyzing Time Block Patterns...")
        
        time_blocks = [
            (0, 5, 'Early Morning (00:00-05:59)'),
            (6, 11, 'Morning (06:00-11:59)'), 
            (12, 17, 'Afternoon (12:00-17:59)'),
            (18, 23, 'Evening (18:00-23:59)')
        ]
        
        for start_hour, end_hour, block_name in time_blocks:
            block_data = self.data[
                (self.data['hour'] >= start_hour) & 
                (self.data['hour'] <= end_hour)
            ]
            if len(block_data) >= self.min_sample_size:
                win_rate = block_data['win'].mean()
                if abs(win_rate - 0.5) >= self.min_win_rate_deviation:
                    p_value = stats.binomtest(block_data['win'].sum(), len(block_data), 0.5).pvalue
                    patterns.append({
                        'category': 'TIME_BLOCK',
                        'pattern_name': block_name,
                        'description': f'เทรดในช่วง {block_name}',
                        'condition': f'hour BETWEEN {start_hour} AND {end_hour}',
                        'win_rate': win_rate,
                        'sample_size': len(block_data),
                        'p_value': p_value,
                        'is_significant': p_value < 0.05,
                        'pattern_strength': abs(win_rate - 0.5) * len(block_data),
                        'actionable': f'เทรดในช่วง {block_name}' if win_rate > 0.5 else f'หลีกเลี่ยงช่วง {block_name}',
                        'dashboard_filter': f"EXTRACT(HOUR FROM entry_time) BETWEEN {start_hour} AND {end_hour}"
                    })
        
        # 4. COMBINATION PATTERNS (รวมที่ดีที่สุด)
        print("  🎯 Analyzing Combination Patterns...")
        
        # Tuesday + specific hours
        good_hours = [8, 15, 21]  # จาก analysis ก่อนหน้า
        for hour in good_hours:
            combo_data = self.data[
                (self.data['day_of_week'] == 2) & 
                (self.data['hour'] == hour)
            ]
            if len(combo_data) >= 20:  # ลด threshold สำหรับ combination
                win_rate = combo_data['win'].mean()
                if abs(win_rate - 0.5) >= self.min_win_rate_deviation:
                    p_value = stats.binomtest(combo_data['win'].sum(), len(combo_data), 0.5).pvalue
                    patterns.append({
                        'category': 'COMBINATION',
                        'pattern_name': f'Tuesday + Hour {hour:02d}:00',
                        'description': f'วันอังคาร ชั่วโมง {hour:02d}:00-{hour:02d}:59',
                        'condition': f'day_of_week = 2 AND hour = {hour}',
                        'win_rate': win_rate,
                        'sample_size': len(combo_data),
                        'p_value': p_value,
                        'is_significant': p_value < 0.05,
                        'pattern_strength': abs(win_rate - 0.5) * len(combo_data),
                        'actionable': 'Golden Combination!' if win_rate > 0.6 else 'เทรดในเวลานี้',
                        'dashboard_filter': f"EXTRACT(DOW FROM entry_time) = 2 AND EXTRACT(HOUR FROM entry_time) = {hour}"
                    })
        
        # Filter and rank patterns
        self.final_patterns = self.filter_and_rank_patterns(patterns)
        
    def filter_and_rank_patterns(self, patterns):
        """Filter out weak patterns and rank by win rate"""
        print("🔍 Filtering and ranking patterns...")
        
        # Filter criteria
        filtered_patterns = []
        for pattern in patterns:
            # Must be statistically significant
            if not pattern['is_significant']:
                continue
            
            # Must have meaningful deviation from 50%
            if abs(pattern['win_rate'] - 0.5) < self.min_win_rate_deviation:
                continue
            
            # Must have enough samples
            if pattern['sample_size'] < (20 if pattern['category'] == 'COMBINATION' else self.min_sample_size):
                continue
            
            filtered_patterns.append(pattern)
        
        # Rank by win rate (descending for good patterns, ascending for bad patterns)
        # Separate good and bad patterns
        good_patterns = [p for p in filtered_patterns if p['win_rate'] > 0.5]
        bad_patterns = [p for p in filtered_patterns if p['win_rate'] < 0.5]
        
        # Sort good patterns by win rate (descending)
        good_patterns.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Sort bad patterns by win rate (ascending - worst first)
        bad_patterns.sort(key=lambda x: x['win_rate'])
        
        # Combine: good patterns first, then bad patterns
        ranked_patterns = good_patterns + bad_patterns
        
        print(f"✅ Filtered to {len(ranked_patterns)} high-quality patterns")
        print(f"   - Good patterns (>50%): {len(good_patterns)}")
        print(f"   - Bad patterns (<50%): {len(bad_patterns)}")
        
        return ranked_patterns
    
    def save_dashboard_patterns(self):
        """Save patterns for dashboard creation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON
        with open(f'/Users/puchong/tradingview/report/dashboard_patterns_{timestamp}.json', 'w') as f:
            json.dump(self.final_patterns, f, indent=2, default=str)
        
        # Generate dashboard report
        report = self.generate_dashboard_report()
        with open(f'/Users/puchong/tradingview/report/DASHBOARD_PATTERNS_LIST.md', 'w') as f:
            f.write(report)
        
        # Generate SQL queries for dashboard
        sql_queries = self.generate_dashboard_sql()
        with open(f'/Users/puchong/tradingview/report/DASHBOARD_SQL_QUERIES.sql', 'w') as f:
            f.write(sql_queries)
        
        print("✅ Dashboard patterns saved!")
    
    def generate_dashboard_report(self):
        """Generate dashboard-ready pattern list"""
        return f"""# 🎯 DASHBOARD PATTERNS LIST
## เทพสุด - เรียงตาม Win Rate

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Patterns**: {len(self.final_patterns)}  
**Min Sample Size**: {self.min_sample_size}  
**Min Win Rate Deviation**: {self.min_win_rate_deviation * 100}%

---

## 🏆 **TOP GOOD PATTERNS (Win Rate > 50%)**

{self.format_good_patterns()}

---

## ☠️ **TOP BAD PATTERNS (Win Rate < 50%) - AVOID!**

{self.format_bad_patterns()}

---

## 📊 **DASHBOARD IMPLEMENTATION**

{self.format_dashboard_implementation()}

---

## 🔥 **PATTERN CATEGORIES SUMMARY**

{self.format_category_summary()}
"""
    
    def format_good_patterns(self):
        good_patterns = [p for p in self.final_patterns if p['win_rate'] > 0.5]
        if not good_patterns:
            return "ไม่มี patterns ที่ดี"
        
        output = ""
        for i, pattern in enumerate(good_patterns, 1):
            tier = "🔥" if pattern['win_rate'] >= 0.7 else "💎" if pattern['win_rate'] >= 0.6 else "⭐"
            
            output += f"""### {tier} **#{i} {pattern['pattern_name']}** - {pattern['win_rate']:.1%}

- **Category**: {pattern['category']}
- **Description**: {pattern['description']}
- **Win Rate**: **{pattern['win_rate']:.1%}**
- **Sample Size**: {pattern['sample_size']:,}
- **P-value**: {pattern['p_value']:.4f}
- **Pattern Strength**: {pattern['pattern_strength']:.1f}
- **Action**: {pattern['actionable']}
- **Dashboard Filter**: `{pattern['dashboard_filter']}`

"""
        return output
    
    def format_bad_patterns(self):
        bad_patterns = [p for p in self.final_patterns if p['win_rate'] < 0.5]
        if not bad_patterns:
            return "ไม่มี patterns ที่แย่"
        
        output = ""
        for i, pattern in enumerate(bad_patterns, 1):
            danger = "💀" if pattern['win_rate'] <= 0.3 else "⚠️" if pattern['win_rate'] <= 0.4 else "🔴"
            
            output += f"""### {danger} **#{i} {pattern['pattern_name']}** - {pattern['win_rate']:.1%}

- **Category**: {pattern['category']}
- **Description**: {pattern['description']}
- **Win Rate**: **{pattern['win_rate']:.1%}** ⚠️
- **Sample Size**: {pattern['sample_size']:,}
- **P-value**: {pattern['p_value']:.4f}
- **Action**: **{pattern['actionable']}**
- **Dashboard Filter**: `{pattern['dashboard_filter']}`

"""
        return output
    
    def format_dashboard_implementation(self):
        return f"""### **📈 Metabase Dashboard Setup:**

**1. Create Pattern Performance Chart:**
```sql
SELECT 
  pattern_name,
  win_rate,
  sample_size,
  category
FROM pattern_analysis_results 
ORDER BY win_rate DESC;
```

**2. Time-based Pattern Visualization:**
```sql
SELECT 
  EXTRACT(HOUR FROM entry_time) as hour,
  COUNT(*) as total_trades,
  AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate
FROM tradingviewdata 
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;
```

**3. Pattern Performance Heatmap:**
```sql
SELECT 
  EXTRACT(DOW FROM entry_time) as day_of_week,
  EXTRACT(HOUR FROM entry_time) as hour,
  COUNT(*) as trades,
  AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate
FROM tradingviewdata 
GROUP BY day_of_week, hour
HAVING COUNT(*) >= 10;
```

**4. Best Pattern Combinations:**
- Tuesday + Hour 21 
- After WIN + Good Hours
- Morning Block + Reliable Signals
"""
    
    def format_category_summary(self):
        categories = {}
        for pattern in self.final_patterns:
            cat = pattern['category']
            if cat not in categories:
                categories[cat] = {'count': 0, 'avg_win_rate': 0, 'patterns': []}
            categories[cat]['count'] += 1
            categories[cat]['patterns'].append(pattern['win_rate'])
        
        output = ""
        for cat, data in categories.items():
            avg_wr = sum(data['patterns']) / len(data['patterns'])
            categories[cat]['avg_win_rate'] = avg_wr
            
            output += f"""**{cat}**: {data['count']} patterns, Avg Win Rate: {avg_wr:.1%}
"""
        
        return output
    
    def generate_dashboard_sql(self):
        """Generate SQL queries for dashboard"""
        sql_queries = f"""-- DASHBOARD SQL QUERIES
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- 1. PATTERN PERFORMANCE OVERVIEW
CREATE VIEW pattern_performance AS
SELECT 
    'Hour Patterns' as category,
    CONCAT('Hour ', LPAD(EXTRACT(HOUR FROM entry_time)::text, 2, '0'), ':00') as pattern_name,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
    STDDEV(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate_stddev
FROM tradingviewdata 
WHERE strategy IN ('MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20')
GROUP BY EXTRACT(HOUR FROM entry_time)
HAVING COUNT(*) >= 50

UNION ALL

SELECT 
    'Day Patterns' as category,
    CASE EXTRACT(DOW FROM entry_time)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday' 
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as pattern_name,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
    STDDEV(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate_stddev
FROM tradingviewdata 
WHERE strategy IN ('MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20')
GROUP BY EXTRACT(DOW FROM entry_time)
HAVING COUNT(*) >= 50
ORDER BY win_rate DESC;

-- 2. TOP PATTERNS ONLY (Win Rate > 55% OR < 45%)
SELECT * FROM pattern_performance 
WHERE win_rate > 0.55 OR win_rate < 0.45
ORDER BY win_rate DESC;

-- 3. TIME HEATMAP DATA
SELECT 
    EXTRACT(DOW FROM entry_time) as day_of_week,
    EXTRACT(HOUR FROM entry_time) as hour,
    COUNT(*) as total_trades,
    SUM(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as wins,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE strategy IN ('MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20')
GROUP BY day_of_week, hour
HAVING COUNT(*) >= 10
ORDER BY day_of_week, hour;

-- 4. GOLDEN COMBINATIONS
SELECT 
    'Tuesday + Hour 21' as combination,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE EXTRACT(DOW FROM entry_time) = 2 
  AND EXTRACT(HOUR FROM entry_time) = 21
  AND strategy IN ('MWP-25', 'MWP-27', 'MWP-30')

UNION ALL

SELECT 
    'Golden Hours (08,15,21)' as combination,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE EXTRACT(HOUR FROM entry_time) IN (8, 15, 21)
  AND strategy IN ('MWP-25', 'MWP-27', 'MWP-30')

UNION ALL

SELECT 
    'Danger Hours (17,19,23)' as combination,
    COUNT(*) as sample_size,
    AVG(CASE WHEN result_60min = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate
FROM tradingviewdata 
WHERE EXTRACT(HOUR FROM entry_time) IN (17, 19, 23)
  AND strategy IN ('MWP-25', 'MWP-27', 'MWP-30')
ORDER BY win_rate DESC;
"""
        return sql_queries
    
    def run_final_analysis(self):
        """Run complete final pattern analysis"""
        print("🎯 Starting FINAL PATTERN RANKING...")
        print("🗑️ Filtering out noise signals...")
        print("🏆 Ranking by pure win rate...")
        print("=" * 60)
        
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_clean_data():
            return False
        
        # Analyze all patterns
        self.analyze_all_patterns()
        
        # Save for dashboard
        self.save_dashboard_patterns()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 FINAL PATTERN RANKING COMPLETE!")
        print(f"⏱️ Duration: {duration}")
        print(f"📊 Total Patterns Found: {len(self.final_patterns)}")
        good_patterns = len([p for p in self.final_patterns if p['win_rate'] > 0.5])
        bad_patterns = len([p for p in self.final_patterns if p['win_rate'] < 0.5])
        print(f"🏆 Good Patterns: {good_patterns}")
        print(f"☠️ Bad Patterns: {bad_patterns}")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    analyzer = FinalPatternRanking()
    analyzer.run_final_analysis()
