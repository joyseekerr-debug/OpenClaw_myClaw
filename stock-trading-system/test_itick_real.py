"""
iTick API 真实环境测试和字段映射验证
"""

import requests
import json
from datetime import datetime

# API配置
API_KEY = '12c4117c795041b78b052cf5ca1e11e393cf3fa873ef490ca91298ce671d2110'
BASE_URL = 'https://api.itick.com'

print("="*70)
print("iTick API 真实环境测试")
print("="*70)
print("Time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print()

# 1. 测试连接
print("[1] Testing API connection...")
print("-"*70)

try:
    # iTick API - 获取港股实时行情
    # 参考文档: https://www.itick.com/docs
    endpoint = '/stock/quote'
    url = BASE_URL + endpoint
    
    params = {
        'code': '1810.HK',
        'region': 'HK'
    }
    
    headers = {
        'Authorization': 'Bearer ' + API_KEY,
        'Content-Type': 'application/json'
    }
    
    print("URL:", url)
    print("Params:", params)
    print("Headers:", {k: v[:20] + '...' if k == 'Authorization' else v for k, v in headers.items()})
    print()
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    print("Status:", response.status_code)
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Connection successful!")
        print()
        print("Raw response (formatted):")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        # 分析字段映射
        print("-"*70)
        print("[2] Field mapping analysis")
        print("-"*70)
        
        if isinstance(data, dict):
            print("Top-level keys:")
            for key in data.keys():
                value = data[key]
                if isinstance(value, (int, float, str)):
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {type(value).__name__}")
            
            print()
            
            # 检查是否有嵌套数据
            if 'data' in data:
                inner_data = data['data']
                print("Nested 'data' keys:")
                if isinstance(inner_data, dict):
                    for key, value in inner_data.items():
                        if isinstance(value, (int, float, str)):
                            print(f"    {key}: {value}")
                        else:
                            print(f"    {key}: {type(value).__name__}")
                elif isinstance(inner_data, list) and len(inner_data) > 0:
                    print(f"    List with {len(inner_data)} items")
                    if isinstance(inner_data[0], dict):
                        print("    First item keys:")
                        for key, value in inner_data[0].items():
                            if isinstance(value, (int, float, str)):
                                print(f"      {key}: {value}")
                            else:
                                print(f"      {key}: {type(value).__name__}")
            
            # 直接检查常见字段名
            print()
            print("Checking common field names:")
            common_fields = ['symbol', 'code', 'price', 'latest', 'close', 'open', 'high', 'low', 
                           'volume', 'change', 'changePercent', 'change_pct', 'prevClose', 'timestamp']
            
            def search_nested(obj, prefix=''):
                results = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = prefix + '.' + key if prefix else key
                        if key in common_fields or any(f in key.lower() for f in ['price', 'close', 'open', 'high', 'low', 'volume', 'change']):
                            if isinstance(value, (int, float, str)):
                                results.append((full_key, value))
                        if isinstance(value, dict):
                            results.extend(search_nested(value, full_key))
                        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                            results.extend(search_nested(value[0], full_key + '[0]'))
                return results
            
            found_fields = search_nested(data)
            for key, value in found_fields[:20]:  # 限制输出数量
                print(f"  {key}: {value}")
    else:
        print("❌ Connection failed")
        print("Response:", response.text[:500])
        
        # 尝试备用API Key
        print()
        print("[2] Trying backup API Key...")
        BACKUP_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
        headers['Authorization'] = 'Bearer ' + BACKUP_KEY
        
        response2 = requests.get(url, params=params, headers=headers, timeout=15)
        print("Backup key status:", response2.status_code)
        if response2.status_code == 200:
            print("✅ Backup key works!")
            print(json.dumps(response2.json(), indent=2)[:500])
        else:
            print("❌ Backup key also failed")
            print(response2.text[:500])

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
