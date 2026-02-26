#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小米集团(01810.HK) 技术分析脚本
"""

import json
import urllib.request
from datetime import datetime

def fetch_kline_data():
    """获取K线数据"""
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk01810,day,,,60,qfq"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    return data['data']['hk01810']['day']

def calculate_ma(prices, period):
    """计算移动平均线"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, period + 1):
        change = prices[-i] - prices[-(i+1)]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    if len(prices) < slow:
        return None, None, None
    
    # 计算EMA
    def ema(data, period):
        multiplier = 2 / (period + 1)
        ema_values = [data[0]]
        for i in range(1, len(data)):
            ema_values.append((data[i] - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values
    
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    
    # MACD线
    macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
    
    # 信号线
    signal_line = ema(macd_line[-(slow+signal):], signal)[-1] if len(macd_line) >= slow+signal else None
    
    # MACD柱状图
    histogram = macd_line[-1] - signal_line if signal_line else None
    
    return macd_line[-1], signal_line, histogram

def calculate_bollinger(prices, period=20, std_dev=2):
    """计算布林带"""
    if len(prices) < period:
        return None, None, None
    
    sma = sum(prices[-period:]) / period
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std = variance ** 0.5
    
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    
    return upper, sma, lower

def find_support_resistance(kline_data, days=20):
    """寻找近期支撑位和阻力位"""
    recent = kline_data[-days:]
    highs = [float(d[4]) for d in recent]  # 最高
    lows = [float(d[3]) for d in recent]   # 最低
    
    resistance = max(highs)
    support = min(lows)
    
    return support, resistance

def analyze_trend(kline_data, days=5):
    """分析短期趋势"""
    recent = kline_data[-days:]
    closes = [float(d[2]) for d in recent]
    
    # 简单趋势判断
    if closes[-1] > closes[0]:
        return "上涨", ((closes[-1] - closes[0]) / closes[0]) * 100
    else:
        return "下跌", ((closes[-1] - closes[0]) / closes[0]) * 100

def main():
    print("=" * 60)
    print("小米集团 (01810.HK) 技术分析报告")
    print("=" * 60)
    print()
    
    # 获取数据
    kline_data = fetch_kline_data()
    closes = [float(d[2]) for d in kline_data]
    current_price = closes[-1]
    
    print(f"分析日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"当前股价: {current_price:.3f} HKD")
    print(f"数据周期: 最近{len(kline_data)}个交易日")
    print()
    
    # 移动平均线
    print("-" * 40)
    print("【移动平均线 (MA)】")
    print("-" * 40)
    ma5 = calculate_ma(closes, 5)
    ma10 = calculate_ma(closes, 10)
    ma20 = calculate_ma(closes, 20)
    ma60 = calculate_ma(closes, 60) if len(closes) >= 60 else None
    
    print(f"MA5:  {ma5:.3f} HKD {'↑' if current_price > ma5 else '↓'}")
    print(f"MA10: {ma10:.3f} HKD {'↑' if current_price > ma10 else '↓'}")
    print(f"MA20: {ma20:.3f} HKD {'↑' if current_price > ma20 else '↓'}")
    if ma60:
        print(f"MA60: {ma60:.3f} HKD {'↑' if current_price > ma60 else '↓'}")
    
    # 判断均线排列
    if ma5 > ma10 > ma20:
        print("\n均线状态: 多头排列 (短期趋势向上)")
    elif ma5 < ma10 < ma20:
        print("\n均线状态: 空头排列 (短期趋势向下)")
    else:
        print("\n均线状态: 震荡整理 (趋势不明朗)")
    print()
    
    # RSI指标
    print("-" * 40)
    print("【RSI 相对强弱指标】")
    print("-" * 40)
    rsi = calculate_rsi(closes)
    print(f"RSI(14): {rsi:.2f}")
    
    if rsi > 70:
        print("状态: 超买区域 (可能回调)")
    elif rsi < 30:
        print("状态: 超卖区域 (可能反弹)")
    elif rsi > 50:
        print("状态: 多头占优")
    else:
        print("状态: 空头占优")
    print()
    
    # MACD指标
    print("-" * 40)
    print("【MACD 指标】")
    print("-" * 40)
    macd, signal, histogram = calculate_macd(closes)
    if macd is not None:
        print(f"MACD:     {macd:.4f}")
        print(f"信号线:   {signal:.4f}")
        print(f"柱状图:   {histogram:.4f}")
        
        if macd > signal and histogram > 0:
            print("状态: 金叉上行 (买入信号)")
        elif macd < signal and histogram < 0:
            print("状态: 死叉下行 (卖出信号)")
        else:
            print("状态: 趋势转换中")
    print()
    
    # 布林带
    print("-" * 40)
    print("【布林带 (Bollinger Bands)】")
    print("-" * 40)
    upper, middle, lower = calculate_bollinger(closes)
    print(f"上轨: {upper:.3f} HKD")
    print(f"中轨: {middle:.3f} HKD")
    print(f"下轨: {lower:.3f} HKD")
    print(f"当前: {current_price:.3f} HKD")
    
    # 布林带位置分析
    band_width = ((current_price - lower) / (upper - lower)) * 100
    print(f"\n带宽位置: {band_width:.1f}%")
    if band_width > 80:
        print("状态: 接近上轨 (偏高)")
    elif band_width < 20:
        print("状态: 接近下轨 (偏低)")
    else:
        print("状态: 中轨附近 (中性)")
    print()
    
    # 支撑阻力位
    print("-" * 40)
    print("【支撑与阻力】")
    print("-" * 40)
    support, resistance = find_support_resistance(kline_data)
    print(f"近期阻力位: {resistance:.3f} HKD")
    print(f"当前股价:   {current_price:.3f} HKD")
    print(f"近期支撑位: {support:.3f} HKD")
    
    # 距离计算
    dist_to_resist = ((resistance - current_price) / current_price) * 100
    dist_to_support = ((current_price - support) / support) * 100
    print(f"\n距阻力位: +{dist_to_resist:.1f}%")
    print(f"距支撑位: -{dist_to_support:.1f}%")
    print()
    
    # 趋势分析
    print("-" * 40)
    print("【趋势分析】")
    print("-" * 40)
    trend_5d, change_5d = analyze_trend(kline_data, 5)
    trend_20d, change_20d = analyze_trend(kline_data, 20)
    
    print(f"5日趋势:  {trend_5d} ({change_5d:+.2f}%)")
    print(f"20日趋势: {trend_20d} ({change_20d:+.2f}%)")
    
    # 52周位置
    high_52w = max([float(d[4]) for d in kline_data])
    low_52w = min([float(d[3]) for d in kline_data])
    position_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
    print(f"\n52周区间: {low_52w:.2f} - {high_52w:.2f} HKD")
    print(f"当前位置: {position_52w:.1f}%")
    print()
    
    # 综合研判
    print("=" * 60)
    print("【综合技术研判】")
    print("=" * 60)
    
    bullish_signals = 0
    bearish_signals = 0
    
    # 均线判断
    if current_price > ma5 > ma10:
        bullish_signals += 1
    elif current_price < ma5 < ma10:
        bearish_signals += 1
    
    # RSI判断
    if 30 < rsi < 50:
        bullish_signals += 0.5  # 超卖后反弹潜力
    elif rsi > 70:
        bearish_signals += 0.5
    elif rsi < 30:
        bullish_signals += 1
    
    # MACD判断
    if macd and signal and macd > signal:
        bullish_signals += 1
    elif macd and signal and macd < signal:
        bearish_signals += 1
    
    # 趋势判断
    if trend_5d == "上涨":
        bullish_signals += 0.5
    else:
        bearish_signals += 0.5
    
    print(f"多头信号强度: {bullish_signals}")
    print(f"空头信号强度: {bearish_signals}")
    print()
    
    if bullish_signals > bearish_signals + 1:
        print("研判结论: 偏多")
        print("   技术指标显示短期有上涨动力")
    elif bearish_signals > bullish_signals + 1:
        print("研判结论: 偏空")
        print("   技术指标显示短期有下跌压力")
    else:
        print("研判结论: 中性震荡")
        print("   技术指标信号不一，建议观望")
    
    print()
    print("-" * 60)
    print("操作建议区间:")
    print(f"  激进买入: < {support * 1.02:.2f} (接近支撑)")
    print(f"  谨慎买入: {ma20:.2f} 附近")
    print(f"  止盈参考: {resistance:.2f}")
    print(f"  止损参考: {support * 0.98:.2f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
