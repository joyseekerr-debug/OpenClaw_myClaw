# -*- coding: utf-8 -*-
"""
24小时优化任务 - 使用真实数据回测
小米集团(1810.HK) 2023年上半年真实数据
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
print("24-Hour Optimization Task - REAL DATA BACKTEST")
print("Xiaomi (1810.HK) - 2023 Real Historical Data")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Load REAL historical data
print("[1/4] Loading REAL historical data...")
df = pd.read_csv('data/xiaomi_2023_real.csv', index_col='timestamp', parse_dates=True)
print(f"  Records: {len(df)} (REAL DATA)")
print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
print(f"  Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
print(f"  Total return: {(df['close'].iloc[-1]/df['close'].iloc[0]-1)*100:.2f}%")

# 2. Feature engineering on real data
print("\n[2/4] Feature engineering on real data...")
from features.feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
df_features = engineer.create_all_features(df)
print(f"  Records after feature engineering: {len(df_features)}")
print(f"  Features: {len(df_features.columns)}")

# 3. Price Action Model on real data
print("\n[3/4] Price Action Model prediction on real data...")
from models.price_action_model import PriceActionPredictor

predictor = PriceActionPredictor()

# Rolling predictions on real data
predictions = []
window = 30

for i in range(window, len(df_features)):
    if i % 5 == 0:  # Every 5 days
        window_df = df_features.iloc[i-window:i]
        
        try:
            sig = predictor.predict(window_df)
            predictions.append({
                'index': i,
                'date': df_features.index[i],
                'signal': sig.signal,
                'confidence': sig.confidence,
                'actual_price': df_features['close'].iloc[i],
                'actual_next': df_features['close'].iloc[min(i+5, len(df_features)-1)]
            })
        except Exception as e:
            pass

print(f"  Generated {len(predictions)} predictions on real data")

# Calculate accuracy on real data
if len(predictions) > 0:
    correct = 0
    for p in predictions:
        if p['signal'] == 'buy' and p['actual_next'] > p['actual_price']:
            correct += 1
        elif p['signal'] == 'sell' and p['actual_next'] < p['actual_price']:
            correct += 1
    
    accuracy = correct / len(predictions) if predictions else 0
    print(f"  Direction accuracy on REAL data: {accuracy:.2%}")

# 4. Backtest on real data
print("\n[4/4] Backtesting on REAL data...")
from backtest.backtest_engine import BacktestEngine

pred_list = [{'signal': p['signal'], 'confidence': p['confidence']} for p in predictions]
df_backtest = df_features.iloc[window:window+len(pred_list)]

if len(df_backtest) > 0 and len(pred_list) > 0:
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run_backtest(df_backtest, pred_list)
    
    print(f"  === REAL DATA BACKTEST RESULTS ===")
    print(f"  Total Trades: {result.total_trades}")
    print(f"  Win Rate: {result.win_rate:.2%}")
    print(f"  Profit Factor: {result.profit_factor:.2f}")
    print(f"  Total Return: {result.total_return_pct:.2%}")
    print(f"  Max Drawdown: {result.max_drawdown_pct:.2%}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    
    # Save results
    import json
    real_results = {
        'timestamp': datetime.now().isoformat(),
        'data_source': 'REAL - Xiaomi 1810.HK 2023H1',
        'records': len(df),
        'total_trades': result.total_trades,
        'win_rate': result.win_rate,
        'profit_factor': result.profit_factor,
        'total_return': result.total_return_pct,
        'max_drawdown': result.max_drawdown_pct,
        'sharpe_ratio': result.sharpe_ratio,
        'direction_accuracy': accuracy if predictions else 0
    }
    
    with open('results/backtest_real_data.json', 'w') as f:
        json.dump(real_results, f, indent=2)
    print(f"\n  Results saved to: results/backtest_real_data.json")

print("\n" + "=" * 70)
print("REAL DATA BACKTEST COMPLETED")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
