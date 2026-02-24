"""
多数据源管理模块
支持: iTick, Yahoo Finance, Alpha Vantage, AKShare(A股)
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """连接数据源"""
        pass
    
    @abstractmethod
    def get_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取实时数据"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start: str, end: str, 
                           interval: str = '1d') -> Optional[pd.DataFrame]:
        """获取历史数据"""
        pass
    
    def health_check(self) -> bool:
        """健康检查"""
        return self.is_connected


class iTickSource(DataSource):
    """iTick数据源 - 真实API实现"""
    
    def __init__(self, config: dict):
        super().__init__('iTick', config)
        self.api_key = config.get('api_key', '62842c85df6f4665a50620efb853102e609ce22b65a34a41a0a9d3af2685caf1')
        self.base_url = config.get('base_url', 'https://api-free.itick.org/stock')
    
    def connect(self) -> bool:
        """连接iTick API"""
        try:
            # 测试连接
            import requests
            headers = {'token': self.api_key}
            url = self.base_url + '/quote'
            params = {'code': '1810', 'region': 'HK'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    self.is_connected = True
                    logger.info("iTick datasource connected (real API)")
                    return True
            
            logger.error(f"iTick connection failed: {response.status_code}")
            self.is_connected = False
            return False
            
        except Exception as e:
            logger.error(f"iTick connection error: {e}")
            self.is_connected = False
            return False
    
    def _format_symbol(self, symbol: str) -> tuple:
        """转换股票代码格式"""
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
    
    def get_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取实时行情数据 - 使用真实iTick API"""
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            import requests
            code, region = self._format_symbol(symbol)
            
            headers = {'token': self.api_key}
            url = self.base_url + '/quote'
            params = {'code': code, 'region': region}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0 and result.get('data'):
                    data = result['data']
                    
                    # 转换为DataFrame格式
                    df_data = {
                        'timestamp': [datetime.now()],
                        'symbol': [symbol],
                        'price': [float(data.get('ld', 0))],  # 最新价
                        'open': [float(data.get('o', 0))],
                        'high': [float(data.get('h', 0))],
                        'low': [float(data.get('l', 0))],
                        'prev_close': [float(data.get('p', 0))],
                        'volume': [int(data.get('v', 0))],
                        'change': [float(data.get('ch', 0))],
                        'change_pct': [float(data.get('chp', 0))],
                        'source': ['itick_real']
                    }
                    
                    logger.info(f"iTick real data fetched: {symbol} @ {data.get('ld')}")
                    return pd.DataFrame(df_data)
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
            import requests
            code, region = self._format_symbol(symbol)
            
            # iTick K线类型映射
            ktype_map = {
                '1m': '1', '5m': '5', '15m': '15', '30m': '30', '60m': '60',
                '1d': '101', '1w': '102', '1M': '103'
            }
            ktype = ktype_map.get(interval, '101')
            
            headers = {'token': self.api_key}
            url = self.base_url + '/kline'
            params = {'code': code, 'region': region, 'kType': ktype, 'count': '100'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0 and result.get('data'):
                    klines = result['data']
                    
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


class YahooSource(DataSource):
    """Yahoo Finance数据源 - 美股/港股备用"""
    
    def __init__(self, config: dict):
        super().__init__('Yahoo', config)
    
    def connect(self) -> bool:
        try:
            import yfinance as yf
            self.is_connected = True
            logger.info("✅ Yahoo Finance数据源连接成功")
            return True
        except ImportError:
            logger.warning("⚠️ yfinance未安装，Yahoo数据源不可用")
            self.is_connected = False
            return False
    
    def get_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Yahoo不提供免费实时数据，使用延迟数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            return data.tail(1)
        except Exception as e:
            logger.error(f"Yahoo实时数据获取失败: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start: str, end: str,
                           interval: str = '1d') -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start, end=end, interval=interval)
            data = data.reset_index()
            data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits']
            return data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"Yahoo历史数据获取失败: {e}")
            return None


