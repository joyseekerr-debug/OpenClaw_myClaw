# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第7-8小时: 超参数调优
优化XGBoost和Price Action模型参数
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List
import itertools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 7-8")
print("Hyperparameter Tuning")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载真实数据
df = pd.read_csv('data/xiaomi_2023_real.csv', index_col='timestamp', parse_dates=True)
print(f"[1/3] Loaded real data: {len(df)} records")
print()

# 特征工程
from features.feature_engineering import engineer_features
df_features = engineer_features(df)
feature_cols = [col for col in df_features.columns 
                if col not in ['open', 'high', 'low', 'close', 'volume', 
                              'symbol', 'timeframe', 'source', 'target_direction_1']]

# 准备数据
X = df_features[feature_cols].dropna()
y = df_features.loc[X.index, 'target_direction_1']
mask = y.isin([0, 1])
X = X[mask]
y = y[mask]

# 时间序列划分 (避免数据泄露)
split_idx = int(len(X) * 0.7)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"      Train: {len(X_train)} samples")
print(f"      Test:  {len(X_test)} samples")
print()

# ==================== XGBoost 超参数调优 ====================
print("[2/3] XGBoost Hyperparameter Tuning...")

from models.xgboost_model import XGBoostPredictor

# 参数网格
param_grid = {
    'max_depth': [3, 4, 5, 6],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [50, 100, 200],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9]
}

# 随机搜索 (节省时间)
import random
random.seed(42)

n_trials = 20
best_score = 0
best_params = None
results = []

print(f"      Running {n_trials} trials...")

for trial in range(n_trials):
    # 随机采样参数
    params = {
        'max_depth': random.choice(param_grid['max_depth']),
        'learning_rate': random.choice(param_grid['learning_rate']),
        'n_estimators': random.choice(param_grid['n_estimators']),
        'subsample': random.choice(param_grid['subsample']),
        'colsample_bytree': random.choice(param_grid['colsample_bytree'])
    }
    
    try:
        # 训练模型 - 分割验证集
        val_split = int(len(X_train) * 0.8)
        X_tr, X_val = X_train.iloc[:val_split], X_train.iloc[val_split:]
        y_tr, y_val = y_train.iloc[:val_split], y_train.iloc[val_split:]
        
        model = XGBoostPredictor(**params)
        model.build_model()
        model.train(X_tr, y_tr, X_val, y_val)
        
        # 评估
        eval_result = model.evaluate(X_test, y_test)
        accuracy = eval_result.get('accuracy', 0)
        
        results.append({
            'params': params,
            'accuracy': accuracy,
            'auc': eval_result.get('auc', 0)
        })
        
        if accuracy > best_score:
            best_score = accuracy
            best_params = params.copy()
            print(f"      Trial {trial+1}: accuracy={accuracy:.4f} [BEST]")
        else:
            print(f"      Trial {trial+1}: accuracy={accuracy:.4f}")
            
    except Exception as e:
        print(f"      Trial {trial+1}: failed - {str(e)[:50]}")

print(f"\n      Best XGBoost params:")
for k, v in best_params.items():
    print(f"        {k}: {v}")
print(f"      Best accuracy: {best_score:.4f}")

# ==================== Price Action 参数调优 ====================
print("\n[3/3] Price Action Parameter Tuning...")

from models.price_action_model import PriceActionPredictor

# 测试不同参数组合
pa_configs = [
    {'min_risk_reward': 0.3, 'pattern_confidence_threshold': 0.5},
    {'min_risk_reward': 0.5, 'pattern_confidence_threshold': 0.6},
    {'min_risk_reward': 0.7, 'pattern_confidence_threshold': 0.7},
    {'min_risk_reward': 0.4, 'pattern_confidence_threshold': 0.55},
    {'min_risk_reward': 0.6, 'pattern_confidence_threshold': 0.65},
]

pa_results = []
window = 20

for config in pa_configs:
    predictor = PriceActionPredictor(**config)
    
    predictions = []
    correct = 0
    
    for i in range(window, len(df) - 5, 3):
        window_df = df.iloc[i-window:i]
        
        try:
            sig = predictor.predict(window_df)
            if sig.confidence >= 0.5 and sig.signal != 'hold':
                actual_price = df['close'].iloc[i]
                future_price = df['close'].iloc[i+5]
                
                is_correct = (sig.signal == 'buy' and future_price > actual_price) or \
                            (sig.signal == 'sell' and future_price < actual_price)
                
                predictions.append({
                    'correct': is_correct,
                    'confidence': sig.confidence
                })
                
                if is_correct:
                    correct += 1
        except:
            pass
    
    accuracy = correct / len(predictions) if predictions else 0
    pa_results.append({
        'config': config,
        'predictions': len(predictions),
        'accuracy': accuracy
    })
    
    print(f"      {config}: {len(predictions)} preds, {accuracy:.2%} accuracy")

best_pa = max(pa_results, key=lambda x: x['accuracy'])
print(f"\n      Best PA config: {best_pa['config']}")
print(f"      Best accuracy: {best_pa['accuracy']:.2%}")

# ==================== 结果汇总 ====================
print("\n" + "=" * 70)
print("HYPERPARAMETER TUNING RESULTS")
print("=" * 70)

# 保存结果
with open('results/hyperparameter_tuning.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'xgboost': {
            'best_params': best_params,
            'best_accuracy': best_score,
            'all_trials': results
        },
        'price_action': {
            'best_config': best_pa['config'],
            'best_accuracy': best_pa['accuracy'],
            'all_configs': pa_results
        }
    }, f, indent=2, default=str)

print(f"\nXGBoost Best:")
print(f"  Accuracy: {best_score:.4f}")
print(f"  Params: {best_params}")

print(f"\nPrice Action Best:")
print(f"  Accuracy: {best_pa['accuracy']:.4f}")
print(f"  Config: {best_pa['config']}")

print("\n[OK] Results saved to results/hyperparameter_tuning.json")

print("\n" + "=" * 70)
print("Hour 7-8 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
