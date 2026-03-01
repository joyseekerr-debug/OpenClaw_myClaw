# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第13-16小时: 策略优化
测试不同阈值、仓位管理和止损策略
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 13-16")
print("Strategy Optimization")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载数据
df = pd.read_csv('data/xiaomi_extended.csv', index_col=0, parse_dates=True)
df.index.name = 'timestamp'

# 特征工程
from features.feature_engineering import engineer_features
df_features = engineer_features(df)
feature_cols = [col for col in df_features.columns 
                if col not in ['open', 'high', 'low', 'close', 'volume', 
                              'symbol', 'timeframe', 'source', 'target_direction_1']]

X = df_features[feature_cols].dropna()
y = df_features.loc[X.index, 'target_direction_1']
mask = y.isin([0, 1])
X = X[mask]
y = y[mask]

# 加载已训练模型
from models.xgboost_model import XGBoostPredictor

best_params = {
    'max_depth': 3,
    'learning_rate': 0.01,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.7
}

# 划分数据
split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# 训练模型
val_split = int(len(X_train) * 0.8)
X_tr, X_val = X_train.iloc[:val_split], X_train.iloc[val_split:]
y_tr, y_val = y_train.iloc[:val_split], y_train.iloc[val_split:]

model = XGBoostPredictor(**best_params)
model.build_model()
model.train(X_tr, y_tr, X_val, y_val)

print(f"[1/4] Model trained: {len(X_train)} train, {len(X_test)} test samples")
print()

# ==================== 测试不同置信度阈值 ====================
print("[2/4] Testing different confidence thresholds...")

class EnhancedBacktest:
    """增强回测引擎 - 支持动态仓位和止损"""
    
    def __init__(self, initial_capital=100000, confidence_threshold=0.5, 
                 position_size=1.0, stop_loss=None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.confidence_threshold = confidence_threshold
        self.position_size = position_size  # 仓位比例
        self.stop_loss = stop_loss  # 止损比例
        
        self.trades = []
        self.equity_curve = []
        self.entry_price = None
    
    def run(self, df_prices, predictions):
        for i in range(len(predictions)):
            if i >= len(df_prices) - 1:
                break
            
            current_price = df_prices['close'].iloc[i]
            pred = predictions.iloc[i]
            signal = pred['prediction']
            confidence = pred['confidence']
            
            # 检查止损
            if self.position == 1 and self.stop_loss:
                loss = (self.entry_price - current_price) / self.entry_price
                if loss >= self.stop_loss:
                    # 止损平仓
                    pnl = (current_price - self.entry_price) / self.entry_price
                    trade_amount = self.capital * self.position_size
                    pnl_amount = trade_amount * pnl
                    self.capital += pnl_amount
                    
                    self.trades.append({
                        'type': 'sell',
                        'price': current_price,
                        'pnl': pnl,
                        'reason': 'stop_loss',
                        'date': df_prices.index[i]
                    })
                    self.position = 0
                    continue
            
            # 交易信号
            if signal == 'up' and self.position == 0 and confidence >= self.confidence_threshold:
                self.position = 1
                self.entry_price = current_price
                self.trades.append({
                    'type': 'buy',
                    'price': current_price,
                    'confidence': confidence,
                    'date': df_prices.index[i]
                })
            
            elif signal == 'down' and self.position == 1:
                pnl = (current_price - self.entry_price) / self.entry_price
                trade_amount = self.capital * self.position_size
                pnl_amount = trade_amount * pnl
                self.capital += pnl_amount
                
                self.trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'pnl': pnl,
                    'reason': 'signal',
                    'date': df_prices.index[i]
                })
                self.position = 0
            
            # 记录权益
            equity = self.capital
            if self.position == 1:
                unrealized = (current_price - self.entry_price) / self.entry_price
                equity = self.capital + (self.capital * self.position_size * unrealized)
            
            self.equity_curve.append({
                'date': df_prices.index[i],
                'equity': equity,
                'price': current_price
            })
        
        # 强制平仓
        if self.position == 1:
            final_price = df_prices['close'].iloc[-1]
            pnl = (final_price - self.entry_price) / self.entry_price
            trade_amount = self.capital * self.position_size
            pnl_amount = trade_amount * pnl
            self.capital += pnl_amount
            self.position = 0
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min()
        
        n_days = len(equity_df)
        annual_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        
        if len(equity_df) > 1:
            daily_returns = equity_df['equity'].pct_change().dropna()
            sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        else:
            sharpe = 0
        
        closed_trades = [t for t in self.trades if t['type'] == 'sell']
        win_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(win_trades) / len(closed_trades) if closed_trades else 0
        
        # 计算Calmar比率
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'calmar_ratio': calmar,
            'win_rate': win_rate,
            'total_trades': len(closed_trades),
            'final_capital': self.capital,
            'threshold': self.confidence_threshold,
            'position_size': self.position_size
        }

