"""
iTick数据源 - 已验证的真实API实现
API地址: https://api-free.itick.org/stock
认证方式: token header
港股格式: code='1810', region='HK' (无.HK后缀)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class iTickSource:
    """iTick数据源 - 真实API实现"""
    
    def __init__(self, config: dict):
        self.name = 'iTick'
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api-free.itick.org/stock')
        self.is_connected = False
    
    def connect(self) -> bool:
        """连接iTick API"""
        try:
            # 测试连接
            headers = {'token': self.api_key}
            url = self.base_url + '/quote'
            params = {'code': '1810', 'region': 'HK'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    self.is_connected = True
                    logger.info("iTick datasource connected")
                    return True
            
            logger.error(f"iTick connection failed: {response.status_code}")
            self.is_connected = False
            return False
            
        except Exception as e:
            logger.error(f"iTick connection error: {e}")
            self.is_connected = False
            return False
    
    def _format_symbol(self, symbol: str) -> tuple:
        """
        转换股票代码格式
        输入: 1810.HK
        输出: ('1810', 'HK')
        """
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
            # 美股或其他
            code = symbol
            region = 'US'
        
        return code, region
    
    def get_realtime_data(self, symbol: str) -> Optional[Dict]:
        """
        获取实时行情数据
        
        iTick字段映射 (已验证):
        - 's'   -> symbol (股票代码)
        - 'p'   -> previous_close (昨收价)
        - 'ld'  -> price/latest_close (最新价/收盘价)
        - 'o'   -> open (开盘价)
        - 'h'   -> high (最高价)
        - 'l'   -> low (最低价)
        - 'v'   -> volume (成交量)
        - 'tu'  -> turnover (成交额)
        - 'ch'  -> change (涨跌额)
        - 'chp' -> change_percent (涨跌幅%)
        - 't'   -> timestamp (时间戳)
        - 'r'   -> region (市场)
        """
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            code, region = self._format_symbol(symbol)
            
            headers = {'token': self.api_key}
            url = self.base_url + '/quote'
            params = {'code': code, 'region': region}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0 and result.get('data'):
                    data = result['data']
                    
                    return {
                        'source': 'itick',
                        'symbol': symbol,
                        'code': data.get('s'),
                        'region': data.get('r'),
                        'price': float(data.get('ld', 0)),        # 最新价/收盘价
                        'previous_close': float(data.get('p', 0)), # 昨收价
                        'open': float(data.get('o', 0)),
                        'high': float(data.get('h', 0)),
                        'low': float(data.get('l', 0)),
                        'volume': int(data.get('v', 0)),
                        'turnover': float(data.get('tu', 0)),
                        'change': float(data.get('ch', 0)),
                        'change_percent': float(data.get('chp', 0)),
                        'timestamp': data.get('t'),
                        'raw_data': data  # 保留原始数据
                    }
                else:
                    logger.warning(f"iTick returned no data for {symbol}")
                    return None
            else:
                logger.error(f"iTick API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"iTick realtime data error: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start: str, end: str,
                           interval: str = '1d') -> Optional[pd.DataFrame]:
        """获取历史K线数据"""
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            code, region = self._format_symbol(symbol)
            
            # iTick K线类型映射
            ktype_map = {
                '1m': '1',
                '5m': '5',
                '15m': '15',
                '30m': '30',
                '60m': '60',
                '1d': '101',
                '1w': '102',
                '1M': '103'
            }
            
            ktype = ktype_map.get(interval, '101')
            
            headers = {'token': self.api_key}
            url = self.base_url + '/kline'
            params = {
                'code': code,
                'region': region,
                'kType': ktype,
                'count': '100'  # 获取100条
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0 and result.get('data'):
                    klines = result['data']
                    
                    # 转换K线数据
                    data = []
                    for k in klines:
                        data.append({
                            'timestamp': datetime.fromtimestamp(k.get('t', 0) / 1000),
                            'open': float(k.get('o', 0)),
                            'high': float(k.get('h', 0)),
                            'low': float(k.get('l', 0)),
                            'close': float(k.get('c', 0)),
                            'volume': int(k.get('v', 0))
                        })
                    
                    df = pd.DataFrame(data)
                    
                    # 过滤日期范围
                    if not df.empty:
                        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
                    
                    return df
                else:
                    logger.warning(f"iTick returned no kline data for {symbol}")
                    return None
            else:
                logger.error(f"iTick kline API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"iTick historical data error: {e}")
            return None


# 测试代码
if __name__ == "__main__":
    print("="*70)
    print("iTick Data Source Test")
    print("="*70)
    print()
    
    config = {
        'api_key': '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1',
        'base_url': 'https://api-free.itick.org/stock'
    }
    
    source = iTickSource(config)
    
    # 测试连接
    print("[1] Testing connection...")
    if source.connect():
        print("   Connected successfully!")
    else:
        print("   Connection failed!")
    
    print()
    
    # 测试实时数据
    print("[2] Testing realtime data for 1810.HK...")
    data = source.get_realtime_data('1810.HK')
    
    if data:
        print(f"   Symbol: {data['symbol']}")
        print(f"   Price: {data['price']}")
        print(f"   Open: {data['open']}")
        print(f"   High: {data['high']}")
        print(f"   Low: {data['low']}")
        print(f"   Change: {data['change']} ({data['change_percent']}%)")
        print(f"   Volume: {data['volume']}")
    else:
        print("   Failed to get data!")
    
    print()
    print("="*70)
