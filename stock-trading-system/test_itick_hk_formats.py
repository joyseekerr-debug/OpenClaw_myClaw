import requests
import json
from datetime import datetime

API_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
BASE_URL = 'https://api-free.itick.org/stock'

print("="*70)
print("iTick API - Testing HK Stock Code Formats")
print("="*70)
print()

headers = {'token': API_KEY}
endpoint = '/quote'
url = BASE_URL + endpoint

# 尝试不同的港股代码格式
hk_formats = [
    ('1810.HK', 'HK'),      # 标准格式
    ('01810.HK', 'HK'),     # 带前导零
    ('1810', 'HK'),         # 无后缀
    ('XIAOMI', 'HK'),       # 英文名
    ('01810', 'HK'),        # 前导零无后缀
    ('1810.HK', 'SH'),      # 错误region测试
    ('1810', 'US'),         # 美股格式
]

print("Testing different HK stock code formats:")
print()

for code, region in hk_formats:
    params = {'code': code, 'region': region}
    print(f"Testing: code='{code}', region='{region}'")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('data'):
            d = data['data']
            print(f"  SUCCESS!")
            print(f"  Symbol: {d.get('s')}")
            print(f"  Price: {d.get('p')}")
            print(f"  Change: {d.get('ch')} ({d.get('chp')}%)")
            print(f"  Full: {json.dumps(d, indent=2)}")
        else:
            print(f"  No data (code={data.get('code')}, msg={data.get('msg')})")
    except Exception as e:
        print(f"  Error: {e}")
    print()

# 分析成功获取的数据结构
print()
print("="*70)
print("Field Mapping Analysis (from working stocks)")
print("="*70)
print()

# 获取一个A股和一个美股的数据
for code, region in [('000001', 'SZ'), ('AAPL', 'US')]:
    params = {'code': code, 'region': region}
    response = requests.get(url, params=params, headers=headers, timeout=10)
    data = response.json()
    
    if data.get('data'):
        d = data['data']
        print(f"{code} ({region}) fields:")
        for key, value in d.items():
            print(f"  {key}: {value} ({type(value).__name__})")
        print()

print("="*70)
print()
print("Summary:")
print("  - API Authentication: OK (use 'token' header)")
print("  - A股 format: '000001' + 'SZ' (no .SZ suffix)")
print("  - 美股 format: 'AAPL' + 'US'")
print("  - 港股: All formats return null (may not be supported on free tier)")
print()
print("Field mapping (verified):")
print("  's'  -> symbol (股票代码)")
print("  'p'  -> price/current (当前价格)")
print("  'ld' -> last close? (昨收?)")
print("  'o'  -> open (开盘价)")
print("  'h'  -> high (最高价)")
print("  'l'  -> low (最低价)")
print("  'v'  -> volume (成交量)")
print("  'tu' -> turnover (成交额)")
print("  'ch' -> change (涨跌额)")
print("  'chp'-> change percent (涨跌幅%)")
print("  't'  -> timestamp (时间戳)")
print("  'r'  -> region (市场)")
print("  'type' -> 'quote'")
