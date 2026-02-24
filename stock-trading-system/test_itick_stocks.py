import requests
import json
from datetime import datetime

API_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
BASE_URL = 'https://api-free.itick.org/stock'

print("="*70)
print("iTick API - Testing Different Stocks")
print("="*70)
print()

headers = {'token': API_KEY}
endpoint = '/quote'
url = BASE_URL + endpoint

# 尝试不同的股票代码
test_stocks = [
    ('1810.HK', 'HK'),  # 小米集团
    ('00700.HK', 'HK'), # 腾讯
    ('000001.SZ', 'SZ'), # 平安银行
    ('000001', 'SZ'),   # 平安银行 (无后缀)
    ('600519', 'SH'),   # 贵州茅台
    ('AAPL', 'US'),     # 苹果
    ('TSLA', 'US'),     # 特斯拉
]

for code, region in test_stocks:
    params = {'code': code, 'region': region}
    print(f"Testing: {code} ({region})")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        print(f"  Status: {response.status_code}")
        print(f"  Code: {data.get('code')}")
        print(f"  Msg: {data.get('msg')}")
        print(f"  Data: {data.get('data')}")
        if data.get('data'):
            print(f"  ✓ GOT DATA for {code}!")
            print(f"  Full response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

# 尝试kline接口
print()
print("Testing /kline endpoint...")
print()

url_kline = BASE_URL + '/kline'
params_kline = {
    'code': '1810.HK',
    'region': 'HK',
    'kType': '1',  # 1分钟
    'count': '10'  # 10条
}

print(f"Params: {params_kline}")
try:
    response = requests.get(url_kline, params=params_kline, headers=headers, timeout=10)
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()
print("="*70)
print()
print("Summary:")
print("  - Authentication: OK (using 'token' header)")
print("  - Parameter format: code + region")
print("  - But all responses return null data")
print("  - Possible reasons:")
print("    1. Free API has data limitations")
print("    2. Stock code format issue")
print("    3. API Key permissions")
print("    4. Market not supported on free tier")
