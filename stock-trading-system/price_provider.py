"""
股票价格获取模块 - 支持实时数据
数据源优先级:
1. 新浪财经API (当前使用)
2. AKShare (备用)
3. Yahoo Finance (备用)
4. 本地模拟 (仅测试)
"""

import random
import time
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
    
    def get_sina_price(self) -> Optional[Dict]:
        """
        从新浪财经获取实时股价
        来源: https://hq.sinajs.cn/
        """
        try:
            url = f'https://hq.sinajs.cn/list={self.sina_code}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.text
                
                # Parse Sina HK format
                match = re.search(r'\"([^\"]+)\"', data)
                if match:
                    fields = match.group(1).split(',')
                    
                    if len(fields) >= 10:
                        # Sina HK stock data format (verified with screenshot):
                        # [0] English name
                        # [1] Chinese name
                        # [2] Open price
                        # [3] Previous close (昨收)
                        # [4] High? - need to verify
                        # [5] Low price
                        # [6] Close price / Latest (收盘价/最新价)
                        # [7] Change amount (涨跌额)
                        # [8] Change percent (涨跌幅%)
                        # [9] Bid price
                        # [10] Ask price
                        
                        return {
                            'source': 'sina_realtime',
                            'symbol': self.symbol,
                            'name': fields[0],
                            'price': float(fields[6]),      # Close/Latest price
                            'open': float(fields[2]),       # Open
                            'high': float(fields[4]),       # High
                            'low': float(fields[5]),        # Low
                            'prev_close': float(fields[3]), # Previous close
                            'volume': int(fields[12]) if len(fields) > 12 else 0,
                            'change': float(fields[7]),     # Change amount
                            'change_pct': float(fields[8]), # Change percent
                            'bid': float(fields[9]) if len(fields) > 9 else 0,
                            'ask': float(fields[10]) if len(fields) > 10 else 0,
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
        """
        获取模拟股价（仅用于测试和调试！）
        
        WARNING: SIMULATED DATA - FOR TESTING ONLY
        DO NOT USE FOR TRADING DECISIONS
        """
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
    
    def get_price(self, use_network: bool = True) -> Dict:
        """获取股价（自动选择最佳方案）"""
        if use_network:
            # 尝试顺序: Sina -> AKShare -> Yahoo
            for method_name, method in [
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
            
            print("All network sources failed, using simulated data")
        else:
            print("Network disabled, using simulated data (FOR TESTING ONLY)")
        
        return self.get_simulated_price()


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
    price = provider.get_price(use_network=True)
    
    print(f"\nSymbol: {price['symbol']}")
    print(f"Source: {price['source']}")
    print(f"Price: HK$ {price['price']:.3f}")
    
    if price['source'] == 'simulated':
        print(f"\n⚠️  WARNING: {price.get('warning', 'SIMULATED DATA')}")
    else:
        print(f"Open: HK$ {price['open']:.3f}")
        print(f"High: HK$ {price['high']:.3f}")
        print(f"Low: HK$ {price['low']:.3f}")
        print(f"Change: {price.get('change_pct', 0):+.2f}%")
        if 'market_time' in price:
            print(f"Market Time: {price['market_time']}")
    
    print(f"\nTimestamp: {price['timestamp']}")
    print("="*60)
