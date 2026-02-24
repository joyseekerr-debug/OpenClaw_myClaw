import yfinance as yf
from datetime import datetime

print('='*60)
print('Xiaomi Stock Price (1810.HK)')
print('='*60)
print()

# Get stock data
ticker = yf.Ticker('1810.HK')

# Get real-time data
hist = ticker.history(period='1d', interval='1m')

if not hist.empty:
    latest = hist.iloc[-1]
    info = ticker.info
    
    print('Stock: 1810.HK')
    print('Name: Xiaomi Corporation')
    print('Time:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    print('-'*60)
    print('Real-time Quote:')
    print('-'*60)
    print('Latest Price: HK$%.2f' % latest['Close'])
    print('Open: HK$%.2f' % latest['Open'])
    print('High: HK$%.2f' % latest['High'])
    print('Low: HK$%.2f' % latest['Low'])
    print('Volume: %s' % "{:,}".format(int(latest['Volume'])))
    print()
    
    # Calculate change
    prev_close = info.get('previousClose', 0)
    if prev_close > 0:
        change = latest['Close'] - prev_close
        change_pct = (change / prev_close) * 100
        print('Prev Close: HK$%.2f' % prev_close)
        print('Change: HK$%+.2f' % change)
        print('Change %%: %+.2f%%' % change_pct)
    print()
    print('='*60)
else:
    print('Unable to fetch data')
