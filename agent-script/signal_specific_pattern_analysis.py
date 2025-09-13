#!/usr/bin/env python3
"""
SIGNAL-SPECIFIC PATTERN ANALYSIS
ตรวจสอบว่า patterns ที่หามาใช้ได้กับทุก signal หรือแต่ละ signal มี patterns ที่แตกต่างกัน
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

class SignalSpecificPatternAnalyzer:
    def __init__(self):
        self.connection = None
        self.data = None
        self.results = {
            'overall_patterns': {},
            'signal_specific_patterns': {},
            'pattern_consistency': {},
            'signal_reliability': {},
            'final_verdict': {}
        }
    
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
    
    def load_signal_data(self):
        """Load data with signal breakdown"""
        try:
            print("📊 Loading data with signal breakdown...")
            
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
            self.data['trade_date'] = pd.to_datetime(self.data['trade_date'])
            self.data['entry_time'] = pd.to_datetime(self.data['entry_time'])
            
            # Add previous result for momentum analysis
            self.data['prev_result'] = self.data['win'].shift(1)
            
            print(f"✅ Loaded {len(self.data)} records!")
            print(f"📈 Strategies found: {self.data['strategy'].nunique()}")
            
            # Show strategy distribution
            strategy_counts = self.data['strategy'].value_counts()
            print("\n📊 Strategy Distribution:")
            for strategy, count in strategy_counts.head(10).items():
                print(f"  - {strategy}: {count} trades")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def analyze_overall_patterns(self):
        """Analyze overall patterns first (as baseline)"""
        print("🎯 Analyzing OVERALL patterns (all signals combined)...")
        
        overall = {}
        
        # 1. Overall momentum pattern
        momentum_stats = []
        for prev_result in [0, 1]:
            momentum_data = self.data[self.data['prev_result'] == prev_result].dropna()
            if len(momentum_data) >= 50:
                win_rate = momentum_data['win'].mean()
                count = len(momentum_data)
                
                p_value = stats.binomtest(momentum_data['win'].sum(), count, 0.5).pvalue
                
                momentum_stats.append({
                    'previous_result': 'WIN' if prev_result == 1 else 'LOSS',
                    'subsequent_win_rate': win_rate,
                    'sample_size': count,
                    'p_value': p_value,
                    'is_significant': p_value < 0.05
                })
        
        overall['momentum'] = momentum_stats
        
        # 2. Overall time patterns
        hour_stats = []
        for hour in range(24):
            hour_data = self.data[self.data['hour'] == hour]
            if len(hour_data) >= 20:
                win_rate = hour_data['win'].mean()
                count = len(hour_data)
                
                p_value = stats.binomtest(hour_data['win'].sum(), count, 0.5).pvalue
                
                if p_value < 0.05:  # Only significant hours
                    hour_stats.append({
                        'hour': hour,
                        'win_rate': win_rate,
                        'sample_size': count,
                        'p_value': p_value,
                        'is_significant': True
                    })
        
        overall['significant_hours'] = hour_stats
        
        # 3. Overall day patterns
        day_stats = []
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for dow in range(7):
            dow_data = self.data[self.data['day_of_week'] == dow]
            if len(dow_data) >= 30:
                win_rate = dow_data['win'].mean()
                count = len(dow_data)
                
                p_value = stats.binomtest(dow_data['win'].sum(), count, 0.5).pvalue
                
                if p_value < 0.05:  # Only significant days
                    day_stats.append({
                        'day_of_week': dow,
                        'day_name': day_names[dow],
                        'win_rate': win_rate,
                        'sample_size': count,
                        'p_value': p_value,
                        'is_significant': True
                    })
        
        overall['significant_days'] = day_stats
        
        self.results['overall_patterns'] = overall
    
    def analyze_signal_specific_patterns(self):
        """Analyze patterns for each signal separately"""
        print("🔍 Analyzing patterns for EACH SIGNAL separately...")
        
        signal_patterns = {}
        
        # Get top strategies (minimum 50 trades)
        strategy_counts = self.data['strategy'].value_counts()
        top_strategies = strategy_counts[strategy_counts >= 50].index.tolist()
        
        print(f"📋 Analyzing {len(top_strategies)} strategies with sufficient data...")
        
        for strategy in top_strategies:
            print(f"  🔸 Analyzing {strategy}...")
            strategy_data = self.data[self.data['strategy'] == strategy].copy()
            
            if len(strategy_data) < 50:
                continue
            
            signal_analysis = {
                'total_trades': len(strategy_data),
                'overall_win_rate': strategy_data['win'].mean(),
                'momentum_patterns': [],
                'time_patterns': [],
                'day_patterns': []
            }
            
            # Add previous result for this strategy's data  
            strategy_data['prev_result'] = strategy_data['win'].shift(1)
            
            # 1. Momentum analysis for this strategy
            for prev_result in [0, 1]:
                momentum_data = strategy_data[strategy_data['prev_result'] == prev_result].dropna()
                if len(momentum_data) >= 10:  # Lower threshold for individual strategies
                    win_rate = momentum_data['win'].mean()
                    count = len(momentum_data)
                    
                    p_value = stats.binomtest(momentum_data['win'].sum(), count, 0.5).pvalue
                    
                    signal_analysis['momentum_patterns'].append({
                        'previous_result': 'WIN' if prev_result == 1 else 'LOSS',
                        'subsequent_win_rate': win_rate,
                        'sample_size': count,
                        'p_value': p_value,
                        'is_significant': p_value < 0.05
                    })
            
            # 2. Time analysis for this strategy
            for hour in range(24):
                hour_data = strategy_data[strategy_data['hour'] == hour]
                if len(hour_data) >= 5:  # Lower threshold
                    win_rate = hour_data['win'].mean()
                    count = len(hour_data)
                    
                    # Only include if significantly different from 50%
                    if abs(win_rate - 0.5) > 0.1:  # At least 10% difference
                        p_value = stats.binomtest(hour_data['win'].sum(), count, 0.5).pvalue
                        
                        signal_analysis['time_patterns'].append({
                            'hour': hour,
                            'win_rate': win_rate,
                            'sample_size': count,
                            'p_value': p_value,
                            'is_significant': p_value < 0.05
                        })
            
            # 3. Day analysis for this strategy
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            for dow in range(7):
                dow_data = strategy_data[strategy_data['day_of_week'] == dow]
                if len(dow_data) >= 5:
                    win_rate = dow_data['win'].mean()
                    count = len(dow_data)
                    
                    if abs(win_rate - 0.5) > 0.1:
                        p_value = stats.binomtest(dow_data['win'].sum(), count, 0.5).pvalue
                        
                        signal_analysis['day_patterns'].append({
                            'day_of_week': dow,
                            'day_name': day_names[dow],
                            'win_rate': win_rate,
                            'sample_size': count,
                            'p_value': p_value,
                            'is_significant': p_value < 0.05
                        })
            
            signal_patterns[strategy] = signal_analysis
        
        self.results['signal_specific_patterns'] = signal_patterns
    
    def analyze_pattern_consistency(self):
        """Check if patterns are consistent across signals"""
        print("🔄 Checking pattern CONSISTENCY across signals...")
        
        consistency = {
            'momentum_consistency': {},
            'time_consistency': {},
            'day_consistency': {},
            'overall_consistency_score': 0
        }
        
        if not self.results['signal_specific_patterns']:
            return
        
        # 1. Momentum pattern consistency
        signals_with_momentum = 0
        consistent_momentum_signals = 0
        
        for strategy, analysis in self.results['signal_specific_patterns'].items():
            momentum_patterns = analysis['momentum_patterns']
            has_win_after_win = False
            has_loss_after_loss = False
            
            for pattern in momentum_patterns:
                if pattern['previous_result'] == 'WIN' and pattern['subsequent_win_rate'] > 0.65:
                    has_win_after_win = True
                if pattern['previous_result'] == 'LOSS' and pattern['subsequent_win_rate'] < 0.35:
                    has_loss_after_loss = True
            
            if momentum_patterns:  # Has momentum data
                signals_with_momentum += 1
                if has_win_after_win or has_loss_after_loss:
                    consistent_momentum_signals += 1
        
        momentum_consistency_rate = consistent_momentum_signals / signals_with_momentum if signals_with_momentum > 0 else 0
        
        consistency['momentum_consistency'] = {
            'total_signals_analyzed': signals_with_momentum,
            'signals_with_consistent_momentum': consistent_momentum_signals,
            'consistency_rate': momentum_consistency_rate,
            'is_consistent': momentum_consistency_rate >= 0.7
        }
        
        # 2. Time pattern consistency (check if same good/bad hours appear)
        overall_good_hours = set()
        overall_bad_hours = set()
        
        for hour_pattern in self.results['overall_patterns']['significant_hours']:
            if hour_pattern['win_rate'] > 0.55:
                overall_good_hours.add(hour_pattern['hour'])
            elif hour_pattern['win_rate'] < 0.45:
                overall_bad_hours.add(hour_pattern['hour'])
        
        signals_with_time_data = 0
        time_consistent_signals = 0
        
        for strategy, analysis in self.results['signal_specific_patterns'].items():
            if analysis['time_patterns']:
                signals_with_time_data += 1
                
                signal_good_hours = set()
                signal_bad_hours = set()
                
                for time_pattern in analysis['time_patterns']:
                    if time_pattern['win_rate'] > 0.55:
                        signal_good_hours.add(time_pattern['hour'])
                    elif time_pattern['win_rate'] < 0.45:
                        signal_bad_hours.add(time_pattern['hour'])
                
                # Check if overlaps with overall patterns
                good_overlap = len(overall_good_hours.intersection(signal_good_hours))
                bad_overlap = len(overall_bad_hours.intersection(signal_bad_hours))
                
                if good_overlap > 0 or bad_overlap > 0:
                    time_consistent_signals += 1
        
        time_consistency_rate = time_consistent_signals / signals_with_time_data if signals_with_time_data > 0 else 0
        
        consistency['time_consistency'] = {
            'total_signals_analyzed': signals_with_time_data,
            'signals_with_consistent_time_patterns': time_consistent_signals,
            'consistency_rate': time_consistency_rate,
            'is_consistent': time_consistency_rate >= 0.5,
            'overall_good_hours': list(overall_good_hours),
            'overall_bad_hours': list(overall_bad_hours)
        }
        
        # Overall consistency score
        consistency['overall_consistency_score'] = (momentum_consistency_rate + time_consistency_rate) / 2
        
        self.results['pattern_consistency'] = consistency
    
    def evaluate_signal_reliability(self):
        """Evaluate which signals are most reliable for patterns"""
        print("⭐ Evaluating signal reliability for patterns...")
        
        reliability = {}
        
        for strategy, analysis in self.results['signal_specific_patterns'].items():
            score = 0
            factors = []
            
            # Factor 1: Sample size (more data = more reliable)
            sample_size = analysis['total_trades']
            if sample_size >= 200:
                score += 3
                factors.append("Large sample size")
            elif sample_size >= 100:
                score += 2
                factors.append("Medium sample size")
            elif sample_size >= 50:
                score += 1
                factors.append("Small sample size")
            
            # Factor 2: Significant momentum patterns
            significant_momentum = sum(1 for p in analysis['momentum_patterns'] if p['is_significant'])
            if significant_momentum >= 2:
                score += 3
                factors.append("Strong momentum patterns")
            elif significant_momentum == 1:
                score += 1
                factors.append("Some momentum patterns")
            
            # Factor 3: Significant time patterns
            significant_time = sum(1 for p in analysis['time_patterns'] if p['is_significant'])
            if significant_time >= 3:
                score += 2
                factors.append("Multiple time patterns")
            elif significant_time >= 1:
                score += 1
                factors.append("Some time patterns")
            
            # Factor 4: Overall win rate (baseline performance)
            overall_wr = analysis['overall_win_rate']
            if overall_wr >= 0.55:
                score += 2
                factors.append("Good baseline performance")
            elif overall_wr >= 0.45:
                score += 1
                factors.append("Neutral baseline performance")
            
            reliability[strategy] = {
                'reliability_score': score,
                'max_possible_score': 10,
                'reliability_percentage': (score / 10) * 100,
                'reliability_factors': factors,
                'sample_size': sample_size,
                'overall_win_rate': overall_wr,
                'significant_momentum_patterns': significant_momentum,
                'significant_time_patterns': significant_time
            }
        
        # Sort by reliability score
        sorted_reliability = dict(sorted(reliability.items(), key=lambda x: x[1]['reliability_score'], reverse=True))
        
        self.results['signal_reliability'] = sorted_reliability
    
    def generate_final_verdict(self):
        """Generate final verdict on pattern universality"""
        print("⚖️ Generating final verdict on pattern universality...")
        
        verdict = {}
        
        # Check consistency scores
        consistency = self.results.get('pattern_consistency', {})
        momentum_consistency = consistency.get('momentum_consistency', {}).get('consistency_rate', 0)
        time_consistency = consistency.get('time_consistency', {}).get('consistency_rate', 0)
        overall_consistency = consistency.get('overall_consistency_score', 0)
        
        # Count reliable signals
        reliability = self.results.get('signal_reliability', {})
        total_signals = len(reliability)
        reliable_signals = sum(1 for r in reliability.values() if r['reliability_percentage'] >= 50)
        
        # Determine universality
        if overall_consistency >= 0.7 and reliable_signals / total_signals >= 0.6:
            universality = "UNIVERSAL"
            recommendation = "Patterns ใช้ได้กับทุกสัญญาน"
            confidence = "HIGH"
        elif overall_consistency >= 0.5 and reliable_signals / total_signals >= 0.4:
            universality = "MOSTLY_UNIVERSAL"
            recommendation = "Patterns ใช้ได้กับสัญญานส่วนใหญ่"
            confidence = "MEDIUM"
        elif overall_consistency >= 0.3:
            universality = "SIGNAL_SPECIFIC"
            recommendation = "Patterns ต้องเลือกใช้กับสัญญานเฉพาะ"
            confidence = "LOW"
        else:
            universality = "NOT_UNIVERSAL"
            recommendation = "Patterns ไม่ใช่แบบ universal ต้องแยกดูแต่ละสัญญาน"
            confidence = "VERY_LOW"
        
        verdict = {
            'universality': universality,
            'recommendation': recommendation,
            'confidence': confidence,
            'momentum_consistency_rate': momentum_consistency,
            'time_consistency_rate': time_consistency,
            'overall_consistency_score': overall_consistency,
            'total_signals_analyzed': total_signals,
            'reliable_signals_count': reliable_signals,
            'reliable_signals_percentage': (reliable_signals / total_signals * 100) if total_signals > 0 else 0,
            'top_reliable_signals': list(reliability.keys())[:5] if reliability else []
        }
        
        self.results['final_verdict'] = verdict
    
    def save_results(self):
        """Save signal-specific analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'/Users/puchong/tradingview/report/signal_specific_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate report
        report = self.generate_signal_report()
        with open(f'/Users/puchong/tradingview/report/SIGNAL_SPECIFIC_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Signal-specific analysis saved!")
    
    def generate_signal_report(self):
        """Generate comprehensive signal-specific report"""
        verdict = self.results.get('final_verdict', {})
        
        return f"""# 🎯 SIGNAL-SPECIFIC PATTERN ANALYSIS
## ทุกสัญญานชัดเจนเหมือนกันหรือไม่?

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Signals Analyzed**: {verdict.get('total_signals_analyzed', 0)}  
**Reliable Signals**: {verdict.get('reliable_signals_count', 0)} ({verdict.get('reliable_signals_percentage', 0):.1f}%)

---

## 🎯 **FINAL VERDICT**

### **Pattern Universality:** 
**{verdict.get('universality', 'Unknown')}**

### **Recommendation:**
**{verdict.get('recommendation', 'Unknown')}**

### **Confidence Level:**
**{verdict.get('confidence', 'Unknown')}**

### **Consistency Scores:**
- **Momentum Patterns**: {verdict.get('momentum_consistency_rate', 0):.1%}
- **Time Patterns**: {verdict.get('time_consistency_rate', 0):.1%}  
- **Overall Consistency**: {verdict.get('overall_consistency_score', 0):.1%}

---

## 🏆 **TOP RELIABLE SIGNALS**

{self.format_reliable_signals()}

---

## 📊 **PATTERN CONSISTENCY ANALYSIS**

{self.format_consistency_analysis()}

---

## 🎲 **SIGNAL-BY-SIGNAL BREAKDOWN**

{self.format_signal_breakdown()}

---

## 💡 **EXECUTIVE SUMMARY**

{self.generate_executive_summary()}
"""
    
    def format_reliable_signals(self):
        reliability = self.results.get('signal_reliability', {})
        if not reliability:
            return "ไม่มีข้อมูล"
        
        output = ""
        for i, (strategy, data) in enumerate(list(reliability.items())[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "⭐"
            
            output += f"""**{emoji} #{i} {strategy}**
- **Reliability Score**: {data['reliability_score']}/10 ({data['reliability_percentage']:.1f}%)
- **Sample Size**: {data['sample_size']} trades
- **Overall Win Rate**: {data['overall_win_rate']:.1%}
- **Momentum Patterns**: {data['significant_momentum_patterns']} significant
- **Time Patterns**: {data['significant_time_patterns']} significant
- **Factors**: {', '.join(data['reliability_factors'])}

"""
        return output
    
    def format_consistency_analysis(self):
        consistency = self.results.get('pattern_consistency', {})
        if not consistency:
            return "ไม่มีข้อมูล"
        
        momentum = consistency.get('momentum_consistency', {})
        time = consistency.get('time_consistency', {})
        
        output = f"""### 🔄 **Momentum Pattern Consistency:**
- **Signals Analyzed**: {momentum.get('total_signals_analyzed', 0)}
- **Consistent Signals**: {momentum.get('signals_with_consistent_momentum', 0)}
- **Consistency Rate**: {momentum.get('consistency_rate', 0):.1%}
- **Is Consistent**: {'✅' if momentum.get('is_consistent', False) else '❌'}

### ⏰ **Time Pattern Consistency:**
- **Signals Analyzed**: {time.get('total_signals_analyzed', 0)}
- **Consistent Signals**: {time.get('signals_with_consistent_time_patterns', 0)}  
- **Consistency Rate**: {time.get('consistency_rate', 0):.1%}
- **Is Consistent**: {'✅' if time.get('is_consistent', False) else '❌'}
- **Overall Good Hours**: {time.get('overall_good_hours', [])}
- **Overall Bad Hours**: {time.get('overall_bad_hours', [])}
"""
        return output
    
    def format_signal_breakdown(self):
        signals = self.results.get('signal_specific_patterns', {})
        if not signals:
            return "ไม่มีข้อมูล"
        
        output = ""
        for strategy, analysis in list(signals.items())[:3]:  # Top 3 for brevity
            output += f"""### **📊 {strategy}**
- **Total Trades**: {analysis['total_trades']}
- **Overall Win Rate**: {analysis['overall_win_rate']:.1%}

**Momentum Patterns**:
"""
            for pattern in analysis['momentum_patterns']:
                significance = "✅" if pattern['is_significant'] else "❌"
                output += f"  - After {pattern['previous_result']}: {pattern['subsequent_win_rate']:.1%} ({pattern['sample_size']} samples) {significance}\n"
            
            output += f"\n**Significant Time Patterns**: {len([p for p in analysis['time_patterns'] if p['is_significant']])}\n"
            output += f"**Significant Day Patterns**: {len([p for p in analysis['day_patterns'] if p['is_significant']])}\n\n"
        
        return output
    
    def generate_executive_summary(self):
        verdict = self.results.get('final_verdict', {})
        universality = verdict.get('universality', 'Unknown')
        
        if universality == "UNIVERSAL":
            return f"""
✅ **UNIVERSAL PATTERNS CONFIRMED!**

**คำตอบ**: ใช่! ทุกสัญญานชัดเจนเหมือนกัน

**หลักฐาน**:
- Momentum Consistency: {verdict.get('momentum_consistency_rate', 0):.1%}
- Time Consistency: {verdict.get('time_consistency_rate', 0):.1%}
- {verdict.get('reliable_signals_count', 0)}/{verdict.get('total_signals_analyzed', 0)} signals มี patterns ที่เชื่อถือได้

**การใช้งาน**:
1. ใช้ patterns เดียวกันกับทุกสัญญาน
2. ไม่ต้องแยกกฎสำหรับแต่ละสัญญาน  
3. Focus ที่ time patterns และ momentum patterns
4. เลือกสัญญานตาม reliability score
"""
        
        elif universality == "MOSTLY_UNIVERSAL":
            return f"""
⚠️ **MOSTLY UNIVERSAL - ใช้ได้กับสัญญานส่วนใหญ่**

**คำตอบ**: ส่วนใหญ่ชัดเจนเหมือนกัน แต่มีข้อยกเว้นบางตัว

**หลักฐาน**:
- {verdict.get('reliable_signals_percentage', 0):.1f}% ของสัญญานมี patterns ที่เชื่อถือได้
- Consistency Score: {verdict.get('overall_consistency_score', 0):.1%}

**การใช้งาน**:
1. ใช้ patterns หลักกับสัญญานที่ reliable
2. ระวังสัญญานที่ reliability score ต่ำ
3. Focus ที่ top {verdict.get('reliable_signals_count', 0)} signals
"""
        
        else:
            return f"""
❌ **NOT UNIVERSAL - แต่ละสัญญานต่างกัน**

**คำตอบ**: ไม่ใช่! แต่ละสัญญานมี patterns ที่แตกต่างกัน

**หลักฐาน**:
- Consistency Score ต่ำ: {verdict.get('overall_consistency_score', 0):.1%}
- เพียง {verdict.get('reliable_signals_percentage', 0):.1f}% ที่มี patterns เชื่อถือได้

**การใช้งาน**:
1. ต้องแยก rules สำหรับแต่ละสัญญาน
2. ไม่ใช้ patterns แบบ one-size-fits-all
3. Focus ที่สัญญานที่มี clear patterns
4. เลี่ยงสัญญานที่ random
"""

    def run_complete_signal_analysis(self):
        """Run complete signal-specific pattern analysis"""
        print("🎯 Starting SIGNAL-SPECIFIC Pattern Analysis...")
        print("🎯 GOAL: ตรวจสอบว่า patterns ใช้ได้กับทุกสัญญานหรือไม่")
        print("=" * 60)
        
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_signal_data():
            return False
        
        # Run analyses
        self.analyze_overall_patterns()
        self.analyze_signal_specific_patterns()
        self.analyze_pattern_consistency()
        self.evaluate_signal_reliability()
        self.generate_final_verdict()
        
        # Save results
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 SIGNAL-SPECIFIC Analysis COMPLETE!")
        print(f"⏱️ Duration: {duration}")
        
        # Show quick verdict
        verdict = self.results.get('final_verdict', {})
        print(f"🎯 VERDICT: {verdict.get('universality', 'Unknown')}")
        print(f"📊 Recommendation: {verdict.get('recommendation', 'Unknown')}")
        print(f"🎲 Confidence: {verdict.get('confidence', 'Unknown')}")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    analyzer = SignalSpecificPatternAnalyzer()
    analyzer.run_complete_signal_analysis()
