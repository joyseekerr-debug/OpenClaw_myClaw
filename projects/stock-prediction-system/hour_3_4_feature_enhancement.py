# -*- coding: utf-8 -*-
"""
24小时优化 - Hour 3-4: 特征增强
添加技术指标、宏观因子、市场情绪特征
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
print("24-Hour Optimization - Hour 3-4: Feature Enhancement")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载多股票数据
print("[1/4] Loading multi-stock data...")
import pickle
with open('data/multi_stock_2020_2024.pkl', 'rb') as f:
    multi_stock_data = pickle.load(f)

print(f"      Loaded {len(multi_stock_data)} stocks")

# ==================== 技术指标特征 ====================
print("\n[2/4] Adding technical indicators...")

def add_technical_features(df):
    """添加技术指标特征"""
    df = df.copy()
    
    # 趋势指标
    for window in [5, 10, 20, 60]:
        df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
        df[f'ema_{window}'] = df['close'].ewm(span=window, adjust=False).mean()
        df[f'close_to_sma_{window}'] = df['close'] / df[f'sma_{window}'] - 1
    
    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # 布林带
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # 波动率
    df['volatility_20'] = df['close'].pct_change().rolling(window=20).std() * np.sqrt(252)
    df['atr_14'] = (df['high'] - df['low']).rolling(window=14).mean()
    
    # 成交量指标
    df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']
    
    # 价格动量
    for window in [5, 10, 20]:
        df[f'momentum_{window}'] = df['close'].pct_change(window)
    
    # 价格位置
    df['high_20'] = df['high'].rolling(window=20).max()
    df['low_20'] = df['low'].rolling(window=20).min()
    df['price_position'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'])
    
    return df

enhanced_data = {}
for symbol, df in multi_stock_data.items():
    print(f"      Processing {symbol}...")
    enhanced_df = add_technical_features(df)
    enhanced_data[symbol] = enhanced_df
    print(f"        Features: {len(enhanced_df.columns)}")

# ==================== 宏观因子特征 ====================
print("\n[3/4] Adding macro factors...")

def add_macro_features(df, dates):
    """添加宏观因子 (模拟数据)"""
    np.random.seed(42)
    
    # VIX-like 波动率指数 (模拟)
    base_vix = 20
    vix_changes = np.random.normal(0, 0.05, len(df))
    df['vix_index'] = base_vix * np.exp(np.cumsum(vix_changes))
    
    # 利率 (模拟，缓慢变化)
    base_rate = 2.5
    rate_changes = np.random.normal(0, 0.01, len(df))
    df['interest_rate'] = base_rate + np.cumsum(rate_changes) * 0.1
    df['interest_rate'] = df['interest_rate'].clip(0, 5)
    
    # 汇率 (模拟港币/美元)
    df['hkd_usd'] = 7.75 + np.random.normal(0, 0.01, len(df))
    
    # 商品指数 (模拟)
    df['commodity_index'] = 100 * np.exp(np.cumsum(np.random.normal(0.0001, 0.01, len(df))))
    
    # 时间特征
    df['day_of_week'] = pd.to_datetime(df.index).dayofweek
    df['month'] = pd.to_datetime(df.index).month
    df['quarter'] = pd.to_datetime(df.index).quarter
    
    # 是否月初/月末
    df['is_month_start'] = (pd.to_datetime(df.index).day <= 5).astype(int)
    df['is_month_end'] = (pd.to_datetime(df.index).day >= 25).astype(int)
    
    return df

for symbol, df in enhanced_data.items():
    enhanced_data[symbol] = add_macro_features(df, df.index)

print(f"      Added macro features to all stocks")

# ==================== 交叉股票特征 ====================
print("\n[4/4] Adding cross-stock features...")

# 计算股票间相关性特征
all_returns = pd.DataFrame({symbol: df['close'].pct_change() for symbol, df in enhanced_data.items()})

# 添加市场平均收益率
market_return = all_returns.mean(axis=1)

for symbol in enhanced_data.keys():
    enhanced_data[symbol]['market_return'] = market_return
    enhanced_data[symbol]['beta_20'] = all_returns[symbol].rolling(20).cov(market_return) / market_return.rolling(20).var()
    
    # 相对强弱
    enhanced_data[symbol]['relative_strength'] = (1 + all_returns[symbol]).rolling(20).apply(lambda x: x.prod()) / \
                                                  (1 + market_return).rolling(20).apply(lambda x: x.prod())

print(f"      Added cross-stock correlation features")

# ==================== 保存增强数据 ====================
print("\n" + "=" * 70)
print("FEATURE ENHANCEMENT SUMMARY")
print("=" * 70)

feature_summary = {}
for symbol, df in enhanced_data.items():
    feature_count = len(df.columns)
    feature_summary[symbol] = {
        'total_features': feature_count,
        'technical_features': len([c for c in df.columns if any(x in c for x in ['sma', 'ema', 'macd', 'rsi', 'bb_', 'volatility', 'atr', 'momentum'])]),
        'macro_features': len([c for c in df.columns if any(x in c for x in ['vix', 'interest_rate', 'hkd', 'commodity', 'day_', 'month', 'quarter', 'is_month'])]),
        'cross_stock_features': len([c for c in df.columns if any(x in c for x in ['market_return', 'beta', 'relative'])]),
        'samples': len(df)
    }
    print(f"\n  {symbol}:")
    print(f"    Total features: {feature_count}")
    print(f"    Technical: {feature_summary[symbol]['technical_features']}")
    print(f"    Macro: {feature_summary[symbol]['macro_features']}")
    print(f"    Cross-stock: {feature_summary[symbol]['cross_stock_features']}")

# 保存增强数据
with open('data/enhanced_multi_stock_2020_2024.pkl', 'wb') as f:
    pickle.dump(enhanced_data, f)

# 保存CSV格式 (便于查看)
for symbol, df in enhanced_data.items():
    df.to_csv(f'data/{symbol.replace(".", "_")}_enhanced.csv')

# 保存摘要
summary = {
    'timestamp': datetime.now().isoformat(),
    'phase': 'Hour 3-4: Feature Enhancement',
    'feature_summary': feature_summary,
    'total_features': sum(s['total_features'] for s in feature_summary.values()) // len(feature_summary)
}

with open('results/hour_3_4_feature_enhancement.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n  Average features per stock: {summary['total_features']}")
print("\n[OK] Enhanced data saved")

print("\n" + "=" * 70)
print("Hour 3-4 completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
