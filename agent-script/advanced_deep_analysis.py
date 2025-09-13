#!/usr/bin/env python3
"""
Advanced Deep Analysis for Trading Pattern Recognition
วิเคราะห์ข้อมูล Trading Pattern อย่างลึกและละเอียดที่สุด
ใช้ Statistical Significance Testing และ Advanced ML Techniques
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Statistical testing
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, mannwhitneyu
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

# Database connection
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class AdvancedPatternAnalyzer:
    def __init__(self):
        """Initialize advanced pattern analyzer"""
        self.connection = None
        self.data = None
        self.results = {
            'statistical_significant_patterns': [],
            'consistent_patterns': [],
            'advanced_ml_insights': [],
            'clustering_results': [],
            'time_series_patterns': [],
            'cross_validation_results': [],
            'pattern_confidence_scores': [],
            'actionable_insights': []
        }
        
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            print("🔗 Connecting to TradingView PostgreSQL database...")
            self.connection = psycopg2.connect(**DB_CONFIG)
            print("✅ Successfully connected!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_all_data(self):
        """Load all trading data from database"""
        try:
            print("📊 Loading all trading data from database...")
            
            query = """
            SELECT 
                id, action, symbol, strategy, tf, entry_time, entry_price,
                price_10min, price_30min, price_60min, price_1day,
                result_10min, result_30min, result_60min, result_1day,
                pnl, created_at, updated_at, trade, martingale,
                EXTRACT(HOUR FROM entry_time) as hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(DAY FROM entry_time) as day_of_month,
                EXTRACT(WEEK FROM entry_time) as week,
                EXTRACT(MONTH FROM entry_time) as month
            FROM tradingviewdata 
            ORDER BY entry_time;
            """
            
            self.data = pd.read_sql_query(query, self.connection)
            print(f"✅ Loaded {len(self.data)} records!")
            
            # Data preprocessing
            self.preprocess_data()
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def preprocess_data(self):
        """Advanced data preprocessing"""
        print("🔧 Preprocessing data...")
        
        # Create win/loss binary columns
        for timeframe in ['10min', '30min', '60min', '1day']:
            col = f'result_{timeframe}'
            if col in self.data.columns:
                self.data[f'win_{timeframe}'] = (self.data[col] == 'WIN').astype(int)
        
        # Create advanced features
        self.data['price_change_10min'] = (self.data['price_10min'] - self.data['entry_price']) / self.data['entry_price'] * 100
        self.data['price_change_30min'] = (self.data['price_30min'] - self.data['entry_price']) / self.data['entry_price'] * 100
        self.data['price_change_60min'] = (self.data['price_60min'] - self.data['entry_price']) / self.data['entry_price'] * 100
        
        # Volatility measures
        self.data['volatility_10min'] = abs(self.data['price_change_10min'])
        self.data['volatility_30min'] = abs(self.data['price_change_30min'])
        self.data['volatility_60min'] = abs(self.data['price_change_60min'])
        
        # Create rolling features
        self.data = self.data.sort_values('entry_time').reset_index(drop=True)
        
        # Rolling win rates
        for window in [5, 10, 20, 50]:
            self.data[f'rolling_win_rate_{window}'] = self.data['win_60min'].rolling(window=window, min_periods=1).mean()
        
        # Win/Loss streaks
        self.data['win_streak'] = 0
        self.data['loss_streak'] = 0
        
        win_streak = 0
        loss_streak = 0
        
        for i in range(len(self.data)):
            if i > 0:
                if self.data.loc[i-1, 'win_60min'] == 1:
                    win_streak += 1
                    loss_streak = 0
                else:
                    loss_streak += 1
                    win_streak = 0
            
            self.data.loc[i, 'win_streak'] = win_streak
            self.data.loc[i, 'loss_streak'] = loss_streak
        
        # Market trend indicators
        self.data['price_trend_short'] = self.data['entry_price'].rolling(window=10).mean()
        self.data['price_trend_long'] = self.data['entry_price'].rolling(window=50).mean()
        self.data['trend_direction'] = np.where(self.data['price_trend_short'] > self.data['price_trend_long'], 1, 0)
        
        # Time-based features
        self.data['is_weekend'] = self.data['day_of_week'].isin([0, 6]).astype(int)
        self.data['is_morning'] = ((self.data['hour'] >= 6) & (self.data['hour'] < 12)).astype(int)
        self.data['is_afternoon'] = ((self.data['hour'] >= 12) & (self.data['hour'] < 18)).astype(int)
        self.data['is_evening'] = ((self.data['hour'] >= 18) & (self.data['hour'] < 24)).astype(int)
        self.data['is_night'] = ((self.data['hour'] >= 0) & (self.data['hour'] < 6)).astype(int)
        
        print(f"✅ Preprocessing complete! Features: {len(self.data.columns)}")
    
    def statistical_significance_testing(self):
        """Advanced statistical significance testing for patterns"""
        print("📊 Running Statistical Significance Testing...")
        
        significant_patterns = []
        overall_win_rate = self.data['win_60min'].mean()
        
        # 1. Time-based patterns with statistical testing
        print("🔍 Testing time-based patterns...")
        
        # Hour analysis with Chi-square test
        hour_analysis = []
        for hour in range(24):
            hour_data = self.data[self.data['hour'] == hour]
            if len(hour_data) >= 10:  # Minimum sample size
                wins = hour_data['win_60min'].sum()
                total = len(hour_data)
                win_rate = wins / total
                
                # Chi-square test
                expected_wins = total * overall_win_rate
                expected_losses = total * (1 - overall_win_rate)
                observed = [wins, total - wins]
                expected = [expected_wins, expected_losses]
                
                if expected_wins > 5 and expected_losses > 5:  # Chi-square assumptions
                    chi2, p_value = stats.chisquare(observed, expected)
                    
                    # Effect size (Cohen's h)
                    p1 = win_rate
                    p2 = overall_win_rate
                    cohens_h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
                    effect_size = abs(cohens_h)
                    
                    significance_level = 'High' if p_value < 0.001 else 'Medium' if p_value < 0.01 else 'Low' if p_value < 0.05 else 'None'
                    
                    hour_analysis.append({
                        'hour': hour,
                        'win_rate': win_rate,
                        'total_signals': total,
                        'difference_from_overall': win_rate - overall_win_rate,
                        'p_value': p_value,
                        'effect_size': effect_size,
                        'significance': significance_level,
                        'wins': wins,
                        'losses': total - wins
                    })
        
        # Sort by effect size and significance
        hour_analysis = sorted(hour_analysis, key=lambda x: (x['significance'] != 'None', x['effect_size']), reverse=True)
        
        # 2. Strategy-time interaction patterns
        print("🔍 Testing strategy-time interaction patterns...")
        strategy_time_patterns = []
        
        for strategy in self.data['strategy'].unique():
            for hour in range(24):
                subset = self.data[(self.data['strategy'] == strategy) & (self.data['hour'] == hour)]
                if len(subset) >= 5:  # Minimum sample size for interaction
                    wins = subset['win_60min'].sum()
                    total = len(subset)
                    win_rate = wins / total
                    
                    # Compare with overall strategy performance
                    strategy_overall = self.data[self.data['strategy'] == strategy]['win_60min'].mean()
                    difference = win_rate - strategy_overall
                    
                    if abs(difference) > 0.2:  # 20% difference threshold
                        strategy_time_patterns.append({
                            'strategy': strategy,
                            'hour': hour,
                            'win_rate': win_rate,
                            'strategy_overall_win_rate': strategy_overall,
                            'difference': difference,
                            'total_signals': total,
                            'confidence': 'High' if total >= 20 else 'Medium' if total >= 10 else 'Low'
                        })
        
        # 3. Consecutive pattern analysis (streak consistency)
        print("🔍 Testing consecutive pattern consistency...")
        consecutive_patterns = []
        
        # Group by strategy and analyze consecutive wins/losses
        for strategy in self.data['strategy'].unique():
            strategy_data = self.data[self.data['strategy'] == strategy].sort_values('entry_time')
            if len(strategy_data) >= 20:
                
                # Calculate consecutive wins/losses
                strategy_data['prev_result'] = strategy_data['win_60min'].shift(1)
                strategy_data['next_result'] = strategy_data['win_60min'].shift(-1)
                
                # Win after win probability
                win_after_win = strategy_data[(strategy_data['prev_result'] == 1) & (strategy_data['win_60min'] == 1)]
                total_after_win = strategy_data[strategy_data['prev_result'] == 1]
                
                # Loss after loss probability
                loss_after_loss = strategy_data[(strategy_data['prev_result'] == 0) & (strategy_data['win_60min'] == 0)]
                total_after_loss = strategy_data[strategy_data['prev_result'] == 0]
                
                if len(total_after_win) > 0 and len(total_after_loss) > 0:
                    win_after_win_rate = len(win_after_win) / len(total_after_win)
                    loss_after_loss_rate = len(loss_after_loss) / len(total_after_loss)
                    
                    consecutive_patterns.append({
                        'strategy': strategy,
                        'win_after_win_rate': win_after_win_rate,
                        'loss_after_loss_rate': loss_after_loss_rate,
                        'win_after_win_count': len(total_after_win),
                        'loss_after_loss_count': len(total_after_loss),
                        'consistency_score': abs(win_after_win_rate - overall_win_rate) + abs((1-loss_after_loss_rate) - overall_win_rate)
                    })
        
        self.results['statistical_significant_patterns'] = {
            'hour_analysis': hour_analysis[:10],  # Top 10
            'strategy_time_patterns': sorted(strategy_time_patterns, key=lambda x: abs(x['difference']), reverse=True)[:20],
            'consecutive_patterns': sorted(consecutive_patterns, key=lambda x: x['consistency_score'], reverse=True)[:10],
            'overall_win_rate': overall_win_rate
        }
        
        print(f"✅ Found {len(hour_analysis)} significant hour patterns")
        print(f"✅ Found {len(strategy_time_patterns)} strategy-time interaction patterns")
        print(f"✅ Found {len(consecutive_patterns)} consecutive patterns")
    
    def advanced_clustering_analysis(self):
        """Advanced clustering to find hidden patterns"""
        print("🔍 Running Advanced Clustering Analysis...")
        
        # Prepare features for clustering
        feature_cols = [
            'hour', 'day_of_week', 'day_of_month',
            'price_change_10min', 'price_change_30min', 'price_change_60min',
            'volatility_10min', 'volatility_30min', 'volatility_60min',
            'win_streak', 'loss_streak', 'rolling_win_rate_10', 'rolling_win_rate_20',
            'trend_direction', 'is_morning', 'is_afternoon', 'is_evening', 'is_night'
        ]
        
        # Clean data for clustering
        clustering_data = self.data[feature_cols + ['win_60min', 'strategy', 'action']].copy()
        clustering_data = clustering_data.dropna()
        
        # Encode categorical variables
        le_strategy = LabelEncoder()
        le_action = LabelEncoder()
        clustering_data['strategy_encoded'] = le_strategy.fit_transform(clustering_data['strategy'])
        clustering_data['action_encoded'] = le_action.fit_transform(clustering_data['action'])
        
        feature_cols_encoded = feature_cols + ['strategy_encoded', 'action_encoded']
        X = clustering_data[feature_cols_encoded]
        y = clustering_data['win_60min']
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-Means clustering
        clustering_results = []
        
        for n_clusters in range(3, 8):
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Analyze each cluster
            cluster_analysis = []
            for cluster in range(n_clusters):
                cluster_mask = cluster_labels == cluster
                cluster_data = clustering_data[cluster_mask]
                
                if len(cluster_data) >= 10:  # Minimum cluster size
                    cluster_win_rate = cluster_data['win_60min'].mean()
                    cluster_size = len(cluster_data)
                    
                    # Cluster characteristics
                    characteristics = {}
                    for col in ['hour', 'strategy', 'action']:
                        mode_value = cluster_data[col].mode().iloc[0] if len(cluster_data[col].mode()) > 0 else 'N/A'
                        characteristics[f'dominant_{col}'] = mode_value
                    
                    characteristics['avg_volatility'] = cluster_data[['volatility_10min', 'volatility_30min', 'volatility_60min']].mean().mean()
                    characteristics['avg_win_streak'] = cluster_data['win_streak'].mean()
                    characteristics['avg_loss_streak'] = cluster_data['loss_streak'].mean()
                    
                    cluster_analysis.append({
                        'cluster_id': cluster,
                        'win_rate': cluster_win_rate,
                        'size': cluster_size,
                        'difference_from_overall': cluster_win_rate - self.data['win_60min'].mean(),
                        'characteristics': characteristics
                    })
            
            clustering_results.append({
                'n_clusters': n_clusters,
                'clusters': sorted(cluster_analysis, key=lambda x: abs(x['difference_from_overall']), reverse=True)
            })
        
        self.results['clustering_results'] = clustering_results
        print(f"✅ Completed clustering analysis for {len(clustering_results)} different cluster configurations")
    
    def advanced_ml_pattern_recognition(self):
        """Advanced ML for pattern recognition with cross-validation"""
        print("🤖 Running Advanced ML Pattern Recognition...")
        
        # Prepare features
        feature_cols = [
            'hour', 'day_of_week', 'day_of_month',
            'price_change_10min', 'price_change_30min', 'price_change_60min',
            'volatility_10min', 'volatility_30min', 'volatility_60min',
            'win_streak', 'loss_streak', 'rolling_win_rate_10', 'rolling_win_rate_20',
            'trend_direction', 'is_morning', 'is_afternoon', 'is_evening', 'is_night'
        ]
        
        # Encode categorical variables
        ml_data = self.data.copy()
        le_strategy = LabelEncoder()
        le_action = LabelEncoder()
        ml_data['strategy_encoded'] = le_strategy.fit_transform(ml_data['strategy'])
        ml_data['action_encoded'] = le_action.fit_transform(ml_data['action'])
        
        feature_cols_encoded = feature_cols + ['strategy_encoded', 'action_encoded']
        
        # Clean data
        ml_data = ml_data[feature_cols_encoded + ['win_60min']].dropna()
        X = ml_data[feature_cols_encoded]
        y = ml_data['win_60min']
        
        # Advanced ML models
        models = {
            'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
            'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=6, random_state=42),
            'LogisticRegression': LogisticRegression(random_state=42, max_iter=1000)
        }
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        ml_results = []
        
        for model_name, model in models.items():
            print(f"🔄 Training {model_name}...")
            
            # Cross-validation scores
            cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
            cv_precision = cross_val_score(model, X, y, cv=cv, scoring='precision')
            cv_recall = cross_val_score(model, X, y, cv=cv, scoring='recall')
            cv_f1 = cross_val_score(model, X, y, cv=cv, scoring='f1')
            
            # Train full model for feature importance
            model.fit(X, y)
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                feature_importance = list(zip(feature_cols_encoded, model.feature_importances_))
                feature_importance.sort(key=lambda x: x[1], reverse=True)
            else:
                feature_importance = []
            
            ml_results.append({
                'model': model_name,
                'cv_accuracy_mean': cv_scores.mean(),
                'cv_accuracy_std': cv_scores.std(),
                'cv_precision_mean': cv_precision.mean(),
                'cv_recall_mean': cv_recall.mean(),
                'cv_f1_mean': cv_f1.mean(),
                'feature_importance': feature_importance[:15]  # Top 15 features
            })
        
        self.results['advanced_ml_insights'] = sorted(ml_results, key=lambda x: x['cv_f1_mean'], reverse=True)
        print(f"✅ Completed ML pattern recognition with {len(models)} models")
    
    def time_series_pattern_analysis(self):
        """Advanced time series pattern analysis"""
        print("📈 Running Time Series Pattern Analysis...")
        
        # Convert to time series
        ts_data = self.data.copy()
        ts_data['entry_time'] = pd.to_datetime(ts_data['entry_time'])
        ts_data = ts_data.sort_values('entry_time')
        
        # Hourly aggregation
        hourly_patterns = []
        for hour in range(24):
            hour_data = ts_data[ts_data['hour'] == hour].copy()
            if len(hour_data) >= 10:
                
                # Daily win rates for this hour
                hour_data['date'] = hour_data['entry_time'].dt.date
                daily_win_rates = hour_data.groupby('date')['win_60min'].mean()
                
                if len(daily_win_rates) >= 3:  # At least 3 days of data
                    consistency = 1 - daily_win_rates.std()  # High consistency = low std
                    trend_slope = np.polyfit(range(len(daily_win_rates)), daily_win_rates.values, 1)[0]
                    
                    hourly_patterns.append({
                        'hour': hour,
                        'overall_win_rate': hour_data['win_60min'].mean(),
                        'consistency_score': consistency,
                        'trend_slope': trend_slope,
                        'days_count': len(daily_win_rates),
                        'total_signals': len(hour_data),
                        'daily_win_rates': daily_win_rates.tolist()
                    })
        
        # Strategy performance over time
        strategy_time_patterns = []
        for strategy in ts_data['strategy'].unique():
            strategy_data = ts_data[ts_data['strategy'] == strategy].copy()
            if len(strategy_data) >= 20:
                
                # Weekly performance
                strategy_data['week_start'] = strategy_data['entry_time'].dt.to_period('W').dt.start_time
                weekly_performance = strategy_data.groupby('week_start')['win_60min'].agg(['mean', 'count']).reset_index()
                weekly_performance = weekly_performance[weekly_performance['count'] >= 3]  # Minimum 3 signals per week
                
                if len(weekly_performance) >= 2:
                    performance_trend = np.polyfit(range(len(weekly_performance)), weekly_performance['mean'].values, 1)[0]
                    performance_std = weekly_performance['mean'].std()
                    
                    strategy_time_patterns.append({
                        'strategy': strategy,
                        'performance_trend': performance_trend,
                        'performance_stability': 1 - performance_std,
                        'weeks_analyzed': len(weekly_performance),
                        'total_signals': len(strategy_data),
                        'current_win_rate': strategy_data['win_60min'].mean()
                    })
        
        self.results['time_series_patterns'] = {
            'hourly_patterns': sorted(hourly_patterns, key=lambda x: (x['consistency_score'], x['overall_win_rate']), reverse=True),
            'strategy_time_patterns': sorted(strategy_time_patterns, key=lambda x: x['performance_stability'], reverse=True)
        }
        
        print(f"✅ Analyzed {len(hourly_patterns)} hourly patterns and {len(strategy_time_patterns)} strategy time patterns")
    
    def generate_actionable_insights(self):
        """Generate actionable insights from all analyses"""
        print("💡 Generating Actionable Insights...")
        
        insights = []
        overall_win_rate = self.data['win_60min'].mean()
        
        # From statistical significance testing
        if 'hour_analysis' in self.results['statistical_significant_patterns']:
            top_hours = [h for h in self.results['statistical_significant_patterns']['hour_analysis'] 
                        if h['significance'] in ['High', 'Medium'] and h['total_signals'] >= 15]
            
            for hour_data in top_hours[:5]:  # Top 5 significant hours
                if hour_data['difference_from_overall'] > 0.15:  # 15% better than overall
                    insights.append({
                        'type': 'Optimal Trading Time',
                        'pattern': f"Hour {hour_data['hour']:02d}:00",
                        'win_rate': f"{hour_data['win_rate']:.1%}",
                        'improvement': f"+{hour_data['difference_from_overall']:.1%} vs overall",
                        'confidence': hour_data['significance'],
                        'sample_size': hour_data['total_signals'],
                        'recommendation': f"Increase trading activity during {hour_data['hour']:02d}:00-{hour_data['hour']+1:02d}:00",
                        'risk_level': 'Low' if hour_data['total_signals'] >= 50 else 'Medium'
                    })
                elif hour_data['difference_from_overall'] < -0.15:  # 15% worse than overall
                    insights.append({
                        'type': 'Avoid Trading Time',
                        'pattern': f"Hour {hour_data['hour']:02d}:00",
                        'win_rate': f"{hour_data['win_rate']:.1%}",
                        'risk': f"{abs(hour_data['difference_from_overall']):.1%} below overall",
                        'confidence': hour_data['significance'],
                        'sample_size': hour_data['total_signals'],
                        'recommendation': f"Avoid or reduce trading during {hour_data['hour']:02d}:00-{hour_data['hour']+1:02d}:00",
                        'risk_level': 'High'
                    })
        
        # From clustering analysis
        if self.results['clustering_results']:
            best_clustering = max(self.results['clustering_results'], 
                                key=lambda x: max([abs(c['difference_from_overall']) for c in x['clusters']]))
            
            for cluster in best_clustering['clusters'][:3]:  # Top 3 clusters
                if abs(cluster['difference_from_overall']) > 0.2 and cluster['size'] >= 20:
                    insights.append({
                        'type': 'Pattern Cluster',
                        'pattern': f"Cluster {cluster['cluster_id']} Pattern",
                        'win_rate': f"{cluster['win_rate']:.1%}",
                        'difference': f"{cluster['difference_from_overall']:+.1%} vs overall",
                        'characteristics': cluster['characteristics'],
                        'sample_size': cluster['size'],
                        'recommendation': 'Focus on' if cluster['difference_from_overall'] > 0 else 'Avoid',
                        'risk_level': 'Low' if cluster['size'] >= 50 else 'Medium'
                    })
        
        # From time series analysis
        if 'hourly_patterns' in self.results['time_series_patterns']:
            consistent_performers = [h for h in self.results['time_series_patterns']['hourly_patterns'] 
                                   if h['consistency_score'] > 0.8 and h['total_signals'] >= 20]
            
            for hour_data in consistent_performers[:3]:
                insights.append({
                    'type': 'Consistent Performance Time',
                    'pattern': f"Hour {hour_data['hour']:02d}:00 (Consistent)",
                    'win_rate': f"{hour_data['overall_win_rate']:.1%}",
                    'consistency': f"{hour_data['consistency_score']:.1%}",
                    'days_analyzed': hour_data['days_count'],
                    'sample_size': hour_data['total_signals'],
                    'recommendation': 'Reliable time slot for consistent performance',
                    'risk_level': 'Very Low'
                })
        
        self.results['actionable_insights'] = sorted(insights, key=lambda x: x.get('sample_size', 0), reverse=True)
        print(f"✅ Generated {len(insights)} actionable insights")
    
    def save_results(self):
        """Save comprehensive analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        with open(f'/Users/puchong/tradingview/report/advanced_deep_analysis_{timestamp}.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save summary report
        report = self.generate_summary_report()
        with open(f'/Users/puchong/tradingview/report/ADVANCED_DEEP_ANALYSIS_REPORT.md', 'w') as f:
            f.write(report)
        
        print("✅ Results saved successfully!")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        report = f"""# Advanced Deep Pattern Analysis Report
## การวิเคราะห์ Pattern อย่างลึกและละเอียดที่สุด

**วันที่วิเคราะห์**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**ข้อมูลที่ใช้**: {len(self.data):,} records จากฐานข้อมูล  
**วิธีการวิเคราะห์**: Statistical Significance + Advanced ML + Clustering + Time Series  

---

## 🎯 สรุปผลการวิเคราะห์

### **Overall Performance**
- **Total Records**: {len(self.data):,}
- **Overall Win Rate**: {self.data['win_60min'].mean():.1%}
- **Analysis Period**: {self.data['entry_time'].min()} ถึง {self.data['entry_time'].max()}

---

## 📊 Significant Patterns ที่พบ (Statistical Significance)

"""
        
        # Add significant hour patterns
        if 'hour_analysis' in self.results['statistical_significant_patterns']:
            report += "### **🕐 เวลาที่มีนัยสำคัญทางสถิติ**\n\n"
            
            significant_hours = [h for h in self.results['statistical_significant_patterns']['hour_analysis'] 
                               if h['significance'] in ['High', 'Medium']]
            
            for i, hour_data in enumerate(significant_hours[:10], 1):
                significance_emoji = "🔥" if hour_data['significance'] == 'High' else "⚡"
                trend_emoji = "📈" if hour_data['difference_from_overall'] > 0 else "📉"
                
                report += f"""**{significance_emoji} #{i} ชั่วโมง {hour_data['hour']:02d}:00** {trend_emoji}
- **Win Rate**: {hour_data['win_rate']:.1%} ({hour_data['difference_from_overall']:+.1%} จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: {hour_data['total_signals']} ครั้ง
- **P-value**: {hour_data['p_value']:.6f}
- **Effect Size**: {hour_data['effect_size']:.3f}
- **ระดับนัยสำคัญ**: {hour_data['significance']}

"""
        
        # Add actionable insights
        if self.results['actionable_insights']:
            report += "\n## 💡 ข้อเสนอแนะที่สามารถนำไปใช้ได้\n\n"
            
            for i, insight in enumerate(self.results['actionable_insights'][:10], 1):
                risk_emoji = "🟢" if insight['risk_level'] == 'Very Low' else "🟡" if insight['risk_level'] == 'Low' else "🟠" if insight['risk_level'] == 'Medium' else "🔴"
                
                report += f"""**{risk_emoji} #{i} {insight['type']}**
- **Pattern**: {insight['pattern']}
- **Win Rate**: {insight.get('win_rate', 'N/A')}
- **ข้อเสนอแนะ**: {insight['recommendation']}
- **ความเสี่ยง**: {insight['risk_level']}
- **จำนวนข้อมูล**: {insight['sample_size']} records

"""
        
        # Add ML insights
        if self.results['advanced_ml_insights']:
            report += "\n## 🤖 ผลการวิเคราะห์ Machine Learning\n\n"
            
            for ml_result in self.results['advanced_ml_insights']:
                report += f"""**{ml_result['model']}**
- **Accuracy**: {ml_result['cv_accuracy_mean']:.3f} ± {ml_result['cv_accuracy_std']:.3f}
- **Precision**: {ml_result['cv_precision_mean']:.3f}
- **Recall**: {ml_result['cv_recall_mean']:.3f}
- **F1-Score**: {ml_result['cv_f1_mean']:.3f}

**Top Features**:
"""
                for feature, importance in ml_result['feature_importance'][:10]:
                    report += f"- {feature}: {importance:.4f}\n"
                report += "\n"
        
        report += f"""
---

## 📈 สถิติการวิเคราะห์

- **Significant Hour Patterns**: {len([h for h in self.results['statistical_significant_patterns']['hour_analysis'] if h['significance'] in ['High', 'Medium']])}
- **Strategy-Time Interactions**: {len(self.results['statistical_significant_patterns']['strategy_time_patterns'])}
- **Clustering Configurations**: {len(self.results['clustering_results'])}
- **ML Models Tested**: {len(self.results['advanced_ml_insights'])}
- **Actionable Insights**: {len(self.results['actionable_insights'])}

---

**รายงานนี้สร้างด้วยการวิเคราะห์ทางสถิติ, Machine Learning, และ Pattern Recognition ขั้นสูง**
"""
        
        return report
    
    def run_complete_analysis(self):
        """Run complete advanced deep analysis"""
        print("🚀 Starting Complete Advanced Deep Pattern Analysis...")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Step 1: Connect and load data
        if not self.connect_database():
            return False
        
        if not self.load_all_data():
            return False
        
        # Step 2: Advanced analyses
        self.statistical_significance_testing()
        self.advanced_clustering_analysis()
        self.advanced_ml_pattern_recognition()
        self.time_series_pattern_analysis()
        
        # Step 3: Generate insights and save results
        self.generate_actionable_insights()
        self.save_results()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        print(f"🎉 Advanced Deep Analysis COMPLETE!")
        print(f"⏱️ Total Duration: {duration}")
        print(f"📊 Records Analyzed: {len(self.data):,}")
        print(f"💡 Insights Generated: {len(self.results['actionable_insights'])}")
        print(f"📁 Results saved to: report/ADVANCED_DEEP_ANALYSIS_REPORT.md")
        print("=" * 80)
        
        return True

if __name__ == "__main__":
    analyzer = AdvancedPatternAnalyzer()
    analyzer.run_complete_analysis()
