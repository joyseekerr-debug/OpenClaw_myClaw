# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第6-7小时: 多模型集成测试
测试不同模型组合的效果
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 6-7")
print("Multi-Model Ensemble Testing")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load real data
df = pd.read_csv('data/xiaomi_2023_real.csv', index_col='timestamp', parse_dates=True)

print("[1/4] Loading data and preparing features...")
from features.feature_engineering import FeatureEngineer
from features.support_resistance import SupportResistanceDetector
from features.chart_patterns import ChartPatternRecognizer
from features.candlestick_patterns import CandlestickRecognizer
from features.multi_timeframe import MultiTimeframeAnalyzer

engineer = FeatureEngineer()
df_features = engineer.create_all_features(df)

print(f"  Data: {len(df_features)} rows, {len(df_features.columns)} features")

# Initialize models
print("\n[2/4] Initializing multiple models...")

sr_detector = SupportResistanceDetector(lookback=20)
chart_recognizer = ChartPatternRecognizer()
candle_recognizer = CandlestickRecognizer()
mt_analyzer = MultiTimeframeAnalyzer()

print("  Models initialized")

# Generate signals from different models
print("\n[3/4] Generating signals from multiple models...")

predictions = []
window = 20

for i in range(window, len(df_features), 3):
    window_df = df_features.iloc[i-window:i]
    
    model_predictions = []
    
    # Model 1: Support Resistance
    try:
        levels = sr_detector.detect_levels(window_df)
        current_price = window_df['close'].iloc[-1]
        
        # Simple SR signal
        if levels['support'] and levels['resistance']:
            nearest_support = levels['support'][0].price
            nearest_resistance = levels['resistance'][0].price
            
            dist_to_support = (current_price - nearest_support) / current_price
            dist_to_resistance = (nearest_resistance - current_price) / current_price
            
            if dist_to_support < 0.02:
                sr_signal = 'buy'
                sr_conf = 0.6
            elif dist_to_resistance < 0.02:
                sr_signal = 'sell'
                sr_conf = 0.6
            else:
                sr_signal = 'hold'
                sr_conf = 0.5
            
            model_predictions.append({
                'model': 'SupportResistance',
                'signal': sr_signal,
                'confidence': sr_conf
            })
    except:
        pass
    
    # Model 2: Chart Patterns
    try:
        patterns = chart_recognizer.detect_all_patterns(window_df)
        if patterns:
            best = patterns[0]
            model_predictions.append({
                'model': 'ChartPattern',
                'signal': 'buy' if best.direction == 'bullish' else 'sell',
                'confidence': best.confidence
            })
    except:
        pass
    
    # Model 3: Candlestick Patterns
    try:
        candle_patterns = candle_recognizer.detect_all_patterns(window_df)
        if candle_patterns:
            # Count bullish vs bearish
            bullish = sum(1 for p in candle_patterns if p.type == 'bullish')
            bearish = sum(1 for p in candle_patterns if p.type == 'bearish')
            
            if bullish > bearish:
                candle_signal = 'buy'
                candle_conf = min(bullish / len(candle_patterns) + 0.3, 1.0)
            elif bearish > bullish:
                candle_signal = 'sell'
                candle_conf = min(bearish / len(candle_patterns) + 0.3, 1.0)
            else:
                candle_signal = 'hold'
                candle_conf = 0.5
            
            model_predictions.append({
                'model': 'Candlestick',
                'signal': candle_signal,
                'confidence': candle_conf
            })
    except:
        pass
    
    if len(model_predictions) >= 2:  # Need at least 2 models
        predictions.append({
            'index': i,
            'date': df_features.index[i],
            'models': model_predictions,
            'actual_price': df_features['close'].iloc[i],
            'actual_next': df_features['close'].iloc[min(i+5, len(df_features)-1)]
        })

print(f"  Generated {len(predictions)} ensemble predictions")

# Ensemble prediction
print("\n[4/4] Testing ensemble strategies...")
from ensemble.model_ensemble import ModelEnsemble, ModelPrediction as MP

ensemble_results = []

for p in predictions:
    # Convert to ModelPrediction objects
    mp_list = [
        MP(m['model'], '1d', 
           0.7 if m['signal'] == 'buy' else 0.3,
           0.3 if m['signal'] == 'buy' else 0.7,
           m['signal'], m['confidence'])
        for m in p['models']
    ]
    
    # Ensemble
    ensemble = ModelEnsemble()
    result = ensemble.predict(mp_list)
    
    # Check accuracy
    correct = (result.prediction == 'buy' and p['actual_next'] > p['actual_price']) or \
              (result.prediction == 'sell' and p['actual_next'] < p['actual_price'])
    
    ensemble_results.append({
        'date': p['date'],
        'ensemble_signal': result.prediction,
        'confidence': result.confidence,
        'consensus': result.consensus_level,
        'correct': correct
    })

# Calculate ensemble accuracy
if ensemble_results:
    correct_count = sum(1 for r in ensemble_results if r['correct'])
    ensemble_accuracy = correct_count / len(ensemble_results)
    avg_confidence = np.mean([r['confidence'] for r in ensemble_results])
    avg_consensus = np.mean([r['consensus'] for r in ensemble_results])
    
    print(f"  Ensemble Accuracy: {ensemble_accuracy:.2%}")
    print(f"  Avg Confidence: {avg_confidence:.2f}")
    print(f"  Avg Consensus: {avg_consensus:.2f}")
    
    # Save results
    ensemble_summary = {
        'timestamp': datetime.now().isoformat(),
        'total_predictions': len(ensemble_results),
        'ensemble_accuracy': ensemble_accuracy,
        'avg_confidence': avg_confidence,
        'avg_consensus': avg_consensus,
        'details': ensemble_results[:10]  # First 10
    }
    
    with open('results/ensemble_results.json', 'w') as f:
        json.dump(ensemble_summary, f, indent=2, default=str)
    
    print(f"\n  Results saved to: results/ensemble_results.json")

print("\n" + "=" * 70)
print("Hour 6-7 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
