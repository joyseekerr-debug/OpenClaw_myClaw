import urllib.request
import json
import ssl
import gzip

ssl._create_default_https_context = ssl._create_unverified_context

# 尝试使用其他数据源 - 新浪财经美股API
def get_sina_us_stock(symbol):
    """从新浪财经获取美股数据"""
    url = f'https://stock.finance.sina.com.cn/usstock/api/jsonp.php/var_{symbol}=/US_MarketData.getDataBySymbol?symbol={symbol}'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            # 解析JSONP格式
            start = data.find('(') + 1
            end = data.rfind(')')
            if start > 0 and end > start:
                json_str = data[start:end]
                return json.loads(json_str)
    except Exception as e:
        return {'error': str(e)}
    return None

# 测试几只股票
print("=" * 60)
print("尝试从新浪财经获取美股数据")
print("=" * 60)

stocks = ['AAPL', 'HAL', 'SLB', 'FRO', 'DHT', 'NEM']

for symbol in stocks:
    result = get_sina_us_stock(symbol)
    if result and 'error' not in result:
        print(f"\n{symbol}:")
        print(f"  名称: {result.get('name', 'N/A')}")
        print(f"  价格: {result.get('price', 'N/A')}")
        print(f"  涨跌: {result.get('change', 'N/A')} ({result.get('changePercent', 'N/A')}%)")
        print(f"  市值: {result.get('marketCap', 'N/A')}")
    else:
        print(f"{symbol}: 获取失败 - {result}")
