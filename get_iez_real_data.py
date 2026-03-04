import urllib.request
import json
import ssl
import pandas as pd

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_stock_data(symbol, period='3mo'):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={period}'
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))
            result = data.get('chart', {}).get('result', [{}])[0]
            prices = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
            if len(prices) >= 2:
                current = prices[-1]
                start = prices[0]
                return_3m = (current - start) / start * 100
                return {'symbol': symbol, 'current_price': current, 'start_price': start, 'return_3m': return_3m}
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}
    return {'symbol': symbol, 'error': 'No data'}

print("=" * 70)
print("获取 IEZ 和能源股数据")
print("=" * 70)

# 先获取IEZ
print("\n获取 IEZ ETF...")
iez_result = get_stock_data('IEZ')
if 'error' not in iez_result:
    print(f"IEZ: 当前 ${iez_result['current_price']:.2f}, 3月涨幅 {iez_result['return_3m']:+.2f}%")
    iez_return = iez_result['return_3m']
    
    # 获取能源股
    energy_stocks = ['HAL', 'SLB', 'NOV', 'NBR', 'RES', 'OII', 'TDW', 'FTI', 'NE', 'HP', 'PTEN']
    
    print(f"\n【IEZ 成分股 (基准: {iez_return:+.2f}%)】")
    print(f"{'代码':8} {'当前价':10} {'3月涨幅':10} {'相对超额':10} {'状态'}")
    print("-" * 70)
    
    results = []
    for symbol in energy_stocks:
        result = get_stock_data(symbol)
        if 'error' not in result:
            relative_excess = result['return_3m'] - iez_return
            
            if relative_excess < -10:
                status = "🎯 TARGET"
            elif relative_excess < -5:
                status = "👀 CANDIDATE"
            else:
                status = "⏸️ WATCH"
            
            results.append({
                'symbol': symbol,
                'etf': 'IEZ',
                'price': result['current_price'],
                'return_3m': result['return_3m'],
                'etf_return': iez_return,
                'relative_excess': relative_excess,
                'status': status
            })
            
            print(f"{symbol:8} ${result['current_price']:8.2f} {result['return_3m']:+8.2f}% {relative_excess:+9.2f}% {status}")
        else:
            print(f"{symbol:8} 错误: {result['error'][:40]}")
    
    # 保存
    if results:
        df = pd.DataFrame(results)
        df.to_csv('IEZ_Stocks_Real_Data.csv', index=False)
        print(f"\n✅ 已保存 {len(results)} 只股票到 IEZ_Stocks_Real_Data.csv")
        
        targets = [r for r in results if 'TARGET' in r['status']]
        candidates = [r for r in results if 'CANDIDATE' in r['status']]
        
        if targets:
            print(f"\n🎯 优先目标 ({len(targets)}只):", ', '.join([t['symbol'] for t in targets]))
        if candidates:
            print(f"👀 候选标的 ({len(candidates)}只):", ', '.join([c['symbol'] for c in candidates]))
else:
    print(f"IEZ 获取失败: {iez_result.get('error', 'Unknown')}")
