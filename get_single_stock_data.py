import urllib.request
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# 获取单个美股历史数据
def get_us_stock_hist(symbol, period='3mo'):
    """从东方财富获取美股历史数据"""
    # 转换为东方财富格式 (美股代码前加105.)
    secid = f"105.{symbol}"
    
    # 计算时间戳 (3个月前到现在)
    import time
    end_time = int(time.time())
    start_time = end_time - 90 * 24 * 60 * 60  # 90天前
    
    url = f'https://push2.eastmoney.com/api/qt/stock/kline/get?ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100,f101,f102,f103,f104,f105,f106,f107,f108,f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197,f198,f199,f200&secid={secid}&klt=101&fqt=1&beg=0&end=20500101&smplmt=460&lmt=1000000'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        return {'error': str(e)}

# 测试获取几只股票
stocks = ['AAPL', 'HAL', 'SLB', 'NOV', 'NBR']

print("=" * 60)
print("美股历史数据获取")
print("=" * 60)

for symbol in stocks:
    print(f"\n正在获取 {symbol}...")
    result = get_us_stock_hist(symbol)
    
    if 'error' in result:
        print(f"  错误: {result['error']}")
        continue
    
    data = result.get('data', {})
    if not data:
        print(f"  无数据")
        continue
    
    klines = data.get('klines', [])
    if not klines:
        print(f"  无K线数据")
        continue
    
    # 解析K线数据 (格式: 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率)
    latest = klines[-1].split(',')
    earliest = klines[0].split(',')
    
    current_price = float(latest[2])  # 收盘价
    start_price = float(earliest[2])
    return_3m = (current_price - start_price) / start_price * 100
    
    print(f"  当前价格: ${current_price:.2f}")
    print(f"  3个月前价格: ${start_price:.2f}")
    print(f"  3个月涨幅: {return_3m:.2f}%")
    print(f"  数据点数: {len(klines)}")
