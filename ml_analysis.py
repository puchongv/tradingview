#!/usr/bin/env python3
"""
Machine Learning Analysis for Binary Options Trading
ใช้ Machine Learning เพื่อหาจุดบ่งชี้ที่ส่งผลต่อ win rate และทำนายอนาคต
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Machine Learning libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt
import seaborn as sns
import json

class MachineLearningAnalyzer:
    def __init__(self, data_files):
        """เริ่มต้นการวิเคราะห์ด้วย Machine Learning"""
        self.data_files = data_files
        self.df = None
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.load_all_data()
    
    def load_all_data(self):
        """โหลดข้อมูลจากไฟล์ทั้งหมด"""
        print("กำลังโหลดข้อมูลจากไฟล์ทั้งหมด...")
        
        all_dataframes = []
        
        for file_path in self.data_files:
            try:
                print(f"โหลดข้อมูลจาก: {file_path}")
                df = pd.read_csv(file_path)
                df['source_file'] = file_path
                all_dataframes.append(df)
                print(f"  - {len(df)} records")
            except Exception as e:
                print(f"ไม่สามารถโหลดไฟล์ {file_path}: {e}")
        
        if all_dataframes:
            self.df = pd.concat(all_dataframes, ignore_index=True)
            print(f"รวมข้อมูลทั้งหมด: {len(self.df)} records")
        else:
            raise ValueError("ไม่พบข้อมูลใดๆ")
        
        # ประมวลผลข้อมูล
        self.process_data()
    
    def process_data(self):
        """ประมวลผลข้อมูลให้พร้อมสำหรับ Machine Learning"""
        print("กำลังประมวลผลข้อมูล...")
        
        # แปลงคอลัมน์เวลา
        self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])
        self.df['price_10min_ts'] = pd.to_datetime(self.df['price_10min_ts'])
        self.df['price_30min_ts'] = pd.to_datetime(self.df['price_30min_ts'])
        self.df['price_60min_ts'] = pd.to_datetime(self.df['price_60min_ts'])
        
        # สร้าง features ใหม่
        self.df['hour'] = self.df['entry_time'].dt.hour
        self.df['day_of_week'] = self.df['entry_time'].dt.day_name()
        self.df['date'] = self.df['entry_time'].dt.date
        self.df['minute'] = self.df['entry_time'].dt.minute
        self.df['day_of_month'] = self.df['entry_time'].dt.day
        self.df['week_of_year'] = self.df['entry_time'].dt.isocalendar().week
        
        # คำนวณ win rate
        self.df['win_10min'] = (self.df['result_10min'] == 'WIN').astype(int)
        self.df['win_30min'] = (self.df['result_30min'] == 'WIN').astype(int)
        self.df['win_60min'] = (self.df['result_60min'] == 'WIN').astype(int)
        
        # คำนวณ price changes และ volatility
        self.df['price_change_10min'] = ((self.df['price_10min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        self.df['price_change_30min'] = ((self.df['price_30min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        self.df['price_change_60min'] = ((self.df['price_60min'] - self.df['entry_price']) / self.df['entry_price'] * 100)
        
        self.df['volatility_10min'] = abs(self.df['price_change_10min'])
        self.df['volatility_30min'] = abs(self.df['price_change_30min'])
        self.df['volatility_60min'] = abs(self.df['price_change_60min'])
        
        # คำนวณ price momentum
        self.df['momentum_10min'] = np.where(self.df['price_change_10min'] > 0, 1, 
                                           np.where(self.df['price_change_10min'] < 0, -1, 0))
        self.df['momentum_30min'] = np.where(self.df['price_change_30min'] > 0, 1, 
                                           np.where(self.df['price_change_30min'] < 0, -1, 0))
        self.df['momentum_60min'] = np.where(self.df['price_change_60min'] > 0, 1, 
                                           np.where(self.df['price_change_60min'] < 0, -1, 0))
        
        # คำนวณ price direction
        self.df['price_direction_10min'] = np.where(self.df['price_change_10min'] > 0, 1, 0)
        self.df['price_direction_30min'] = np.where(self.df['price_change_30min'] > 0, 1, 0)
        self.df['price_direction_60min'] = np.where(self.df['price_change_60min'] > 0, 1, 0)
        
        # คำนวณ market trend
        trend_ranges = pd.cut(self.df['price_change_60min'], bins=4, labels=[0, 1, 2, 3])
        self.df['market_trend'] = trend_ranges.astype(int)
        
        # คำนวณ volatility level
        vol_ranges = pd.cut(self.df['volatility_60min'], bins=3, labels=[0, 1, 2])
        self.df['volatility_level'] = vol_ranges.astype(int)
        
        # คำนวณ price range
        price_ranges = pd.cut(self.df['entry_price'], bins=10, labels=False)
        self.df['price_range'] = price_ranges
        
        # สร้าง features เพิ่มเติม
        self.create_advanced_features()
        
        print(f"ข้อมูลครอบคลุม: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        print(f"Total Records: {len(self.df)}")
    
    def create_advanced_features(self):
        """สร้าง features ขั้นสูง"""
        print("สร้าง advanced features...")
        
        # เรียงข้อมูลตามเวลา
        self.df = self.df.sort_values(['strategy', 'entry_time']).reset_index(drop=True)
        
        # สร้าง rolling features
        for strategy in self.df['strategy'].unique():
            strategy_mask = self.df['strategy'] == strategy
            strategy_data = self.df[strategy_mask].copy()
            
            # Rolling win rate
            self.df.loc[strategy_mask, 'rolling_win_rate_10'] = strategy_data['win_60min'].rolling(window=10, min_periods=1).mean()
            self.df.loc[strategy_mask, 'rolling_win_rate_20'] = strategy_data['win_60min'].rolling(window=20, min_periods=1).mean()
            
            # Rolling volatility
            self.df.loc[strategy_mask, 'rolling_volatility_10'] = strategy_data['volatility_60min'].rolling(window=10, min_periods=1).mean()
            self.df.loc[strategy_mask, 'rolling_volatility_20'] = strategy_data['volatility_60min'].rolling(window=20, min_periods=1).mean()
            
            # Previous results
            self.df.loc[strategy_mask, 'prev_win_60min'] = strategy_data['win_60min'].shift(1)
            self.df.loc[strategy_mask, 'prev_2_win_60min'] = strategy_data['win_60min'].shift(2)
            self.df.loc[strategy_mask, 'prev_3_win_60min'] = strategy_data['win_60min'].shift(3)
            
            # Win streak
            self.df.loc[strategy_mask, 'win_streak'] = (strategy_data['win_60min'] * (strategy_data['win_60min'].groupby((strategy_data['win_60min'] != strategy_data['win_60min'].shift()).cumsum()).cumcount() + 1)).where(strategy_data['win_60min'] == 1, 0)
            
            # Loss streak
            self.df.loc[strategy_mask, 'loss_streak'] = ((1 - strategy_data['win_60min']) * ((1 - strategy_data['win_60min']).groupby(((1 - strategy_data['win_60min']) != (1 - strategy_data['win_60min']).shift()).cumsum()).cumcount() + 1)).where(strategy_data['win_60min'] == 0, 0)
        
        # สร้าง time-based features
        self.df['is_weekend'] = self.df['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)
        self.df['is_morning'] = ((self.df['hour'] >= 6) & (self.df['hour'] < 12)).astype(int)
        self.df['is_afternoon'] = ((self.df['hour'] >= 12) & (self.df['hour'] < 18)).astype(int)
        self.df['is_evening'] = ((self.df['hour'] >= 18) & (self.df['hour'] < 24)).astype(int)
        self.df['is_night'] = ((self.df['hour'] >= 0) & (self.df['hour'] < 6)).astype(int)
        
        # สร้าง interaction features
        self.df['strategy_action_interaction'] = self.df['strategy'].astype(str) + '_' + self.df['action'].astype(str)
        self.df['hour_strategy_interaction'] = self.df['hour'].astype(str) + '_' + self.df['strategy'].astype(str)
        
        print("Advanced features created successfully")
    
    def prepare_features(self):
        """เตรียม features สำหรับ Machine Learning"""
        print("\n=== PREPARING FEATURES ===")
        
        # เลือก features ที่สำคัญ
        feature_columns = [
            'hour', 'day_of_month', 'week_of_year', 'minute',
            'entry_price', 'price_change_10min', 'price_change_30min', 'price_change_60min',
            'volatility_10min', 'volatility_30min', 'volatility_60min',
            'momentum_10min', 'momentum_30min', 'momentum_60min',
            'price_direction_10min', 'price_direction_30min', 'price_direction_60min',
            'market_trend', 'volatility_level', 'price_range',
            'rolling_win_rate_10', 'rolling_win_rate_20',
            'rolling_volatility_10', 'rolling_volatility_20',
            'prev_win_60min', 'prev_2_win_60min', 'prev_3_win_60min',
            'win_streak', 'loss_streak',
            'is_weekend', 'is_morning', 'is_afternoon', 'is_evening', 'is_night'
        ]
        
        # สร้าง categorical features
        categorical_columns = ['strategy', 'action', 'day_of_week']
        
        # Encode categorical features
        for col in categorical_columns:
            le = LabelEncoder()
            self.df[f'{col}_encoded'] = le.fit_transform(self.df[col])
            self.encoders[col] = le
            feature_columns.append(f'{col}_encoded')
        
        # เลือก features
        X = self.df[feature_columns].fillna(0)
        
        # เลือก target variables
        y_10min = self.df['win_10min'].values
        y_30min = self.df['win_30min'].values
        y_60min = self.df['win_60min'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['features'] = scaler
        
        print(f"Features: {len(feature_columns)} features")
        print(f"Feature columns: {feature_columns}")
        print(f"Target variables: win_10min, win_30min, win_60min")
        
        return X_scaled, y_10min, y_30min, y_60min, feature_columns
    
    def create_models(self):
        """สร้าง Machine Learning models"""
        print("\n=== CREATING MODELS ===")
        
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'neural_network': MLPClassifier(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                solver='adam',
                alpha=0.001,
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            ),
            'svm': SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                probability=True,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                C=1.0,
                max_iter=1000,
                random_state=42
            )
        }
        
        return models
    
    def train_models(self, X, y_10min, y_30min, y_60min):
        """ฝึก models สำหรับแต่ละ timeframe"""
        print("\n=== TRAINING MODELS ===")
        
        # แบ่งข้อมูล train/test
        X_train, X_test, y_10min_train, y_10min_test = train_test_split(
            X, y_10min, test_size=0.2, random_state=42, stratify=y_10min
        )
        
        X_train, X_test, y_30min_train, y_30min_test = train_test_split(
            X, y_30min, test_size=0.2, random_state=42, stratify=y_30min
        )
        
        X_train, X_test, y_60min_train, y_60min_test = train_test_split(
            X, y_60min, test_size=0.2, random_state=42, stratify=y_60min
        )
        
        # สร้าง models
        base_models = self.create_models()
        
        # ฝึก models
        timeframes = ['10min', '30min', '60min']
        y_train_data = [y_10min_train, y_30min_train, y_60min_train]
        y_test_data = [y_10min_test, y_30min_test, y_60min_test]
        
        for i, (tf_name, y_train, y_test) in enumerate(zip(timeframes, y_train_data, y_test_data)):
            print(f"\nTraining {tf_name} models...")
            
            # ฝึกแต่ละ model
            for model_name, model in base_models.items():
                print(f"  Training {model_name}...")
                
                # ฝึก model
                model.fit(X_train, y_train)
                
                # ประเมินผล
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                # บันทึก model
                self.models[f'{model_name}_{tf_name}'] = model
                
                print(f"    Accuracy: {accuracy:.4f}")
            
            # สร้าง Ensemble model
            ensemble_models = [
                base_models['random_forest'],
                base_models['gradient_boosting'],
                base_models['neural_network']
            ]
            
            ensemble = VotingClassifier(
                estimators=[(f'{name}_{tf_name}', model) for name, model in zip(['rf', 'gb', 'nn'], ensemble_models)],
                voting='soft'
            )
            
            ensemble.fit(X_train, y_train)
            y_pred_ensemble = ensemble.predict(X_test)
            accuracy_ensemble = accuracy_score(y_test, y_pred_ensemble)
            
            self.models[f'ensemble_{tf_name}'] = ensemble
            print(f"  Ensemble Accuracy: {accuracy_ensemble:.4f}")
    
    def analyze_feature_importance(self, X, feature_columns):
        """วิเคราะห์ความสำคัญของ features"""
        print("\n=== ANALYZING FEATURE IMPORTANCE ===")
        
        # ใช้ Random Forest เพื่อหาความสำคัญ
        rf_model = self.models.get('random_forest_60min')
        if rf_model is not None:
            feature_importance = dict(zip(feature_columns, rf_model.feature_importances_))
        else:
            # ใช้ permutation importance
            feature_importance = {}
            for model_name, model in self.models.items():
                if '60min' in model_name and hasattr(model, 'feature_importances_'):
                    importance_scores = model.feature_importances_
                    feature_importance[model_name] = dict(zip(feature_columns, importance_scores))
            
            # รวมความสำคัญจากทุก models
            combined_importance = {}
            for col in feature_columns:
                scores = []
                for model_name, importance in feature_importance.items():
                    if col in importance:
                        scores.append(importance[col])
                combined_importance[col] = np.mean(scores) if scores else 0
            
            feature_importance = combined_importance
        
        # เรียงตามความสำคัญ
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        print("Top 15 Most Important Features:")
        for i, (feature, importance) in enumerate(sorted_importance[:15], 1):
            print(f"{i:2d}. {feature}: {importance:.4f}")
        
        self.feature_importance = feature_importance
        return sorted_importance
    
    def evaluate_models(self, X, y_10min, y_30min, y_60min):
        """ประเมินผล models"""
        print("\n=== EVALUATING MODELS ===")
        
        evaluation_results = {}
        
        timeframes = ['10min', '30min', '60min']
        y_data = [y_10min, y_30min, y_60min]
        
        for tf_name, y_true in zip(timeframes, y_data):
            print(f"\n{tf_name} Results:")
            evaluation_results[tf_name] = {}
            
            for model_name, model in self.models.items():
                if tf_name in model_name:
                    # ทำนาย
                    y_pred = model.predict(X)
                    y_pred_proba = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else None
                    
                    # คำนวณ metrics
                    accuracy = accuracy_score(y_true, y_pred)
                    auc = roc_auc_score(y_true, y_pred_proba) if y_pred_proba is not None else 0
                    
                    evaluation_results[tf_name][model_name] = {
                        'accuracy': accuracy,
                        'auc': auc,
                        'total_predictions': len(y_pred),
                        'correct_predictions': np.sum(y_pred == y_true)
                    }
                    
                    print(f"  {model_name}: Accuracy={accuracy:.4f}, AUC={auc:.4f}")
        
        return evaluation_results
    
    def generate_insights(self, feature_importance, evaluation_results):
        """สร้าง insights จากผลการวิเคราะห์"""
        print("\n=== GENERATING INSIGHTS ===")
        
        insights = {
            'top_features': feature_importance[:15],
            'model_performance': evaluation_results,
            'recommendations': [],
            'key_findings': []
        }
        
        # หา model ที่ดีที่สุด
        best_models = {}
        for tf_name, models in evaluation_results.items():
            best_model = max(models.items(), key=lambda x: x[1]['accuracy'])
            best_models[tf_name] = best_model
        
        # สร้าง key findings
        insights['key_findings'] = [
            f"Best model for 10min: {best_models['10min'][0]} (Accuracy: {best_models['10min'][1]['accuracy']:.4f})",
            f"Best model for 30min: {best_models['30min'][0]} (Accuracy: {best_models['30min'][1]['accuracy']:.4f})",
            f"Best model for 60min: {best_models['60min'][0]} (Accuracy: {best_models['60min'][1]['accuracy']:.4f})",
            f"Top 3 features: {', '.join([f[0] for f in feature_importance[:3]])}",
            f"Total features analyzed: {len(feature_importance)}"
        ]
        
        # สร้างคำแนะนำ
        top_features = [f[0] for f in feature_importance[:5]]
        insights['recommendations'] = [
            f"Focus on top features: {', '.join(top_features)}",
            "Use ensemble models for better accuracy",
            "Monitor feature importance regularly",
            "Retrain models with new data",
            "Consider feature engineering for top features"
        ]
        
        return insights
    
    def save_results(self, insights):
        """บันทึกผลการวิเคราะห์"""
        print("\n=== SAVING RESULTS ===")
        
        # บันทึก feature importance
        with open('ml_feature_importance.json', 'w', encoding='utf-8') as f:
            json.dump(self.feature_importance, f, indent=2, ensure_ascii=False)
        
        # บันทึก insights
        with open('ml_insights.json', 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False, default=str)
        
        print("ผลการวิเคราะห์บันทึกเสร็จ:")
        print("- ml_feature_importance.json")
        print("- ml_insights.json")
    
    def run_ml_analysis(self):
        """รันการวิเคราะห์ Machine Learning แบบครบถ้วน"""
        print("เริ่มต้น Machine Learning Analysis...")
        print("="*80)
        
        # เตรียม features
        X, y_10min, y_30min, y_60min, feature_columns = self.prepare_features()
        
        # ฝึก models
        self.train_models(X, y_10min, y_30min, y_60min)
        
        # วิเคราะห์ feature importance
        feature_importance = self.analyze_feature_importance(X, feature_columns)
        
        # ประเมิน models
        evaluation_results = self.evaluate_models(X, y_10min, y_30min, y_60min)
        
        # สร้าง insights
        insights = self.generate_insights(feature_importance, evaluation_results)
        
        # บันทึกผลลัพธ์
        self.save_results(insights)
        
        print("\n" + "="*80)
        print("MACHINE LEARNING ANALYSIS COMPLETE")
        print("="*80)
        
        return insights

if __name__ == "__main__":
    # กำหนดไฟล์ข้อมูล
    data_files = [
        "Result Last 120HR.csv",
        "Result 2568-09-11 22-54-00.csv"
    ]
    
    # เริ่มต้น Machine Learning Analyzer
    analyzer = MachineLearningAnalyzer(data_files)
    
    # รันการวิเคราะห์ Machine Learning
    insights = analyzer.run_ml_analysis()
