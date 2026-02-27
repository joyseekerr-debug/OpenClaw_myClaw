# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第2-3小时: 价格行为模型训练与回测
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
print("24-Hour Optimization Task - Hour 2-3")
print("Price Action Model Training & Backtesting")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Load optimized data
print("[1/4] Loading optimized features...")
df = pd.read_csv('data/features_optimized.csv', index_col='timestamp', parse_dates=True)
print(f"  Records: {len(df)}")

# 2. Train Price Action Model
print("\n[2/4] Training Price Action Model...")
from models.price_action_model import PriceActionPredictor

predictor = PriceActionPredictor()
signal = predictor.predict(df)

print(f"  Signal: {signal.signal}")
print(f"  Confidence: {signal.confidence:.2f}")
print(f"  Reason: {signal.reason}")
print(f"  Target Price: {signal.target_price}")
print(f"  Stop Loss: {signal.stop_loss}")

# 3. Generate predictions for backtest
print("\n[3/4] Generating rolling predictions...")

predictions = []
window = 50

for i in range(window, len(df)):
    if i % 10 == 0:  # 每10天预测一次
        window_df = df.iloc[i-window:i]
        
        try:
            sig = predictor.predict(window_df)
            predictions.append({
                'index': i,
                'date': df.index[i],
                'signal': sig.signal,
                'confidence': sig.confidence,
                'price': df['close'].iloc[i]
            })
        except:
            predictions.append({
                'index': i,
                'date': df.index[i],
                'signal': 'hold',
                'confidence': 0.5,
                'price': df['close'].iloc[i]
            })

print(f"  Generated {len(predictions)} predictions")

# 4. Simple backtest
print("\n[4/4] Running backtest...")
from backtest.backtest_engine import BacktestEngine

# Create prediction list for backtest
pred_list = [
    {'signal': p['signal'], 'confidence': p['confidence']}
    for p in predictions
]

# Align data
df_backtest = df.iloc[window:window+len(pred_list)]

engine = BacktestEngine(initial_capital=100000)
result = engine.run_backtest(df_backtest, pred_list)

print(f"  Total Trades: {result.total_trades}")
print(f"  Win Rate: {result.win_rate:.2%}")
print(f"  Profit Factor: {result.profit_factor:.2f}")
print(f"  Total Return: {result.total_return_pct:.2%}")
print(f"  Max Drawdown: {result.max_drawdown_pct:.2%}")
print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'model': 'PriceAction',
    'total_trades': result.total_trades,
    'win_rate': result.win_rate,
    'profit_factor': result.profit_factor,
    'total_return': result.total_return_pct,
    'max_drawdown': result.max_drawdown_pct,
    'sharpe_ratio': result.sharpe_ratio
}

import json
with open('results/backtest_price_action.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 70)
print("Hour 2-3 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
