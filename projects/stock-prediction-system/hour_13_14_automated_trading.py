# -*- coding: utf-8 -*-
"""
24小时优化 - Hour 13-14: 自动化交易
模拟盘自动执行框架
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization - Hour 13-14: Automated Trading")
print("Paper Trading Framework")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("[1/4] Building automated trading engine...")

class PaperTradingEngine:
    """模拟盘交易引擎"""
    
    def __init__(self, initial_capital=100000, commission=0.001, slippage=0.001):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.positions = {}  # symbol -> {shares, avg_cost}
        self.orders = []
        self.trades = []
        self.equity_history = []
        
        self.is_running = False
    
    def place_order(self, symbol: str, side: str, quantity: float, 
                   price: float, order_type='market') -> Dict:
        """下单"""
        
        # 模拟滑点
        if side == 'buy':
            executed_price = price * (1 + self.slippage)
        else:
            executed_price = price * (1 - self.slippage)
        
        # 计算成本
        gross_amount = quantity * executed_price
        commission = gross_amount * self.commission
        net_amount = gross_amount + commission if side == 'buy' else gross_amount - commission
        
        order = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'requested_price': price,
            'executed_price': executed_price,
            'commission': commission,
            'net_amount': net_amount,
            'status': 'filled'
        }
        
        self.orders.append(order)
        
        # 更新持仓
        if side == 'buy':
            if net_amount <= self.capital:
                self.capital -= net_amount
                
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    total_cost = pos['shares'] * pos['avg_cost'] + quantity * executed_price
                    pos['shares'] += quantity
                    pos['avg_cost'] = total_cost / pos['shares']
                else:
                    self.positions[symbol] = {
                        'shares': quantity,
                        'avg_cost': executed_price
                    }
                
                self.trades.append({
                    'timestamp': order['timestamp'],
                    'symbol': symbol,
                    'side': 'buy',
                    'price': executed_price,
                    'quantity': quantity
                })
            else:
                order['status'] = 'rejected'
                order['reject_reason'] = 'insufficient_capital'
        
        else:  # sell
            if symbol in self.positions and self.positions[symbol]['shares'] >= quantity:
                self.capital += net_amount
                self.positions[symbol]['shares'] -= quantity
                
                if self.positions[symbol]['shares'] == 0:
                    del self.positions[symbol]
                
                self.trades.append({
                    'timestamp': order['timestamp'],
                    'symbol': symbol,
                    'side': 'sell',
                    'price': executed_price,
                    'quantity': quantity
                })
            else:
                order['status'] = 'rejected'
                order['reject_reason'] = 'insufficient_position'
        
        return order
    
    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        """计算组合价值"""
        portfolio_value = self.capital
        for symbol, pos in self.positions.items():
            if symbol in prices:
                portfolio_value += pos['shares'] * prices[symbol]
        return portfolio_value
    
    def record_equity(self, prices: Dict[str, float]):
        """记录权益"""
        equity = self.get_portfolio_value(prices)
        self.equity_history.append({
            'timestamp': datetime.now().isoformat(),
            'equity': equity,
            'cash': self.capital,
            'positions': len(self.positions)
        })
    
    def get_performance_metrics(self) -> Dict:
        """计算绩效指标"""
        if not self.equity_history:
            return {}
        
        equity_df = pd.DataFrame(self.equity_history)
        
        total_return = (equity_df['equity'].iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min()
        
        # 胜率
        closed_trades = [t for t in self.trades if t['side'] == 'sell']
        # 简化为计算有卖出的交易
        
        return {
            'total_return': float(total_return),
            'max_drawdown': float(max_drawdown),
            'final_equity': float(equity_df['equity'].iloc[-1]),
            'total_trades': len(self.trades),
            'final_cash': float(self.capital),
            'open_positions': len(self.positions)
        }

# 创建交易引擎
engine = PaperTradingEngine(initial_capital=100000, commission=0.001)
print(f"      Engine created")
print(f"      Initial capital: $100,000")
print()

# ==================== 策略执行器 ====================
print("[2/4] Building strategy executor...")

class StrategyExecutor:
    """策略执行器"""
    
    def __init__(self, trading_engine, strategy_config):
        self.engine = trading_engine
        self.config = strategy_config
        self.signal_history = []
    
    def execute_signal(self, symbol: str, signal: str, confidence: float, price: float):
        """执行交易信号"""
        
        # 根据信心度调整仓位
        if confidence >= self.config['min_confidence']:
            
            # 计算仓位大小
            position_size = self.calculate_position_size(confidence)
            
            if signal == 'buy':
                # 检查是否已有持仓
                if symbol not in self.engine.positions:
                    shares = (self.engine.capital * position_size) / price
                    order = self.engine.place_order(symbol, 'buy', shares, price)
                    self.signal_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'signal': signal,
                        'confidence': confidence,
                        'shares': shares,
                        'status': order['status']
                    })
                    return order
            
            elif signal == 'sell':
                # 检查是否有持仓可卖
                if symbol in self.engine.positions:
                    shares = self.engine.positions[symbol]['shares']
                    order = self.engine.place_order(symbol, 'sell', shares, price)
                    self.signal_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'signal': signal,
                        'confidence': confidence,
                        'shares': shares,
                        'status': order['status']
                    })
                    return order
        
        return None
    
    def calculate_position_size(self, confidence: float) -> float:
        """计算仓位大小"""
        base_size = self.config['base_position']
        # 信心度越高，仓位越大
        size_multiplier = 0.5 + confidence  # 0.5 - 1.5倍
        return min(base_size * size_multiplier, self.config['max_position'])

# 策略配置
strategy_config = {
    'min_confidence': 0.6,
    'base_position': 0.3,  # 30%基础仓位
    'max_position': 0.8    # 最大80%仓位
}

executor = StrategyExecutor(engine, strategy_config)
print(f"      Strategy executor created")
print(f"      Min confidence: {strategy_config['min_confidence']}")
print(f"      Base position: {strategy_config['base_position']}")
print()

# ==================== 模拟交易运行 ====================
print("[3/4] Running paper trading simulation...")

# 加载历史数据用于模拟
import pickle
with open('data/enhanced_multi_stock_2020_2024.pkl', 'rb') as f:
    stock_data = pickle.load(f)

df = stock_data['1810.HK']

# 使用最近100天模拟实时交易
recent_data = df.tail(100)

print(f"      Simulating {len(recent_data)} days of trading...")

for i in range(len(recent_data)):
    price = recent_data['close'].iloc[i]
    date = recent_data.index[i]
    
    # 生成简单信号 (基于价格动量)
    if i > 0:
        momentum = (price - recent_data['close'].iloc[i-1]) / recent_data['close'].iloc[i-1]
        
        if momentum > 0.02:
            signal = 'buy'
            confidence = min(0.6 + momentum * 10, 0.95)
        elif momentum < -0.02:
            signal = 'sell'
            confidence = min(0.6 + abs(momentum) * 10, 0.95)
        else:
            signal = 'hold'
            confidence = 0.5
        
        if signal != 'hold':
            executor.execute_signal('1810.HK', signal, confidence, price)
    
    # 记录权益
    prices = {'1810.HK': price}
    engine.record_equity(prices)
    
    if (i + 1) % 20 == 0:
        print(f"        Day {i+1}: Equity ${engine.get_portfolio_value(prices):,.2f}")

print()

# ==================== 绩效报告 ====================
print("[4/4] Generating performance report...")

metrics = engine.get_performance_metrics()

print("\n" + "=" * 70)
print("PAPER TRADING PERFORMANCE")
print("=" * 70)

print(f"\n  Initial Capital: $100,000.00")
print(f"  Final Equity: ${metrics.get('final_equity', 0):,.2f}")
print(f"  Total Return: {metrics.get('total_return', 0):.2%}")
print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
print(f"  Total Trades: {metrics.get('total_trades', 0)}")
print(f"  Final Cash: ${metrics.get('final_cash', 0):,.2f}")
print(f"  Open Positions: {metrics.get('open_positions', 0)}")

# 保存结果
results = {
    'timestamp': datetime.now().isoformat(),
    'phase': 'Hour 13-14: Automated Trading',
    'engine_config': {
        'initial_capital': 100000,
        'commission': 0.001,
        'slippage': 0.001
    },
    'strategy_config': strategy_config,
    'performance': metrics,
    'trades': engine.trades[-10:],  # 最近10笔交易
    'orders_count': len(engine.orders)
}

with open('results/hour_13_14_automated_trading.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

# 保存权益曲线
pd.DataFrame(engine.equity_history).to_csv('results/paper_trading_equity.csv')

print("\n[OK] Results saved")

print("\n" + "=" * 70)
print("Hour 13-14 completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
