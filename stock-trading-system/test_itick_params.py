import requests
import json
from datetime import datetime

API_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
BASE_URL = 'https://api-free.itick.org/stock'

print("="*70)
print("iTick API - Testing Parameters")
print("="*70)
print()

headers = {'token': API_KEY}

# 尝试不同的参数格式
param_variants = [
    {'code': '1810.HK', 'region': 'HK'},
    {'symbol': '1810.HK', 'region': 'HK'},
    {'code': '01810', 'market': 'HK'},
    {'symbol': '01810', 'exchange': 'HK'},
    {'stock_code': '1810.HK'},
    {'ticker': '1810.HK'},
]

endpoint = '/quote'
url = BASE_URL + endpoint

for params in param_variants:
    print(f"Testing params: {params}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            if data.get('data'):
                print(f"  ✓ Got data!")
                break
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

# 尝试其他端点
print()
print("Testing other endpoints...")
print()

endpoints = ['/tick', '/kline', '/trade', '/quote']
params = {'code': '1810.HK', 'region': 'HK'}

for ep in endpoints:
    url = BASE_URL + ep
    print(f"Endpoint: {ep}")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

print("="*70)
