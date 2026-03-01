# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第17-20小时: 风险管理集成
实现完整的风险控制框架
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 17-20")
print("Risk Management Integration")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载数据
df = pd.read_csv('data/xiaomi_extended.csv', index_col=0, parse_dates=True)
df.index.name = 'timestamp'

from features.feature_engineering import engineer_features
from models.xgboost_model import XGBoostPredictor

df_features = engineer_features(df)
feature_cols = [col for col in df_features.columns 
                if col not in ['open', 'high', 'low', 'close', 'volume', 
                              'symbol', 'timeframe', 'source', 'target_direction_1']]

X = df_features[feature_cols].dropna()
y = df_features.loc[X.index, 'target_direction_1']
mask = y.isin([0, 1])
X = X[mask]
y = y[mask]

# 训练模型
split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

val_split = int(len(X_train) * 0.8)
X_tr, X_val = X_train.iloc[:val_split], X_train.iloc[val_split:]
y_tr, y_val = y_train.iloc[:val_split], y_train.iloc[val_split:]

best_params = {
    'max_depth': 3,
    'learning_rate': 0.01,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.7
}

model = XGBoostPredictor(**best_params)
model.build_model()
model.train(X_tr, y_tr, X_val, y_val)

print(f"[1/4] Model ready")
print()

# ==================== 完整风险管理系统 ====================
print("[2/4] Building risk management framework...")

class RiskManager:
    """风险管理系统"""
    
    def __init__(self, max_position_pct=0.5, max_drawdown_pct=0.1, 
                 var_limit=0.02, correlation_threshold=0.7):
        self.max_position_pct = max_position_pct  # 最大仓位比例
        self.max_drawdown_pct = max_drawdown_pct  # 最大回撤限制
        self.var_limit = var_limit  # VaR限制
        self.correlation_threshold = correlation_threshold
        self.daily_pnl = []
        self.risk_metrics_history = []
    
    def calculate_var(self, returns, confidence=0.95):
        """计算VaR (风险价值)"""
        if len(returns) == 0:
            return 0
        return np.percentile(returns, (1 - confidence) * 100)
    
    def calculate_cvar(self, returns, confidence=0.95):
        """计算CVaR (条件风险价值)"""
        var = self.calculate_var(returns, confidence)
        return np.mean([r for r in returns if r <= var])
    
    def check_risk_limits(self, portfolio_value, peak_value, daily_return):
        """检查风险限制"""
        violations = []
        
        # 检查回撤
        drawdown = (peak_value - portfolio_value) / peak_value if peak_value > 0 else 0
        if drawdown > self.max_drawdown_pct:
            violations.append(f"Max drawdown exceeded: {drawdown:.2%}")
        
        # 记录每日收益
        self.daily_pnl.append(daily_return)
        
        # 检查VaR (需要至少20天数据)
        if len(self.daily_pnl) >= 20:
            var = self.calculate_var(self.daily_pnl[-20:])
            if abs(var) > self.var_limit:
                violations.append(f"VaR limit exceeded: {var:.2%}")
        
        return len(violations) == 0, violations
    
    def get_position_limit(self, volatility):
        """基于波动率调整仓位"""
        # 波动率越高，仓位越小
        if volatility < 0.01:
            return self.max_position_pct
        elif volatility < 0.02:
            return self.max_position_pct * 0.8
        elif volatility < 0.03:
            return self.max_position_pct * 0.6
        else:
            return self.max_position_pct * 0.4

