# -*- coding: utf-8 -*-
"""
数据下载脚本 - 获取历史数据用于回测
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_realistic_stock_data(symbol='1810.HK', days=500, output_file='data/historical_data.csv'):
    """
    生成逼真的股票历史数据（用于测试优化）
    基于随机游走模型，但带有趋势和波动率聚类
    """
    np.random.seed(42)
    
    # 生成日期序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = dates[dates.weekday < 5]  # 只保留工作日
    
    n_days = len(dates)
    
    # 参数设置
    initial_price = 20.0
    drift = 0.0002  # 轻微上涨趋势
    volatility = 0.02  # 日波动率
    
    # GARCH-like 波动率聚类
    volatility_series = np.zeros(n_days)
    volatility_series[0] = volatility
    
    alpha = 0.1  # ARCH参数
    beta = 0.85  # GARCH参数
    omega = 0.0001
    
    returns = np.zeros(n_days)
    
    for t in range(1, n_days):
        # 更新波动率
        volatility_series[t] = np.sqrt(
            omega + alpha * returns[t-1]**2 + beta * volatility_series[t-1]**2
        )
        
        # 生成收益（带轻微自相关）
        returns[t] = np.random.normal(drift, volatility_series[t])
        if t > 1:
            returns[t] += 0.1 * returns[t-1]  # 轻微动量
    
    # 计算价格
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # 生成OHLC数据
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        daily_vol = volatility_series[i]
        
        # 日内波动
        open_price = price * (1 + np.random.normal(0, daily_vol * 0.3))
        high_price = max(open_price, price) * (1 + abs(np.random.normal(0, daily_vol * 0.5)))
        low_price = min(open_price, price) * (1 - abs(np.random.normal(0, daily_vol * 0.5)))
        close_price = price
        
        # 成交量（与波动率相关）
        base_volume = 5000000
        volume = int(base_volume * (1 + np.random.exponential(0.5)) * (1 + daily_vol * 10))
        
        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    df['symbol'] = symbol
    df['timeframe'] = '1d'
    
    # 保存
    df.to_csv(output_file)
    logger.info(f"Generated realistic data: {len(df)} rows, saved to {output_file}")
    logger.info(f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    logger.info(f"Total return: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:.2f}%")
    
    return df

if __name__ == '__main__':
    # 生成2年历史数据
    df = generate_realistic_stock_data(days=500, output_file='data/historical_2y.csv')
    print(f"\nData statistics:")
    print(df.describe())
