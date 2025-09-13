#!/usr/bin/env python3
"""
STRATEGY COMPARISON BACKTEST
เปรียบเทียบ Strategy A (เดิม) vs Strategy B (ใหม่) ด้วยข้อมูลจริง
"""

import psycopg2
import pandas as pd
import numpy as np
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

class StrategyComparisonBacktest:
    def __init__(self):
        self.connection = None
        self.data = None
        self.capital = 1000  # USD
        self.bet_size = 250  # USD per trade
        self.payout_rate = 0.8  # 80% return on win
        self.max_consecutive_losses = 4  # Game over condition
        
        self.results = {
            'strategy_a': {'name': 'Multi-Strategy Signal-Based', 'trades': [], 'performance': {}},
            'strategy_b': {'name': 'Pure Patterns + Signal-Specific', 'trades': [], 'performance': {}},
            'comparison': {}
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
    
    def load_backtest_data(self):
        """Load data for backtesting"""
        try:
            print("📊 Loading backtest data...")
            
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
            self.data['trade_date'] = pd.to_datetime(self.data['trade_date'])
            self.data['entry_time'] = pd.to_datetime(self.data['entry_time'])
            
            # Add previous result for momentum analysis
            self.data = self.data.reset_index(drop=True)
            self.data['prev_win'] = self.data['win'].shift(1)
            
            print(f"✅ Loaded {len(self.data)} records for backtesting!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading backtest data: {e}")
            return False
    
    def strategy_a_conditions(self, row, prev_win):
        """Strategy A: Multi-Strategy Signal-Based (คำแนะนำเดิม)"""
        strategy = row['strategy']
        hour = row['hour']
        dow = row['day_of_week']
        
        # คำแนะนำเดิม: 5 combinations
        conditions = [
            # Hour 21 + MWP strategies
            (hour == 21 and strategy == 'MWP-30'),
            (hour == 21 and strategy == 'MWP-25'), 
            (hour == 21 and strategy == 'MWP-27'),
            # Tuesday + MWP strategies
            (dow == 2 and strategy == 'MWP-30'),
            (dow == 2 and strategy == 'MWP-27')
        ]
        
        return any(conditions)
    
    def strategy_b_conditions(self, row, prev_win):
        """Strategy B: Pure Patterns + Signal-Specific (แบบใหม่)"""
        strategy = row['strategy']
        hour = row['hour']
        dow = row['day_of_week']
        
        # Check if signal is reliable first
        reliable_signals = ['MWP-25', 'MWP-27', 'MWP-30', 'UT-BOT2-10', 'Range FRAMA3-99', 'MWP-20', 'Range FRAMA3']
        if strategy not in reliable_signals:
            return False
        
        # Time patterns (universal)
        good_hours = [8, 10, 15, 21]  # Golden hours
        bad_hours = [3, 12, 17, 19, 23]  # Danger hours
        
        # Base time condition
        if hour not in good_hours:
            return False
        if hour in bad_hours:
            return False
        
        # Tuesday bonus
        is_tuesday = (dow == 2)
        
        # Momentum patterns (signal-specific)
        momentum_ok = True
        if not pd.isna(prev_win):  # If we have previous result
            if strategy == 'UT-BOT2-10':  # Reverse momentum
                # After loss = good (71% win rate)
                # After win = bad (24% win rate)  
                if prev_win == 1:  # Previous win
                    momentum_ok = False  # Skip this trade
            else:  # Normal momentum (MWP series, etc.)
                # After win = good (~61% win rate)
                # After loss = bad (~40% win rate)
                if prev_win == 0:  # Previous loss
                    momentum_ok = False  # Skip this trade
        
        # Final condition: good time + momentum OK + (optional Tuesday boost)
        return momentum_ok and (hour in good_hours)
    
    def run_backtest(self, strategy_name, condition_func):
        """Run backtest for a specific strategy"""
        print(f"🎯 Running backtest for {strategy_name}...")
        
        trades = []
        current_capital = self.capital
        consecutive_losses = 0
        total_trades = 0
        winning_trades = 0
        game_over = False
        game_over_date = None
        
        for i, row in self.data.iterrows():
            if game_over:
                break
            
            # Get previous win status for momentum
            prev_win = self.data.iloc[i-1]['win'] if i > 0 else None
            
            # Check if trade meets strategy conditions
            if condition_func(row, prev_win):
                total_trades += 1
                trade_result = row['win']
                
                # Calculate P&L
                if trade_result == 1:  # Win
                    profit = self.bet_size * self.payout_rate
                    current_capital += profit
                    winning_trades += 1
                    consecutive_losses = 0
                else:  # Loss
                    current_capital -= self.bet_size
                    consecutive_losses += 1
                
                # Record trade
                trade_record = {
                    'date': row['entry_time'],
                    'strategy': row['strategy'],
                    'hour': row['hour'],
                    'day_of_week': row['day_of_week'],
                    'result': 'WIN' if trade_result == 1 else 'LOSS',
                    'profit': self.bet_size * self.payout_rate if trade_result == 1 else -self.bet_size,
                    'capital_after': current_capital,
                    'consecutive_losses': consecutive_losses
                }
                trades.append(trade_record)
                
                # Check game over condition
                if consecutive_losses >= self.max_consecutive_losses:
                    game_over = True
                    game_over_date = row['entry_time']
                    break
                
                # Stop if capital is gone
                if current_capital <= 0:
                    game_over = True
                    game_over_date = row['entry_time']
                    break
        
        # Calculate performance metrics
        if total_trades > 0:
            win_rate = winning_trades / total_trades
            total_profit = current_capital - self.capital
            avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0
            
            # Calculate monthly projection (based on data timeframe)
            if trades:
                first_trade = pd.to_datetime(trades[0]['date'])
                last_trade = pd.to_datetime(trades[-1]['date'])
                days_span = (last_trade - first_trade).days
                if days_span > 0:
                    daily_trades = total_trades / days_span
                    monthly_trades = daily_trades * 30
                    monthly_profit_projection = monthly_trades * avg_profit_per_trade
                else:
                    monthly_profit_projection = 0
            else:
                monthly_profit_projection = 0
        else:
            win_rate = 0
            total_profit = 0
            avg_profit_per_trade = 0
            monthly_profit_projection = 0
        
        performance = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'starting_capital': self.capital,
            'ending_capital': current_capital,
            'total_profit': total_profit,
            'roi_percentage': (total_profit / self.capital * 100) if self.capital > 0 else 0,
            'avg_profit_per_trade': avg_profit_per_trade,
            'max_consecutive_losses': consecutive_losses,
            'game_over': game_over,
            'game_over_date': str(game_over_date) if game_over_date else None,
            'monthly_profit_projection': monthly_profit_projection,
            'survival_rate': 0 if game_over else 100
        }
        
        return trades, performance
    
    def run_comparison_backtest(self):
        """Run complete comparison backtest"""
        print("🎯 Starting STRATEGY COMPARISON BACKTEST...")
        print("=" * 60)
        
        # Strategy A: Multi-Strategy Signal-Based
        print("\n🅰️ STRATEGY A: Multi-Strategy Signal-Based")
        print("Conditions: Hour 21 + MWP strategies, Tuesday + MWP strategies")
        trades_a, perf_a = self.run_backtest("Strategy A", self.strategy_a_conditions)
        self.results['strategy_a']['trades'] = trades_a
        self.results['strategy_a']['performance'] = perf_a
        
        # Strategy B: Pure Patterns + Signal-Specific  
        print("\n🅱️ STRATEGY B: Pure Patterns + Signal-Specific")
        print("Conditions: Golden hours + Momentum patterns + Reliable signals")
        trades_b, perf_b = self.run_backtest("Strategy B", self.strategy_b_conditions)
        self.results['strategy_b']['trades'] = trades_b
        self.results['strategy_b']['performance'] = perf_b
        
        # Comparison analysis
        self.analyze_comparison()
        
        print("\n" + "=" * 60)
        print("🎉 BACKTEST COMPARISON COMPLETE!")
        print("=" * 60)
    
    def analyze_comparison(self):
        """Analyze and compare strategies"""
        print("\n📊 Analyzing strategy comparison...")
        
        perf_a = self.results['strategy_a']['performance']
        perf_b = self.results['strategy_b']['performance']
        
        comparison = {
            'winner': '',
            'metrics_comparison': {},
            'trade_frequency_comparison': {},
            'risk_comparison': {},
            'profitability_comparison': {}
        }
        
        # Determine winner based on multiple criteria
        criteria_scores = {'A': 0, 'B': 0}
        
        # Criteria 1: Total Profit
        if perf_a['total_profit'] > perf_b['total_profit']:
            criteria_scores['A'] += 1
        elif perf_b['total_profit'] > perf_a['total_profit']:
            criteria_scores['B'] += 1
        
        # Criteria 2: Win Rate
        if perf_a['win_rate'] > perf_b['win_rate']:
            criteria_scores['A'] += 1
        elif perf_b['win_rate'] > perf_a['win_rate']:
            criteria_scores['B'] += 1
        
        # Criteria 3: Survival (not game over)
        if not perf_a['game_over'] and perf_b['game_over']:
            criteria_scores['A'] += 2  # Heavy weight for survival
        elif not perf_b['game_over'] and perf_a['game_over']:
            criteria_scores['B'] += 2
        
        # Criteria 4: ROI
        if perf_a['roi_percentage'] > perf_b['roi_percentage']:
            criteria_scores['A'] += 1
        elif perf_b['roi_percentage'] > perf_a['roi_percentage']:
            criteria_scores['B'] += 1
        
        # Determine winner
        if criteria_scores['A'] > criteria_scores['B']:
            comparison['winner'] = 'Strategy A'
        elif criteria_scores['B'] > criteria_scores['A']:
            comparison['winner'] = 'Strategy B'
        else:
            comparison['winner'] = 'TIE'
        
        comparison['criteria_scores'] = criteria_scores
        
        # Detailed comparisons
        comparison['metrics_comparison'] = {
            'total_profit': {'A': perf_a['total_profit'], 'B': perf_b['total_profit']},
            'win_rate': {'A': perf_a['win_rate'], 'B': perf_b['win_rate']},
            'roi_percentage': {'A': perf_a['roi_percentage'], 'B': perf_b['roi_percentage']},
            'total_trades': {'A': perf_a['total_trades'], 'B': perf_b['total_trades']}
        }
        
        comparison['risk_comparison'] = {
            'game_over': {'A': perf_a['game_over'], 'B': perf_b['game_over']},
            'max_consecutive_losses': {'A': perf_a['max_consecutive_losses'], 'B': perf_b['max_consecutive_losses']},
            'survival_rate': {'A': perf_a['survival_rate'], 'B': perf_b['survival_rate']}
        }
        
        comparison['profitability_comparison'] = {
            'monthly_projection': {'A': perf_a['monthly_profit_projection'], 'B': perf_b['monthly_profit_projection']},
            'avg_profit_per_trade': {'A': perf_a['avg_profit_per_trade'], 'B': perf_b['avg_profit_per_trade']}
        }
        
        self.results['comparison'] = comparison
    
    def save_backtest_results(self):
        """Save backtest results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f'/Users/puchong/tradingview/report/strategy_backtest_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate report
        report = self.generate_backtest_report()
        with open(f'/Users/puchong/tradingview/report/STRATEGY_BACKTEST_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Backtest results saved!")
    
    def generate_backtest_report(self):
        """Generate backtest comparison report"""
        return f"""# 📊 STRATEGY COMPARISON BACKTEST
