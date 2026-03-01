# -*- coding: utf-8 -*-
"""
24小时优化 - Hour 5-6: 模型升级
LSTM/Transformer多尺度集成模型
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization - Hour 5-6: Model Upgrade")
print("LSTM/Transformer Multi-Scale Ensemble")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载增强数据
print("[1/4] Loading enhanced data...")
import pickle
with open('data/enhanced_multi_stock_2020_2024.pkl', 'rb') as f:
    enhanced_data = pickle.load(f)

# 使用小米数据作为主要训练集
df = enhanced_data['1810.HK'].copy()
print(f"      Using 1810.HK: {len(df)} records, {len(df.columns)} features")

# 准备特征和目标
feature_cols = [c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume']]
X = df[feature_cols].dropna()

# 创建目标变量 (5天后收益率方向)
df['target'] = (df['close'].shift(-5) / df['close'] - 1).apply(lambda x: 1 if x > 0.02 else (0 if x < -0.02 else 2))
X = X[X.index.isin(df.index)]
y = df.loc[X.index, 'target']

# 只保留涨跌样本 (去掉持有)
mask = y != 2
X = X[mask]
y = y[mask]

print(f"      Training samples: {len(X)}")
print(f"      Features: {len(feature_cols)}")

# 时间序列划分
split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"      Train: {len(X_train)}, Test: {len(X_test)}")
print()

# ==================== XGBoost基准模型 ====================
print("[2/4] Training XGBoost baseline...")

from models.xgboost_model import XGBoostPredictor

xgb_params = {
    'max_depth': 4,
    'learning_rate': 0.05,
    'n_estimators': 150,
    'subsample': 0.8,
    'colsample_bytree': 0.8
}

xgb_model = XGBoostPredictor(**xgb_params)
xgb_model.build_model()

# 划分验证集
val_split = int(len(X_train) * 0.8)
xgb_model.train(X_train.iloc[:val_split], y_train.iloc[:val_split], 
                X_train.iloc[val_split:], y_train.iloc[val_split:])

# 评估
xgb_eval = xgb_model.evaluate(X_test, y_test)
print(f"      XGBoost Test Accuracy: {xgb_eval.get('accuracy', 0):.4f}")
print(f"      XGBoost F1: {xgb_eval.get('f1_score', 0):.4f}")
print()

# ==================== LSTM模型 ====================
print("[3/4] Training LSTM model...")

# 尝试导入TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
    print("      TensorFlow available")
except ImportError:
    TF_AVAILABLE = False
    print("      TensorFlow not available, skipping LSTM")

lstm_results = {}

if TF_AVAILABLE:
    # 准备序列数据
    sequence_length = 60  # 60天序列
    
    def create_sequences(X, y, seq_length):
        X_seq, y_seq = [], []
        for i in range(len(X) - seq_length):
            X_seq.append(X.iloc[i:i+seq_length].values)
            y_seq.append(y.iloc[i+seq_length])
        return np.array(X_seq), np.array(y_seq)
    
    X_seq_train, y_seq_train = create_sequences(X_train, y_train, sequence_length)
    X_seq_test, y_seq_test = create_sequences(X_test, y_test, sequence_length)
    
    print(f"      Sequence data: train={len(X_seq_train)}, test={len(X_seq_test)}")
    
    # 构建LSTM模型
    n_features = X_train.shape[1]
    
    lstm_model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(sequence_length, n_features)),
        BatchNormalization(),
        Dropout(0.3),
        LSTM(32, return_sequences=False),
        BatchNormalization(),
        Dropout(0.3),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    lstm_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    # 早停
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    
    # 训练
    history = lstm_model.fit(
        X_seq_train, y_seq_train,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=0
    )
    
    # 评估
    lstm_loss, lstm_acc = lstm_model.evaluate(X_seq_test, y_seq_test, verbose=0)
    print(f"      LSTM Test Accuracy: {lstm_acc:.4f}")
    print(f"      Epochs trained: {len(history.history['loss'])}")
    
    lstm_results = {
        'accuracy': float(lstm_acc),
        'epochs': len(history.history['loss'])
    }
else:
    lstm_results = {'error': 'TensorFlow not available'}

print()

# ==================== 集成预测 ====================
print("[4/4] Ensemble prediction...")

class MultiScaleEnsemble:
    """多尺度集成模型"""
    
    def __init__(self, xgb_model, lstm_model=None):
        self.xgb_model = xgb_model
        self.lstm_model = lstm_model
        self.xgb_weight = 0.6
        self.lstm_weight = 0.4 if lstm_model else 0
    
    def predict(self, X_xgb, X_lstm=None):
        """集成预测"""
        # XGBoost预测
        xgb_pred = self.xgb_model.predict(X_xgb)
        xgb_prob = xgb_pred['confidence'] if xgb_pred['prediction'] == 'up' else 1 - xgb_pred['confidence']
        
        if self.lstm_model and X_lstm is not None:
            # LSTM预测
            lstm_prob = float(self.lstm_model.predict(X_lstm.reshape(1, *X_lstm.shape), verbose=0)[0][0])
            
            # 加权集成
            ensemble_prob = self.xgb_weight * xgb_prob + self.lstm_weight * lstm_prob
        else:
            ensemble_prob = xgb_prob
        
        return {
            'prediction': 'up' if ensemble_prob > 0.5 else 'down',
            'confidence': float(ensemble_prob),
            'xgb_component': float(xgb_prob)
        }

# 测试集成模型
ensemble = MultiScaleEnsemble(xgb_model, lstm_model if TF_AVAILABLE else None)

# 在测试集上评估
ensemble_preds = []
for i in range(min(50, len(X_test))):  # 评估50个样本
    pred = ensemble.predict(X_test.iloc[i:i+1])
    
    # 获取真实标签
    actual = y_test.iloc[i]
    correct = (pred['prediction'] == 'up' and actual == 1) or (pred['prediction'] == 'down' and actual == 0)
    
    ensemble_preds.append({
        'predicted': pred['prediction'],
        'confidence': pred['confidence'],
        'actual': 'up' if actual == 1 else 'down',
        'correct': correct
    })

ensemble_acc = sum(p['correct'] for p in ensemble_preds) / len(ensemble_preds)
print(f"      Ensemble Accuracy (50 samples): {ensemble_acc:.4f}")

# ==================== 保存结果 ====================
print("\n" + "=" * 70)
print("MODEL UPGRADE SUMMARY")
print("=" * 70)

results = {
    'timestamp': datetime.now().isoformat(),
    'phase': 'Hour 5-6: Model Upgrade',
    'models': {
        'xgboost': {
            'accuracy': float(xgb_eval.get('accuracy', 0)),
            'f1_score': float(xgb_eval.get('f1_score', 0)),
            'params': xgb_params
        },
        'lstm': lstm_results,
        'ensemble': {
            'accuracy': float(ensemble_acc),
            'xgb_weight': 0.6,
            'lstm_weight': 0.4 if TF_AVAILABLE else 0
        }
    }
}

print(f"\n  XGBoost:")
print(f"    Accuracy: {results['models']['xgboost']['accuracy']:.4f}")
print(f"    F1 Score: {results['models']['xgboost']['f1_score']:.4f}")

if TF_AVAILABLE:
    print(f"\n  LSTM:")
    print(f"    Accuracy: {results['models']['lstm']['accuracy']:.4f}")

print(f"\n  Ensemble:")
print(f"    Accuracy: {results['models']['ensemble']['accuracy']:.4f}")

# 保存模型
import pickle
with open('models/xgb_baseline.pkl', 'wb') as f:
    pickle.dump(xgb_model, f)

if TF_AVAILABLE:
    lstm_model.save('models/lstm_model.keras')
    print("\n  Models saved to models/")

with open('results/hour_5_6_model_upgrade.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n[OK] Results saved to results/hour_5_6_model_upgrade.json")

print("\n" + "=" * 70)
print("Hour 5-6 completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
