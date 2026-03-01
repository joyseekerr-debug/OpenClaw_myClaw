# -*- coding: utf-8 -*-
"""
24小时优化 - Hour 9-10: 风险管理
VaR计算、压力测试、极端行情回测
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
print("24-Hour Optimization - Hour 9-10: Risk Management")
print("VaR, Stress Testing, Extreme Scenarios")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载数据
print("[1/4] Loading data...")
import pickle
with open('data/enhanced_multi_stock_2020_2024.pkl', 'rb') as f:
    data = pickle.load(f)

df = data['1810.HK'].copy()
returns = df['close'].pct_change().dropna()
print(f"      Data: {len(df)} records")
print(f"      Returns: {len(returns)} observations")
print()

# ==================== VaR计算 ====================
print("[2/4] Calculating Value at Risk (VaR)...")

def calculate_var(returns, confidence_levels=[0.95, 0.99]):
    """计算VaR"""
    var_results = {}
    
    for conf in confidence_levels:
        # 历史VaR
        historical_var = np.percentile(returns, (1 - conf) * 100)
        
        # 参数VaR (正态分布假设)
        mean = returns.mean()
        std = returns.std()
        parametric_var = mean - std * {0.95: 1.645, 0.99: 2.326}[conf]
        
        # CVaR (条件VaR)
        cvar = returns[returns <= historical_var].mean()
        
        var_results[f'{int(conf*100)}%'] = {
            'historical_var': float(historical_var),
            'parametric_var': float(parametric_var),
            'cvar': float(cvar)
        }
    
    return var_results

var_results = calculate_var(returns)

print("      VaR Results:")
for conf, values in var_results.items():
    print(f"        {conf} Historical VaR: {values['historical_var']:.2%}")
    print(f"        {conf} Parametric VaR: {values['parametric_var']:.2%}")
    print(f"        {conf} CVaR: {values['cvar']:.2%}")
print()

# ==================== 压力测试 ====================
print("[3/4] Stress testing...")

def stress_test_scenarios(df, initial_capital=100000):
    """压力测试场景"""
    
    scenarios = {
        'market_crash_2008': {'drop': -0.40, 'description': '2008年金融危机'},
        'covid_crash': {'drop': -0.35, 'description': 'COVID-19崩盘'},
        'flash_crash': {'drop': -0.10, 'description': '闪崩'},
        'prolonged_bear': {'drop': -0.50, 'description': '长期熊市'}
    }
    
    results = {}
    current_price = df['close'].iloc[-1]
    position_value = initial_capital * 0.5  # 假设50%仓位
    
    for scenario_name, params in scenarios.items():
        drop = params['drop']
        stressed_price = current_price * (1 + drop)
        loss = position_value * abs(drop)
        remaining = initial_capital - loss
        
        results[scenario_name] = {
            'description': params['description'],
            'price_drop': drop,
            'stressed_price': float(stressed_price),
            'portfolio_loss': float(loss),
            'remaining_capital': float(remaining),
            'loss_percentage': float(loss / initial_capital)
        }
        
        print(f"      {scenario_name}:")
        print(f"        {params['description']}")
        print(f"        Price drop: {drop:.1%}")
        print(f"        Portfolio loss: ${loss:,.2f} ({loss/initial_capital:.1%})")
    
    return results

stress_results = stress_test_scenarios(df)
print()

# ==================== 极端行情回测 ====================
print("[4/4] Extreme market backtest...")

def extreme_market_backtest(df, initial_capital=100000):
    """在极端行情期间回测"""
    
    # 定义极端行情期间 (基于波动率)
    df['volatility_20'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
    high_vol_periods = df[df['volatility_20'] > df['volatility_20'].quantile(0.9)]
    
    print(f"      High volatility periods: {len(high_vol_periods)} days")
    
    # 简单策略: 高波动时减仓
    capital = initial_capital
    position = 0
    equity_curve = []
    
    for i in range(20, len(df)):
        price = df['close'].iloc[i]
        vol = df['volatility_20'].iloc[i]
        
        # 根据波动率调整仓位
        if vol > 0.5:  # 高波动
            target_position = 0.2  # 20%仓位
        elif vol > 0.3:  # 中等波动
            target_position = 0.5  # 50%仓位
        else:  # 低波动
            target_position = 0.8  # 80%仓位
        
        # 调整仓位
        current_value = position * price
        target_value = capital * target_position
        
        if target_value > current_value:
            # 买入
            buy_value = target_value - current_value
            shares_to_buy = buy_value / price
            cost = shares_to_buy * price * 1.001  # 包含手续费
            if cost <= capital:
                position += shares_to_buy
                capital -= cost
        elif target_value < current_value:
            # 卖出
            sell_value = current_value - target_value
            shares_to_sell = sell_value / price
            position -= shares_to_sell
            capital += shares_to_sell * price * 0.999
        
        equity = capital + position * price
        equity_curve.append(equity)
    
    # 计算指标
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    total_return = (final_equity - initial_capital) / initial_capital
    
    # 计算回撤
    equity_series = pd.Series(equity_curve)
    peak = equity_series.expanding().max()
    drawdown = (equity_series - peak) / peak
    max_dd = drawdown.min()
    
    return {
        'total_return': float(total_return),
        'max_drawdown': float(max_dd),
        'final_equity': float(final_equity),
        'high_vol_days': len(high_vol_periods)
    }

extreme_results = extreme_market_backtest(df)

print(f"\n      Extreme Market Backtest:")
print(f"        Total Return: {extreme_results['total_return']:.2%}")
print(f"        Max Drawdown: {extreme_results['max_drawdown']:.2%}")
print(f"        Final Equity: ${extreme_results['final_equity']:,.2f}")

# ==================== 保存结果 ====================
print("\n" + "=" * 70)
print("RISK MANAGEMENT SUMMARY")
print("=" * 70)

results = {
    'timestamp': datetime.now().isoformat(),
    'phase': 'Hour 9-10: Risk Management',
    'var': var_results,
    'stress_test': stress_results,
    'extreme_backtest': extreme_results
}

print(f"\n  VaR (95%): {var_results['95%']['historical_var']:.2%}")
print(f"  VaR (99%): {var_results['99%']['historical_var']:.2%}")
print(f"  CVaR (99%): {var_results['99%']['cvar']:.2%}")
print(f"\n  Worst scenario loss: {max(s['loss_percentage'] for s in stress_results.values()):.1%}")
print(f"  Extreme backtest return: {extreme_results['total_return']:.2%}")

with open('results/hour_9_10_risk_management.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n[OK] Results saved to results/hour_9_10_risk_management.json")

print("\n" + "=" * 70)
print("Hour 9-10 completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
