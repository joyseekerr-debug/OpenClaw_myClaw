import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print("=" * 70)
print("美股地缘主题筛选 - 真实数据获取")
print("=" * 70)

# 定义ETF和个股列表
etfs = {
    'IEZ': 'iShares U.S. Oil Equipment & Services ETF',
    'BWET': 'Breakwave Tanker Shipping ETF', 
    'GDX': 'VanEck Gold Miners ETF'
}

# 重点个股列表
stocks = {
    'IEZ': ['HAL', 'SLB', 'NOV', 'NBR', 'RES', 'OII', 'TDW', 'FTI', 'NE', 'HP', 'PTEN'],
    'BWET': ['FRO', 'STNG', 'DHT', 'TNK', 'NAT', 'TEN', 'ASC'],
    'GDX': ['NEM', 'GOLD', 'AEM', 'AU', 'WPM', 'FNV', 'K', 'PAAS', 'RGLD', 'AG', 'CDE', 'HL']
}

# 计算3个月前的日期
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

print(f"\n数据时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
print("-" * 70)

# 获取ETF数据
print("\n【ETF基准数据】")
etf_returns = {}

for symbol, name in etfs.items():
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if len(hist) > 0:
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            return_3m = (end_price - start_price) / start_price * 100
            etf_returns[symbol] = return_3m
            
            print(f"{symbol:6} | {name[:35]:35} | 3月涨幅: {return_3m:+.2f}%")
    except Exception as e:
        print(f"{symbol}: 获取失败 - {e}")

print("-" * 70)

# 获取个股数据并计算相对超额
print("\n【个股数据 - 相对超额分析】")
print(f"{'代码':8} {'板块':12} {'3月涨幅':10} {'ETF基准':10} {'相对超额':10} {'Z-Score':8} {'状态'}")
print("-" * 70)

results = []

for etf_symbol, stock_list in stocks.items():
    etf_return = etf_returns.get(etf_symbol, 0)
    
    for symbol in stock_list:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if len(hist) > 0:
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                stock_return = (end_price - start_price) / start_price * 100
                
                # 计算相对超额
                relative_excess = stock_return - etf_return
                
                # 获取基本面数据
                info = ticker.info
                pe = info.get('trailingPE', 0) or info.get('forwardPE', 0)
                market_cap = info.get('marketCap', 0) / 1e9  # 转换为十亿美元
                
                # 简单判断状态
                if relative_excess < -10:
                    status = "TARGET"
                elif relative_excess < -5:
                    status = "CANDIDATE"
                else:
                    status = "WATCH"
                
                # 估算Z-Score (假设标准差为5%)
                z_score = relative_excess / 5
                
                results.append({
                    'symbol': symbol,
                    'etf': etf_symbol,
                    'stock_return': stock_return,
                    'etf_return': etf_return,
                    'relative_excess': relative_excess,
                    'z_score': z_score,
                    'pe': pe,
                    'market_cap': market_cap,
                    'status': status
                })
                
                print(f"{symbol:8} {etf_symbol:12} {stock_return:+.2f}%    {etf_return:+.2f}%    {relative_excess:+.2f}%    {z_score:+.1f}      {status}")
                
        except Exception as e:
            print(f"{symbol}: 获取失败 - {e}")

# 保存到CSV
if results:
    df = pd.DataFrame(results)
    df.to_csv('us_stock_real_data.csv', index=False)
    print(f"\n✅ 数据已保存到 us_stock_real_data.csv")
    print(f"   共获取 {len(results)} 只股票数据")
    
    # 输出优先目标
    targets = [r for r in results if r['status'] == 'TARGET']
    if targets:
        print(f"\n🎯 优先目标 ({len(targets)}只):")
        for t in targets:
            print(f"   {t['symbol']}: 相对超额 {t['relative_excess']:+.2f}%, P/E {t['pe']:.1f}")
