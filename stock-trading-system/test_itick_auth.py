import requests
import json
from datetime import datetime

API_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
BASE_URL = 'https://api-free.itick.org/stock'

print("="*70)
print("iTick API Debug - 401 Error")
print("="*70)
print()

# 尝试不同的认证方式
auth_methods = [
    ('Bearer Token', {'Authorization': 'Bearer ' + API_KEY}),
    ('API Key Header', {'X-API-Key': API_KEY}),
    ('API Key Header 2', {'api-key': API_KEY}),
    ('Token Header', {'token': API_KEY}),
]

endpoint = '/quote'
url = BASE_URL + endpoint
params = {'code': '1810.HK', 'region': 'HK'}

print("Testing different auth methods...")
print()

for method_name, headers in auth_methods:
    print(f"Method: {method_name}")
    print(f"  Headers: {headers}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  SUCCESS!")
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:500]}")
            break
        else:
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print()

# 也尝试不用认证
print("Trying without authentication...")
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("="*70)
print()
print("Note: 401 error typically means:")
print("  - API key is invalid or expired")
print("  - Wrong authentication method")
print("  - API endpoint requires different format")
print("  - Need to check official documentation")
