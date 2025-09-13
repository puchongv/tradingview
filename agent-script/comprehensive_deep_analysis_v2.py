#!/usr/bin/env python3
"""
COMPREHENSIVE DEEP ANALYSIS V2 - การวิเคราะห์ลึกที่สุด ครอบคลุมทุกมิติ
รวม TREND CHANGE PATTERN analysis และ Dynamic Signal Performance
ทำอย่างละเอียดรอบคอบที่สุด ไม่พลาดมิติไหนเลย
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Statistical and ML libraries
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class ComprehensiveDeepAnalysisV2:
    def __init__(self):
        self.connection = None
        self.raw_data = None
        self.clean_data = None
        
        # Analysis results
        self.results = {
            'metadata': {},
            'data_quality': {},
            'patterns': {
                'time_patterns': {},
                'momentum_patterns': {},
                'signal_patterns': {},
                'combination_patterns': {},
                'sequence_patterns': {}
            },
            'trend_change': {
                'signal_performance_over_time': {},
                'performance_cycles': {},
                'optimal_refresh_intervals': {},
                'hot_cold_cycles': {},
                'trend_shift_detection': {}
            },
            'advanced_analysis': {
                'correlation_matrix': {},
                'feature_importance': {},
                'clustering_analysis': {},
                'anomaly_detection': {},
                'market_regime_analysis': {}
            },
            'statistical_tests': {},
            'forecasting': {},
            'actionable_insights': []
        }
    
    def connect_database(self):
        """Connect to database"""
        try:
            print("🔗 Connecting to database...")
            self.connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_comprehensive_data(self):
        """Load comprehensive dataset with all possible features"""
        try:
            print("📊 Loading comprehensive dataset...")
            
            query = """
            WITH lag_data AS (
                SELECT *,
                    LAG(result_60min, 1) OVER (ORDER BY entry_time) as prev_result_1,
                    LAG(result_60min, 2) OVER (ORDER BY entry_time) as prev_result_2,
                    LAG(result_60min, 3) OVER (ORDER BY entry_time) as prev_result_3,
                    LAG(strategy, 1) OVER (ORDER BY entry_time) as prev_strategy,
                    LAG(entry_price, 1) OVER (ORDER BY entry_time) as prev_price
                FROM tradingviewdata 
                WHERE entry_time IS NOT NULL
                  AND result_60min IS NOT NULL
                  AND strategy IS NOT NULL
                  AND strategy != ''
            )
            SELECT 
                id,
                strategy,
                action,
                entry_time,
                entry_price,
                result_60min,
                prev_result_1,
                prev_result_2, 
                prev_result_3,
                prev_strategy,
                prev_price,
                
                -- Time features
                EXTRACT(HOUR FROM entry_time) as hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(DAY FROM entry_time) as day_of_month,
                EXTRACT(WEEK FROM entry_time) as week_of_year,
                EXTRACT(MONTH FROM entry_time) as month,
                DATE(entry_time) as trade_date,
                EXTRACT(EPOCH FROM entry_time) as timestamp,
                
                -- Price features  
                entry_price - LAG(entry_price, 1) OVER (ORDER BY entry_time) as price_change_1,
                entry_price - LAG(entry_price, 5) OVER (ORDER BY entry_time) as price_change_5,
                entry_price - LAG(entry_price, 10) OVER (ORDER BY entry_time) as price_change_10,
                
                -- Row number for sequence analysis
                ROW_NUMBER() OVER (ORDER BY entry_time) as sequence_id
                
            FROM lag_data
            ORDER BY entry_time;
            """
            
            self.raw_data = pd.read_sql_query(query, self.connection)
            
            print(f"✅ Loaded {len(self.raw_data)} comprehensive records!")
            
            # Metadata
            self.results['metadata'] = {
                'total_records': len(self.raw_data),
                'date_range': {
                    'start': str(self.raw_data['entry_time'].min()),
                    'end': str(self.raw_data['entry_time'].max()),
                    'days_span': (self.raw_data['entry_time'].max() - self.raw_data['entry_time'].min()).days
                },
                'strategies': list(self.raw_data['strategy'].unique()),
                'actions': list(self.raw_data['action'].unique())
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading comprehensive data: {e}")
            return False
    
    def perform_data_quality_analysis(self):
        """Deep data quality analysis"""
        print("🔍 Performing comprehensive data quality analysis...")
        
        quality = {}
        
        # Missing data analysis
        missing_analysis = {}
        for col in self.raw_data.columns:
            missing_count = self.raw_data[col].isna().sum()
            missing_percentage = (missing_count / len(self.raw_data)) * 100
            missing_analysis[col] = {
                'missing_count': int(missing_count),
                'missing_percentage': float(missing_percentage)
            }
        
        quality['missing_data'] = missing_analysis
        
        # Data distribution analysis
        win_rate_overall = (self.raw_data['result_60min'] == 'WIN').mean()
        quality['overall_metrics'] = {
            'win_rate': float(win_rate_overall),
            'loss_rate': float(1 - win_rate_overall),
            'total_trades': len(self.raw_data)
        }
        
        # Strategy distribution
        strategy_dist = self.raw_data['strategy'].value_counts()
        quality['strategy_distribution'] = {
            str(k): int(v) for k, v in strategy_dist.items()
        }
        
        # Time distribution
        hourly_dist = self.raw_data['hour'].value_counts().sort_index()
        quality['hourly_distribution'] = {
            int(k): int(v) for k, v in hourly_dist.items()
        }
        
        # Data completeness by strategy
        strategy_completeness = {}
        for strategy in self.raw_data['strategy'].unique():
            strategy_data = self.raw_data[self.raw_data['strategy'] == strategy]
            strategy_completeness[strategy] = {
                'count': len(strategy_data),
                'win_rate': float((strategy_data['result_60min'] == 'WIN').mean()),
                'date_range_days': (strategy_data['entry_time'].max() - strategy_data['entry_time'].min()).days
            }
        
        quality['strategy_completeness'] = strategy_completeness
        
        self.results['data_quality'] = quality
    
    def create_engineered_features(self):
        """Create advanced engineered features"""
        print("⚙️ Creating advanced engineered features...")
        
        # Convert to datetime
        self.raw_data['entry_time'] = pd.to_datetime(self.raw_data['entry_time'])
        self.raw_data['trade_date'] = pd.to_datetime(self.raw_data['trade_date'])
        
        # Binary target
        self.raw_data['win'] = (self.raw_data['result_60min'] == 'WIN').astype(int)
        
        # Time-based features
        self.raw_data['hour_sin'] = np.sin(2 * np.pi * self.raw_data['hour'] / 24)
        self.raw_data['hour_cos'] = np.cos(2 * np.pi * self.raw_data['hour'] / 24)
        self.raw_data['dow_sin'] = np.sin(2 * np.pi * self.raw_data['day_of_week'] / 7)
        self.raw_data['dow_cos'] = np.cos(2 * np.pi * self.raw_data['day_of_week'] / 7)
        
        # Time blocks
        self.raw_data['time_block'] = pd.cut(self.raw_data['hour'], 
                                           bins=[0, 6, 12, 18, 24], 
                                           labels=['Night', 'Morning', 'Afternoon', 'Evening'])
        
        # Momentum features - previous results
        self.raw_data['prev_win_1'] = (self.raw_data['prev_result_1'] == 'WIN').astype(float)
        self.raw_data['prev_win_2'] = (self.raw_data['prev_result_2'] == 'WIN').astype(float) 
        self.raw_data['prev_win_3'] = (self.raw_data['prev_result_3'] == 'WIN').astype(float)
        
        # Rolling statistics
        for window in [3, 5, 10, 20]:
            self.raw_data[f'rolling_winrate_{window}'] = (
                self.raw_data['win'].rolling(window=window, min_periods=1).mean()
            )
            self.raw_data[f'rolling_volatility_{window}'] = (
                self.raw_data['win'].rolling(window=window, min_periods=1).std().fillna(0)
            )
        
        # Streak features
        self.raw_data['win_streak'] = 0
        self.raw_data['loss_streak'] = 0
        
        current_win_streak = 0
        current_loss_streak = 0
        
        for i in range(len(self.raw_data)):
            if self.raw_data.iloc[i]['win'] == 1:
                current_win_streak += 1
                current_loss_streak = 0
            else:
                current_loss_streak += 1
                current_win_streak = 0
            
            self.raw_data.at[self.raw_data.index[i], 'win_streak'] = current_win_streak
            self.raw_data.at[self.raw_data.index[i], 'loss_streak'] = current_loss_streak
        
        # Price features (handle NaN)
        self.raw_data['price_change_1'] = self.raw_data['price_change_1'].fillna(0)
        self.raw_data['price_change_5'] = self.raw_data['price_change_5'].fillna(0)
        self.raw_data['price_change_10'] = self.raw_data['price_change_10'].fillna(0)
        
        # Volatility features
        for window in [5, 10, 20]:
            self.raw_data[f'price_volatility_{window}'] = (
                self.raw_data['entry_price'].rolling(window=window, min_periods=1).std().fillna(0)
            )
        
        # Market regime features
        self.raw_data['price_trend_5'] = np.where(self.raw_data['price_change_5'] > 0, 'Up', 'Down')
        self.raw_data['price_trend_10'] = np.where(self.raw_data['price_change_10'] > 0, 'Up', 'Down')
        
        # Label encoding
        le_strategy = LabelEncoder()
        le_action = LabelEncoder()
        
        self.raw_data['strategy_encoded'] = le_strategy.fit_transform(self.raw_data['strategy'])
        self.raw_data['action_encoded'] = le_action.fit_transform(self.raw_data['action'])
        
        # Clean data (remove NaN rows)
        self.clean_data = self.raw_data.dropna(subset=[
            'prev_win_1', 'prev_win_2', 'prev_win_3'
        ]).copy()
        
        print(f"✅ Feature engineering complete! Clean data: {len(self.clean_data)} records")
    
    def analyze_comprehensive_patterns(self):
        """Comprehensive pattern analysis"""
        print("🎯 Analyzing comprehensive patterns...")
        
        patterns = self.results['patterns']
        
        # 1. DEEP TIME PATTERNS
        print("  ⏰ Deep time pattern analysis...")
        time_patterns = {}
        
        # Hourly patterns with statistical significance
        hourly_analysis = []
        for hour in range(24):
            hour_data = self.clean_data[self.clean_data['hour'] == hour]
            if len(hour_data) >= 10:
                win_rate = hour_data['win'].mean()
                sample_size = len(hour_data)
                
                # Statistical test
                successes = hour_data['win'].sum()
                p_value = stats.binomtest(successes, sample_size, 0.5).pvalue
                
                # Effect size (Cohen's h)
                effect_size = 2 * (np.arcsin(np.sqrt(win_rate)) - np.arcsin(np.sqrt(0.5)))
                
                hourly_analysis.append({
                    'hour': hour,
                    'win_rate': float(win_rate),
                    'sample_size': sample_size,
                    'p_value': float(p_value),
                    'effect_size': float(effect_size),
                    'is_significant': p_value < 0.05,
                    'significance_level': 'High' if p_value < 0.01 else 'Medium' if p_value < 0.05 else 'Low'
                })
        
        time_patterns['hourly'] = hourly_analysis
        
        # Day of week patterns
        dow_analysis = []
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for dow in range(7):
            dow_data = self.clean_data[self.clean_data['day_of_week'] == dow]
            if len(dow_data) >= 20:
                win_rate = dow_data['win'].mean()
                sample_size = len(dow_data)
                
                successes = dow_data['win'].sum()
                p_value = stats.binomtest(successes, sample_size, 0.5).pvalue
                effect_size = 2 * (np.arcsin(np.sqrt(win_rate)) - np.arcsin(np.sqrt(0.5)))
                
                dow_analysis.append({
                    'day_of_week': dow,
                    'day_name': day_names[dow],
                    'win_rate': float(win_rate),
                    'sample_size': sample_size,
                    'p_value': float(p_value),
                    'effect_size': float(effect_size),
                    'is_significant': p_value < 0.05
                })
        
        time_patterns['daily'] = dow_analysis
        
        # Time block analysis
        time_block_analysis = []
        for block in self.clean_data['time_block'].unique():
            if pd.notna(block):
                block_data = self.clean_data[self.clean_data['time_block'] == block]
                if len(block_data) >= 30:
                    win_rate = block_data['win'].mean()
                    sample_size = len(block_data)
                    
                    successes = block_data['win'].sum()
                    p_value = stats.binomtest(successes, sample_size, 0.5).pvalue
                    
                    time_block_analysis.append({
                        'time_block': str(block),
                        'win_rate': float(win_rate),
                        'sample_size': sample_size,
                        'p_value': float(p_value),
                        'is_significant': p_value < 0.05
                    })
        
        time_patterns['time_blocks'] = time_block_analysis
        patterns['time_patterns'] = time_patterns
        
        # 2. DEEP MOMENTUM PATTERNS
        print("  🔄 Deep momentum pattern analysis...")
        momentum_patterns = {}
        
        # Single step momentum
        momentum_analysis = []
        for prev_result in [0, 1]:
            momentum_data = self.clean_data[self.clean_data['prev_win_1'] == prev_result]
            if len(momentum_data) >= 50:
                win_rate = momentum_data['win'].mean()
                sample_size = len(momentum_data)
                
                successes = momentum_data['win'].sum()
                p_value = stats.binomtest(successes, sample_size, 0.5).pvalue
                effect_size = 2 * (np.arcsin(np.sqrt(win_rate)) - np.arcsin(np.sqrt(0.5)))
                
                momentum_analysis.append({
                    'previous_result': 'WIN' if prev_result == 1 else 'LOSS',
                    'subsequent_win_rate': float(win_rate),
                    'sample_size': sample_size,
                    'p_value': float(p_value),
                    'effect_size': float(effect_size),
                    'is_significant': p_value < 0.05
                })
        
        momentum_patterns['single_step'] = momentum_analysis
        
        # Multi-step momentum patterns
        multi_momentum = []
        
        # 2-step patterns (WW, WL, LW, LL)
        for prev2, prev1 in [(0,0), (0,1), (1,0), (1,1)]:
            pattern_data = self.clean_data[
                (self.clean_data['prev_win_2'] == prev2) & 
                (self.clean_data['prev_win_1'] == prev1)
            ]
            if len(pattern_data) >= 20:
                win_rate = pattern_data['win'].mean()
                sample_size = len(pattern_data)
                
                pattern_name = ('W' if prev2 else 'L') + ('W' if prev1 else 'L')
                
                successes = pattern_data['win'].sum()
                p_value = stats.binomtest(successes, sample_size, 0.5).pvalue
                
                multi_momentum.append({
                    'pattern': pattern_name,
                    'description': f"After {pattern_name}",
                    'subsequent_win_rate': float(win_rate),
                    'sample_size': sample_size,
                    'p_value': float(p_value),
                    'is_significant': p_value < 0.05
                })
        
        momentum_patterns['multi_step'] = multi_momentum
        patterns['momentum_patterns'] = momentum_patterns
        
        # 3. SIGNAL-SPECIFIC PATTERNS
        print("  📊 Signal-specific pattern analysis...")
        signal_patterns = {}
        
        for strategy in self.clean_data['strategy'].unique():
            strategy_data = self.clean_data[self.clean_data['strategy'] == strategy]
            if len(strategy_data) >= 30:
                
                # Overall strategy performance
                win_rate = strategy_data['win'].mean()
                sample_size = len(strategy_data)
                
                # Time preferences
                best_hours = []
                for hour in range(24):
                    hour_data = strategy_data[strategy_data['hour'] == hour]
                    if len(hour_data) >= 5:
                        hour_wr = hour_data['win'].mean()
                        if hour_wr > win_rate + 0.05:  # 5% above strategy average
                            best_hours.append({
                                'hour': hour,
                                'win_rate': float(hour_wr),
                                'sample_size': len(hour_data)
                            })
                
                # Day preferences
                best_days = []
                for dow in range(7):
                    day_data = strategy_data[strategy_data['day_of_week'] == dow]
                    if len(day_data) >= 5:
                        day_wr = day_data['win'].mean()
                        if day_wr > win_rate + 0.05:
                            best_days.append({
                                'day_of_week': dow,
                                'day_name': day_names[dow],
                                'win_rate': float(day_wr),
                                'sample_size': len(day_data)
                            })
                
                # Momentum preferences
                momentum_prefs = []
                for prev_result in [0, 1]:
                    prev_data = strategy_data[strategy_data['prev_win_1'] == prev_result]
                    if len(prev_data) >= 10:
                        prev_wr = prev_data['win'].mean()
                        momentum_prefs.append({
                            'after_result': 'WIN' if prev_result == 1 else 'LOSS',
                            'win_rate': float(prev_wr),
                            'sample_size': len(prev_data)
                        })
                
                signal_patterns[strategy] = {
                    'overall_win_rate': float(win_rate),
                    'overall_sample_size': sample_size,
                    'best_hours': best_hours,
                    'best_days': best_days,
                    'momentum_preferences': momentum_prefs
                }
        
        patterns['signal_patterns'] = signal_patterns
    
    def analyze_trend_change_patterns(self):
        """Deep trend change and dynamic performance analysis"""
        print("📈 Analyzing TREND CHANGE patterns...")
        
        trend_change = self.results['trend_change']
        
        # 1. SIGNAL PERFORMANCE OVER TIME
        print("  📊 Signal performance over time...")
        
        # Calculate rolling performance for each strategy
        performance_over_time = {}
        
        for strategy in self.clean_data['strategy'].unique():
            strategy_data = self.clean_data[self.clean_data['strategy'] == strategy].copy()
            if len(strategy_data) >= 50:
                
                # Sort by time
                strategy_data = strategy_data.sort_values('entry_time')
                
                # Calculate rolling win rates
                windows = [10, 20, 50, 100]
                rolling_stats = {}
                
                for window in windows:
                    if len(strategy_data) >= window:
                        rolling_wr = strategy_data['win'].rolling(window=window, min_periods=window//2).mean()
                        rolling_stats[f'rolling_{window}'] = {
                            'values': rolling_wr.dropna().tolist(),
                            'mean': float(rolling_wr.mean()),
                            'std': float(rolling_wr.std()),
                            'min': float(rolling_wr.min()),
                            'max': float(rolling_wr.max()),
                            'volatility': float(rolling_wr.std() / rolling_wr.mean()) if rolling_wr.mean() > 0 else 0
                        }
                
                # Performance trend analysis
                if len(strategy_data) >= 30:
                    # Divide into segments
                    n_segments = 5
                    segment_size = len(strategy_data) // n_segments
                    
                    segment_performance = []
                    for i in range(n_segments):
                        start_idx = i * segment_size
                        end_idx = (i + 1) * segment_size if i < n_segments - 1 else len(strategy_data)
                        segment_data = strategy_data.iloc[start_idx:end_idx]
                        
                        if len(segment_data) > 0:
                            segment_performance.append({
                                'segment': i + 1,
                                'win_rate': float(segment_data['win'].mean()),
                                'sample_size': len(segment_data),
                                'start_date': str(segment_data['entry_time'].min()),
                                'end_date': str(segment_data['entry_time'].max())
                            })
                    
                    # Trend detection
                    win_rates = [seg['win_rate'] for seg in segment_performance]
                    if len(win_rates) >= 3:
                        # Linear trend
                        x = np.arange(len(win_rates))
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x, win_rates)
                        
                        trend_direction = 'Improving' if slope > 0.01 else 'Declining' if slope < -0.01 else 'Stable'
                        trend_strength = abs(r_value)
                        
                        performance_over_time[strategy] = {
                            'rolling_statistics': rolling_stats,
                            'segment_performance': segment_performance,
                            'trend_analysis': {
                                'direction': trend_direction,
                                'slope': float(slope),
                                'strength': float(trend_strength),
                                'p_value': float(p_value),
                                'is_significant': p_value < 0.05
                            }
                        }
        
        trend_change['signal_performance_over_time'] = performance_over_time
        
        # 2. HOT/COLD CYCLES DETECTION
        print("  🌡️ Hot/Cold cycles detection...")
        
        hot_cold_cycles = {}
        
        for strategy in self.clean_data['strategy'].unique():
            strategy_data = self.clean_data[self.clean_data['strategy'] == strategy].copy()
            if len(strategy_data) >= 100:
                
                strategy_data = strategy_data.sort_values('entry_time')
                
                # Calculate rolling 20-period win rate
                rolling_20 = strategy_data['win'].rolling(window=20, min_periods=10).mean()
                overall_mean = strategy_data['win'].mean()
                
                # Define hot/cold thresholds
                hot_threshold = overall_mean + 0.1  # 10% above average
                cold_threshold = overall_mean - 0.1  # 10% below average
                
                # Find hot/cold periods
                cycles = []
                current_state = None
                current_start = None
                current_duration = 0
                
                for i, wr in enumerate(rolling_20):
                    if pd.notna(wr):
                        if wr >= hot_threshold and current_state != 'hot':
                            if current_state is not None:
                                cycles.append({
                                    'state': current_state,
                                    'start_index': current_start,
                                    'duration': current_duration,
                                    'performance': float(rolling_20[current_start:i].mean())
                                })
                            current_state = 'hot'
                            current_start = i
                            current_duration = 1
                        elif wr <= cold_threshold and current_state != 'cold':
                            if current_state is not None:
                                cycles.append({
                                    'state': current_state,
                                    'start_index': current_start,
                                    'duration': current_duration,
                                    'performance': float(rolling_20[current_start:i].mean())
                                })
                            current_state = 'cold'
                            current_start = i
                            current_duration = 1
                        elif cold_threshold < wr < hot_threshold and current_state != 'neutral':
                            if current_state is not None:
                                cycles.append({
                                    'state': current_state,
                                    'start_index': current_start,
                                    'duration': current_duration,
                                    'performance': float(rolling_20[current_start:i].mean())
                                })
                            current_state = 'neutral'
                            current_start = i
                            current_duration = 1
                        else:
                            current_duration += 1
                
                # Add final cycle
                if current_state is not None:
                    cycles.append({
                        'state': current_state,
                        'start_index': current_start,
                        'duration': current_duration,
                        'performance': float(rolling_20[current_start:].mean())
                    })
                
                # Cycle statistics
                hot_cycles = [c for c in cycles if c['state'] == 'hot']
                cold_cycles = [c for c in cycles if c['state'] == 'cold']
                
                hot_cold_cycles[strategy] = {
                    'overall_mean': float(overall_mean),
                    'hot_threshold': float(hot_threshold),
                    'cold_threshold': float(cold_threshold),
                    'cycles': cycles,
                    'cycle_statistics': {
                        'total_cycles': len(cycles),
                        'hot_cycles': len(hot_cycles),
                        'cold_cycles': len(cold_cycles),
                        'avg_hot_duration': float(np.mean([c['duration'] for c in hot_cycles])) if hot_cycles else 0,
                        'avg_cold_duration': float(np.mean([c['duration'] for c in cold_cycles])) if cold_cycles else 0,
                        'avg_hot_performance': float(np.mean([c['performance'] for c in hot_cycles])) if hot_cycles else 0,
                        'avg_cold_performance': float(np.mean([c['performance'] for c in cold_cycles])) if cold_cycles else 0
                    }
                }
        
        trend_change['hot_cold_cycles'] = hot_cold_cycles
        
        # 3. OPTIMAL REFRESH INTERVALS
        print("  🔄 Optimal refresh intervals analysis...")
        
        refresh_analysis = {}
        
        # Test different refresh intervals
        intervals = [6, 12, 24, 48, 72]  # hours
        
        for interval_hours in intervals:
            interval_results = {}
            
            for strategy in self.clean_data['strategy'].unique():
                strategy_data = self.clean_data[self.clean_data['strategy'] == strategy].copy()
                if len(strategy_data) >= 100:
                    
                    strategy_data = strategy_data.sort_values('entry_time')
                    
                    # Create time-based segments
                    strategy_data['time_segment'] = (
                        (strategy_data['entry_time'] - strategy_data['entry_time'].min()).dt.total_seconds() 
                        // (interval_hours * 3600)
                    ).astype(int)
                    
                    # Calculate performance for each segment
                    segment_performance = []
                    for segment in sorted(strategy_data['time_segment'].unique()):
                        segment_data = strategy_data[strategy_data['time_segment'] == segment]
                        if len(segment_data) >= 5:
                            segment_performance.append({
                                'segment': segment,
                                'win_rate': float(segment_data['win'].mean()),
                                'sample_size': len(segment_data),
                                'volatility': float(segment_data['win'].std())
                            })
                    
                    if len(segment_performance) >= 3:
                        # Performance consistency analysis
                        win_rates = [seg['win_rate'] for seg in segment_performance]
                        consistency = 1 / (np.std(win_rates) + 1e-6)  # Higher is more consistent
                        
                        # Trend persistence
                        improvements = 0
                        for i in range(1, len(win_rates)):
                            if win_rates[i] > win_rates[i-1]:
                                improvements += 1
                        
                        trend_persistence = improvements / (len(win_rates) - 1) if len(win_rates) > 1 else 0
                        
                        interval_results[strategy] = {
                            'segment_count': len(segment_performance),
                            'avg_win_rate': float(np.mean(win_rates)),
                            'win_rate_std': float(np.std(win_rates)),
                            'consistency_score': float(consistency),
                            'trend_persistence': float(trend_persistence),
                            'segment_performance': segment_performance
                        }
            
            refresh_analysis[f'{interval_hours}h'] = interval_results
        
        trend_change['optimal_refresh_intervals'] = refresh_analysis
        
        # 4. PERFORMANCE DECAY ANALYSIS
        print("  📉 Performance decay analysis...")
        
        decay_analysis = {}
        
        for strategy in self.clean_data['strategy'].unique():
            strategy_data = self.clean_data[self.clean_data['strategy'] == strategy].copy()
            if len(strategy_data) >= 50:
                
                strategy_data = strategy_data.sort_values('entry_time')
                
                # Find periods of peak performance
                rolling_performance = strategy_data['win'].rolling(window=20, min_periods=10).mean()
                overall_mean = strategy_data['win'].mean()
                
                # Identify peaks (performance significantly above average)
                peaks = []
                peak_threshold = overall_mean + 0.15  # 15% above average
                
                in_peak = False
                peak_start = None
                
                for i, perf in enumerate(rolling_performance):
                    if pd.notna(perf):
                        if perf >= peak_threshold and not in_peak:
                            in_peak = True
                            peak_start = i
                        elif perf < peak_threshold and in_peak:
                            in_peak = False
                            peaks.append({
                                'start': peak_start,
                                'end': i,
                                'duration': i - peak_start,
                                'peak_performance': float(rolling_performance[peak_start:i].max()),
                                'avg_performance': float(rolling_performance[peak_start:i].mean())
                            })
                
                # Analyze decay after peaks
                decay_patterns = []
                for peak in peaks:
                    # Look at performance after peak
                    post_peak_start = peak['end']
                    post_peak_data = rolling_performance[post_peak_start:post_peak_start+50]  # Next 50 periods
                    
                    if len(post_peak_data) >= 10:
                        # Calculate decay rate
                        x = np.arange(len(post_peak_data))
                        y = post_peak_data.values
                        
                        try:
                            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                            
                            decay_patterns.append({
                                'peak_performance': peak['peak_performance'],
                                'decay_rate': float(slope),
                                'decay_r_squared': float(r_value**2),
                                'recovery_time': self.find_recovery_time(post_peak_data, peak['peak_performance'] * 0.9),
                                'final_performance': float(post_peak_data.iloc[-1]) if len(post_peak_data) > 0 else None
                            })
                        except:
                            continue
                
                if decay_patterns:
                    decay_analysis[strategy] = {
                        'peak_count': len(peaks),
                        'avg_peak_duration': float(np.mean([p['duration'] for p in peaks])),
                        'avg_peak_performance': float(np.mean([p['peak_performance'] for p in peaks])),
                        'decay_patterns': decay_patterns,
                        'avg_decay_rate': float(np.mean([d['decay_rate'] for d in decay_patterns])),
                        'avg_recovery_time': float(np.mean([d['recovery_time'] for d in decay_patterns if d['recovery_time'] is not None]))
                    }
        
        trend_change['performance_cycles'] = decay_analysis
    
    def find_recovery_time(self, post_peak_data, target_performance):
        """Helper function to find recovery time to target performance"""
        for i, perf in enumerate(post_peak_data):
            if perf >= target_performance:
                return i
        return None
    
    def perform_advanced_analysis(self):
        """Advanced statistical and ML analysis"""
        print("🧠 Performing advanced analysis...")
        
        advanced = self.results['advanced_analysis']
        
        # 1. CORRELATION MATRIX
        print("  📊 Correlation analysis...")
        
        # Select numerical features
        numerical_features = [
            'hour', 'day_of_week', 'day_of_month', 'week_of_year', 'month',
            'prev_win_1', 'prev_win_2', 'prev_win_3',
            'rolling_winrate_3', 'rolling_winrate_5', 'rolling_winrate_10', 'rolling_winrate_20',
            'win_streak', 'loss_streak',
            'price_change_1', 'price_change_5', 'price_change_10',
            'price_volatility_5', 'price_volatility_10', 'price_volatility_20',
            'strategy_encoded', 'action_encoded',
            'win'
        ]
        
        # Filter existing columns
        available_features = [col for col in numerical_features if col in self.clean_data.columns]
        
        correlation_data = self.clean_data[available_features]
        correlation_matrix = correlation_data.corr()
        
        # Find strong correlations with target
        win_correlations = correlation_matrix['win'].abs().sort_values(ascending=False)
        
        advanced['correlation_matrix'] = {
            'win_correlations': {
                str(k): float(v) for k, v in win_correlations.items()
            },
            'strong_correlations': {
                str(k): float(v) for k, v in win_correlations.items() 
                if abs(v) > 0.1 and k != 'win'
            }
        }
        
        # 2. FEATURE IMPORTANCE WITH ML
        print("  🤖 Feature importance analysis...")
        
        # Prepare data
        feature_cols = [col for col in available_features if col != 'win']
        X = correlation_data[feature_cols].fillna(0)
        y = correlation_data['win']
        
        # Random Forest feature importance
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        rf_importance = dict(zip(feature_cols, rf.feature_importances_))
        rf_importance_sorted = dict(sorted(rf_importance.items(), key=lambda x: x[1], reverse=True))
        
        # Gradient Boosting feature importance
        gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
        gb.fit(X, y)
        
        gb_importance = dict(zip(feature_cols, gb.feature_importances_))
        gb_importance_sorted = dict(sorted(gb_importance.items(), key=lambda x: x[1], reverse=True))
        
        # Cross-validation scores
        rf_scores = cross_val_score(rf, X, y, cv=5)
        gb_scores = cross_val_score(gb, X, y, cv=5)
        
        advanced['feature_importance'] = {
            'random_forest': {
                'importance': {str(k): float(v) for k, v in rf_importance_sorted.items()},
                'cv_score_mean': float(rf_scores.mean()),
                'cv_score_std': float(rf_scores.std())
            },
            'gradient_boosting': {
                'importance': {str(k): float(v) for k, v in gb_importance_sorted.items()},
                'cv_score_mean': float(gb_scores.mean()),
                'cv_score_std': float(gb_scores.std())
            }
        }
        
        # 3. CLUSTERING ANALYSIS
        print("  🎪 Clustering analysis...")
        
        # K-means clustering on features
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Try different number of clusters
        clustering_results = {}
        for n_clusters in [3, 4, 5, 6]:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Analyze clusters
            cluster_analysis = []
            for cluster_id in range(n_clusters):
                cluster_mask = cluster_labels == cluster_id
                cluster_data = self.clean_data[cluster_mask]
                
                if len(cluster_data) > 0:
                    cluster_analysis.append({
                        'cluster_id': cluster_id,
                        'size': len(cluster_data),
                        'win_rate': float(cluster_data['win'].mean()),
                        'avg_hour': float(cluster_data['hour'].mean()),
                        'avg_dow': float(cluster_data['day_of_week'].mean()),
                        'top_strategies': list(cluster_data['strategy'].value_counts().head(3).index.tolist())
                    })
            
            clustering_results[f'{n_clusters}_clusters'] = {
                'cluster_analysis': cluster_analysis,
                'silhouette_score': float(self.calculate_silhouette_score(X_scaled, cluster_labels))
            }
        
        advanced['clustering_analysis'] = clustering_results
    
    def calculate_silhouette_score(self, X, labels):
        """Calculate silhouette score"""
        try:
            from sklearn.metrics import silhouette_score
            return silhouette_score(X, labels)
        except:
            return 0.0
    
    def perform_statistical_tests(self):
        """Comprehensive statistical testing"""
        print("📊 Performing statistical tests...")
        
        tests = {}
        
        # 1. Chi-square test for independence
        # Test if strategy and time are independent
        contingency_table = pd.crosstab(self.clean_data['strategy'], self.clean_data['hour'])
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
        
        tests['strategy_time_independence'] = {
            'chi2_statistic': float(chi2),
            'p_value': float(p_val),
            'degrees_of_freedom': int(dof),
            'is_independent': p_val > 0.05
        }
        
        # 2. ANOVA test for win rates across strategies
        strategy_groups = []
        strategy_names = []
        for strategy in self.clean_data['strategy'].unique():
            strategy_data = self.clean_data[self.clean_data['strategy'] == strategy]['win']
            if len(strategy_data) >= 10:
                strategy_groups.append(strategy_data)
                strategy_names.append(strategy)
        
        if len(strategy_groups) >= 2:
            f_stat, p_val = stats.f_oneway(*strategy_groups)
            
            tests['strategy_anova'] = {
                'f_statistic': float(f_stat),
                'p_value': float(p_val),
                'strategies_tested': strategy_names,
                'significantly_different': p_val < 0.05
            }
        
        # 3. Kolmogorov-Smirnov test for normality
        ks_stat, ks_p = stats.kstest(self.clean_data['rolling_winrate_10'].dropna(), 'norm')
        
        tests['normality_test'] = {
            'ks_statistic': float(ks_stat),
            'p_value': float(ks_p),
            'is_normal': ks_p > 0.05
        }
        
        self.results['statistical_tests'] = tests
    
    def generate_actionable_insights(self):
        """Generate practical actionable insights"""
        print("💡 Generating actionable insights...")
        
        insights = []
        
        # Time-based insights
        time_patterns = self.results['patterns']['time_patterns']
        if 'hourly' in time_patterns:
            significant_hours = [h for h in time_patterns['hourly'] if h['is_significant']]
            
            good_hours = [h for h in significant_hours if h['win_rate'] > 0.55]
            bad_hours = [h for h in significant_hours if h['win_rate'] < 0.45]
            
            if good_hours:
                best_hour = max(good_hours, key=lambda x: x['win_rate'])
                insights.append({
                    'category': 'TIME',
                    'type': 'GOLDEN_HOUR',
                    'title': f"Golden Hour: {best_hour['hour']:02d}:00",
                    'description': f"Hour {best_hour['hour']:02d}:00 shows {best_hour['win_rate']:.1%} win rate",
                    'win_rate': best_hour['win_rate'],
                    'sample_size': best_hour['sample_size'],
                    'action': f"Prioritize trading during {best_hour['hour']:02d}:00-{best_hour['hour']:02d}:59",
                    'confidence': 'HIGH' if best_hour['p_value'] < 0.01 else 'MEDIUM'
                })
            
            if bad_hours:
                worst_hour = min(bad_hours, key=lambda x: x['win_rate'])
                insights.append({
                    'category': 'TIME',
                    'type': 'DANGER_HOUR',
                    'title': f"Danger Hour: {worst_hour['hour']:02d}:00",
                    'description': f"Hour {worst_hour['hour']:02d}:00 shows only {worst_hour['win_rate']:.1%} win rate",
                    'win_rate': worst_hour['win_rate'],
                    'sample_size': worst_hour['sample_size'],
                    'action': f"Avoid trading during {worst_hour['hour']:02d}:00-{worst_hour['hour']:02d}:59",
                    'confidence': 'HIGH' if worst_hour['p_value'] < 0.01 else 'MEDIUM'
                })
        
        # Momentum insights
        momentum_patterns = self.results['patterns']['momentum_patterns']
        if 'single_step' in momentum_patterns:
            for momentum in momentum_patterns['single_step']:
                if momentum['is_significant']:
                    insights.append({
                        'category': 'MOMENTUM',
                        'type': 'SINGLE_STEP',
                        'title': f"After {momentum['previous_result']} Pattern",
                        'description': f"After {momentum['previous_result']}, win rate is {momentum['subsequent_win_rate']:.1%}",
                        'win_rate': momentum['subsequent_win_rate'],
                        'sample_size': momentum['sample_size'],
                        'action': 'Increase confidence' if momentum['subsequent_win_rate'] > 0.55 else 'Exercise caution',
                        'confidence': 'HIGH' if momentum['p_value'] < 0.01 else 'MEDIUM'
                    })
        
        # Trend change insights
        trend_change = self.results['trend_change']
        if 'hot_cold_cycles' in trend_change:
            for strategy, cycle_data in trend_change['hot_cold_cycles'].items():
                if cycle_data['cycle_statistics']['hot_cycles'] > 0:
                    insights.append({
                        'category': 'TREND_CHANGE',
                        'type': 'HOT_CYCLES',
                        'title': f"{strategy} Hot Cycles",
                        'description': f"{strategy} shows {cycle_data['cycle_statistics']['hot_cycles']} hot cycles with {cycle_data['cycle_statistics']['avg_hot_performance']:.1%} avg performance",
                        'win_rate': cycle_data['cycle_statistics']['avg_hot_performance'],
                        'action': f"Monitor {strategy} for hot cycle opportunities",
                        'confidence': 'MEDIUM',
                        'additional_info': {
                            'avg_hot_duration': cycle_data['cycle_statistics']['avg_hot_duration'],
                            'hot_threshold': cycle_data['hot_threshold']
                        }
                    })
        
        # Signal-specific insights
        signal_patterns = self.results['patterns']['signal_patterns']
        for strategy, pattern_data in signal_patterns.items():
            if pattern_data['best_hours']:
                best_combo = max(pattern_data['best_hours'], key=lambda x: x['win_rate'])
                if best_combo['win_rate'] > 0.6:  # 60%+ win rate
                    insights.append({
                        'category': 'SIGNAL_SPECIFIC',
                        'type': 'GOLDEN_COMBINATION',
                        'title': f"{strategy} + Hour {best_combo['hour']:02d}:00",
                        'description': f"{strategy} at {best_combo['hour']:02d}:00 shows {best_combo['win_rate']:.1%} win rate",
                        'win_rate': best_combo['win_rate'],
                        'sample_size': best_combo['sample_size'],
                        'action': f"Combine {strategy} with {best_combo['hour']:02d}:00 timing",
                        'confidence': 'HIGH' if best_combo['sample_size'] > 20 else 'MEDIUM'
                    })
        
        # Advanced analysis insights
        if 'feature_importance' in self.results['advanced_analysis']:
            rf_importance = self.results['advanced_analysis']['feature_importance']['random_forest']['importance']
            top_feature = max(rf_importance.items(), key=lambda x: x[1])
            
            insights.append({
                'category': 'ADVANCED',
                'type': 'FEATURE_IMPORTANCE',
                'title': f"Top Predictive Feature: {top_feature[0]}",
                'description': f"{top_feature[0]} is the most important feature with {top_feature[1]:.3f} importance",
                'action': f"Focus on optimizing {top_feature[0]} for better predictions",
                'confidence': 'MEDIUM',
                'importance_score': top_feature[1]
            })
        
        # Sort by confidence and win rate
        insights.sort(key=lambda x: (
            {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(x['confidence'], 0),
            x.get('win_rate', 0.5)
        ), reverse=True)
        
        self.results['actionable_insights'] = insights[:20]  # Top 20 insights
    
    def save_comprehensive_results(self):
        """Save all comprehensive results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON
        with open(f'/Users/puchong/tradingview/report/comprehensive_analysis_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report()
        with open(f'/Users/puchong/tradingview/report/COMPREHENSIVE_ANALYSIS_V2.md', 'w') as f:
            f.write(report)
        
        print("✅ Comprehensive analysis results saved!")
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        metadata = self.results['metadata']
        quality = self.results['data_quality']
        
        return f"""# 🔥 COMPREHENSIVE DEEP ANALYSIS V2
## การวิเคราะห์ลึกที่สุด - ครอบคลุมทุกมิติ

**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Period**: {metadata['date_range']['start']} to {metadata['date_range']['end']}  
**Total Records**: {metadata['total_records']:,}  
**Analysis Duration**: {metadata['date_range']['days_span']} days  

---

## 📊 **DATA QUALITY SUMMARY**

### **Overall Performance**
- **Overall Win Rate**: {quality['overall_metrics']['win_rate']:.1%}
- **Total Trades**: {quality['overall_metrics']['total_trades']:,}
- **Strategies Analyzed**: {len(metadata['strategies'])}

### **Strategy Distribution**
{self.format_strategy_distribution()}

---

## ⏰ **TIME PATTERNS ANALYSIS**

{self.format_time_patterns()}

---

## 🔄 **MOMENTUM PATTERNS ANALYSIS** 

{self.format_momentum_patterns()}

---

## 📈 **TREND CHANGE PATTERNS**

{self.format_trend_change_patterns()}

---

## 📊 **SIGNAL-SPECIFIC PATTERNS**

{self.format_signal_patterns()}

---

## 🧠 **ADVANCED ANALYSIS**

{self.format_advanced_analysis()}

---

## 📊 **STATISTICAL TESTS**

{self.format_statistical_tests()}

---

## 💡 **TOP ACTIONABLE INSIGHTS**

{self.format_actionable_insights()}

---

## 🎯 **EXECUTIVE SUMMARY**

{self.generate_executive_summary()}

---

**This analysis represents the most comprehensive examination of trading patterns, including trend changes, signal dynamics, and advanced statistical modeling.**
"""
    
    def format_strategy_distribution(self):
        quality = self.results['data_quality']
        output = ""
        
        for strategy, count in list(quality['strategy_distribution'].items())[:10]:
            completeness = quality['strategy_completeness'].get(strategy, {})
            win_rate = completeness.get('win_rate', 0)
            output += f"- **{strategy}**: {count:,} trades ({win_rate:.1%} win rate)\n"
        
        return output
    
    def format_time_patterns(self):
        time_patterns = self.results['patterns']['time_patterns']
        output = ""
        
        if 'hourly' in time_patterns:
            significant_hours = [h for h in time_patterns['hourly'] if h['is_significant']]
            significant_hours.sort(key=lambda x: x['win_rate'], reverse=True)
            
            output += "### **🔥 Significant Hourly Patterns**\n"
            for i, hour in enumerate(significant_hours[:10], 1):
                emoji = "🔥" if hour['win_rate'] > 0.6 else "💎" if hour['win_rate'] > 0.55 else "⚠️" if hour['win_rate'] < 0.45 else "⭐"
                output += f"{emoji} **#{i} Hour {hour['hour']:02d}:00**: {hour['win_rate']:.1%} ({hour['sample_size']} trades, p={hour['p_value']:.4f})\n"
        
        if 'daily' in time_patterns:
            significant_days = [d for d in time_patterns['daily'] if d['is_significant']]
            if significant_days:
                significant_days.sort(key=lambda x: x['win_rate'], reverse=True)
                
                output += "\n### **📅 Significant Daily Patterns**\n"
                for day in significant_days:
                    emoji = "🔥" if day['win_rate'] > 0.6 else "💎" if day['win_rate'] > 0.55 else "⚠️"
                    output += f"{emoji} **{day['day_name']}**: {day['win_rate']:.1%} ({day['sample_size']} trades, p={day['p_value']:.4f})\n"
        
        return output
    
    def format_momentum_patterns(self):
        momentum = self.results['patterns']['momentum_patterns']
        output = ""
        
        if 'single_step' in momentum:
            output += "### **⚡ Single-Step Momentum**\n"
            for pattern in momentum['single_step']:
                if pattern['is_significant']:
                    emoji = "🔥" if pattern['subsequent_win_rate'] > 0.7 else "💎" if pattern['subsequent_win_rate'] > 0.6 else "⚠️"
                    output += f"{emoji} **After {pattern['previous_result']}**: {pattern['subsequent_win_rate']:.1%} win rate ({pattern['sample_size']} trades)\n"
        
        if 'multi_step' in momentum:
            significant_multi = [p for p in momentum['multi_step'] if p['is_significant']]
            if significant_multi:
                output += "\n### **🔄 Multi-Step Momentum**\n"
                for pattern in significant_multi:
                    emoji = "🔥" if pattern['subsequent_win_rate'] > 0.6 else "⚠️" if pattern['subsequent_win_rate'] < 0.4 else "⭐"
                    output += f"{emoji} **{pattern['pattern']}**: {pattern['subsequent_win_rate']:.1%} win rate ({pattern['sample_size']} trades)\n"
        
        return output
    
    def format_trend_change_patterns(self):
        trend_change = self.results['trend_change']
        output = ""
        
        # Signal performance over time
        if 'signal_performance_over_time' in trend_change:
            output += "### **📊 Signal Performance Trends**\n"
            
            for strategy, perf_data in list(trend_change['signal_performance_over_time'].items())[:5]:
                trend = perf_data.get('trend_analysis', {})
                direction = trend.get('direction', 'Unknown')
                
                emoji = "📈" if direction == 'Improving' else "📉" if direction == 'Declining' else "📊"
                output += f"{emoji} **{strategy}**: {direction} trend"
                
                if trend.get('is_significant'):
                    output += f" (p={trend.get('p_value', 0):.4f})"
                
                output += "\n"
        
        # Hot/Cold cycles
        if 'hot_cold_cycles' in trend_change:
            output += "\n### **🌡️ Hot/Cold Cycles Analysis**\n"
            
            for strategy, cycle_data in list(trend_change['hot_cold_cycles'].items())[:3]:
                stats = cycle_data['cycle_statistics']
                if stats['hot_cycles'] > 0:
                    output += f"🔥 **{strategy}**: {stats['hot_cycles']} hot cycles, avg {stats['avg_hot_performance']:.1%} performance\n"
        
        # Optimal refresh intervals
        if 'optimal_refresh_intervals' in trend_change:
            output += "\n### **🔄 Optimal Refresh Analysis**\n"
            output += "Analysis of different refresh intervals shows varying consistency across strategies.\n"
        
        return output
    
    def format_signal_patterns(self):
        signal_patterns = self.results['patterns']['signal_patterns']
        output = ""
        
        # Top performing signal combinations
        top_combos = []
        for strategy, data in signal_patterns.items():
            for hour_data in data.get('best_hours', []):
                if hour_data['win_rate'] > 0.6 and hour_data['sample_size'] >= 10:
                    top_combos.append({
                        'strategy': strategy,
                        'hour': hour_data['hour'],
                        'win_rate': hour_data['win_rate'],
                        'sample_size': hour_data['sample_size']
                    })
        
        if top_combos:
            top_combos.sort(key=lambda x: x['win_rate'], reverse=True)
            
            output += "### **🏆 Top Signal + Time Combinations**\n"
            for i, combo in enumerate(top_combos[:10], 1):
                emoji = "🔥" if combo['win_rate'] > 0.7 else "💎"
                output += f"{emoji} **#{i} {combo['strategy']} + Hour {combo['hour']:02d}:00**: {combo['win_rate']:.1%} ({combo['sample_size']} trades)\n"
        
        return output
    
    def format_advanced_analysis(self):
        advanced = self.results['advanced_analysis']
        output = ""
        
        # Feature importance
        if 'feature_importance' in advanced:
            rf_importance = advanced['feature_importance']['random_forest']['importance']
            top_features = list(rf_importance.items())[:5]
            
            output += "### **🎯 Top Predictive Features**\n"
            for i, (feature, importance) in enumerate(top_features, 1):
                output += f"**#{i} {feature}**: {importance:.4f}\n"
        
        # Correlation analysis
        if 'correlation_matrix' in advanced:
            strong_corr = advanced['correlation_matrix']['strong_correlations']
            if strong_corr:
                output += "\n### **🔗 Strong Correlations with Win Rate**\n"
                for feature, correlation in list(strong_corr.items())[:5]:
                    direction = "positive" if correlation > 0 else "negative"
                    output += f"- **{feature}**: {correlation:.3f} ({direction})\n"
        
        return output
    
    def format_statistical_tests(self):
        tests = self.results['statistical_tests']
        output = ""
        
        for test_name, test_data in tests.items():
            if test_name == 'strategy_time_independence':
                result = "Independent" if test_data['is_independent'] else "Dependent"
                output += f"- **Strategy-Time Independence**: {result} (p={test_data['p_value']:.4f})\n"
            elif test_name == 'strategy_anova':
                result = "Significantly different" if test_data['significantly_different'] else "Not significantly different"
                output += f"- **Strategy Performance ANOVA**: {result} (p={test_data['p_value']:.4f})\n"
        
        return output
    
    def format_actionable_insights(self):
        insights = self.results['actionable_insights']
        output = ""
        
        for i, insight in enumerate(insights[:15], 1):
            emoji = "🔥" if insight['confidence'] == 'HIGH' else "💎" if insight['confidence'] == 'MEDIUM' else "⭐"
            output += f"{emoji} **#{i} {insight['title']}**\n"
            output += f"   - {insight['description']}\n"
            output += f"   - Action: {insight['action']}\n"
            output += f"   - Confidence: {insight['confidence']}\n\n"
        
        return output
    
    def generate_executive_summary(self):
        insights = self.results['actionable_insights']
        high_confidence = [i for i in insights if i['confidence'] == 'HIGH']
        
        time_insights = [i for i in high_confidence if i['category'] == 'TIME']
        momentum_insights = [i for i in high_confidence if i['category'] == 'MOMENTUM']
        trend_insights = [i for i in insights if i['category'] == 'TREND_CHANGE']
        
        return f"""
### **🏆 Key Findings**

1. **Time Patterns**: Found {len(time_insights)} high-confidence time-based patterns
2. **Momentum Effects**: Identified {len(momentum_insights)} significant momentum patterns  
3. **Trend Changes**: Analyzed {len(trend_insights)} trend change patterns across signals
4. **Signal Dynamics**: Comprehensive analysis of hot/cold cycles and performance decay

### **💡 Primary Recommendations**

1. **Focus on verified time patterns** - Use statistically significant hours and days
2. **Leverage momentum effects** - Strong patterns after wins/losses identified
3. **Monitor signal performance dynamically** - Implement trend change detection
4. **Use combination patterns** - Signal + time combinations show enhanced performance

### **🎯 Implementation Priority**

1. **High**: Time and momentum patterns (statistically significant)
2. **Medium**: Signal-specific combinations (good sample sizes)
3. **Low**: Complex multi-factor patterns (require validation)

This analysis provides the most comprehensive view of market patterns and signal dynamics available from the current dataset.
"""
    
    def run_complete_comprehensive_analysis(self):
        """Run the complete comprehensive analysis"""
        print("🔥 Starting COMPREHENSIVE DEEP ANALYSIS V2...")
        print("🎯 Goal: ลึกที่สุด ครอบคลุบทุกมิติ รวม TREND CHANGE")
        print("=" * 70)
        
        start_time = datetime.now()
        
        # Connect and load data
        if not self.connect_database():
            return False
        
        if not self.load_comprehensive_data():
            return False
        
        # Perform comprehensive analysis
        print("\n🔍 Phase 1: Data Quality Analysis...")
        self.perform_data_quality_analysis()
        
        print("⚙️ Phase 2: Feature Engineering...")
        self.create_engineered_features()
        
        print("🎯 Phase 3: Comprehensive Pattern Analysis...")
        self.analyze_comprehensive_patterns()
        
        print("📈 Phase 4: Trend Change Analysis...")
        self.analyze_trend_change_patterns()
        
        print("🧠 Phase 5: Advanced Statistical Analysis...")
        self.perform_advanced_analysis()
        
        print("📊 Phase 6: Statistical Testing...")
        self.perform_statistical_tests()
        
        print("💡 Phase 7: Generate Actionable Insights...")
        self.generate_actionable_insights()
        
        print("💾 Phase 8: Save Results...")
        self.save_comprehensive_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print(f"⏱️ Total Duration: {duration}")
        print(f"📊 Records Analyzed: {len(self.clean_data):,}")
        print(f"🎯 Patterns Found: {len([i for i in self.results['actionable_insights'] if i['confidence'] == 'HIGH'])}")
        print(f"📈 Trend Changes: Analyzed for {len(self.results['trend_change']['hot_cold_cycles'])} signals")
        print("🔥 Analysis depth: MAXIMUM - ทุกมิติครบถ้วน!")
        print("=" * 70)
        
        return True

if __name__ == "__main__":
    analyzer = ComprehensiveDeepAnalysisV2()
    analyzer.run_complete_comprehensive_analysis()
