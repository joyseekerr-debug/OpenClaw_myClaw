# -*- coding: utf-8 -*-
"""
24小时优化 - Hour 7-8: 策略优化
动态仓位、多因子信号融合
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
print("24-Hour Optimization - Hour 7-8: Strategy Optimization")
print("Dynamic Position Sizing + Multi-Factor Signals")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载数据
print("[1/4] Loading data...")
import pickle
with open('data/enhanced_multi_stock_2020_2024.pkl', 'rb') as f:
    data = pickle.load(f)

df = data['1810.HK'].copy()
print(f"      Data: {len(df)} records")

# ==================== 信号生成器 ====================
print("\n[2/4] Building multi-factor signal generator...")

class MultiFactorStrategy:
    """多因子策略"""
    
    def __init__(self):
        self.signals = []
    
    def generate_signals(self, df):
        """生成多因子信号"""
        signals = pd.DataFrame(index=df.index)
        
        # 趋势因子
        signals['trend'] = np.where(df['close'] > df['sma_20'], 1, 
                                   np.where(df['close'] < df['sma_20'], -1, 0))
        
        # 动量因子
        signals['momentum'] = np.where(df['momentum_10'] > 0.05, 1,
                                      np.where(df['momentum_10'] < -0.05, -1, 0))
        
        # RSI因子
        signals['rsi'] = np.where(df['rsi_14'] < 30, 1,
                                 np.where(df['rsi_14'] > 70, -1, 0))
        
        # MACD因子
        signals['macd'] = np.where(df['macd_hist'] > 0, 1, -1)
        
        # 布林带因子
        signals['bb'] = np.where(df['bb_position'] < 0.2, 1,
                                np.where(df['bb_position'] > 0.8, -1, 0))
        
        # 成交量因子
        signals['volume'] = np.where(df['volume_ratio'] > 1.5, 1,
                                    np.where(df['volume_ratio'] < 0.5, -1, 0))
        
        # 综合信号 (加权投票)
        weights = {'trend': 0.25, 'momentum': 0.20, 'rsi': 0.15, 
                   'macd': 0.20, 'bb': 0.10, 'volume': 0.10}
        
        signals['composite'] = sum(signals[factor] * weight 
                                   for factor, weight in weights.items())
        
        signals['signal'] = np.where(signals['composite'] >= 0.3, 1,
                                    np.where(signals['composite'] <= -0.3, -1, 0))
        
        return signals

strategy = MultiFactorStrategy()
signals = strategy.generate_signals(df)

print(f"      Generated {len(signals)} signals")
print(f"      Buy signals: {(signals['signal'] == 1).sum()}")
print(f"      Sell signals: {(signals['signal'] == -1).sum()}")
print(f"      Hold signals: {(signals['signal'] == 0).sum()}")
print()

# ==================== 动态仓位管理 ====================
print("[3/4] Dynamic position sizing...")

class PositionSizer:
    """动态仓位管理器"""
    
    def __init__(self, max_position=1.0, risk_per_trade=0.02):
        self.max_position = max_position
        self.risk_per_trade = risk_per_trade
    
    def calculate_position(self, df, i, signal_strength):
        """计算仓位大小"""
        if i < 20:
            return 0.0
        
        # 基于波动率的仓位调整
        volatility = df['volatility_20'].iloc[i]
        vol_factor = 0.15 / max(volatility, 0.05)  # 波动率越高，仓位越小
        
        # 基于信号强度的仓位
        signal_factor = abs(signal_strength)
        
        # 基于趋势的仓位
        trend = df['close'].iloc[i] / df['sma_60'].iloc[i] - 1
        trend_factor = min(abs(trend) * 5, 1.0)
        
        # 综合仓位
        position = self.max_position * vol_factor * signal_factor * trend_factor
        
        return min(position, self.max_position)

position_sizer = PositionSizer(max_position=1.0, risk_per_trade=0.02)

# 计算每个信号点的仓位
positions = []
for i in range(len(df)):
    if i < len(signals):
        signal_strength = signals['composite'].iloc[i]
        pos = position_sizer.calculate_position(df, i, signal_strength)
        positions.append(pos)
    else:
        positions.append(0)

signals['position_size'] = positions

print(f"      Average position: {np.mean(positions):.2%}")
print(f"      Max position: {np.max(positions):.2%}")
print()

# ==================== 回测引擎 ====================
print("[4/4] Backtesting strategy...")

class StrategyBacktest:
    """策略回测引擎"""
    
    def __init__(self, initial_capital=100000, commission=0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.capital = initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
    
    def run(self, df, signals):
        """执行回测"""
        for i in range(1, len(df)):
            price = df['close'].iloc[i]
            prev_price = df['close'].iloc[i-1]
            signal = signals['signal'].iloc[i-1]
            position_size = signals['position_size'].iloc[i-1]
            
            # 交易逻辑
            if signal == 1 and self.position == 0:
                # 买入
                shares = (self.capital * position_size) / price
                cost = shares * price * (1 + self.commission)
                if cost <= self.capital:
                    self.position = shares
                    self.capital -= cost
                    self.trades.append({
                        'type': 'buy',
                        'price': price,
                        'shares': shares,
                        'date': df.index[i]
                    })
            
            elif signal == -1 and self.position > 0:
                # 卖出
                proceeds = self.position * price * (1 - self.commission)
                pnl = proceeds - (self.position * self.trades[-1]['price'])
                self.capital += proceeds
                self.trades.append({
                    'type': 'sell',
                    'price': price,
                    'pnl': pnl,
                    'date': df.index[i]
                })
                self.position = 0
            
            # 计算权益
            equity = self.capital + (self.position * price if self.position > 0 else 0)
            self.equity_curve.append({
                'date': df.index[i],
                'equity': equity,
                'price': price
            })
        
        # 平仓
        if self.position > 0:
            final_price = df['close'].iloc[-1]
            proceeds = self.position * final_price * (1 - self.commission)
            self.capital += proceeds
            self.position = 0
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """计算回测指标"""
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        # 最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min()
        
        # 夏普比率
        returns = equity_df['equity'].pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
        
        # 胜率
        closed_trades = [t for t in self.trades if t['type'] == 'sell']
        wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(wins) / len(closed_trades) if closed_trades else 0
        
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'total_trades': len(closed_trades),
            'final_capital': self.capital
        }

# 运行回测
backtest = StrategyBacktest(initial_capital=100000, commission=0.001)
metrics = backtest.run(df, signals)

print("\n" + "=" * 70)
print("STRATEGY BACKTEST RESULTS")
print("=" * 70)

print(f"\n  Initial Capital: $100,000")
print(f"  Final Capital: ${metrics.get('final_capital', 0):,.2f}")
print(f"  Total Return: {metrics.get('total_return', 0):.2%}")
print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
print(f"  Win Rate: {metrics.get('win_rate', 0):.2%}")
print(f"  Total Trades: {metrics.get('total_trades', 0)}")

# 保存结果
results = {
    'timestamp': datetime.now().isoformat(),
    'phase': 'Hour 7-8: Strategy Optimization',
    'strategy': 'Multi-Factor with Dynamic Position Sizing',
    'metrics': metrics,
    'signals': {
        'total': len(signals),
        'buy': int((signals['signal'] == 1).sum()),
        'sell': int((signals['signal'] == -1).sum()),
        'hold': int((signals['signal'] == 0).sum())
    }
}

with open('results/hour_7_8_strategy_optimization.json', 'w') as f:
    json.dump(results, f, indent=2)

# 保存信号数据
signals.to_csv('results/multi_factor_signals.csv')

print("\n[OK] Results saved")

print("\n" + "=" * 70)
print("Hour 7-8 completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