# 获取预测
test_dates = X_test.index
predictions_list = []

for idx in test_dates:
    try:
        X_sample = X_test.loc[[idx]]
        pred = model.predict(X_sample)
        predictions_list.append({
            'prediction': pred['prediction'],
            'confidence': pred['confidence']
        })
    except:
        predictions_list.append({
            'prediction': 'hold',
            'confidence': 0.5
        })

predictions_df = pd.DataFrame(predictions_list, index=test_dates)
test_prices = df.loc[test_dates]

# 测试不同阈值
thresholds = [0.5, 0.55, 0.6, 0.65, 0.7]
threshold_results = []

for thresh in thresholds:
    bt = EnhancedBacktest(initial_capital=100000, confidence_threshold=thresh)
    metrics = bt.run(test_prices, predictions_df)
    threshold_results.append(metrics)
    print(f"  Threshold {thresh}: {metrics.get('total_trades', 0)} trades, "
          f"{metrics.get('total_return', 0):.2%} return, "
          f"{metrics.get('win_rate', 0):.0%} win rate")

print()

# ==================== 测试不同仓位管理 ====================
print("[3/4] Testing position sizing strategies...")

position_sizes = [0.5, 0.7, 1.0, 1.5]
position_results = []

for size in position_sizes:
    bt = EnhancedBacktest(initial_capital=100000, confidence_threshold=0.55, position_size=size)
    metrics = bt.run(test_prices, predictions_df)
    position_results.append(metrics)
    print(f"  Position {size:.0%}: {metrics.get('total_return', 0):.2%} return, "
          f"{metrics.get('max_drawdown', 0):.2%} drawdown")

print()

# ==================== 测试止损策略 ====================
print("[4/4] Testing stop-loss strategies...")

stop_losses = [None, 0.03, 0.05, 0.07]
stop_loss_results = []

for sl in stop_losses:
    bt = EnhancedBacktest(initial_capital=100000, confidence_threshold=0.55, 
                          position_size=1.0, stop_loss=sl)
    metrics = bt.run(test_prices, predictions_df)
    stop_loss_results.append(metrics)
    sl_str = f"{sl:.0%}" if sl else "None"
    print(f"  Stop-loss {sl_str}: {metrics.get('total_return', 0):.2%} return, "
          f"{metrics.get('max_drawdown', 0):.2%} drawdown")

print()

# ==================== 最优策略汇总 ====================
print("=" * 70)
print("STRATEGY OPTIMIZATION RESULTS")
print("=" * 70)

# 找最优阈值
best_thresh = max(threshold_results, key=lambda x: x.get('calmar_ratio', 0))
print(f"\nBest Confidence Threshold:")
print(f"  Value: {best_thresh.get('threshold')}")
print(f"  Return: {best_thresh.get('total_return', 0):.2%}")
print(f"  Trades: {best_thresh.get('total_trades')}")
print(f"  Win Rate: {best_thresh.get('win_rate', 0):.1%}")
print(f"  Calmar: {best_thresh.get('calmar_ratio', 0):.2f}")

# 找最优仓位
best_pos = max(position_results, key=lambda x: x.get('sharpe_ratio', 0))
print(f"\nBest Position Size:")
print(f"  Size: {best_pos.get('position_size', 1):.0%}")
print(f"  Return: {best_pos.get('total_return', 0):.2%}")
print(f"  Sharpe: {best_pos.get('sharpe_ratio', 0):.2f}")

# 保存结果
results = {
    'timestamp': datetime.now().isoformat(),
    'threshold_optimization': threshold_results,
    'position_optimization': position_results,
    'stoploss_optimization': stop_loss_results,
    'best_threshold': best_thresh.get('threshold'),
    'best_position_size': best_pos.get('position_size')
}

with open('results/strategy_optimization.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n[OK] Results saved to results/strategy_optimization.json")

print("\n" + "=" * 70)
print("Hour 13-16 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
