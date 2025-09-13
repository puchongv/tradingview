#!/usr/bin/env python3
"""
Aggressive Profit Analysis - วิเคราะห์หาทางทำกำไร 20,000 USD/เดือน
Multi-strategy approach + เพิ่มความถี่การเทรด
"""

import psycopg2
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
import json
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

class AggressiveProfitAnalyzer:
    def __init__(self):
        self.connection = None
        self.data = None
        self.results = {
            'multi_strategy_combinations': [],
            'frequency_analysis': [],
            'scaling_scenarios': [],
            '20k_achievement_plans': []
        }
        
        # Trading parameters
        self.TARGET_MONTHLY = 20000  # USD
        self.CAPITAL = 1000  # USD
        self.BET_SIZE = 250  # USD per trade
        self.WIN_PAYOUT = 0.8  # 80% return
        self.MAX_LOSSES = 4  # แพ้ 4 ไม้ติด = จบเกม
    
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
    
    def load_data(self):
        """Load and prepare data"""
        try:
            print("📊 Loading data...")
            
            query = """
            SELECT 
                id, action, symbol, strategy, entry_time, entry_price,
                result_60min,
                EXTRACT(HOUR FROM entry_time) as hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(DAY FROM entry_time) as day_of_month,
                DATE(entry_time) as trade_date
            FROM tradingviewdata 
            WHERE entry_time IS NOT NULL
              AND result_60min IS NOT NULL
            ORDER BY entry_time;
            """
            
            self.data = pd.read_sql_query(query, self.connection)
            self.data['win_60min'] = (self.data['result_60min'] == 'WIN').astype(int)
            self.data['trade_date'] = pd.to_datetime(self.data['trade_date'])
            
            print(f"✅ Loaded {len(self.data)} records!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def analyze_all_profitable_combinations(self):
        """หาทุก combinations ที่ทำกำไรได้"""
        print("💎 Analyzing ALL profitable combinations...")
        
        profitable_combos = []
        
        # Define all possible good conditions
        conditions = {
            'golden_hours': [21],  # ขยายเป็น [20, 21, 22] ถ้าต้องการ
            'good_days': [2],  # Tuesday, ขยายเป็น [1, 2] ถ้าต้องการ
            'mwp_strategies': ['MWP-30', 'MWP-27', 'MWP-25'],
            'other_strategies': ['Range Filter5', 'Range FRAMA3'],
            'price_levels': []  # จะเพิ่มทีหลัง
        }
        
        # 1. Single condition analysis
        single_conditions = [
            {'name': 'Hour 21 Only', 'filter': lambda df: df['hour'] == 21},
            {'name': 'Hour 20 Only', 'filter': lambda df: df['hour'] == 20},
            {'name': 'Hour 22 Only', 'filter': lambda df: df['hour'] == 22},
            {'name': 'Tuesday Only', 'filter': lambda df: df['day_of_week'] == 2},
            {'name': 'Monday Only', 'filter': lambda df: df['day_of_week'] == 1},
            {'name': 'Wednesday Only', 'filter': lambda df: df['day_of_week'] == 3},
            {'name': 'MWP-30 Only', 'filter': lambda df: df['strategy'] == 'MWP-30'},
            {'name': 'MWP-27 Only', 'filter': lambda df: df['strategy'] == 'MWP-27'},
            {'name': 'MWP-25 Only', 'filter': lambda df: df['strategy'] == 'MWP-25'},
        ]
        
        # 2. Double combination analysis
        double_combinations = [
            {'name': 'Hour 21 + MWP-30', 'filter': lambda df: (df['hour'] == 21) & (df['strategy'] == 'MWP-30')},
            {'name': 'Hour 21 + MWP-27', 'filter': lambda df: (df['hour'] == 21) & (df['strategy'] == 'MWP-27')},
            {'name': 'Hour 21 + MWP-25', 'filter': lambda df: (df['hour'] == 21) & (df['strategy'] == 'MWP-25')},
            {'name': 'Hour 20 + MWP-30', 'filter': lambda df: (df['hour'] == 20) & (df['strategy'] == 'MWP-30')},
            {'name': 'Hour 22 + MWP-30', 'filter': lambda df: (df['hour'] == 22) & (df['strategy'] == 'MWP-30')},
            {'name': 'Tuesday + MWP-30', 'filter': lambda df: (df['day_of_week'] == 2) & (df['strategy'] == 'MWP-30')},
            {'name': 'Tuesday + MWP-27', 'filter': lambda df: (df['day_of_week'] == 2) & (df['strategy'] == 'MWP-27')},
            {'name': 'Tuesday + MWP-25', 'filter': lambda df: (df['day_of_week'] == 2) & (df['strategy'] == 'MWP-25')},
            {'name': 'Monday + MWP-30', 'filter': lambda df: (df['day_of_week'] == 1) & (df['strategy'] == 'MWP-30')},
            {'name': 'Wednesday + MWP-30', 'filter': lambda df: (df['day_of_week'] == 3) & (df['strategy'] == 'MWP-30')},
        ]
        
        # 3. Triple combination analysis  
        triple_combinations = [
            {'name': 'Hour 21 + Tuesday + MWP-30', 'filter': lambda df: (df['hour'] == 21) & (df['day_of_week'] == 2) & (df['strategy'] == 'MWP-30')},
            {'name': 'Hour 20 + Tuesday + MWP-30', 'filter': lambda df: (df['hour'] == 20) & (df['day_of_week'] == 2) & (df['strategy'] == 'MWP-30')},
            {'name': 'Hour 21 + Monday + MWP-30', 'filter': lambda df: (df['hour'] == 21) & (df['day_of_week'] == 1) & (df['strategy'] == 'MWP-30')},
        ]
        
        all_combinations = single_conditions + double_combinations + triple_combinations
        
        # Analyze each combination
        for combo in all_combinations:
            combo_data = self.data[combo['filter'](self.data)]
            
            if len(combo_data) >= 3:  # Minimum sample size
                win_rate = combo_data['win_60min'].mean()
                sample_size = len(combo_data)
                
                # Calculate profitability
                def calculate_profit_metrics(wr, size):
                    # Expected profit per 4 trades
                    expected_wins = 4 * wr
                    expected_losses = 4 * (1 - wr)
                    profit_per_4 = (expected_wins * self.BET_SIZE * self.WIN_PAYOUT) - (expected_losses * self.BET_SIZE)
                    
                    # Survival probability (not losing 4 in a row)
                    survival_prob = 1 - (1 - wr) ** 4
                    
                    # Game over probability 
                    game_over_prob = (1 - wr) ** 4
                    
                    return profit_per_4, survival_prob, game_over_prob
                
                profit_per_4, survival_prob, game_over_prob = calculate_profit_metrics(win_rate, sample_size)
                
                # Only include profitable combinations
                if profit_per_4 > 0 and survival_prob > 0.8:  # Must be profitable and >80% survival
                    profitable_combos.append({
                        'combination': combo['name'],
                        'win_rate': win_rate,
                        'sample_size': sample_size,
                        'profit_per_4_trades': profit_per_4,
                        'survival_probability': survival_prob,
                        'game_over_risk': game_over_prob,
                        'profitability_score': profit_per_4 * survival_prob,  # Combined score
                        'frequency_estimate': self.estimate_monthly_frequency(combo_data)
                    })
        
        self.results['multi_strategy_combinations'] = sorted(profitable_combos, 
                                                           key=lambda x: x['profitability_score'], 
                                                           reverse=True)
    
    def estimate_monthly_frequency(self, combo_data):
        """ประเมินความถี่รายเดือนของแต่ละ combination"""
        if len(combo_data) == 0:
            return 0
        
        # คำนวณจำนวนวันที่มีข้อมูล
        date_range = (combo_data['trade_date'].max() - combo_data['trade_date'].min()).days
        if date_range <= 0:
            return 0
        
        # คำนวณ signals per day
        signals_per_day = len(combo_data) / max(date_range, 1)
        
        # ประเมิน trades per month (30 วัน)
        signals_per_month = signals_per_day * 30
        
        # แปลงเป็นจำนวนรอบ (4 trades per รอบ)
        rounds_per_month = signals_per_month / 4
        
        return {
            'signals_per_month': signals_per_month,
            'rounds_per_month': rounds_per_month,
            'signals_per_day': signals_per_day
        }
    
    def analyze_scaling_scenarios(self):
        """วิเคราะห์ scenarios ต่างๆ เพื่อไปถึงเป้าหมาย 20k"""
        print("🚀 Analyzing scaling scenarios for 20K target...")
        
        scaling_scenarios = []
        top_combos = self.results['multi_strategy_combinations'][:10]  # Top 10 combinations
        
        for combo in top_combos:
            profit_per_4 = combo['profit_per_4_trades']
            frequency = combo['frequency_estimate']
            
            if profit_per_4 > 0 and frequency['rounds_per_month'] > 0:
                # Scenario 1: Use this combo alone
                monthly_profit_single = profit_per_4 * frequency['rounds_per_month']
                rounds_needed_for_20k = self.TARGET_MONTHLY / profit_per_4
                
                # Scenario 2: Scale up bet size
                current_bet_ratio = self.BET_SIZE / self.CAPITAL  # 250/1000 = 0.25
                
                # Different capital scenarios
                capital_scenarios = []
                for capital_multiplier in [2, 3, 4, 5, 10]:  # 2x to 10x capital
                    new_capital = self.CAPITAL * capital_multiplier
                    new_bet_size = self.BET_SIZE * capital_multiplier
                    
                    # Check if still within reasonable risk (max 4 losses = capital gone)
                    if new_bet_size * 4 <= new_capital:
                        scaled_profit_per_4 = profit_per_4 * capital_multiplier
                        scaled_monthly_profit = scaled_profit_per_4 * frequency['rounds_per_month']
                        
                        capital_scenarios.append({
                            'capital_multiplier': capital_multiplier,
                            'required_capital': new_capital,
                            'new_bet_size': new_bet_size,
                            'profit_per_4_trades': scaled_profit_per_4,
                            'monthly_profit_potential': scaled_monthly_profit,
                            'achieves_20k': scaled_monthly_profit >= self.TARGET_MONTHLY
                        })
                
                scaling_scenarios.append({
                    'combination': combo['combination'],
                    'base_stats': {
                        'win_rate': combo['win_rate'],
                        'sample_size': combo['sample_size'],
                        'survival_probability': combo['survival_probability'],
                        'profit_per_4_trades': profit_per_4,
                        'estimated_monthly_rounds': frequency['rounds_per_month'],
                        'base_monthly_profit': monthly_profit_single
                    },
                    'scaling_requirements': {
                        'rounds_needed_for_20k': rounds_needed_for_20k,
                        'frequency_multiplier_needed': rounds_needed_for_20k / frequency['rounds_per_month'] if frequency['rounds_per_month'] > 0 else float('inf')
                    },
                    'capital_scaling_scenarios': capital_scenarios
                })
        
        self.results['scaling_scenarios'] = scaling_scenarios
    
    def create_20k_achievement_plans(self):
        """สร้างแผนการไปถึง 20k USD/เดือน"""
        print("🎯 Creating 20K achievement plans...")
        
        achievement_plans = []
        
        # Plan 1: Multi-strategy approach
        top_combos = self.results['multi_strategy_combinations'][:5]  # Top 5 combinations
        
        multi_strategy_plan = {
            'plan_name': 'Multi-Strategy Combination Plan',
            'description': 'รวมหลาย strategies ที่ดีที่สุด',
            'strategies': [],
            'total_expected_monthly': 0,
            'total_rounds_needed': 0,
            'capital_required': self.CAPITAL
        }
        
        for combo in top_combos:
            if combo['profit_per_4_trades'] > 0:
                strategy_contribution = {
                    'combination': combo['combination'],
                    'monthly_rounds': combo['frequency_estimate']['rounds_per_month'],
                    'profit_per_round': combo['profit_per_4_trades'],
                    'monthly_contribution': combo['profit_per_4_trades'] * combo['frequency_estimate']['rounds_per_month'],
                    'win_rate': combo['win_rate'],
                    'survival_rate': combo['survival_probability']
                }
                
                multi_strategy_plan['strategies'].append(strategy_contribution)
                multi_strategy_plan['total_expected_monthly'] += strategy_contribution['monthly_contribution']
                multi_strategy_plan['total_rounds_needed'] += strategy_contribution['monthly_rounds']
        
        achievement_plans.append(multi_strategy_plan)
        
        # Plan 2: Scale-up single best strategy
        if self.results['scaling_scenarios']:
            best_combo = self.results['scaling_scenarios'][0]
            
            # Find capital scenario that achieves 20K
            best_capital_scenario = None
            for scenario in best_combo['capital_scaling_scenarios']:
                if scenario['achieves_20k'] and scenario['capital_multiplier'] <= 10:  # Reasonable multiplier
                    best_capital_scenario = scenario
                    break
            
            if best_capital_scenario:
                scale_up_plan = {
                    'plan_name': 'Scale-Up Single Strategy Plan',
                    'description': f'Focus บน {best_combo["combination"]} และขยาย capital',
                    'strategy': best_combo['combination'],
                    'base_win_rate': best_combo['base_stats']['win_rate'],
                    'survival_probability': best_combo['base_stats']['survival_probability'],
                    'required_capital': best_capital_scenario['required_capital'],
                    'new_bet_size': best_capital_scenario['new_bet_size'],
                    'expected_monthly_profit': best_capital_scenario['monthly_profit_potential'],
                    'capital_multiplier': best_capital_scenario['capital_multiplier'],
                    'monthly_rounds_needed': best_combo['base_stats']['estimated_monthly_rounds']
                }
                achievement_plans.append(scale_up_plan)
        
        # Plan 3: Aggressive frequency plan
        aggressive_plan = {
            'plan_name': 'Aggressive High-Frequency Plan',
            'description': 'เพิ่มความถี่การเทรดโดยใช้หลาย conditions',
            'approach': 'ขยาย time windows และเพิ่ม strategies',
            'expanded_conditions': [
                'Hours: 20, 21, 22 (แทนแค่ 21)',
                'Days: Monday, Tuesday, Wednesday (แทนแค่ Tuesday)',
                'All MWP strategies + Range strategies',
                'Price level conditions'
            ],
            'frequency_multiplier': 3,  # เป้าหมายเพิ่ม 3 เท่า
            'estimated_monthly_profit': multi_strategy_plan['total_expected_monthly'] * 3,
            'additional_risk': 'เพิ่มความถี่ = เพิ่มความเสี่ยง',
            'capital_required': self.CAPITAL
        }
        achievement_plans.append(aggressive_plan)
        
        self.results['20k_achievement_plans'] = achievement_plans
    
    def save_results(self):
        """Save analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'/Users/puchong/tradingview/report/aggressive_profit_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate report
        report = self.generate_aggressive_report()
        with open(f'/Users/puchong/tradingview/report/AGGRESSIVE_PROFIT_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Aggressive profit analysis saved!")
    
    def generate_aggressive_report(self):
        """Generate comprehensive report for 20K target"""
        return f"""# 💥 AGGRESSIVE PROFIT ANALYSIS
## เป้าหมาย: 20,000 USD/เดือน 

**Current Capital**: {self.CAPITAL} USD  
**Target Monthly**: {self.TARGET_MONTHLY:,} USD  
**Multiplier Required**: {self.TARGET_MONTHLY / self.CAPITAL:.1f}x  

---

## 🏆 **TOP PROFITABLE COMBINATIONS**

{self.format_profitable_combinations()}

---

## 🚀 **SCALING SCENARIOS**

{self.format_scaling_scenarios()}

---

## 🎯 **20K ACHIEVEMENT PLANS**

{self.format_achievement_plans()}

---

## 💡 **EXECUTIVE SUMMARY**

{self.generate_executive_summary()}
"""
    
    def format_profitable_combinations(self):
        if not self.results['multi_strategy_combinations']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for i, combo in enumerate(self.results['multi_strategy_combinations'][:10], 1):
            freq = combo['frequency_estimate']
            profit_emoji = "💎" if combo['profit_per_4_trades'] > 500 else "💰" if combo['profit_per_4_trades'] > 200 else "💵"
            
            output += f"""**{profit_emoji} #{i} {combo['combination']}**
- **Win Rate**: {combo['win_rate']:.1%}
- **Sample Size**: {combo['sample_size']}
- **Profit per 4 trades**: {combo['profit_per_4_trades']:.0f} USD
- **Survival Rate**: {combo['survival_probability']:.1%}
- **Est. Monthly Rounds**: {freq['rounds_per_month']:.1f}
- **Est. Monthly Profit**: {combo['profit_per_4_trades'] * freq['rounds_per_month']:.0f} USD
- **Signals/Day**: {freq['signals_per_day']:.1f}

"""
        return output
    
    def format_scaling_scenarios(self):
        if not self.results['scaling_scenarios']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for scenario in self.results['scaling_scenarios'][:3]:
            output += f"""**{scenario['combination']}**

Base Performance:
- Win Rate: {scenario['base_stats']['win_rate']:.1%}
- Monthly Profit (Base): {scenario['base_stats']['base_monthly_profit']:.0f} USD
- Rounds Needed for 20K: {scenario['scaling_requirements']['rounds_needed_for_20k']:.1f}

Capital Scaling Options:
"""
            for cap_scenario in scenario['capital_scaling_scenarios']:
                if cap_scenario['achieves_20k']:
                    output += f"""  🎯 **{cap_scenario['capital_multiplier']}x Capital Scale:**
  - Required Capital: {cap_scenario['required_capital']:,} USD
  - New Bet Size: {cap_scenario['new_bet_size']} USD
  - Monthly Profit: {cap_scenario['monthly_profit_potential']:.0f} USD ✅
"""
            output += "\n"
        
        return output
    
    def format_achievement_plans(self):
        if not self.results['20k_achievement_plans']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for i, plan in enumerate(self.results['20k_achievement_plans'], 1):
            plan_emoji = "🎯" if i == 1 else "🚀" if i == 2 else "⚡"
            
            output += f"""**{plan_emoji} Plan #{i}: {plan['plan_name']}**
- **Description**: {plan['description']}
"""
            
            if 'strategies' in plan:  # Multi-strategy plan
                output += f"- **Total Expected Monthly**: {plan['total_expected_monthly']:.0f} USD\n"
                output += f"- **Strategies Count**: {len(plan['strategies'])}\n"
                for strategy in plan['strategies'][:3]:  # Top 3 strategies
                    output += f"  - {strategy['combination']}: {strategy['monthly_contribution']:.0f} USD/month\n"
            
            elif 'required_capital' in plan:  # Scale-up plan
                output += f"- **Strategy**: {plan['strategy']}\n"
                output += f"- **Required Capital**: {plan['required_capital']:,} USD\n"
                output += f"- **New Bet Size**: {plan['new_bet_size']} USD\n"
                output += f"- **Expected Monthly**: {plan['expected_monthly_profit']:.0f} USD\n"
            
            elif 'frequency_multiplier' in plan:  # Aggressive plan
                output += f"- **Frequency Multiplier**: {plan['frequency_multiplier']}x\n"
                output += f"- **Estimated Monthly**: {plan['estimated_monthly_profit']:.0f} USD\n"
                output += f"- **Additional Risk**: {plan['additional_risk']}\n"
            
            output += "\n"
        
        return output
    
    def generate_executive_summary(self):
        if not self.results['20k_achievement_plans']:
            return "ไม่สามารถสรุปได้"
        
        # หาแผนที่ดีที่สุด
        best_plan = None
        for plan in self.results['20k_achievement_plans']:
            if 'expected_monthly_profit' in plan and plan['expected_monthly_profit'] >= self.TARGET_MONTHLY:
                best_plan = plan
                break
        
        if best_plan:
            return f"""
🏆 **RECOMMENDED APPROACH**: {best_plan['plan_name']}

**Key Points**:
- เป้าหมาย 20,000 USD/เดือน **ทำได้!**
- แนวทางที่แนะนำ: {best_plan['description']}
- Capital ที่ต้องการ: {best_plan.get('required_capital', self.CAPITAL):,} USD
- Expected Monthly Profit: {best_plan['expected_monthly_profit']:.0f} USD

**Next Steps**:
1. เตรียม capital ตามที่กำหนด
2. ทดสอบ strategy ด้วยเงินจำนวนน้อยก่อน
3. สร้าง automated system สำหรับ monitoring
4. กำหนด strict risk management rules
"""
        else:
            return f"""
⚠️ **CHALLENGE ALERT**: เป้าหมาย 20,000 USD/เดือนยังไม่เป็นไปได้ด้วย current strategies

**ทางเลือก**:
1. เพิ่ม capital มากกว่า 10x (>10,000 USD)
2. หา strategies เพิ่มเติมที่มี win rate สูงกว่า
3. ลดเป้าหมายเป็น 10,000-15,000 USD/เดือน
4. รวม multiple income sources
"""
    
    def run_complete_aggressive_analysis(self):
        """Run complete aggressive profit analysis"""
        print("💥 Starting AGGRESSIVE Profit Analysis...")
        print(f"🎯 TARGET: {self.TARGET_MONTHLY:,} USD/month")
        print("=" * 60)
        
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_data():
            return False
        
        # Run aggressive analyses
        self.analyze_all_profitable_combinations()
        self.analyze_scaling_scenarios()  
        self.create_20k_achievement_plans()
        
        # Save results
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 AGGRESSIVE Analysis COMPLETE!")
        print(f"⏱️ Duration: {duration}")
        print(f"🎯 Goal: Find ways to make {self.TARGET_MONTHLY:,} USD/month")
        print("💡 Result: Multiple strategies and scaling options analyzed")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    analyzer = AggressiveProfitAnalyzer()
    analyzer.run_complete_aggressive_analysis()
