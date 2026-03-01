# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第11-12小时: 完整回测验证
使用最优参数进行端到端回测
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 11-12")
print("Complete Backtest Validation")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载扩展数据集
df = pd.read_csv('data/xiaomi_extended.csv', index_col=0, parse_dates=True)
df.index.name = 'timestamp'
print(f"[1/3] Dataset: {len(df)} records")

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

print(f"      Features: {len(feature_cols)}")
print(f"      Samples: {len(X)}")
print()

# 使用最优参数训练最终模型
print("[2/3] Training final model with optimized parameters...")

from models.xgboost_model import XGBoostPredictor

best_params = {
    'max_depth': 3,
    'learning_rate': 0.01,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.7
}

# 时间序列划分 - 用前80%训练，后20%回测
split_idx = int(len(X) * 0.8)
X_train, X_backtest = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_backtest = y.iloc[:split_idx], y.iloc[split_idx:]

# 进一步划分训练集用于早停
val_split = int(len(X_train) * 0.8)
X_tr, X_val = X_train.iloc[:val_split], X_train.iloc[val_split:]
y_tr, y_val = y_train.iloc[:val_split], y_train.iloc[val_split:]

# 训练模型
model = XGBoostPredictor(**best_params)
model.build_model()
model.train(X_tr, y_tr, X_val, y_val)

# 评估训练集
print(f"      Training completed")
print(f"      Train samples: {len(X_train)}")
print(f"      Backtest samples: {len(X_backtest)}")
print()

# ==================== 回测引擎 ====================
print("[3/3] Running backtest simulation...")

class SimpleBacktest:
    """简化回测引擎"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # 0=空仓, 1=多头
        self.trades = []
        self.equity_curve = []
    
    def run(self, df_prices, predictions):
        """运行回测"""
        equity = self.initial_capital
        
        for i, (idx, pred) in enumerate(predictions.iterrows()):
            if i >= len(df_prices) - 1:
                break
            
            current_price = df_prices['close'].iloc[i]
            next_price = df_prices['close'].iloc[i + 1]
            
            signal = pred['prediction']
            confidence = pred['confidence']
            
            # 交易逻辑
            if signal == 'up' and self.position == 0 and confidence > 0.6:
                # 买入
                self.position = 1
                self.entry_price = current_price
                self.trades.append({
                    'type': 'buy',
                    'price': current_price,
                    'date': df_prices.index[i]
                })
            
            elif signal == 'down' and self.position == 1:
                # 卖出
                pnl = (current_price - self.entry_price) / self.entry_price
                self.capital *= (1 + pnl)
                self.position = 0
                self.trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'pnl': pnl,
                    'date': df_prices.index[i]
                })
            
            # 记录权益
            if self.position == 1:
                unrealized = (current_price - self.entry_price) / self.entry_price
                equity = self.capital * (1 + unrealized)
            else:
                equity = self.capital
            
            self.equity_curve.append({
                'date': df_prices.index[i],
                'equity': equity,
                'price': current_price
            })
        
        # 平仓
        if self.position == 1:
            final_price = df_prices['close'].iloc[-1]
            pnl = (final_price - self.entry_price) / self.entry_price
            self.capital *= (1 + pnl)
            self.position = 0
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """计算回测指标"""
        equity_df = pd.DataFrame(self.equity_curve)
        
        if len(equity_df) == 0:
            return {}
        
        # 收益率
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        # 最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min()
        
        # 年化收益率 (假设252交易日)
        n_days = len(equity_df)
        annual_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        
        # 夏普比率 (简化)
        if len(equity_df) > 1:
            daily_returns = equity_df['equity'].pct_change().dropna()
            sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        else:
            sharpe = 0
        
        # 胜率
        closed_trades = [t for t in self.trades if t['type'] == 'sell']
        win_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(win_trades) / len(closed_trades) if closed_trades else 0
        
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'total_trades': len(closed_trades),
            'winning_trades': len(win_trades),
            'final_capital': self.capital
        }

# 获取回测期间的预测
backtest_dates = X_backtest.index
predictions_list = []

for idx in backtest_dates:
    try:
        X_sample = X_backtest.loc[[idx]]
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

predictions_df = pd.DataFrame(predictions_list, index=backtest_dates)

# 对齐价格数据
backtest_prices = df.loc[backtest_dates]

# 运行回测
backtest = SimpleBacktest(initial_capital=100000)
metrics = backtest.run(backtest_prices, predictions_df)

print("\n" + "=" * 70)
print("BACKTEST RESULTS")
print("=" * 70)

print(f"\n初始资金: HK$ 100,000")
print(f"最终资金: HK$ {metrics.get('final_capital', 0):,.2f}")
print(f"总收益率: {metrics.get('total_return', 0):.2%}")
print(f"年化收益: {metrics.get('annual_return', 0):.2%}")
print(f"最大回撤: {metrics.get('max_drawdown', 0):.2%}")
print(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
print(f"交易次数: {metrics.get('total_trades', 0)}")
print(f"胜率: {metrics.get('win_rate', 0):.2%}")

# 保存结果
results = {
    'timestamp': datetime.now().isoformat(),
    'backtest_period': f"{backtest_dates[0]} to {backtest_dates[-1]}",
    'metrics': metrics,
    'model_params': best_params,
    'trades': backtest.trades[-10:]  # 最近10笔交易
}

with open('results/final_backtest.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n[OK] Results saved to results/final_backtest.json")

print("\n" + "=" * 70)
print("Hour 11-12 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
