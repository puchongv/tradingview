#!/usr/bin/env python3
"""
Deep Learning Analysis for Binary Options Trading
ใช้ Deep Learning เพื่อหาจุดบ่งชี้ที่ส่งผลต่อ win rate และทำนายอนาคต
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Deep Learning libraries
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, GRU, Dropout, BatchNormalization, Input, Concatenate
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

class DeepLearningAnalyzer:
    def __init__(self, data_files):
        """เริ่มต้นการวิเคราะห์ด้วย Deep Learning"""
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
        """ประมวลผลข้อมูลให้พร้อมสำหรับ Deep Learning"""
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
        
        print(f"ข้อมูลครอบคลุม: {self.df['entry_time'].min()} ถึง {self.df['entry_time'].max()}")
        print(f"Strategies: {self.df['strategy'].nunique()} ตัว")
        print(f"Actions: {self.df['action'].nunique()} ตัว")
        print(f"Total Records: {len(self.df)}")
    
    def prepare_features(self):
        """เตรียม features สำหรับ Deep Learning"""
        print("\n=== PREPARING FEATURES ===")
        
        # เลือก features ที่สำคัญ
        feature_columns = [
            'hour', 'day_of_month', 'week_of_year', 'minute',
            'entry_price', 'price_change_10min', 'price_change_30min', 'price_change_60min',
            'volatility_10min', 'volatility_30min', 'volatility_60min',
            'momentum_10min', 'momentum_30min', 'momentum_60min',
            'price_direction_10min', 'price_direction_30min', 'price_direction_60min',
            'market_trend', 'volatility_level', 'price_range'
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
    
    def create_lstm_model(self, input_shape, name):
        """สร้าง LSTM model"""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def create_dense_model(self, input_shape, name):
        """สร้าง Dense model"""
        model = Sequential([
            Dense(256, activation='relu', input_shape=input_shape),
            BatchNormalization(),
            Dropout(0.3),
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def create_ensemble_model(self, input_shape, name):
        """สร้าง Ensemble model"""
        # Input layer
        inputs = Input(shape=input_shape)
        
        # LSTM branch
        lstm_branch = LSTM(64, return_sequences=True)(inputs)
        lstm_branch = Dropout(0.2)(lstm_branch)
        lstm_branch = LSTM(32)(lstm_branch)
        lstm_branch = Dropout(0.2)(lstm_branch)
        
        # Dense branch
        dense_branch = Dense(128, activation='relu')(inputs)
        dense_branch = BatchNormalization()(dense_branch)
        dense_branch = Dropout(0.3)(dense_branch)
        dense_branch = Dense(64, activation='relu')(dense_branch)
        dense_branch = Dropout(0.2)(dense_branch)
        
        # Concatenate branches
        combined = Concatenate()([lstm_branch, dense_branch])
        combined = Dense(64, activation='relu')(combined)
        combined = BatchNormalization()(combined)
        combined = Dropout(0.3)(combined)
        combined = Dense(32, activation='relu')(combined)
        combined = Dropout(0.2)(combined)
        combined = Dense(1, activation='sigmoid')(combined)
        
        model = Model(inputs=inputs, outputs=combined, name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
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
        
        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss', patience=10, restore_best_weights=True
        )
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=0.0001
        )
        
        # ฝึก models
        timeframes = ['10min', '30min', '60min']
        y_train_data = [y_10min_train, y_30min_train, y_60min_train]
        y_test_data = [y_10min_test, y_30min_test, y_60min_test]
        
        for i, (tf_name, y_train, y_test) in enumerate(zip(timeframes, y_train_data, y_test_data)):
            print(f"\nTraining {tf_name} models...")
            
            # Dense Model
            dense_model = self.create_dense_model((X_train.shape[1],), f'dense_{tf_name}')
            dense_history = dense_model.fit(
                X_train, y_train,
                validation_data=(X_test, y_test),
                epochs=100,
                batch_size=32,
                callbacks=[early_stopping, reduce_lr],
                verbose=1
            )
            
            # Ensemble Model
            ensemble_model = self.create_ensemble_model((X_train.shape[1],), f'ensemble_{tf_name}')
            ensemble_history = ensemble_model.fit(
                X_train, y_train,
                validation_data=(X_test, y_test),
                epochs=100,
                batch_size=32,
                callbacks=[early_stopping, reduce_lr],
                verbose=1
            )
            
            # บันทึก models
            self.models[f'dense_{tf_name}'] = dense_model
            self.models[f'ensemble_{tf_name}'] = ensemble_model
            
            # ประเมินผล
            dense_pred = (dense_model.predict(X_test) > 0.5).astype(int)
            ensemble_pred = (ensemble_model.predict(X_test) > 0.5).astype(int)
            
            print(f"\n{tf_name} Results:")
            print(f"Dense Model - Accuracy: {accuracy_score(y_test, dense_pred):.4f}")
            print(f"Ensemble Model - Accuracy: {accuracy_score(y_test, ensemble_pred):.4f}")
    
    def analyze_feature_importance(self, X, feature_columns):
        """วิเคราะห์ความสำคัญของ features"""
        print("\n=== ANALYZING FEATURE IMPORTANCE ===")
        
        # ใช้ permutation importance
        from sklearn.inspection import permutation_importance
        
        feature_importance = {}
        
        for model_name, model in self.models.items():
            if 'dense' in model_name:
                # สำหรับ Dense model
                perm_importance = permutation_importance(
                    model, X, model.predict(X), n_repeats=10, random_state=42
                )
                
                importance_scores = perm_importance.importances_mean
                feature_importance[model_name] = dict(zip(feature_columns, importance_scores))
        
        # รวมความสำคัญจากทุก models
        combined_importance = {}
        for col in feature_columns:
            scores = []
            for model_name, importance in feature_importance.items():
                if col in importance:
                    scores.append(importance[col])
            combined_importance[col] = np.mean(scores) if scores else 0
        
        # เรียงตามความสำคัญ
        sorted_importance = sorted(combined_importance.items(), key=lambda x: x[1], reverse=True)
        
        print("Top 10 Most Important Features:")
        for i, (feature, importance) in enumerate(sorted_importance[:10], 1):
            print(f"{i:2d}. {feature}: {importance:.4f}")
        
        self.feature_importance = combined_importance
        return sorted_importance
    
    def predict_future(self, X_new):
        """ทำนายอนาคต"""
        print("\n=== PREDICTING FUTURE ===")
        
        predictions = {}
        
        for model_name, model in self.models.items():
            pred = model.predict(X_new)
            predictions[model_name] = pred
        
        return predictions
    
    def generate_insights(self, feature_importance):
        """สร้าง insights จากผลการวิเคราะห์"""
        print("\n=== GENERATING INSIGHTS ===")
        
        insights = {
            'top_features': feature_importance[:10],
            'model_performance': {},
            'recommendations': []
        }
        
        # วิเคราะห์ performance ของ models
        for model_name, model in self.models.items():
            # ใช้ข้อมูลทั้งหมดเพื่อประเมิน
            X_all = self.df[list(self.scalers['features'].feature_names_in_)].fillna(0)
            X_all_scaled = self.scalers['features'].transform(X_all)
            
            if '10min' in model_name:
                y_true = self.df['win_10min'].values
            elif '30min' in model_name:
                y_true = self.df['win_30min'].values
            elif '60min' in model_name:
                y_true = self.df['win_60min'].values
            else:
                continue
            
            y_pred = (model.predict(X_all_scaled) > 0.5).astype(int)
            accuracy = accuracy_score(y_true, y_pred)
            
            insights['model_performance'][model_name] = {
                'accuracy': accuracy,
                'total_predictions': len(y_pred),
                'correct_predictions': np.sum(y_pred == y_true)
            }
        
        # สร้างคำแนะนำ
        top_features = [f[0] for f in feature_importance[:5]]
        insights['recommendations'] = [
            f"Focus on top features: {', '.join(top_features)}",
            "Use ensemble models for better accuracy",
            "Monitor feature importance regularly",
            "Retrain models with new data"
        ]
        
        return insights
    
    def save_results(self, insights):
        """บันทึกผลการวิเคราะห์"""
        print("\n=== SAVING RESULTS ===")
        
        # บันทึก feature importance
        with open('feature_importance.json', 'w', encoding='utf-8') as f:
            json.dump(self.feature_importance, f, indent=2, ensure_ascii=False)
        
        # บันทึก insights
        with open('deep_learning_insights.json', 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False, default=str)
        
        # บันทึก models
        for model_name, model in self.models.items():
            model.save(f'models/{model_name}.h5')
        
        print("ผลการวิเคราะห์บันทึกเสร็จ:")
        print("- feature_importance.json")
        print("- deep_learning_insights.json")
        print("- models/ (saved models)")
    
    def run_deep_learning_analysis(self):
        """รันการวิเคราะห์ Deep Learning แบบครบถ้วน"""
        print("เริ่มต้น Deep Learning Analysis...")
        print("="*80)
        
        # เตรียม features
        X, y_10min, y_30min, y_60min, feature_columns = self.prepare_features()
        
        # ฝึก models
        self.train_models(X, y_10min, y_30min, y_60min)
        
        # วิเคราะห์ feature importance
        feature_importance = self.analyze_feature_importance(X, feature_columns)
        
        # สร้าง insights
        insights = self.generate_insights(feature_importance)
        
        # บันทึกผลลัพธ์
        self.save_results(insights)
        
        print("\n" + "="*80)
        print("DEEP LEARNING ANALYSIS COMPLETE")
        print("="*80)
        
        return insights

if __name__ == "__main__":
    # กำหนดไฟล์ข้อมูล
    data_files = [
        "Result Last 120HR.csv",
        "Result 2568-09-11 22-54-00.csv"
    ]
    
    # เริ่มต้น Deep Learning Analyzer
    analyzer = DeepLearningAnalyzer(data_files)
    
    # รันการวิเคราะห์ Deep Learning
    insights = analyzer.run_deep_learning_analysis()