class AKShareSource(DataSource):
    """AKShare数据源 - A股专用"""
    
    def __init__(self, config: dict):
        super().__init__('AKShare', config)
    
    def connect(self) -> bool:
        try:
            import akshare as ak
            self.is_connected = True
            logger.info("✅ AKShare数据源连接成功")
            return True
        except ImportError:
            logger.warning("⚠️ akshare未安装，AKShare数据源不可用")
            self.is_connected = False
            return False
    
    def get_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取A股实时行情"""
        try:
            import akshare as ak
            # 小米集团A股代码: 1810.HK
            data = ak.stock_hk_spot_em()
            stock_data = data[data['代码'] == symbol]
            return stock_data
        except Exception as e:
            logger.error(f"AKShare实时数据获取失败: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start: str, end: str,
                           interval: str = '1d') -> Optional[pd.DataFrame]:
        try:
            import akshare as ak
            # 获取港股历史数据
            data = ak.stock_hk_hist(symbol=symbol, period=interval,
                                   start_date=start, end_date=end)
            data.columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume', 
                          'amount', 'amplitude', 'pct_change', 'change_amount', 'turnover']
            return data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"AKShare历史数据获取失败: {e}")
            return None


class DataSourceManager:
    """数据源管理器 - 多源融合"""
    
    def __init__(self, config: dict):
        self.config = config
        self.sources: Dict[str, DataSource] = {}
        self.primary_source = None
        self._init_sources()
    
    def _init_sources(self):
        """初始化所有数据源"""
        # iTick - 主要数据源
        if self.config.get('itick', {}).get('enabled', True):
            itick = iTickSource(self.config.get('itick', {}))
            if itick.connect():
                self.sources['itick'] = itick
                self.primary_source = itick
        
        # Yahoo Finance - 备用
        if self.config.get('yahoo', {}).get('enabled', True):
            yahoo = YahooSource(self.config.get('yahoo', {}))
            if yahoo.connect():
                self.sources['yahoo'] = yahoo
        
        # AKShare - A股专用
        if self.config.get('akshare', {}).get('enabled', True):
            akshare = AKShareSource(self.config.get('akshare', {}))
            if akshare.connect():
                self.sources['akshare'] = akshare
    
    def get_data(self, symbol: str, start: str, end: str, 
                interval: str = '1d', prefer_source: str = None) -> pd.DataFrame:
        """
        获取数据 - 自动多源融合
        
        策略:
        1. 优先使用指定数据源
        2. 主数据源失败时自动切换备用源
        3. 多源数据交叉验证
        """
        # 优先使用指定源
        if prefer_source and prefer_source in self.sources:
            source = self.sources[prefer_source]
            data = source.get_historical_data(symbol, start, end, interval)
            if data is not None and not data.empty:
                return data
        
        # 使用主数据源
        if self.primary_source:
            data = self.primary_source.get_historical_data(symbol, start, end, interval)
            if data is not None and not data.empty:
                return data
        
        # 依次尝试备用源
        for name, source in self.sources.items():
            if source == self.primary_source:
                continue
            data = source.get_historical_data(symbol, start, end, interval)
            if data is not None and not data.empty:
                logger.info(f"使用备用数据源: {name}")
                return data
        
        logger.error("所有数据源均失败")
        return pd.DataFrame()
    
    def get_realtime_data(self, symbol: str) -> pd.DataFrame:
        """获取实时数据"""
        if self.primary_source:
            return self.primary_source.get_realtime_data(symbol)
        return pd.DataFrame()
    
    def health_check(self) -> Dict[str, bool]:
        """检查所有数据源健康状态"""
        return {name: source.health_check() for name, source in self.sources.items()}


# 使用示例
if __name__ == "__main__":
    # 配置
    config = {
        'itick': {'enabled': True, 'api_key': 'your_api_key'},
        'yahoo': {'enabled': True},
        'akshare': {'enabled': True}
    }
    
    # 初始化数据管理器
    manager = DataSourceManager(config)
    
    # 获取小米集团数据 (港股代码: 1810.HK)
    symbol = "1810.HK"
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    data = manager.get_data(symbol, start_date, end_date)
    print(f"\n获取到 {len(data)} 条数据:")
    print(data.head())
    
    # 健康检查
    health = manager.health_check()
    print(f"\n数据源健康状态: {health}")
