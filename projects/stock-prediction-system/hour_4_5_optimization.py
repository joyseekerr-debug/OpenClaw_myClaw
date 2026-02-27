# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第4-5小时: 策略参数优化
优化Price Action模型的阈值参数
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 4-5")
print("Strategy Parameter Optimization")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load real data
df = pd.read_csv('data/xiaomi_2023_real.csv', index_col='timestamp', parse_dates=True)

print("[1/3] Testing different confidence thresholds...")

# Test different confidence thresholds
thresholds = [0.5, 0.55, 0.6, 0.65, 0.7]
results = []

from models.price_action_model import PriceActionPredictor

for threshold in thresholds:
    predictor = PriceActionPredictor(min_risk_reward=threshold)
    
    # Generate predictions
    predictions = []
    window = 20
    
    for i in range(window, len(df), 3):  # Every 3 days for more signals
        window_df = df.iloc[i-window:i]
        
        try:
            sig = predictor.predict(window_df)
            if sig.confidence >= threshold and sig.signal != 'hold':
                predictions.append({
                    'index': i,
                    'signal': sig.signal,
                    'confidence': sig.confidence,
                    'actual_price': df['close'].iloc[i],
                    'actual_next': df['close'].iloc[min(i+5, len(df)-1)]
                })
        except:
            pass
    
    # Calculate accuracy
    if predictions:
        correct = sum(1 for p in predictions 
                     if (p['signal'] == 'buy' and p['actual_next'] > p['actual_price']) or
                        (p['signal'] == 'sell' and p['actual_next'] < p['actual_price']))
        accuracy = correct / len(predictions)
    else:
        accuracy = 0
    
    results.append({
        'threshold': threshold,
        'predictions': len(predictions),
        'accuracy': accuracy
    })
    
    print(f"  Threshold {threshold}: {len(predictions)} predictions, {accuracy:.2%} accuracy")

# Find best threshold
best = max(results, key=lambda x: x['accuracy'] if x['predictions'] >= 3 else 0)
print(f"\n  Best threshold: {best['threshold']} with {best['accuracy']:.2%} accuracy")

# Save optimization results
import json
with open('results/parameter_optimization.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'optimization': 'confidence_threshold',
        'results': results,
        'best_threshold': best['threshold'],
        'best_accuracy': best['accuracy']
    }, f, indent=2)

print("\n[2/3] Testing different lookback periods...")

# Test different lookback periods
lookbacks = [10, 20, 30, 50]
lb_results = []

for lookback in lookbacks:
    predictor = PriceActionPredictor()
    predictor.sr_detector.lookback = lookback
    
    predictions = []
    for i in range(lookback, len(df), 5):
        window_df = df.iloc[i-lookback:i]
        
        try:
            sig = predictor.predict(window_df)
            if sig.signal != 'hold':
                predictions.append({
                    'index': i,
                    'signal': sig.signal,
                    'actual_price': df['close'].iloc[i],
                    'actual_next': df['close'].iloc[min(i+5, len(df)-1)]
                })
        except:
            pass
    
    if predictions:
        correct = sum(1 for p in predictions 
                     if (p['signal'] == 'buy' and p['actual_next'] > p['actual_price']) or
                        (p['signal'] == 'sell' and p['actual_next'] < p['actual_price']))
        accuracy = correct / len(predictions)
    else:
        accuracy = 0
    
    lb_results.append({
        'lookback': lookback,
        'predictions': len(predictions),
        'accuracy': accuracy
    })
    
    print(f"  Lookback {lookback}: {len(predictions)} predictions, {accuracy:.2%} accuracy")

print("\n[3/3] Summary of optimizations...")
print("=" * 70)
print("OPTIMIZATION RESULTS")
print("=" * 70)
print("\nConfidence Threshold:")
for r in results:
    print(f"  {r['threshold']}: {r['predictions']} preds, {r['accuracy']:.2%} accuracy")

print("\nLookback Period:")
for r in lb_results:
    print(f"  {r['lookback']}: {r['predictions']} preds, {r['accuracy']:.2%} accuracy")

print("\n" + "=" * 70)
print("Hour 4-5 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
