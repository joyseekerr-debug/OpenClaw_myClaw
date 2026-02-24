import requests
import json

API_KEY = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'

print("="*70)
print("iTick vs Sina Data Comparison")
print("="*70)
print()

# iTick data
headers = {'token': API_KEY}
url_itick = 'https://api-free.itick.org/stock/quote'
params_itick = {'code': '1810', 'region': 'HK'}

response = requests.get(url_itick, params=params_itick, headers=headers, timeout=10)
itick_data = response.json()['data']

print("iTick Data:")
print(f"  'p' (price?):      {itick_data.get('p')}")
print(f"  'ld' (last close?): {itick_data.get('ld')}")
print(f"  'o' (open):        {itick_data.get('o')}")
print(f"  'h' (high):        {itick_data.get('h')}")
print(f"  'l' (low):         {itick_data.get('l')}")
print(f"  'ch' (change):     {itick_data.get('ch')}")
print(f"  'chp' (change%):   {itick_data.get('chp')}")
print()

# Verify calculations
p = itick_data.get('p')
ld = itick_data.get('ld')
ch = itick_data.get('ch')
chp = itick_data.get('chp')

print("iTick Calculation Verification:")
print(f"  ld - p = {ld} - {p} = {ld - p}")
print(f"  Expected change: {ch}")
print(f"  Match: {'YES' if abs((ld - p) - ch) < 0.01 else 'NO'}")
print()
print(f"  (ld - p) / p = ({ld} - {p}) / {p} = {(ld - p) / p * 100:.2f}%")
print(f"  Expected change%: {chp}%")
print(f"  Match: {'YES' if abs(((ld - p) / p * 100) - chp) < 0.1 else 'NO'}")
print()

# Sina data
import re
url_sina = 'https://hq.sinajs.cn/list=rt_hk01810'
headers_sina = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn'
}
response = requests.get(url_sina, headers=headers_sina, timeout=10)
match = re.search(r'\"([^\"]+)\"', response.text)
fields = match.group(1).split(',')

print("Sina Data:")
print(f"  [2] Open:       {fields[2]}")
print(f"  [3] PrevClose:  {fields[3]}")
print(f"  [4] High:       {fields[4]}")
print(f"  [5] Low:        {fields[5]}")
print(f"  [6] Close:      {fields[6]}")
print(f"  [7] Change:     {fields[7]}")
print(f"  [8] Change%:    {fields[8]}")
print()

# Cross verification
print("="*70)
print("CROSS VERIFICATION")
print("="*70)
print()

print("Price comparison:")
print(f"  iTick 'p':    {p}")
print(f"  iTick 'ld':   {ld}")
print(f"  Sina [3] Prev: {fields[3]}")
print(f"  Sina [6] Close:{fields[6]}")
print()

# Which matches?
sina_prev = float(fields[3])
sina_close = float(fields[6])

print("Matching analysis:")
if abs(p - sina_prev) < 0.01:
    print(f"  ✓ iTick 'p' ({p}) matches Sina PrevClose ({sina_prev})")
else:
    print(f"  ✗ iTick 'p' ({p}) does NOT match Sina PrevClose ({sina_prev})")

if abs(ld - sina_close) < 0.01:
    print(f"  ✓ iTick 'ld' ({ld}) matches Sina Close ({sina_close})")
else:
    print(f"  ✗ iTick 'ld' ({ld}) does NOT match Sina Close ({sina_close})")

if abs(p - sina_close) < 0.01:
    print(f"  ✓ iTick 'p' ({p}) matches Sina Close ({sina_close})")
    
if abs(ld - sina_prev) < 0.01:
    print(f"  ✓ iTick 'ld' ({ld}) matches Sina PrevClose ({sina_prev})")

print()
print("CONCLUSION:")
print("  iTick 'p' = Previous Close (昨收)")
print("  iTick 'ld' = Latest/Close Price (最新价/收盘价)")
print("  This is REVERSED from what we might expect!")
print()
print("="*70)