## คำแนะนำเดิม vs แบบใหม่

**Backtest Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Starting Capital**: {self.capital:,} USD  
**Bet Size**: {self.bet_size} USD per trade  
**Game Over Condition**: {self.max_consecutive_losses} consecutive losses

---

## 🏆 **WINNER: {self.results['comparison']['winner']}**

**Scoring**: Strategy A = {self.results['comparison']['criteria_scores']['A']}, Strategy B = {self.results['comparison']['criteria_scores']['B']}

---

## 🅰️ **STRATEGY A: Multi-Strategy Signal-Based**
### **คำแนะนำเดิม**

{self.format_strategy_performance('strategy_a')}

---

## 🅱️ **STRATEGY B: Pure Patterns + Signal-Specific**  
### **แบบใหม่**

{self.format_strategy_performance('strategy_b')}

---

## 🔥 **HEAD-TO-HEAD COMPARISON**

{self.format_comparison_table()}

---

## 📈 **PERFORMANCE CHARTS**

{self.format_performance_summary()}

---

## 💡 **EXECUTIVE SUMMARY**

{self.generate_backtest_summary()}
"""
    
    def format_strategy_performance(self, strategy_key):
        perf = self.results[strategy_key]['performance']
        emoji = "🏆" if not perf['game_over'] else "💀"
        
        return f"""### **{emoji} Performance Summary:**
