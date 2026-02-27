# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第5-6小时: 应用优化参数重新回测
使用找到的最优参数组合
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
print("24-Hour Optimization Task - Hour 5-6")
print("Apply Optimized Parameters")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load real data
df = pd.read_csv('data/xiaomi_2023_real.csv', index_col='timestamp', parse_dates=True)

print("[1/3] Applying optimized parameters...")
print("  Optimal threshold: 0.5")
print("  Optimal lookback: 20 days")

# Apply optimized parameters
from models.price_action_model import PriceActionPredictor
from features.support_resistance import SupportResistanceDetector

predictor = PriceActionPredictor()
predictor.sr_detector.lookback = 20  # Optimized lookback

# Generate predictions with optimized parameters
print("\n[2/3] Generating predictions with optimized parameters...")

predictions = []
window = 20

for i in range(window, len(df), 3):  # Every 3 days for more signals
    window_df = df.iloc[i-window:i]
    
    try:
        sig = predictor.predict(window_df)
        
        # Apply optimized threshold
        if sig.confidence >= 0.5 and sig.signal != 'hold':
            predictions.append({
                'index': i,
                'date': df.index[i],
                'signal': sig.signal,
                'confidence': sig.confidence,
                'actual_price': df['close'].iloc[i],
                'actual_next': df['close'].iloc[min(i+5, len(df)-1)]
            })
    except Exception as e:
        pass

print(f"  Generated {len(predictions)} predictions")

# Calculate accuracy on real data
if predictions:
    correct = sum(1 for p in predictions
                 if (p['signal'] == 'buy' and p['actual_next'] > p['actual_price']) or
                    (p['signal'] == 'sell' and p['actual_next'] < p['actual_price']))
    accuracy = correct / len(predictions)
    print(f"  Direction accuracy: {accuracy:.2%}")

# Full backtest with optimized parameters
print("\n[3/3] Full backtest with optimized parameters...")
from backtest.backtest_engine import BacktestEngine

pred_list = [{'signal': p['signal'], 'confidence': p['confidence']} for p in predictions]
df_backtest = df.iloc[window:window+len(pred_list)]

if len(df_backtest) > 0 and len(pred_list) > 0:
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run_backtest(df_backtest, pred_list)
    
    print(f"  === OPTIMIZED BACKTEST RESULTS ===")
    print(f"  Total Trades: {result.total_trades}")
    print(f"  Win Rate: {result.win_rate:.2%}")
    print(f"  Profit Factor: {result.profit_factor:.2f}")
    print(f"  Total Return: {result.total_return_pct:.2%}")
    print(f"  Max Drawdown: {result.max_drawdown_pct:.2%}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    
    # Save optimized results
    optimized_results = {
        'timestamp': datetime.now().isoformat(),
        'data_source': 'REAL - Xiaomi 1810.HK 2023H1',
        'optimization_applied': True,
        'optimal_threshold': 0.5,
        'optimal_lookback': 20,
        'total_predictions': len(predictions),
        'direction_accuracy': accuracy if predictions else 0,
        'backtest': {
            'total_trades': result.total_trades,
            'win_rate': result.win_rate,
            'profit_factor': result.profit_factor,
            'total_return': result.total_return_pct,
            'max_drawdown': result.max_drawdown_pct,
            'sharpe_ratio': result.sharpe_ratio
        }
    }
    
    with open('results/backtest_optimized.json', 'w') as f:
        json.dump(optimized_results, f, indent=2)
    
    print(f"\n  Results saved to: results/backtest_optimized.json")

print("\n" + "=" * 70)
print("Hour 5-6 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
