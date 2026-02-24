import requests
from datetime import datetime

print('='*60)
print('实时股价查询 - 小米集团 (1810.HK)')
print('='*60)
print('Time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print()

# 新浪财经API
try:
    url = 'https://hq.sinajs.cn/list=rt_hk01810'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn'
    }
    
    print('[Sina Finance] Fetching...')
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code == 200:
        data = response.text
        print('Raw data:', data[:200])
        print()
        
        # Parse data
        if 'var hq_str_rt_hk01810=' in data:
            import re
            match = re.search(r'\"([^\"]+)\"', data)
            if match:
                stock_data = match.group(1)
                fields = stock_data.split(',')
                
                if len(fields) >= 6:
                    print('Stock: 1810.HK (Xiaomi Corp)')
                    print('Name:', fields[0])
                    print('Latest: HK$' + fields[3])
                    print('Open: HK$' + fields[2])
                    print('Prev Close: HK$' + fields[4])
                    print('High: HK$' + fields[5])
                    print('Low: HK$' + fields[6])
                    print()
                    
                    # Calculate change
                    try:
                        current = float(fields[3])
                        prev = float(fields[4])
                        change = current - prev
                        change_pct = (change / prev) * 100
                        print('Change: HK$%+.2f' % change)
                        print('Change %%: %+.2f%%' % change_pct)
                        print()
                        print('='*60)
                        print('SUCCESS: Real-time price fetched!')
                    except:
                        print('Calculate error')
                else:
                    print('Data fields insufficient')
            else:
                print('Parse error')
        else:
            print('Stock data not found in response')
    else:
        print('HTTP Error:', response.status_code)
        
except Exception as e:
    print('Error:', str(e))
    print('Type:', type(e).__name__)