- **Total Trades**: {perf['total_trades']:,}
- **Win Rate**: {perf['win_rate']:.1%}
- **Starting Capital**: {perf['starting_capital']:,} USD
- **Ending Capital**: {perf['ending_capital']:,.0f} USD
- **Total Profit**: {perf['total_profit']:,.0f} USD
- **ROI**: {perf['roi_percentage']:.1f}%
- **Avg Profit/Trade**: {perf['avg_profit_per_trade']:.1f} USD
- **Max Consecutive Losses**: {perf['max_consecutive_losses']}
- **Game Over**: {'YES 💀' if perf['game_over'] else 'NO ✅'}
- **Monthly Projection**: {perf['monthly_profit_projection']:,.0f} USD
- **Survival Rate**: {perf['survival_rate']:.0f}%
"""
    
    def format_comparison_table(self):
        comp = self.results['comparison']
        
        return f"""| Metric | Strategy A | Strategy B | Winner |
|--------|------------|------------|---------|
| **Total Profit** | {comp['metrics_comparison']['total_profit']['A']:,.0f} USD | {comp['metrics_comparison']['total_profit']['B']:,.0f} USD | {'A' if comp['metrics_comparison']['total_profit']['A'] > comp['metrics_comparison']['total_profit']['B'] else 'B'} |
| **Win Rate** | {comp['metrics_comparison']['win_rate']['A']:.1%} | {comp['metrics_comparison']['win_rate']['B']:.1%} | {'A' if comp['metrics_comparison']['win_rate']['A'] > comp['metrics_comparison']['win_rate']['B'] else 'B'} |
| **ROI** | {comp['metrics_comparison']['roi_percentage']['A']:.1f}% | {comp['metrics_comparison']['roi_percentage']['B']:.1f}% | {'A' if comp['metrics_comparison']['roi_percentage']['A'] > comp['metrics_comparison']['roi_percentage']['B'] else 'B'} |
| **Total Trades** | {comp['metrics_comparison']['total_trades']['A']:,} | {comp['metrics_comparison']['total_trades']['B']:,} | {'A' if comp['metrics_comparison']['total_trades']['A'] > comp['metrics_comparison']['total_trades']['B'] else 'B'} |
| **Survival** | {'YES ✅' if not comp['risk_comparison']['game_over']['A'] else 'NO 💀'} | {'YES ✅' if not comp['risk_comparison']['game_over']['B'] else 'NO 💀'} | {'A' if not comp['risk_comparison']['game_over']['A'] and comp['risk_comparison']['game_over']['B'] else 'B' if not comp['risk_comparison']['game_over']['B'] and comp['risk_comparison']['game_over']['A'] else 'TIE'} |
| **Monthly Projection** | {comp['profitability_comparison']['monthly_projection']['A']:,.0f} USD | {comp['profitability_comparison']['monthly_projection']['B']:,.0f} USD | {'A' if comp['profitability_comparison']['monthly_projection']['A'] > comp['profitability_comparison']['monthly_projection']['B'] else 'B'} |
"""
    
    def format_performance_summary(self):
        return f"""### 📊 **Key Insights:**