class RiskManagedBacktest:
    """带风险管理的回测引擎"""
    
    def __init__(self, initial_capital=100000, confidence_threshold=0.55,
                 risk_manager=None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.confidence_threshold = confidence_threshold
        self.risk_manager = risk_manager or RiskManager()
        
        self.position = 0
        self.trades = []
        self.equity_curve = []
        self.peak_value = initial_capital
        self.entry_price = None
        self.position_size = 0
    
    def calculate_volatility(self, prices, window=20):
        """计算历史波动率"""
        if len(prices) < window:
            return 0.02
        # 使用pandas Series来计算收益率
        prices_series = pd.Series(prices[-window:])
        returns = prices_series.pct_change().dropna()
        return returns.std() * np.sqrt(252)
    
    def run(self, df_prices, predictions):
        for i in range(len(predictions)):
            if i >= len(df_prices) - 1:
                break
            
            current_price = df_prices['close'].iloc[i]
            pred = predictions.iloc[i]
            signal = pred['prediction']
            confidence = pred['confidence']
            
            # 计算当前权益
            equity = self.capital
            if self.position == 1:
                unrealized = (current_price - self.entry_price) / self.entry_price
                equity = self.capital + (self.initial_capital * self.position_size * unrealized)
            
            # 更新峰值
            if equity > self.peak_value:
                self.peak_value = equity
            
            # 检查风险限制
            daily_return = 0
            if i > 0 and len(self.equity_curve) > 0:
                daily_return = (equity - self.equity_curve[-1]['equity']) / self.equity_curve[-1]['equity']
            
            can_trade, violations = self.risk_manager.check_risk_limits(
                equity, self.peak_value, daily_return
            )
            
            # 如果违反风险限制，强制平仓
            if violations and self.position == 1:
                pnl = (current_price - self.entry_price) / self.entry_price
                pnl_amount = self.initial_capital * self.position_size * pnl
                self.capital += pnl_amount
                
                self.trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'pnl': pnl,
                    'reason': 'risk_limit',
                    'violations': violations,
                    'date': df_prices.index[i]
                })
                self.position = 0
                continue
            
            # 交易逻辑
            if signal == 'up' and self.position == 0 and confidence >= self.confidence_threshold and can_trade:
                # 基于波动率计算仓位
                volatility = self.calculate_volatility(df_prices['close'].iloc[:i+1].values)
                position_limit = self.risk_manager.get_position_limit(volatility)
                
                self.position = 1
                self.entry_price = current_price
                self.position_size = position_limit
                
                self.trades.append({
                    'type': 'buy',
                    'price': current_price,
                    'confidence': confidence,
                    'position_size': position_limit,
                    'volatility': volatility,
                    'date': df_prices.index[i]
                })
            
            elif signal == 'down' and self.position == 1:
                pnl = (current_price - self.entry_price) / self.entry_price
                pnl_amount = self.initial_capital * self.position_size * pnl
                self.capital += pnl_amount
                
                self.trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'pnl': pnl,
                    'reason': 'signal',
                    'date': df_prices.index[i]
                })
                self.position = 0
            
            self.equity_curve.append({
                'date': df_prices.index[i],
                'equity': equity,
                'price': current_price,
                'position': self.position
            })
        
        # 强制平仓
        if self.position == 1:
            final_price = df_prices['close'].iloc[-1]
            pnl = (final_price - self.entry_price) / self.entry_price
            pnl_amount = self.initial_capital * self.position_size * pnl
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
            volatility = daily_returns.std() * np.sqrt(252)
        else:
            sharpe = 0
            volatility = 0
        
        closed_trades = [t for t in self.trades if t['type'] == 'sell']
        win_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(win_trades) / len(closed_trades) if closed_trades else 0
        
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'calmar_ratio': calmar,
            'volatility': volatility,
            'win_rate': win_rate,
            'total_trades': len(closed_trades),
            'final_capital': self.capital
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

# 运行带风险管理的回测
print("[3/4] Running risk-managed backtest...")

risk_manager = RiskManager(
    max_position_pct=0.5,
    max_drawdown_pct=0.1,
    var_limit=0.02
)

bt = RiskManagedBacktest(
    initial_capital=100000,
    confidence_threshold=0.55,
    risk_manager=risk_manager
)

metrics = bt.run(test_prices, predictions_df)

print("\n" + "=" * 70)
print("RISK-MANAGED BACKTEST RESULTS")
print("=" * 70)
print(f"\n初始资金: HK$ 100,000")
print(f"最终资金: HK$ {metrics.get('final_capital', 0):,.2f}")
print(f"总收益率: {metrics.get('total_return', 0):.2%}")
print(f"年化收益: {metrics.get('annual_return', 0):.2%}")
print(f"波动率: {metrics.get('volatility', 0):.2%}")
print(f"最大回撤: {metrics.get('max_drawdown', 0):.2%}")
print(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
print(f"Calmar比率: {metrics.get('calmar_ratio', 0):.2f}")
print(f"交易次数: {metrics.get('total_trades', 0)}")
print(f"胜率: {metrics.get('win_rate', 0):.1%}")

# ==================== 生成交易报告 ====================
print("\n[4/4] Generating trade report...")

print(f"\n交易记录:")
for trade in bt.trades[:10]:
    date_str = str(trade['date'])[:10]
    if trade['type'] == 'buy':
        print(f"  BUY  {date_str} @ HK${trade['price']:.2f} "
              f"(size: {trade.get('position_size', 1):.0%})")
    else:
        print(f"  SELL {date_str} @ HK${trade['price']:.2f} "
              f"P&L: {trade.get('pnl', 0):+.2%} [{trade.get('reason', 'signal')}]")

# 保存结果
results = {
    'timestamp': datetime.now().isoformat(),
    'risk_management': {
        'max_position': 0.5,
        'max_drawdown': 0.1,
        'var_limit': 0.02
    },
    'performance': metrics,
    'trades': bt.trades
}

with open('results/risk_managed_backtest.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n[OK] Results saved to results/risk_managed_backtest.json")

print("\n" + "=" * 70)
print("Hour 17-20 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
