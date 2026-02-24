import requests
import re

url = 'https://hq.sinajs.cn/list=rt_hk01810'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn'
}

response = requests.get(url, headers=headers, timeout=15)
match = re.search(r'\"([^\"]+)\"', response.text)
fields = match.group(1).split(',')

print('Sina Finance HK Stock Data Format Analysis')
print('='*60)
print()

# Print all fields
for i, v in enumerate(fields[:20]):
    print('[%2d]: %s' % (i, v))

print()
print('Analysis:')
print('-'*60)

# Based on Sina Finance HK format:
# [0] English name
# [1] Chinese name  
# [2] Open price
# [3] Last trade price / Current price
# [4] Previous close
# [5] High
# [6] Low
# [7] Change amount
# [8] Change percent
# [9] Bid
# [10] Ask

open_p = float(fields[2])
current = float(fields[3])
prev_close = float(fields[4])
high = float(fields[5])
low = float(fields[6])
change = float(fields[7])
change_pct = float(fields[8])

print('Open price [2]:     %.3f' % open_p)
print('Current [3]:        %.3f' % current)
print('Previous close [4]: %.3f' % prev_close)
print('High [5]:           %.3f' % high)
print('Low [6]:            %.3f' % low)
print('Change [7]:         %.3f' % change)
print('Change%% [8]:        %.3f%%' % change_pct)
print()

# Verify calculations
print('Verification:')
calc_change = current - prev_close
calc_change_pct = (calc_change / prev_close) * 100
print('  Current - Prev = %.3f (data shows %.3f)' % (calc_change, change))
print('  Calc change%% = %.3f%% (data shows %.3f%%)' % (calc_change_pct, change_pct))
print()

# Check which is the actual close
print('Note: If market is closed, Current price [3] should equal Close price')
print('      If data shows different values, check field [6] which is %.3f' % low)
print()
print('Correction: [6] appears to be LOW price, not close')
print('           The CLOSE price is likely [3] = %.3f' % current)