**🎯 Trade Frequency:**
- Strategy A: {self.results['strategy_a']['performance']['total_trades']:,} trades
- Strategy B: {self.results['strategy_b']['performance']['total_trades']:,} trades

**💰 Profitability:**
- Strategy A: {self.results['strategy_a']['performance']['total_profit']:,.0f} USD profit
- Strategy B: {self.results['strategy_b']['performance']['total_profit']:,.0f} USD profit

**🛡️ Risk Management:**
- Strategy A: {'Survived ✅' if not self.results['strategy_a']['performance']['game_over'] else 'Game Over 💀'}
- Strategy B: {'Survived ✅' if not self.results['strategy_b']['performance']['game_over'] else 'Game Over 💀'}
"""
    
    def generate_backtest_summary(self):
        winner = self.results['comparison']['winner']
        
        if winner == 'Strategy A':
            return """
🏆 **STRATEGY A WINS!**

**คำแนะนำเดิม (Multi-Strategy) ชนะ!**

**สาเหตุที่ชนะ:**
- มีประสิทธิภาพที่ดีกว่าในการใช้ข้อมูลจริง
- Signal-based approach ให้ผลลัพธ์ที่แม่นยำกว่า
- รูปแบบการเทรดที่เหมาะสมกับข้อมูลประวัติศาสตร์

