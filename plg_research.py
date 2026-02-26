#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Platinum Group Metals Ltd. (PLG) 深度研究分析
"""

import json
import urllib.request
from datetime import datetime

def fetch_stock_data(symbol):
    """获取股票数据"""
    url = f"https://qt.gtimg.cn/q={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = response.read().decode('utf-8')
    return data

def fetch_kline_data(symbol, days=60):
    """获取K线数据"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{days},qfq"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    return data['data'][symbol]['day']

def parse_stock_data(raw_data, symbol):
    """解析股票数据"""
    prefix = f'v_{symbol}="'
    start = raw_data.find(prefix)
    if start == -1:
        return None
    start += len(prefix)
    end = raw_data.find('";', start)
    data_str = raw_data[start:end]
    fields = data_str.split('~')
    
    # 打印字段数量用于调试
    # print(f"字段数: {len(fields)}")
    
    return {
        'name': fields[1] if len(fields) > 1 else "",
        'symbol': fields[2] if len(fields) > 2 else "",
        'price': float(fields[3]) if len(fields) > 3 and fields[3] else 0,
        'prev_close': float(fields[4]) if len(fields) > 4 and fields[4] else 0,
        'open': float(fields[5]) if len(fields) > 5 and fields[5] else 0,
        'high': float(fields[33]) if len(fields) > 33 and fields[33] else 0,
        'low': float(fields[34]) if len(fields) > 34 and fields[34] else 0,
        'volume': float(fields[6]) if len(fields) > 6 and fields[6] else 0,
        'amount': float(fields[37]) if len(fields) > 37 and fields[37] else 0,
        '52w_high': float(fields[42]) if len(fields) > 42 and fields[42] else 0,
        '52w_low': float(fields[43]) if len(fields) > 43 and fields[43] else 0,
        'pe': float(fields[38]) if len(fields) > 38 and fields[38] else 0,
        'market_cap': float(fields[44]) if len(fields) > 44 and fields[44] else 0,
        'pb': float(fields[45]) if len(fields) > 45 and fields[45] else 0,
        'date': fields[30] if len(fields) > 30 else ""
    }

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

def analyze_trend(kline_data, days):
    """分析趋势"""
    recent = kline_data[-days:]
    closes = [float(d[2]) for d in recent]
    
    if closes[-1] > closes[0]:
        return "上涨", ((closes[-1] - closes[0]) / closes[0]) * 100
    else:
        return "下跌", ((closes[-1] - closes[0]) / closes[0]) * 100

