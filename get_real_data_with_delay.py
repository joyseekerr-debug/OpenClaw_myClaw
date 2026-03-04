import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

print("=" * 70)
print("美股地缘主题筛选 - 真实数据获取 (带延迟)")
print("=" * 70)

# 定义重点个股列表
stocks = ['HAL', 'NOV', 'NBR', 'RES', 'OII', 'TDW', 'FRO', 'DHT', 'TNK', 'NEM', 'GOLD', 'AG']
etfs = ['IEZ', 'GDX']

# 计算3个月前的日期
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

print(f"\n数据时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
print("-" * 70)

results = []

# 先获取ETF数据
print("\n【ETF基准数据】")
etf_returns = {}

for symbol in etfs:
    try:
        print(f"获取 {symbol}...", end=" ")
        ticker = yf.Ticker(symbol)
        time.sleep(2)  # 延迟避免频率限制
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if len(hist) > 0:
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            return_3m = (end_price - start_price) / start_price * 100
            etf_returns[symbol] = return_3m
            print(f"✓ 3月涨幅: {return_3m:+.2f}%")
        else:
            print("✗ 无数据")
    except Exception as e:
        print(f"✗ {str(e)[:50]}")

print("-" * 70)

# 获取个股数据
print("\n【个股数据 - 相对超额分析】")
print(f"{'代码':6} {'ETF':6} {'3月涨幅':10} {'ETF基准':10} {'相对超额':10} {'状态'}")
print("-" * 70)

for symbol in stocks:
    try:
        # 确定属于哪个ETF
        etf_symbol = 'IEZ' if symbol in ['HAL', 'NOV', 'NBR', 'RES', 'OII', 'TDW'] else 'GDX'
        
        print(f"{symbol:6} {etf_symbol:6} ", end="")
        
        ticker = yf.Ticker(symbol)
        time.sleep(3)  # 延迟3秒避免频率限制
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if len(hist) > 0 and etf_symbol in etf_returns:
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            stock_return = (end_price - start_price) / start_price * 100
            
            etf_return = etf_returns[etf_symbol]
            relative_excess = stock_return - etf_return
            
            # 获取基本面数据
            info = ticker.info
            time.sleep(1)
            pe = info.get('trailingPE', 0) or info.get('forwardPE', 0)
            market_cap = info.get('marketCap', 0) / 1e9
            
            # 判断状态
            if relative_excess < -10:
                status = "🎯 TARGET"
            elif relative_excess < -5:
                status = "👀 CANDIDATE"
            else:
                status = "⏸️ WATCH"
            
            results.append({
                'symbol': symbol,
                'etf': etf_symbol,
                'stock_return': stock_return,
                'etf_return': etf_return,
                'relative_excess': relative_excess,
                'pe': pe,
                'market_cap': market_cap,
                'status': status
            })
            
            print(f"{stock_return:+.2f}%     {etf_return:+.2f}%     {relative_excess:+.2f}%     {status}")
        else:
            print("无数据或ETF基准缺失")
            
    except Exception as e:
        print(f"错误: {str(e)[:40]}")

# 保存结果
if results:
    df = pd.DataFrame(results)
    df.to_csv('us_stock_real_data.csv', index=False)
    print("\n" + "=" * 70)
    print(f"✅ 数据已保存到 us_stock_real_data.csv")
    print(f"   共获取 {len(results)} 只股票数据")
    
    # 输出优先目标
    targets = [r for r in results if 'TARGET' in r['status']]
    if targets:
        print(f"\n🎯 优先目标 ({len(targets)}只):")
        for t in targets:
            print(f"   {t['symbol']}: 相对超额 {t['relative_excess']:+.2f}%, P/E {t['pe']:.1f}, 市值 ${t['market_cap']:.1f}B")
else:
    print("\n❌ 未能获取有效数据")
