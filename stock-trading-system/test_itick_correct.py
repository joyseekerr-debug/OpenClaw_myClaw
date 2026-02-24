"""
iTick API 使用正确的官方地址测试
API: https://api-free.itick.org/stock
"""

import requests
import json
from datetime import datetime

# 正确的API配置
API_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
BASE_URL = 'https://api-free.itick.org/stock'

print("="*70)
print("iTick API Test - Correct Endpoint")
print("="*70)
print("Time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("URL:", BASE_URL)
print()

# 测试获取实时行情
try:
    # iTick股票实时行情API
    # 港股代码格式: 1810.HK
    endpoint = '/quote'
    url = BASE_URL + endpoint
    
    params = {
        'code': '1810.HK',
        'region': 'HK'
    }
    
    headers = {
        'Authorization': 'Bearer ' + API_KEY,
        'Content-Type': 'application/json'
    }
    
    print("Request:")
    print("  URL:", url)
    print("  Params:", params)
    print()
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    print("Response:")
    print("  Status:", response.status_code)
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print()
        print("Raw response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        # 分析字段结构
        print("-"*70)
        print("Field Analysis:")
        print("-"*70)
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float, str)):
                    print(f"  {key}: {value}")
                elif isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        if isinstance(v, (int, float, str)):
                            print(f"    {k}: {v}")
                        else:
                            print(f"    {k}: {type(v).__name__}")
                else:
                    print(f"  {key}: {type(value).__name__}")
        
        print()
        print("="*70)
        print("VERIFICATION - Compare with screenshot:")
        print("="*70)
        print("Expected from screenshot:")
        print("  Latest: 35.740")
        print("  Open: 36.080")
        print("  High: 36.480")
        print("  Low: 35.440")
        print("  Change: -0.820")
        print("  Change%: -2.24%")
        
    else:
        print("❌ Request failed")
        print("Status:", response.status_code)
        print("Response:", response.text[:500])
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