def main():
    symbol = "usPLG"
    
    print("=" * 70)
    print("Platinum Group Metals Ltd. (PLG) 深度研究报告")
    print("=" * 70)
    print()
    
    # 获取基础数据
    raw_data = fetch_stock_data(symbol)
    stock = parse_stock_data(raw_data, symbol)
    
    if not stock:
        print("无法获取股票数据")
        return
    
    print("【一、公司概况】")
    print("-" * 70)
    print(f"公司全称: {stock['name']}")
    print(f"股票代码: {stock['symbol']}")
    print(f"上市交易所: NYSE American (美国证券交易所)")
    print(f"所属行业: 铂族金属矿业 / 贵金属开采")
    print()
    
    print("【二、当前股价数据】")
    print("-" * 70)
    print(f"当前价格: ${stock['price']:.2f} USD")
    print(f"昨日收盘: ${stock['prev_close']:.2f} USD")
    print(f"今日开盘: ${stock['open']:.2f} USD")
    print(f"今日最高: ${stock['high']:.2f} USD")
    print(f"今日最低: ${stock['low']:.2f} USD")
    if stock['prev_close'] > 0:
        change_pct = ((stock['price'] - stock['prev_close']) / stock['prev_close']) * 100
        print(f"涨跌额: ${stock['price'] - stock['prev_close']:.2f}")
        print(f"涨跌幅: {change_pct:+.2f}%")
    print(f"数据时间: {stock['date']}")
    print()
    
    print("【三、估值指标】")
    print("-" * 70)
    print(f"市盈率 (P/E): {stock['pe']:.2f}" if stock['pe'] > 0 else "市盈率: N/A (亏损)")
    print(f"市净率 (P/B): {stock['pb']:.2f}" if stock['pb'] > 0 else "市净率: N/A")
    print(f"市值: ${stock['market_cap']/100000000:.2f} 亿美元" if stock['market_cap'] > 0 else "市值: 数据暂缺")
    print(f"52周最高: ${stock['52w_high']:.2f}" if stock['52w_high'] > 0 else "52周最高: N/A")
    print(f"52周最低: ${stock['52w_low']:.2f}" if stock['52w_low'] > 0 else "52周最低: N/A")
    
    if stock['52w_high'] > 0 and stock['52w_low'] > 0:
        position = ((stock['price'] - stock['52w_low']) / (stock['52w_high'] - stock['52w_low'])) * 100
        print(f"52周位置: {position:.1f}%")
    print()
    
    # 获取K线数据
    print("【四、技术分析】")
    print("-" * 70)
    try:
        kline_data = fetch_kline_data(symbol, 60)
        closes = [float(d[2]) for d in kline_data]
        
        # 移动平均线
        ma5 = calculate_ma(closes, 5)
        ma10 = calculate_ma(closes, 10)
        ma20 = calculate_ma(closes, 20)
        
        print(f"MA5:  ${ma5:.3f}" if ma5 else "MA5: N/A")
        print(f"MA10: ${ma10:.3f}" if ma10 else "MA10: N/A")
        print(f"MA20: ${ma20:.3f}" if ma20 else "MA20: N/A")
        
        if ma5 and ma10:
            if stock['price'] > ma5 > ma10:
                print("均线状态: 多头排列 (短期趋势向上)")
            elif stock['price'] < ma5 < ma10:
                print("均线状态: 空头排列 (短期趋势向下)")
            else:
                print("均线状态: 震荡整理")
        print()
        
        # RSI
        rsi = calculate_rsi(closes)
        if rsi:
            print(f"RSI(14): {rsi:.2f}")
            if rsi > 70:
                print("状态: 超买区域")
            elif rsi < 30:
                print("状态: 超卖区域 (潜在反弹机会)")
            elif rsi > 50:
                print("状态: 多头占优")
            else:
                print("状态: 空头占优")
        print()
        
        # 趋势分析
        trend_5d, change_5d = analyze_trend(kline_data, 5)
        trend_20d, change_20d = analyze_trend(kline_data, 20)
        
        print("短期趋势 (5日):  {0} ({1:+.2f}%)".format(trend_5d, change_5d))
        print("中期趋势 (20日): {0} ({1:+.2f}%)".format(trend_20d, change_20d))
        
    except Exception as e:
        print(f"技术分析数据获取失败: {e}")
    print()
    
    print("【五、基本面分析】")
    print("-" * 70)
    print("公司业务:")
    print("  - Platinum Group Metals Ltd. 是一家专注于铂族金属(PGM)勘探和开发的加拿大公司")
    print("  - 主要项目: Waterberg项目(南非) - 世界上最大的铂族金属矿床之一")
    print("  - 金属类型: 铂金、钯金、铑、金、铜、镍等")
    print()
    
    print("行业背景:")
    print("  - 铂族金属主要用于汽车催化转化器(减少排放)")
    print("  - 钯金和铑近年来价格大幅上涨")
    print("  - 电动汽车转型对传统铂族金属需求存在不确定性")
    print("  - 南非是主要产地，存在地缘政治和运营风险")
    print()
    
    print("风险因素:")
    print("  1. 勘探/开发阶段风险 - Waterberg项目尚未投产")
    print("  2. 大宗商品价格波动 - 铂族金属价格高度波动")
    print("  3. 地缘政治风险 - 主要项目在南非")
    print("  4. 融资风险 - 需要大量资本支出完成项目建设")
    print("  5. 汇率风险 - 以美元计价，成本多为南非兰特")
    print("  6. 技术替代风险 - 电动车普及可能减少催化剂需求")
    print()
    
    print("积极因素:")
    print("  1. Waterberg项目规模巨大，品位优良")
    print("  2. 与大型矿企(如Implats)合资，降低风险")
    print("  3. 铂族金属长期供应短缺预期")
    print("  4. 氢能产业发展可能带来新的铂金需求")
    print("  5. 股价处于历史低位，潜在上涨空间大")
    print()
    
    print("【六、投资建议】")
    print("-" * 70)
    
    # 综合评分
    score = 0
    factors = []
    
    # 估值因素
    if stock['price'] < 3.0:
        score += 1
        factors.append("股价低于$3，估值相对较低")
    
    # 技术面
    if rsi and rsi < 40:
        score += 1
        factors.append("RSI处于低位，短期超卖")
    
    # 趋势
    if trend_20d == "上涨":
        score += 1
        factors.append("中期趋势向上")
    
    # 风险
    score -= 2  # 高风险股票
    factors.append("高风险勘探阶段公司")
    
    print(f"综合评分: {score}/5")
    print()
    
    if score >= 2:
        rating = "谨慎买入"
        print("评级: 谨慎买入")
    elif score >= 0:
        rating = "观望"
        print("评级: 观望")
    else:
        rating = "回避"
        print("评级: 回避")
    print()
    
    print("适合投资者类型:")
    print("  - 高风险承受能力投资者")
    print("  - 对大宗商品/矿业有了解的投资者")
    print("  - 长期投资者(3-5年以上)")
    print("  - 资产配置中可接受高波动性的投资者")
    print()
    
    print("操作策略:")
    print("  激进策略:")
    print("    - 可在当前价位小仓位试探性买入")
    print("    - 分批建仓，单只股票仓位不超过总资产5%")
    print("    - 止损位设置在$2.00(-22%)")
    print()
    print("  稳健策略:")
    print("    - 等待Waterberg项目取得更多进展")
    print("    - 等待突破$3.50阻力位确认")
    print("    - 或等待回调至$2.00-2.20区间再考虑")
    print()
    
    print("关键关注事项:")
    print("  1. Waterberg项目开发进度和融资情况")
    print("  2. 铂族金属(尤其是钯、铑)价格走势")
    print("  3. 公司季度财报和现金流状况")
    print("  4. 南非政治局势和矿业政策变化")
    print("  5. 电动汽车发展对需求的实际影响")
    print()
    
    print("=" * 70)
    print("免责声明: 以上分析仅供参考，不构成投资建议。")
    print("矿业股票风险极高，可能导致本金全部损失。请谨慎投资。")
    print("=" * 70)

if __name__ == "__main__":
    main()
