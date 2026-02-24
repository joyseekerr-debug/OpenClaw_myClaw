import requests
import re
from datetime import datetime

url = 'https://hq.sinajs.cn/list=rt_hk01810'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn'
}

print('='*60)
print('Stock Data Verification')
print('='*60)
print('Current time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print()

response = requests.get(url, headers=headers, timeout=15)
print('Raw response:')
print(response.text)
print()

# Parse
match = re.search(r'\"([^\"]+)\"', response.text)
if match:
    fields = match.group(1).split(',')
    print('-'*60)
    print('Parsed fields:')
    print('  Name:', fields[0])
    print('  Open price:', fields[2])
    print('  Current/Latest:', fields[3])
    print('  Previous Close:', fields[4])
    print('  High:', fields[5])
    print('  Low:', fields[6])
    print('  Change amount:', fields[8])
    print('  Change percent:', fields[9], '%')
    print('  Volume:', fields[12] if len(fields) > 12 else 'N/A')
    print('  Date in data:', fields[17] if len(fields) > 17 else 'N/A')
    print('  Time in data:', fields[18] if len(fields) > 18 else 'N/A')
    print('-'*60)
    print()
    
    # Market status check
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    current_time = current_hour * 100 + current_minute
    
    # HK market: 0930-1200, 1300-1600
    market_open = (930 <= current_time <= 1200) or (1300 <= current_time <= 1600)
    
    print('Market Status Check:')
    print('  Current time:', '%02d:%02d' % (current_hour, current_minute))
    print('  HK Market hours: 09:30-12:00, 13:00-16:00')
    
    if market_open:
        print('  Status: MARKET OPEN')
    else:
        print('  Status: MARKET CLOSED')
        print('  Note: Data shows last closing price')
    
    print()
    print('Data freshness:')
    if len(fields) > 18:
        data_time = fields[18]
        print('  Timestamp in data:', data_time)
        print('  Current system time:', datetime.now().strftime('%H:%M:%S'))
        
        # Check if same day
        if len(fields) > 17:
            data_date = fields[17]
            today = datetime.now().strftime('%Y/%m/%d')
            print('  Date in data:', data_date)
            print('  Today:', today)
            if data_date == today:
                print('  Date match: YES (today)')
            else:
                print('  Date match: NO - Data is from', data_date)

print('='*60)