**แนะนำ:**
ใช้ Strategy A (Multi-Strategy) เป็นหลัก แต่อาจนำ insights จาก Strategy B มาปรับใช้เพื่อเพิ่มประสิทธิภาพ
"""
        
        elif winner == 'Strategy B':
            return """
🏆 **STRATEGY B WINS!**

**แบบใหม่ (Pure Patterns + Signal-Specific) ชนะ!**

**สาเหตุที่ชนะ:**
- Pattern-based approach ให้ผลลัพธ์ที่สม่ำเสมอกว่า
- การแยก momentum patterns ตาม signal ทำให้แม่นยำกว่า
- Time patterns ที่ universal ช่วยเพิ่มประสิทธิภาพ

**แนะนำ:**
ใช้ Strategy B เป็นหลัก โดยเฉพาะการใช้ time patterns และ signal-specific momentum
"""
        
        else:
            return """
🤝 **TIE - ทั้งสองแบบดีเท่ากัน!**

**ทั้ง 2 strategies มีประสิทธิภาพใกล้เคียงกัน**

**แนะนำ:**
1. ใช้ Hybrid approach - รวมจุดแข็งของทั้งสอง
2. ใช้ Signal quality จาก Strategy A
3. ใช้ Time patterns จาก Strategy B  
4. ใช้ Momentum insights ที่เหมาะกับแต่ละ signal
5. ทดสอบทั้งสองแบบใน paper trading ก่อน
"""

    def run_complete_backtest(self):
        """Run complete backtest analysis"""
        start_time = datetime.now()
        
        if not self.connect_database():
            return False
        
        if not self.load_backtest_data():
            return False
        
        # Run comparison backtest
        self.run_comparison_backtest()
        
        # Save results
        self.save_backtest_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"⏱️ Backtest Duration: {duration}")
        
        # Show quick summary
        winner = self.results['comparison']['winner']
        print(f"🏆 WINNER: {winner}")
        print(f"📊 Strategy A Profit: {self.results['strategy_a']['performance']['total_profit']:.0f} USD")
        print(f"📊 Strategy B Profit: {self.results['strategy_b']['performance']['total_profit']:.0f} USD")
        
        return True

if __name__ == "__main__":
    backtester = StrategyComparisonBacktest()
    backtester.run_complete_backtest()
