import urllib.request
import json
import ssl

# 创建SSL上下文
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("=" * 70)
print("尝试直接访问Yahoo Finance API")
print("=" * 70)

# 尝试获取IEZ数据
symbols = ['IEZ', 'AAPL', 'GDX']

for symbol in symbols:
    print(f"\n尝试获取 {symbol}...")
    
    # Yahoo Finance chart API
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo'
    
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
            }
        )
        
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            result = data.get('chart', {}).get('result', [{}])[0]
            meta = result.get('meta', {})
            timestamps = result.get('timestamp', [])
            prices = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
            
            if len(prices) >= 2:
                current = prices[-1]
                start = prices[0]
                return_3m = (current - start) / start * 100
                
                print(f"  ✅ 成功!")
                print(f"     当前价格: ${current:.2f}")
                print(f"     3月前价格: ${start:.2f}")
                print(f"     3月涨幅: {return_3m:.2f}%")
                print(f"     数据点数: {len(prices)}")
            else:
                print(f"  ⚠️ 数据不完整")
                
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

print("\n" + "=" * 70)
print("尝试完成")
print("=" * 70)
