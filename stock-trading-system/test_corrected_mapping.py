import requests
import re

url = 'https://hq.sinajs.cn/list=rt_hk01810'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn'
}

print('Testing corrected field mapping...')
print()

try:
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code == 200:
        data = response.text
        match = re.search(r'\"([^\"]+)\"', data)
        
        if match:
            fields = match.group(1).split(',')
            
            print('Corrected field mapping:')
            print('  [0] Name (EN):      %s' % fields[0])
            print('  [1] Name (CN):      %s' % fields[1])
            print('  [2] Open:           %s' % fields[2])
            print('  [3] Prev Close:     %s' % fields[3])
            print('  [4] High:           %s' % fields[4])
            print('  [5] Low:            %s' % fields[5])
            print('  [6] Close/Latest:   %s' % fields[6])
            print('  [7] Change:         %s' % fields[7])
            print('  [8] Change%%:        %s' % fields[8])
            print('  [9] Bid:            %s' % fields[9])
            print('  [10] Ask:           %s' % fields[10])
            print('  [12] Volume:        %s' % (fields[12] if len(fields) > 12 else 'N/A'))
            print()
            
            # Verify calculation
            close = float(fields[6])
            prev = float(fields[3])
            change = float(fields[7])
            change_pct = float(fields[8])
            
            print('Verification:')
            print('  Close price:      %.3f' % close)
            print('  Previous close:   %.3f' % prev)
            print('  Change:           %.3f' % change)
            print('  Calculated:       %.3f (%.3f - %.3f)' % (close - prev, close, prev))
            print('  Match:            %s' % ('YES' if abs((close - prev) - change) < 0.01 else 'NO'))
            print()
            
            print('Expected (from screenshot):')
            print('  Close: 35.740')
            print('  Open:  36.080')
            print('  High:  36.480')
            print('  Low:   35.440')
            print('  Prev:  36.560')
            print('  Change: -0.820')
            print()
            
            # Check if values match screenshot
            matches = []
            if abs(close - 35.740) < 0.01:
                matches.append('Close price matches!')
            if abs(float(fields[2]) - 36.080) < 0.01:
                matches.append('Open price matches!')
            if abs(float(fields[4]) - 36.480) < 0.01:
                matches.append('High price matches!')
            if abs(float(fields[5]) - 35.440) < 0.01:
                matches.append('Low price matches!')
            if abs(prev - 36.560) < 0.01:
                matches.append('Prev close matches!')
                
            if matches:
                print('Matching fields:')
                for m in matches:
                    print('  - ' + m)
            else:
                print('Warning: Values may not match screenshot')
                
except Exception as e:
    print('Error: %s' % e)
