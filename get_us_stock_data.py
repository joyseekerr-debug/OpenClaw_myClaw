import urllib.request
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# 美股代码列表 (能源设备服务板块)
stocks = ['HAL', 'SLB', 'NOV', 'NBR', 'RES', 'OII', 'TDW', 'FTI', 'NE', 'RIG', 'VAL', 'HP', 'PTEN']

print("=" * 60)
print("美股能源设备服务板块数据获取")
print("=" * 60)

results = []

for symbol in stocks:
    url = f'https://push2.eastmoney.com/api/qt/stock/get?ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=2&invt=2&fields=f43,f57,f58,f60,f116,f117,f140,f141,f162,f163,f164,f165,f170,f171,f177,f183,f184,f185,f186,f187,f188,f189,f190&secid=105.{symbol}'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('data'):
                d = data['data']
                result = {
                    'symbol': symbol,
                    'name': d.get('f58', 'N/A'),
                    'price': d.get('f43', 0) / 100 if d.get('f43') else 0,
                    'change_pct': d.get('f170', 0) / 100 if d.get('f170') else 0,
                    'market_cap': d.get('f116', 0) / 100000000 if d.get('f116') else 0,  # 亿美元
                    'pe': d.get('f162', 0) / 100 if d.get('f162') else 0,
                    'pb': d.get('f163', 0) / 100 if d.get('f163') else 0,
                    'volume': d.get('f47', 0) / 100 if d.get('f47') else 0,
                }
                results.append(result)
                print(f"{symbol}: {result['name'][:20]:<20} ${result['price']:.2f}  市值:{result['market_cap']:.1f}亿 PE:{result['pe']:.1f}")
            else:
                print(f"{symbol}: 无数据")
    except Exception as e:
        print(f"{symbol}: 错误 - {e}")

# 保存结果
print("\n" + "=" * 60)
print(f"成功获取 {len(results)} 只股票数据")
print("=" * 60)

# 输出CSV格式
print("\nCSV格式输出:")
print("Symbol,Name,Price,Change_Pct,Market_Cap_USD,PE_TTM")
for r in results:
    print(f"{r['symbol']},{r['name']},{r['price']:.2f},{r['change_pct']:.2f},{r['market_cap']:.2f},{r['pe']:.2f}")
