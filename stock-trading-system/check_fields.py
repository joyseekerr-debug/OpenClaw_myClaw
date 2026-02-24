import requests
import re

url = 'https://hq.sinajs.cn/list=rt_hk01810'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn'
}

response = requests.get(url, headers=headers, timeout=15)

match = re.search(r'\"([^\"]+)\"', response.text)
if match:
    fields = match.group(1).split(',')
    
    print('Field index - value mapping:')
    for i, v in enumerate(fields):
        print('  [%d]: %s' % (i, v))
    
    print()
    print('Verification:')
    close = 35.740
    prev = 36.480
    change_pct = (close - prev) / prev * 100
    print('  Close: %.3f' % close)
    print('  Prev: %.3f' % prev)
    print('  Change%%: %.3f%%' % change_pct)
    print('  Data shows: -2.243%')
