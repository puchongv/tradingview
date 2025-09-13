#!/usr/bin/env python3
"""
Survival Analysis for Binary Options Trading
คำนวณโอกาสในการรอด (ไม่แพ้ 4 ไม้ติด) และโอกาสทำกำไร
Focus: ลดโอกาสแพ้ 4 ไม้ติด ให้น้อยที่สุด
"""

import psycopg2
import pandas as pd
import numpy as np
import math
from datetime import datetime
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

class SurvivalAnalyzer:
    def __init__(self):
        self.connection = None
        self.data = None
        self.results = {
            'survival_scenarios': [],
            'consecutive_loss_analysis': [],
            'optimal_strategies': [],
            'profit_calculations': []
        }
        
        # Trading parameters
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
                EXTRACT(DOW FROM entry_time) as day_of_week
            FROM tradingviewdata 
            WHERE entry_time IS NOT NULL
              AND result_60min IS NOT NULL
            ORDER BY entry_time;
            """
            
            self.data = pd.read_sql_query(query, self.connection)
            self.data['win_60min'] = (self.data['result_60min'] == 'WIN').astype(int)
            
            print(f"✅ Loaded {len(self.data)} records!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def analyze_consecutive_losses(self):
        """วิเคราะห์การแพ้ติดกัน - สำคัญที่สุด!"""
        print("💀 Analyzing consecutive losses (MOST IMPORTANT!)...")
        
        consecutive_analysis = []
        
        # Overall consecutive losses
        self.data = self.data.sort_values('entry_time').reset_index(drop=True)
        
        # Calculate consecutive losses
        loss_streaks = []
        current_streak = 0
        
        for i, row in self.data.iterrows():
            if row['win_60min'] == 0:  # Loss
                current_streak += 1
            else:  # Win
                if current_streak > 0:
                    loss_streaks.append(current_streak)
                current_streak = 0
        
        # Add final streak if it exists
        if current_streak > 0:
            loss_streaks.append(current_streak)
        
        # Analyze loss streaks
        total_loss_streaks = len(loss_streaks)
        deadly_streaks = sum(1 for streak in loss_streaks if streak >= 4)  # 4+ consecutive losses = game over
        max_loss_streak = max(loss_streaks) if loss_streaks else 0
        
        consecutive_analysis.append({
            'scenario': 'Overall Trading',
            'total_trades': len(self.data),
            'win_rate': self.data['win_60min'].mean(),
            'total_loss_streaks': total_loss_streaks,
            'deadly_streaks_4plus': deadly_streaks,
            'max_consecutive_losses': max_loss_streak,
            'survival_rate': 1 - (deadly_streaks / total_loss_streaks) if total_loss_streaks > 0 else 1,
            'loss_streak_distribution': {
                '1_loss': sum(1 for s in loss_streaks if s == 1),
                '2_consecutive': sum(1 for s in loss_streaks if s == 2),
                '3_consecutive': sum(1 for s in loss_streaks if s == 3),
                '4_consecutive': sum(1 for s in loss_streaks if s == 4),
                '5plus_consecutive': sum(1 for s in loss_streaks if s >= 5)
            }
        })
        
        # Analyze by best patterns
        patterns_to_analyze = [
            {'name': 'Golden Hour 21', 'filter': lambda df: df['hour'] == 21},
            {'name': 'Tuesday', 'filter': lambda df: df['day_of_week'] == 2},
            {'name': 'MWP-30 Strategy', 'filter': lambda df: df['strategy'] == 'MWP-30'},
            {'name': 'Golden Hour + Tuesday', 'filter': lambda df: (df['hour'] == 21) & (df['day_of_week'] == 2)}
        ]
        
        for pattern in patterns_to_analyze:
            pattern_data = self.data[pattern['filter'](self.data)].copy()
            if len(pattern_data) >= 20:  # Minimum sample size
                
                # Calculate consecutive losses for this pattern
                pattern_loss_streaks = []
                current_streak = 0
                
                for i, row in pattern_data.iterrows():
                    if row['win_60min'] == 0:  # Loss
                        current_streak += 1
                    else:  # Win
                        if current_streak > 0:
                            pattern_loss_streaks.append(current_streak)
                        current_streak = 0
                
                if current_streak > 0:
                    pattern_loss_streaks.append(current_streak)
                
                # Analyze pattern loss streaks
                pattern_deadly = sum(1 for streak in pattern_loss_streaks if streak >= 4)
                pattern_max_loss = max(pattern_loss_streaks) if pattern_loss_streaks else 0
                
                consecutive_analysis.append({
                    'scenario': pattern['name'],
                    'total_trades': len(pattern_data),
                    'win_rate': pattern_data['win_60min'].mean(),
                    'total_loss_streaks': len(pattern_loss_streaks),
                    'deadly_streaks_4plus': pattern_deadly,
                    'max_consecutive_losses': pattern_max_loss,
                    'survival_rate': 1 - (pattern_deadly / len(pattern_loss_streaks)) if len(pattern_loss_streaks) > 0 else 1,
                    'loss_streak_distribution': {
                        '1_loss': sum(1 for s in pattern_loss_streaks if s == 1),
                        '2_consecutive': sum(1 for s in pattern_loss_streaks if s == 2),
                        '3_consecutive': sum(1 for s in pattern_loss_streaks if s == 3),
                        '4_consecutive': sum(1 for s in pattern_loss_streaks if s == 4),
                        '5plus_consecutive': sum(1 for s in pattern_loss_streaks if s >= 5)
                    }
                })
        
        self.results['consecutive_loss_analysis'] = sorted(consecutive_analysis, 
                                                          key=lambda x: x['survival_rate'], 
                                                          reverse=True)
    
    def calculate_survival_scenarios(self):
        """คำนวณ scenario ต่างๆ สำหรับการรอด"""
        print("🛡️ Calculating survival scenarios...")
        
        survival_scenarios = []
        
        # สำหรับแต่ละ pattern ที่ดีที่สุด
        top_patterns = self.results['consecutive_loss_analysis'][:4]  # Top 4 patterns
        
        for pattern in top_patterns:
            win_rate = pattern['win_rate']
            
            # คำนวณโอกาสแพ้ 4 ไม้ติด
            prob_4_consecutive_losses = (1 - win_rate) ** 4
            
            # คำนวณโอกาสชนะ 2 ไม้ใน 4 ไม้
            def comb(n, k):
                return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
            
            prob_win_2_in_4 = sum(
                comb(4, k) * (win_rate ** k) * ((1 - win_rate) ** (4 - k))
                for k in range(2, 5)  # Win 2, 3, or 4 out of 4
            )
            
            # คำนวณกำไรเฉลี่ย
            expected_wins_in_4 = 4 * win_rate
            expected_losses_in_4 = 4 * (1 - win_rate)
            expected_profit = (expected_wins_in_4 * self.BET_SIZE * self.WIN_PAYOUT) - (expected_losses_in_4 * self.BET_SIZE)
            
            survival_scenarios.append({
                'scenario': pattern['scenario'],
                'win_rate': win_rate,
                'sample_size': pattern['total_trades'],
                'prob_survive_4_trades': 1 - prob_4_consecutive_losses,
                'prob_profit_2plus_wins': prob_win_2_in_4,
                'prob_game_over': prob_4_consecutive_losses,
                'expected_profit_per_4trades': expected_profit,
                'survival_rating': pattern['survival_rate']
            })
        
        self.results['survival_scenarios'] = sorted(survival_scenarios, 
                                                   key=lambda x: x['prob_survive_4_trades'], 
                                                   reverse=True)
    
    def find_optimal_strategies(self):
        """หา strategy ที่ดีที่สุดสำหรับเป้าหมาย"""
        print("🎯 Finding optimal strategies...")
        
        optimal_strategies = []
        
        # เงื่อนไขที่ดีที่สุด
        best_conditions = []
        
        # 1. เงื่อนไขรวม: Golden Hour + Tuesday + MWP-30
        combined_filter = (self.data['hour'] == 21) & (self.data['day_of_week'] == 2) & (self.data['strategy'] == 'MWP-30')
        combined_data = self.data[combined_filter]
        
        if len(combined_data) >= 5:
            best_conditions.append({
                'name': 'ULTIMATE: Hour 21 + Tuesday + MWP-30',
                'data': combined_data,
                'description': 'เงื่อนไขรวมที่ดีที่สุด'
            })
        
        # 2. Golden Hour เฉพาะ MWP strategies
        for strategy in ['MWP-30', 'MWP-27', 'MWP-25']:
            golden_strategy = self.data[(self.data['hour'] == 21) & (self.data['strategy'] == strategy)]
            if len(golden_strategy) >= 10:
                best_conditions.append({
                    'name': f'Golden Hour + {strategy}',
                    'data': golden_strategy,
                    'description': f'ช่วงเวลา 21:xx กับ {strategy}'
                })
        
        # 3. Tuesday เฉพาะ MWP strategies
        for strategy in ['MWP-30', 'MWP-27', 'MWP-25']:
            tuesday_strategy = self.data[(self.data['day_of_week'] == 2) & (self.data['strategy'] == strategy)]
            if len(tuesday_strategy) >= 10:
                best_conditions.append({
                    'name': f'Tuesday + {strategy}',
                    'data': tuesday_strategy,
                    'description': f'วันอังคาร กับ {strategy}'
                })
        
        # วิเคราะห์แต่ละเงื่อนไข
        for condition in best_conditions:
            data = condition['data']
            win_rate = data['win_60min'].mean()
            
            # คำนวณความปลอดภัย
            prob_4_losses = (1 - win_rate) ** 4
            prob_survive = 1 - prob_4_losses
            
            # คำนวณกำไร
            prob_win_2_in_4 = sum(
                math.factorial(4) / (math.factorial(k) * math.factorial(4-k)) * 
                (win_rate ** k) * ((1 - win_rate) ** (4-k))
                for k in range(2, 5)
            )
            
            optimal_strategies.append({
                'strategy_name': condition['name'],
                'description': condition['description'],
                'win_rate': win_rate,
                'sample_size': len(data),
                'survival_probability': prob_survive,
                'profit_probability': prob_win_2_in_4,
                'game_over_probability': prob_4_losses,
                'recommendation': 'Highly Recommended' if win_rate > 0.65 else 'Recommended' if win_rate > 0.55 else 'Risky'
            })
        
        self.results['optimal_strategies'] = sorted(optimal_strategies, 
                                                   key=lambda x: x['survival_probability'], 
                                                   reverse=True)
    
    def calculate_profit_scenarios(self):
        """คำนวณ scenario กำไรจริง"""
        print("💰 Calculating real profit scenarios...")
        
        profit_scenarios = []
        
        for strategy in self.results['optimal_strategies'][:3]:  # Top 3 strategies
            win_rate = strategy['win_rate']
            
            # Scenario: เล่น 4 ไม้
            scenarios = {
                'win_4': win_rate ** 4,
                'win_3': 4 * (win_rate ** 3) * (1 - win_rate),
                'win_2': 6 * (win_rate ** 2) * ((1 - win_rate) ** 2),
                'win_1': 4 * win_rate * ((1 - win_rate) ** 3),
                'win_0': (1 - win_rate) ** 4  # Game Over
            }
            
            # คำนวณกำไร/ขาดทุนแต่ละ scenario
            profits = {
                'win_4': 4 * self.BET_SIZE * self.WIN_PAYOUT,  # 800 USD
                'win_3': (3 * self.BET_SIZE * self.WIN_PAYOUT) - self.BET_SIZE,  # 600 - 250 = 350 USD
                'win_2': (2 * self.BET_SIZE * self.WIN_PAYOUT) - (2 * self.BET_SIZE),  # 400 - 500 = -100 USD
                'win_1': (1 * self.BET_SIZE * self.WIN_PAYOUT) - (3 * self.BET_SIZE),  # 200 - 750 = -550 USD
                'win_0': -4 * self.BET_SIZE  # -1000 USD (Game Over)
            }
            
            # Expected profit
            expected_profit = sum(scenarios[k] * profits[k] for k in scenarios.keys())
            
            # Probability of profit (win 2+ games)
            prob_profit = scenarios['win_4'] + scenarios['win_3'] + scenarios['win_2']
            
            profit_scenarios.append({
                'strategy': strategy['strategy_name'],
                'win_rate': win_rate,
                'scenarios': scenarios,
                'profits': profits,
                'expected_profit': expected_profit,
                'probability_of_profit': prob_profit,
                'probability_of_game_over': scenarios['win_0'],
                'breakeven_needed': 2  # ต้องชนะอย่างน้อย 2 ไม้
            })
        
        self.results['profit_calculations'] = profit_scenarios
    
    def save_results(self):
        """Save analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'/Users/puchong/tradingview/report/survival_analysis_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate report
        report = self.generate_survival_report()
        with open(f'/Users/puchong/tradingview/report/SURVIVAL_ANALYSIS_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Survival analysis results saved!")
    
    def generate_survival_report(self):
        """Generate comprehensive survival report"""
        return f"""# 🛡️ Survival Analysis Report
## การวิเคราะห์การรอด: หลีกเลี่ยงการแพ้ 4 ไม้ติด

**Capital**: {self.CAPITAL} USD  
**Bet Size**: {self.BET_SIZE} USD/trade  
**Game Over**: แพ้ 4 ไม้ติด = เงินหมด  
**Target**: ชนะ 2 ไม้ = กำไร 400 USD  

---

## 💀 **การวิเคราะห์การแพ้ติดกัน (CRITICAL)**

{self.format_consecutive_loss_analysis()}

---

## 🛡️ **Survival Scenarios**

{self.format_survival_scenarios()}

---

## 🎯 **Optimal Strategies (เรียงตามความปลอดภัย)**

{self.format_optimal_strategies()}

---

## 💰 **Profit Scenarios (เล่น 4 ไม้)**

{self.format_profit_scenarios()}

---

## 🔥 **คำแนะนำสุดท้าย**

### **🏆 Strategy ที่แนะนำ:**
{self.get_final_recommendation()}

### **⚠️ ข้อควรระวัง:**
- แม้ว่า win rate จะสูง แต่ยังมีโอกาสแพ้ 4 ไม้ติด
- ควรมี backup plan หากเกิด worst case scenario
- อย่าลืมว่า binary options มี inherent risk สูง

---

**สรุป: Focus ที่การ "รอด" มากกว่าการ "ทำกำไรสูงสุด"**
"""

    def format_consecutive_loss_analysis(self):
        if not self.results['consecutive_loss_analysis']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for analysis in self.results['consecutive_loss_analysis'][:5]:
            deadly_rate = (analysis['deadly_streaks_4plus'] / analysis['total_loss_streaks'] * 100) if analysis['total_loss_streaks'] > 0 else 0
            
            output += f"""**{analysis['scenario']}**:
- **Win Rate**: {analysis['win_rate']:.1%}
- **Total Loss Streaks**: {analysis['total_loss_streaks']}
- **Deadly Streaks (4+)**: {analysis['deadly_streaks_4plus']} ({deadly_rate:.1f}%)
- **Max Consecutive Losses**: {analysis['max_consecutive_losses']}
- **Survival Rate**: {analysis['survival_rate']:.1%}

Loss Distribution:
- 1 loss: {analysis['loss_streak_distribution']['1_loss']}
- 2 consecutive: {analysis['loss_streak_distribution']['2_consecutive']}  
- 3 consecutive: {analysis['loss_streak_distribution']['3_consecutive']}
- 4 consecutive (DEADLY): {analysis['loss_streak_distribution']['4_consecutive']}
- 5+ consecutive (GAME OVER): {analysis['loss_streak_distribution']['5plus_consecutive']}

"""
        return output
    
    def format_survival_scenarios(self):
        if not self.results['survival_scenarios']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for scenario in self.results['survival_scenarios']:
            output += f"""**{scenario['scenario']}**:
- **Survival Rate (4 trades)**: {scenario['prob_survive_4_trades']:.1%}
- **Profit Probability (2+ wins)**: {scenario['prob_profit_2plus_wins']:.1%}
- **Game Over Probability**: {scenario['prob_game_over']:.1%}
- **Expected Profit/4 trades**: {scenario['expected_profit_per_4trades']:.0f} USD
- **Sample Size**: {scenario['sample_size']} trades

"""
        return output
    
    def format_optimal_strategies(self):
        if not self.results['optimal_strategies']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for i, strategy in enumerate(self.results['optimal_strategies'], 1):
            safety_emoji = "🟢" if strategy['survival_probability'] > 0.9 else "🟡" if strategy['survival_probability'] > 0.8 else "🔴"
            
            output += f"""**{safety_emoji} #{i} {strategy['strategy_name']}**
- **Description**: {strategy['description']}
- **Win Rate**: {strategy['win_rate']:.1%}
- **Survival Probability**: {strategy['survival_probability']:.1%}
- **Profit Probability**: {strategy['profit_probability']:.1%}
- **Game Over Risk**: {strategy['game_over_probability']:.1%}
- **Recommendation**: {strategy['recommendation']}
- **Sample Size**: {strategy['sample_size']} trades

"""
        return output
    
    def format_profit_scenarios(self):
        if not self.results['profit_calculations']:
            return "ไม่มีข้อมูล"
        
        output = ""
        for calc in self.results['profit_calculations']:
            output += f"""**{calc['strategy']}** (Win Rate: {calc['win_rate']:.1%}):

Scenario Probabilities:
- Win 4/4: {calc['scenarios']['win_4']:.1%} → Profit: {calc['profits']['win_4']:.0f} USD
- Win 3/4: {calc['scenarios']['win_3']:.1%} → Profit: {calc['profits']['win_3']:.0f} USD  
- Win 2/4: {calc['scenarios']['win_2']:.1%} → Loss: {calc['profits']['win_2']:.0f} USD
- Win 1/4: {calc['scenarios']['win_1']:.1%} → Loss: {calc['profits']['win_1']:.0f} USD
- Win 0/4: {calc['scenarios']['win_0']:.1%} → **GAME OVER**: {calc['profits']['win_0']:.0f} USD

**Expected Profit**: {calc['expected_profit']:.0f} USD
**Profit Probability**: {calc['probability_of_profit']:.1%}
**Game Over Risk**: {calc['probability_of_game_over']:.1%}

"""
        return output
    
    def get_final_recommendation(self):
        if not self.results['optimal_strategies']:
            return "ไม่สามารถให้คำแนะนำได้"
        
        best_strategy = self.results['optimal_strategies'][0]
        
        if best_strategy['survival_probability'] > 0.9:
            safety_level = "ปลอดภัยสูง"
        elif best_strategy['survival_probability'] > 0.8:
            safety_level = "ปลอดภัยปานกลาง" 
        else:
            safety_level = "มีความเสี่ยง"
        
        return f"""
**🥇 อันดับ 1: {best_strategy['strategy_name']}**
- **Win Rate**: {best_strategy['win_rate']:.1%}
- **Survival Rate**: {best_strategy['survival_probability']:.1%}
- **Safety Level**: {safety_level}

**วิธีใช้**:
- เทรดเฉพาะเมื่อตรงกับเงื่อนไขนี้เท่านั้น
- ใช้ bet size {self.BET_SIZE} USD
- หยุดเมื่อชนะ 2 ไม้ (กำไร 400 USD)
- หยุดเมื่อแพ้ 3 ไม้ติด (เหลือเงิน 250 USD สำหรับ comeback)
"""
    
    def run_complete_survival_analysis(self):
        """Run complete survival analysis"""
        print("🛡️ Starting Survival Analysis...")
        print("=" * 60)
        
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_data():
            return False
        
        # Run survival analyses
        self.analyze_consecutive_losses()
        self.calculate_survival_scenarios()
        self.find_optimal_strategies()
        self.calculate_profit_scenarios()
        
        # Save results
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 Survival Analysis COMPLETE!")
        print(f"⏱️ Duration: {duration}")
        print(f"📊 Focus: ลดโอกาสแพ้ 4 ไม้ติด ให้น้อยที่สุด")
        print("💡 Key Goal: รอดให้นานที่สุด + ทำกำไร 400 USD")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    analyzer = SurvivalAnalyzer()
    analyzer.run_complete_survival_analysis()
