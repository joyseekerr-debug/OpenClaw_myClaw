import urllib.request
import json
import ssl
import pandas as pd
from datetime import datetime

# 创建SSL上下文
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_stock_data(symbol, period='3mo'):
    """从Yahoo Finance获取股票数据"""
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={period}'
    
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
        )
        
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            result = data.get('chart', {}).get('result', [{}])[0]
            prices = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
            
            if len(prices) >= 2:
                current = prices[-1]
                start = prices[0]
                return_3m = (current - start) / start * 100
                return {
                    'symbol': symbol,
                    'current_price': current,
                    'start_price': start,
                    'return_3m': return_3m,
                    'data_points': len(prices)
                }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}
    
    return {'symbol': symbol, 'error': 'No data'}

print("=" * 70)
print("美股地缘主题筛选 - 真实数据获取")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 70)

# 定义ETF基准
etfs = ['IEZ', 'BWET', 'GDX']
etf_returns = {}

print("\n【ETF基准数据】")
print("-" * 70)

for etf in etfs:
    result = get_stock_data(etf)
    if 'error' not in result:
        etf_returns[etf] = result['return_3m']
        print(f"{etf:6} | 当前: ${result['current_price']:7.2f} | 3月前: ${result['start_price']:7.2f} | 涨幅: {result['return_3m']:+7.2f}%")
    else:
        print(f"{etf:6} | 错误: {result['error']}")

print("\n" + "=" * 70)

# 获取个股数据
stocks = {
    'IEZ': ['HAL', 'SLB', 'NOV', 'NBR', 'RES', 'OII', 'TDW', 'FTI', 'NE', 'HP', 'PTEN'],
    'GDX': ['NEM', 'GOLD', 'AEM', 'WPM', 'FNV', 'RGLD', 'AG', 'CDE', 'HL']
}

results = []

for etf, symbols in stocks.items():
    if etf not in etf_returns:
        continue
    
    print(f"\n【{etf} 成分股 (基准: {etf_returns[etf]:+.2f}%)】")
    print(f"{'代码':8} {'当前价':10} {'3月涨幅':10} {'相对超额':10} {'状态'}")
    print("-" * 70)
    
    for symbol in symbols:
        result = get_stock_data(symbol)
        
        if 'error' not in result:
            relative_excess = result['return_3m'] - etf_returns[etf]
            
            if relative_excess < -10:
                status = "🎯 TARGET"
            elif relative_excess < -5:
                status = "👀 CANDIDATE"
            else:
                status = "⏸️ WATCH"
            
            results.append({
                'symbol': symbol,
                'etf': etf,
                'price': result['current_price'],
                'return_3m': result['return_3m'],
                'etf_return': etf_returns[etf],
                'relative_excess': relative_excess,
                'status': status
            })
            
            print(f"{symbol:8} ${result['current_price']:8.2f} {result['return_3m']:+8.2f}% {relative_excess:+9.2f}% {status}")
        else:
            print(f"{symbol:8} 错误: {result['error'][:40]}")

# 保存结果
if results:
    df = pd.DataFrame(results)
    df.to_csv('US_Stock_Real_Data_Final.csv', index=False)
    
    print("\n" + "=" * 70)
    print(f"✅ 数据已保存到 US_Stock_Real_Data_Final.csv")
    print(f"   共获取 {len(results)} 只股票数据")
    
    # 优先目标
    targets = [r for r in results if 'TARGET' in r['status']]
    candidates = [r for r in results if 'CANDIDATE' in r['status']]
    
    if targets:
        print(f"\n🎯 优先目标 ({len(targets)}只):")
        for t in targets:
            print(f"   {t['symbol']}: 相对超额 {t['relative_excess']:+.2f}%")
    
    if candidates:
        print(f"\n👀 候选标的 ({len(candidates)}只):")
        for c in candidates:
            print(f"   {c['symbol']}: 相对超额 {c['relative_excess']:+.2f}%")

print("=" * 70)
