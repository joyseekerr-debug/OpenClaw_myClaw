"""
股票价格获取模块 - 支持实时数据
数据源优先级:
1. iTick API (已验证的真实数据)
2. 新浪财经API (备用)
3. AKShare (备用)
4. Yahoo Finance (备用)
"""

import random
import re
import requests
from datetime import datetime
from typing import Dict, Optional
import json
import os


class StockPriceProvider:
    """股票价格提供者"""
    
    def __init__(self, symbol: str = '1810.HK'):
        self.symbol = symbol
        self.sina_code = 'rt_hk' + symbol.replace('.HK', '')
        self.base_price = 15.0
        self.current_price = self.base_price
        self.price_history = []
        
        # iTick配置
        self.itick_api_key = '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1'
        self.itick_base_url = 'https://api-free.itick.org/stock'
        
        # 加载历史数据
        self._load_history()
    
    def _load_history(self):
        """加载历史价格数据"""
        history_file = f'data/{self.symbol.replace(".", "_")}_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                self.price_history = json.load(f)
                if self.price_history:
                    self.current_price = self.price_history[-1]['price']
    
    def _save_history(self):
        """保存价格历史"""
        os.makedirs('data', exist_ok=True)
        history_file = f'data/{self.symbol.replace(".", "_")}_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.price_history[-1000:], f)
    
    def _format_symbol_itick(self, symbol: str) -> tuple:
        """转换股票代码格式为iTick格式"""
        if '.HK' in symbol:
            code = symbol.replace('.HK', '')
            region = 'HK'
        elif '.SZ' in symbol:
            code = symbol.replace('.SZ', '')
            region = 'SZ'
        elif '.SH' in symbol:
            code = symbol.replace('.SH', '')
            region = 'SH'
        else:
            code = symbol
            region = 'US'
        return code, region
    
    def get_itick_price(self) -> Optional[Dict]:
        """从iTick获取实时股价 - 已验证的真实数据源"""
        try:
            code, region = self._format_symbol_itick(self.symbol)
            
            headers = {'token': self.itick_api_key}
            url = self.itick_base_url + '/quote'
            params = {'code': code, 'region': region}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0 and result.get('data'):
                    data = result['data']
                    
                    return {
                        'source': 'itick_real',
                        'symbol': self.symbol,
                        'name': data.get('s'),
                        'price': float(data.get('ld', 0)),
                        'previous_close': float(data.get('p', 0)),
                        'open': float(data.get('o', 0)),
                        'high': float(data.get('h', 0)),
                        'low': float(data.get('l', 0)),
                        'volume': int(data.get('v', 0)),
                        'turnover': float(data.get('tu', 0)),
                        'change': float(data.get('ch', 0)),
                        'change_pct': float(data.get('chp', 0)),
                        'timestamp': datetime.now().isoformat(),
                        'region': data.get('r')
                    }
        except Exception as e:
            print(f"iTick API error: {e}")
        
        return None
    
    def get_sina_price(self) -> Optional[Dict]:
        """从新浪财经获取实时股价"""
        try:
            url = f'https://hq.sinajs.cn/list={self.sina_code}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.text
                
                match = re.search(r'\"([^\"]+)\"', data)
                if match:
                    fields = match.group(1).split(',')
                    
                    if len(fields) >= 10:
                        return {
                            'source': 'sina_realtime',
                            'symbol': self.symbol,
                            'name': fields[0],
                            'price': float(fields[6]),
                            'open': float(fields[2]),
                            'high': float(fields[4]),
                            'low': float(fields[5]),
                            'prev_close': float(fields[3]),
                            'volume': int(fields[12]) if len(fields) > 12 else 0,
                            'change': float(fields[7]),
                            'change_pct': float(fields[8]),
                            'timestamp': datetime.now().isoformat(),
                            'market_time': fields[18] if len(fields) > 18 else ''
                        }
        except Exception as e:
            print(f"Sina API error: {e}")
        
        return None
    
    def get_akshare_price(self) -> Optional[Dict]:
        """从AKShare获取股价"""
        try:
            import akshare as ak
            hk_df = ak.stock_hk_spot_em()
            xiaomi = hk_df[hk_df['代码'] == '01810']
            
            if not xiaomi.empty:
                row = xiaomi.iloc[0]
                return {
                    'source': 'akshare',
                    'symbol': self.symbol,
                    'price': float(row.get('最新价', 0)),
                    'open': float(row.get('开盘价', 0)),
                    'high': float(row.get('最高价', 0)),
                    'low': float(row.get('最低价', 0)),
                    'prev_close': float(row.get('昨收', 0)),
                    'volume': str(row.get('成交量', 'N/A')),
                    'change_pct': float(row.get('涨跌幅', 0)),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"AKShare error: {e}")
        
        return None
    
    def get_yahoo_price(self) -> Optional[Dict]:
        """从Yahoo Finance获取股价"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period='1d', interval='1m')
            
            if not hist.empty:
                latest = hist.iloc[-1]
                info = ticker.info
                prev_close = info.get('previousClose', latest['Close'])
                
                return {
                    'source': 'yahoo',
                    'symbol': self.symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'prev_close': float(prev_close),
                    'volume': int(latest['Volume']),
                    'change_pct': (latest['Close'] - prev_close) / prev_close * 100,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Yahoo error: {e}")
        
        return None
    
    def get_simulated_price(self) -> Dict:
        """获取模拟股价（仅用于测试和调试！）"""
        change = random.gauss(0, 0.005)
        self.current_price *= (1 + change)
        
        open_price = self.current_price * (1 + random.gauss(0, 0.002))
        high_price = max(self.current_price, open_price) * (1 + abs(random.gauss(0, 0.01)))
        low_price = min(self.current_price, open_price) * (1 - abs(random.gauss(0, 0.01)))
        prev_close = self.base_price
        change_pct = (self.current_price - prev_close) / prev_close * 100
        
        data = {
            'source': 'simulated',
            'warning': 'SIMULATED DATA - FOR TESTING ONLY - DO NOT USE FOR TRADING',
            'symbol': self.symbol,
            'price': round(self.current_price, 3),
            'open': round(open_price, 3),
            'high': round(high_price, 3),
            'low': round(low_price, 3),
            'prev_close': round(prev_close, 3),
            'volume': random.randint(1000000, 10000000),
            'change_pct': round(change_pct, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        self.price_history.append(data)
        if len(self.price_history) % 10 == 0:
            self._save_history()
        
        return data
    
    def get_price(self, use_network: bool = True, allow_simulated: bool = False) -> Dict:
        """获取股价（自动选择最佳方案）"""
        if use_network:
            # 尝试顺序: iTick -> Sina -> AKShare -> Yahoo
            for method_name, method in [
                ('iTick', self.get_itick_price),
                ('Sina', self.get_sina_price),
                ('AKShare', self.get_akshare_price),
                ('Yahoo', self.get_yahoo_price)
            ]:
                try:
                    result = method()
                    if result:
                        return result
                except Exception as e:
                    print(f"{method_name} failed: {e}")
                    continue
            
            if not allow_simulated:
                raise Exception(
                    "CRITICAL: All real data sources failed! "
                    "Cannot get stock price for production use. "
                    "Simulated data is strictly prohibited for trading!"
                )
            
            print("WARNING: All network sources failed, using simulated data")
        
        if allow_simulated:
            return self.get_simulated_price()
        else:
            raise Exception("Simulated data is disabled for production use")


# 全局实例
_price_provider = None

def get_price_provider(symbol: str = '1810.HK') -> StockPriceProvider:
    global _price_provider
    if _price_provider is None or _price_provider.symbol != symbol:
        _price_provider = StockPriceProvider(symbol)
    return _price_provider


if __name__ == "__main__":
    print("="*60)
    print("Stock Price Fetcher - Xiaomi (1810.HK)")
    print("="*60)
    print()
    
    provider = StockPriceProvider('1810.HK')
    
    try:
        price = provider.get_price(use_network=True, allow_simulated=False)
        
        print(f"\nSymbol: {price['symbol']}")
        print(f"Source: {price['source']}")
        print(f"Price: HK$ {price['price']:.3f}")
        print(f"Open: HK$ {price['open']:.3f}")
        print(f"High: HK$ {price['high']:.3f}")
        print(f"Low: HK$ {price['low']:.3f}")
        print(f"Change: {price.get('change_pct', 0):+.2f}%")
        print(f"\nTimestamp: {price['timestamp']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("="*60)
