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

print('Checking which field is the CLOSE price...')
print()

# Get values
prev_close = float(fields[4])  # 昨日收盘
change = float(fields[7])      # 涨跌额
change_pct = float(fields[8])  # 涨跌幅%

# Calculate what close should be
expected_close = prev_close + change
expected_from_pct = prev_close * (1 + change_pct/100)

print('Previous close (field 4): %.3f' % prev_close)
print('Change amount (field 7): %.3f' % change)
print('Change percent (field 8): %.3f%%' % change_pct)
print()
print('Calculated close from change: %.3f' % expected_close)
print('Calculated close from pct:    %.3f' % expected_from_pct)
print()

# Check all price fields
prices = {
    'field [2] (open)': float(fields[2]),
    'field [3]': float(fields[3]),
    'field [5]': float(fields[5]),
    'field [6]': float(fields[6]),
    'field [9]': float(fields[9]),
    'field [10]': float(fields[10]),
}

print('All price fields:')
for name, value in prices.items():
    print('  %s: %.3f' % (name, value))

print()
print('Matching with expected close (%.3f):' % expected_close)
for name, value in prices.items():
    diff = abs(value - expected_close)
    match_str = 'MATCH!' if diff < 0.01 else 'no match'
    print('  %s: %.3f (diff=%.3f) - %s' % (name, value, diff, match_str))
