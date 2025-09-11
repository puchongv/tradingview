#!/usr/bin/env python3
"""
Binary Options Prediction Engine
ระบบทำนาย strategy ที่ดีที่สุดสำหรับ Binary Options
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BinaryOptionsPredictor:
    def __init__(self, csv_file):
        """เริ่มต้นระบบทำนาย"""
        self.csv_file = csv_file
        self.df = None
        self.patterns = {}
        self.indicators = {}
        self.load_data()
        self.analyze_patterns()
    
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
            
            # เพิ่มคอลัมน์สำหรับการวิเคราะห์
            self.df['hour'] = self.df['entry_time'].dt.hour
            self.df['day_of_week'] = self.df['entry_time'].dt.day_name()
            self.df['date'] = self.df['entry_time'].dt.date
            self.df['minute'] = self.df['entry_time'].dt.minute
            
            print("แปลงข้อมูลเวลาเสร็จสิ้น")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    
    def analyze_patterns(self):
        """วิเคราะห์ pattern และ indicators"""
        print("\nกำลังวิเคราะห์ patterns...")
        
        timeframes = ['10min', '30min', '60min']
        
        for tf in timeframes:
            result_col = f'result_{tf}'
            if result_col in self.df.columns:
                print(f"\nวิเคราะห์ {tf}...")
                
                # วิเคราะห์ pattern ตามเงื่อนไขต่างๆ
                self.patterns[tf] = self._analyze_timeframe_patterns(tf)
                self.indicators[tf] = self._extract_indicators(tf)
    
    def _analyze_timeframe_patterns(self, timeframe):
        """วิเคราะห์ pattern สำหรับแต่ละ timeframe"""
        result_col = f'result_{timeframe}'
        valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
        
        patterns = {
            'strategy_performance': {},
            'time_patterns': {},
            'action_patterns': {},
            'price_patterns': {},
            'winning_conditions': {},
            'losing_conditions': {}
        }
        
        # 1. วิเคราะห์ performance ของแต่ละ strategy
        strategy_perf = valid_data.groupby('strategy').agg({
            result_col: ['count', lambda x: (x == 'WIN').sum()]
        }).round(2)
        strategy_perf.columns = ['total_trades', 'wins']
        strategy_perf['win_rate'] = (strategy_perf['wins'] / strategy_perf['total_trades'] * 100).round(2)
        strategy_perf['risk_score'] = self._calculate_risk_score(valid_data, 'strategy', result_col)
        patterns['strategy_performance'] = strategy_perf.to_dict('index')
        
        # 2. วิเคราะห์ pattern ตามเวลา
        hourly_perf = valid_data.groupby('hour').agg({
            result_col: ['count', lambda x: (x == 'WIN').sum()]
        }).round(2)
        hourly_perf.columns = ['total_trades', 'wins']
        hourly_perf['win_rate'] = (hourly_perf['wins'] / hourly_perf['total_trades'] * 100).round(2)
        patterns['time_patterns']['hourly'] = hourly_perf.to_dict('index')
        
        # 3. วิเคราะห์ pattern ตาม action
        action_perf = valid_data.groupby('action').agg({
            result_col: ['count', lambda x: (x == 'WIN').sum()]
        }).round(2)
        action_perf.columns = ['total_trades', 'wins']
        action_perf['win_rate'] = (action_perf['wins'] / action_perf['total_trades'] * 100).round(2)
        patterns['action_patterns'] = action_perf.to_dict('index')
        
        # 4. วิเคราะห์ price patterns
        if timeframe == '10min' and 'price_10min' in valid_data.columns:
            price_patterns = self._analyze_price_patterns(valid_data, 'price_10min', result_col)
            patterns['price_patterns'] = price_patterns
        
        # 5. หา winning conditions
        winning_conditions = self._find_winning_conditions(valid_data, result_col)
        patterns['winning_conditions'] = winning_conditions
        
        # 6. หา losing conditions
        losing_conditions = self._find_losing_conditions(valid_data, result_col)
        patterns['losing_conditions'] = losing_conditions
        
        return patterns
    
    def _calculate_risk_score(self, data, group_col, result_col):
        """คำนวณ risk score สำหรับแต่ละ group"""
        risk_scores = {}
        
        for group in data[group_col].unique():
            group_data = data[data[group_col] == group].sort_values('entry_time')
            
            # คำนวณ lost streak
            group_data['is_loss'] = (group_data[result_col] == 'LOSE').astype(int)
            group_data['streak_group'] = (group_data['is_loss'] != group_data['is_loss'].shift()).cumsum()
            
            loss_streaks = group_data[group_data['is_loss'] == 1].groupby('streak_group')['is_loss'].count()
            max_streak = loss_streaks.max() if len(loss_streaks) > 0 else 0
            avg_streak = loss_streaks.mean() if len(loss_streaks) > 0 else 0
            
            # คำนวณ risk score (0-100, ยิ่งต่ำยิ่งเสี่ยงน้อย)
            risk_score = min(100, (max_streak * 5) + (avg_streak * 2))
            risk_scores[group] = round(risk_score, 2)
        
        return risk_scores
    
    def _analyze_price_patterns(self, data, price_col, result_col):
        """วิเคราะห์ price patterns"""
        if price_col not in data.columns or 'entry_price' not in data.columns:
            return {}
        
        data['price_change'] = ((data[price_col] - data['entry_price']) / data['entry_price'] * 100)
        
        # แบ่ง price movement เป็น ranges
        price_ranges = [
            (-np.inf, -0.1, "Strong Down"),
            (-0.1, -0.05, "Down"),
            (-0.05, 0.05, "Sideways"),
            (0.05, 0.1, "Up"),
            (0.1, np.inf, "Strong Up")
        ]
        
        patterns = {}
        for min_val, max_val, label in price_ranges:
            range_data = data[(data['price_change'] >= min_val) & (data['price_change'] < max_val)]
            if len(range_data) > 0:
                wins = len(range_data[range_data[result_col] == 'WIN'])
                total = len(range_data)
                win_rate = wins / total * 100 if total > 0 else 0
                patterns[label] = {
                    'win_rate': round(win_rate, 2),
                    'total_trades': total,
                    'wins': wins
                }
        
        return patterns
    
    def _find_winning_conditions(self, data, result_col):
        """หาเงื่อนไขที่ทำให้ชนะ"""
        winning_data = data[data[result_col] == 'WIN']
        
        # หา combination ที่ชนะบ่อย
        combinations = winning_data.groupby(['strategy', 'action', 'hour']).size().reset_index(name='wins')
        total_combinations = data.groupby(['strategy', 'action', 'hour']).size().reset_index(name='total')
        
        combo_analysis = pd.merge(combinations, total_combinations, on=['strategy', 'action', 'hour'])
        combo_analysis['win_rate'] = (combo_analysis['wins'] / combo_analysis['total'] * 100).round(2)
        combo_analysis = combo_analysis[combo_analysis['total'] >= 3].sort_values('win_rate', ascending=False)
        
        return combo_analysis.head(20).to_dict('records')
    
    def _find_losing_conditions(self, data, result_col):
        """หาเงื่อนไขที่ทำให้แพ้"""
        losing_data = data[data[result_col] == 'LOSE']
        
        # หา combination ที่แพ้บ่อย
        combinations = losing_data.groupby(['strategy', 'action', 'hour']).size().reset_index(name='losses')
        total_combinations = data.groupby(['strategy', 'action', 'hour']).size().reset_index(name='total')
        
        combo_analysis = pd.merge(combinations, total_combinations, on=['strategy', 'action', 'hour'])
        combo_analysis['loss_rate'] = (combo_analysis['losses'] / combo_analysis['total'] * 100).round(2)
        combo_analysis = combo_analysis[combo_analysis['total'] >= 3].sort_values('loss_rate', ascending=False)
        
        return combo_analysis.head(20).to_dict('records')
    
    def _extract_indicators(self, timeframe):
        """สกัด indicators ที่สำคัญ"""
        result_col = f'result_{timeframe}'
        valid_data = self.df[self.df[result_col].notna() & (self.df[result_col] != '')].copy()
        
        indicators = {
            'high_win_rate_strategies': [],
            'low_risk_strategies': [],
            'best_time_slots': [],
            'best_combinations': [],
            'avoid_conditions': []
        }
        
        # 1. หา strategy ที่มี win rate สูงและเสี่ยงต่ำ
        strategy_perf = valid_data.groupby('strategy').agg({
            result_col: ['count', lambda x: (x == 'WIN').sum()]
        }).round(2)
        strategy_perf.columns = ['total_trades', 'wins']
        strategy_perf['win_rate'] = (strategy_perf['wins'] / strategy_perf['total_trades'] * 100).round(2)
        strategy_perf = strategy_perf[strategy_perf['total_trades'] >= 20]
        
        # คำนวณ risk score
        risk_scores = self._calculate_risk_score(valid_data, 'strategy', result_col)
        strategy_perf['risk_score'] = strategy_perf.index.map(risk_scores)
        
        # หา strategy ที่ดี (win rate > 55% และ risk score < 30)
        good_strategies = strategy_perf[
            (strategy_perf['win_rate'] >= 55) & 
            (strategy_perf['risk_score'] <= 30)
        ].sort_values(['win_rate', 'risk_score'], ascending=[False, True])
        
        indicators['high_win_rate_strategies'] = good_strategies.head(5).to_dict('index')
        
        # 2. หา time slot ที่ดีที่สุด
        hourly_perf = valid_data.groupby('hour').agg({
            result_col: ['count', lambda x: (x == 'WIN').sum()]
        }).round(2)
        hourly_perf.columns = ['total_trades', 'wins']
        hourly_perf['win_rate'] = (hourly_perf['wins'] / hourly_perf['total_trades'] * 100).round(2)
        hourly_perf = hourly_perf[hourly_perf['total_trades'] >= 10].sort_values('win_rate', ascending=False)
        
        indicators['best_time_slots'] = hourly_perf.head(5).to_dict('index')
        
        # 3. หา combination ที่ดีที่สุด
        winning_conditions = self._find_winning_conditions(valid_data, result_col)
        indicators['best_combinations'] = winning_conditions[:10]
        
        # 4. หาเงื่อนไขที่ควรหลีกเลี่ยง
        losing_conditions = self._find_losing_conditions(valid_data, result_col)
        indicators['avoid_conditions'] = losing_conditions[:10]
        
        return indicators
    
    def predict_best_strategy(self, current_time=None, timeframe='10min'):
        """ทำนาย strategy ที่ดีที่สุดสำหรับเวลาปัจจุบัน"""
        if current_time is None:
            current_time = datetime.now()
        
        current_hour = current_time.hour
        
        print(f"\n{'='*60}")
        print(f"ทำนาย Strategy ที่ดีที่สุด - {timeframe.upper()}")
        print(f"เวลาปัจจุบัน: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        if timeframe not in self.indicators:
            print(f"ไม่พบข้อมูลสำหรับ {timeframe}")
            return None
        
        indicators = self.indicators[timeframe]
        
        # 1. ตรวจสอบ strategy ที่ดี
        print(f"\nกลยุทธ์ที่แนะนำ ({timeframe}):")
        if indicators['high_win_rate_strategies']:
            for strategy, data in indicators['high_win_rate_strategies'].items():
                print(f"  {strategy}: {data['win_rate']:.1f}% win rate, Risk: {data['risk_score']:.1f}")
        else:
            print("  ไม่พบกลยุทธ์ที่แนะนำ")
        
        # 2. ตรวจสอบ time slot ปัจจุบัน
        print(f"\nประสิทธิภาพชั่วโมงปัจจุบัน ({current_hour:02d}:00):")
        if str(current_hour) in indicators['best_time_slots']:
            data = indicators['best_time_slots'][str(current_hour)]
            print(f"  Win Rate: {data['win_rate']:.1f}% ({data['wins']:.0f}/{data['total_trades']:.0f})")
        else:
            print("  ข้อมูลไม่เพียงพอสำหรับชั่วโมงนี้")
        
        # 3. แนะนำ combination ที่ดีที่สุด
        print(f"\nCombination ที่แนะนำ ({timeframe}):")
        for i, combo in enumerate(indicators['best_combinations'][:5], 1):
            print(f"  {i}. {combo['strategy']} + {combo['action']} + {combo['hour']:02d}:00 = {combo['win_rate']:.1f}%")
        
        # 4. เงื่อนไขที่ควรหลีกเลี่ยง
        print(f"\nเงื่อนไขที่ควรหลีกเลี่ยง ({timeframe}):")
        for i, combo in enumerate(indicators['avoid_conditions'][:5], 1):
            print(f"  {i}. {combo['strategy']} + {combo['action']} + {combo['hour']:02d}:00 = {combo['loss_rate']:.1f}% loss rate")
        
        # 5. สรุปคำแนะนำ
        print(f"\n{'='*60}")
        print("สรุปคำแนะนำ:")
        
        if indicators['high_win_rate_strategies']:
            best_strategy = list(indicators['high_win_rate_strategies'].keys())[0]
            best_data = indicators['high_win_rate_strategies'][best_strategy]
            print(f"1. ใช้กลยุทธ์: {best_strategy}")
            print(f"   - Win Rate: {best_data['win_rate']:.1f}%")
            print(f"   - Risk Score: {best_data['risk_score']:.1f}")
        
        if str(current_hour) in indicators['best_time_slots']:
            current_data = indicators['best_time_slots'][str(current_hour)]
            if current_data['win_rate'] >= 60:
                print(f"2. เวลาปัจจุบัน ({current_hour:02d}:00) มีประสิทธิภาพดี: {current_data['win_rate']:.1f}%")
            else:
                print(f"2. เวลาปัจจุบัน ({current_hour:02d}:00) มีประสิทธิภาพปานกลาง: {current_data['win_rate']:.1f}%")
        else:
            print("2. เวลาปัจจุบันไม่มีข้อมูลเพียงพอ")
        
        # หา combination ที่เหมาะกับเวลาปัจจุบัน
        current_combinations = [combo for combo in indicators['best_combinations'] if combo['hour'] == current_hour]
        if current_combinations:
            best_combo = current_combinations[0]
            print(f"3. Combination ที่เหมาะกับเวลานี้: {best_combo['strategy']} + {best_combo['action']} = {best_combo['win_rate']:.1f}%")
        else:
            print("3. ไม่พบ combination ที่เหมาะกับเวลานี้")
        
        return {
            'recommended_strategy': best_strategy if indicators['high_win_rate_strategies'] else None,
            'current_hour_performance': indicators['best_time_slots'].get(str(current_hour), {}),
            'best_combinations': indicators['best_combinations'][:5],
            'avoid_conditions': indicators['avoid_conditions'][:5]
        }
    
    def get_risk_assessment(self, strategy, action, hour, timeframe='10min'):
        """ประเมินความเสี่ยงของ strategy ที่เลือก"""
        if timeframe not in self.patterns:
            return None
        
        patterns = self.patterns[timeframe]
        
        # ตรวจสอบ strategy performance
        strategy_data = patterns['strategy_performance'].get(strategy, {})
        if not strategy_data:
            return {"error": "ไม่พบข้อมูล strategy นี้"}
        
        # ตรวจสอบ time performance
        time_data = patterns['time_patterns']['hourly'].get(str(hour), {})
        
        # ตรวจสอบ action performance
        action_data = patterns['action_patterns'].get(action, {})
        
        # คำนวณ risk score
        risk_factors = []
        
        if strategy_data.get('win_rate', 0) < 50:
            risk_factors.append("Strategy มี win rate ต่ำ")
        
        if strategy_data.get('risk_score', 0) > 50:
            risk_factors.append("Strategy มี lost streak สูง")
        
        if time_data.get('win_rate', 0) < 50:
            risk_factors.append("เวลานี้มีประสิทธิภาพต่ำ")
        
        if action_data.get('win_rate', 0) < 50:
            risk_factors.append("Action นี้มีประสิทธิภาพต่ำ")
        
        # คำนวณ overall risk score
        overall_risk = 0
        if strategy_data.get('win_rate', 0) < 50:
            overall_risk += 30
        if strategy_data.get('risk_score', 0) > 50:
            overall_risk += 25
        if time_data.get('win_rate', 0) < 50:
            overall_risk += 20
        if action_data.get('win_rate', 0) < 50:
            overall_risk += 15
        
        risk_level = "ต่ำ" if overall_risk < 30 else "ปานกลาง" if overall_risk < 60 else "สูง"
        
        return {
            'strategy': strategy,
            'action': action,
            'hour': hour,
            'timeframe': timeframe,
            'strategy_win_rate': strategy_data.get('win_rate', 0),
            'strategy_risk_score': strategy_data.get('risk_score', 0),
            'time_win_rate': time_data.get('win_rate', 0),
            'action_win_rate': action_data.get('win_rate', 0),
            'overall_risk_score': overall_risk,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': "แนะนำ" if overall_risk < 30 else "ระวัง" if overall_risk < 60 else "ไม่แนะนำ"
        }
    
    def generate_metabase_data(self):
        """สร้างข้อมูลสำหรับ Metabase"""
        metabase_data = {
            'strategy_performance': {},
            'time_performance': {},
            'risk_assessment': {},
            'predictions': {}
        }
        
        for timeframe in ['10min', '30min', '60min']:
            if timeframe in self.patterns:
                patterns = self.patterns[timeframe]
                indicators = self.indicators[timeframe]
                
                # Strategy performance
                metabase_data['strategy_performance'][timeframe] = patterns['strategy_performance']
                
                # Time performance
                metabase_data['time_performance'][timeframe] = patterns['time_patterns']['hourly']
                
                # Risk assessment
                metabase_data['risk_assessment'][timeframe] = indicators['high_win_rate_strategies']
                
                # Predictions
                metabase_data['predictions'][timeframe] = {
                    'best_strategies': indicators['high_win_rate_strategies'],
                    'best_time_slots': indicators['best_time_slots'],
                    'best_combinations': indicators['best_combinations'],
                    'avoid_conditions': indicators['avoid_conditions']
                }
        
        return metabase_data

def main():
    """ฟังก์ชันหลัก"""
    print("Binary Options Prediction Engine")
    print("=" * 60)
    
    predictor = BinaryOptionsPredictor('/Users/puchong/tradingview/Result Last 120HR.csv')
    
    # ทำนาย strategy ที่ดีที่สุด
    prediction_10min = predictor.predict_best_strategy(timeframe='10min')
    prediction_30min = predictor.predict_best_strategy(timeframe='30min')
    prediction_60min = predictor.predict_best_strategy(timeframe='60min')
    
    # ตัวอย่างการประเมินความเสี่ยง
    print(f"\n{'='*60}")
    print("ตัวอย่างการประเมินความเสี่ยง:")
    print("="*60)
    
    risk_assessment = predictor.get_risk_assessment('Range FRAMA3', 'Buy', 16, '10min')
    if risk_assessment:
        print(f"Strategy: {risk_assessment['strategy']}")
        print(f"Action: {risk_assessment['action']}")
        print(f"Hour: {risk_assessment['hour']:02d}:00")
        print(f"Strategy Win Rate: {risk_assessment['strategy_win_rate']:.1f}%")
        print(f"Strategy Risk Score: {risk_assessment['strategy_risk_score']:.1f}")
        print(f"Time Win Rate: {risk_assessment['time_win_rate']:.1f}%")
        print(f"Action Win Rate: {risk_assessment['action_win_rate']:.1f}%")
        print(f"Overall Risk Score: {risk_assessment['overall_risk_score']}")
        print(f"Risk Level: {risk_assessment['risk_level']}")
        print(f"Recommendation: {risk_assessment['recommendation']}")
        if risk_assessment['risk_factors']:
            print(f"Risk Factors: {', '.join(risk_assessment['risk_factors'])}")
    
    # สร้างข้อมูลสำหรับ Metabase
    metabase_data = predictor.generate_metabase_data()
    
    # บันทึกข้อมูลสำหรับ Metabase
    import json
    with open('/Users/puchong/tradingview/metabase_data.json', 'w', encoding='utf-8') as f:
        json.dump(metabase_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\nบันทึกข้อมูลสำหรับ Metabase เรียบร้อย: metabase_data.json")

if __name__ == "__main__":
    main()
