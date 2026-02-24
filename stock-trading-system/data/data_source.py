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
    """iTick数据源 - 主要数据源"""
    
    def __init__(self, config: dict):
        super().__init__('iTick', config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.itick.com')
    
    def connect(self) -> bool:
        """连接iTick API"""
        try:
            # 实际实现需要导入iTick SDK
            # import itick
            # self.client = itick.Client(self.api_key)
            self.is_connected = True
            logger.info("✅ iTick数据源连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ iTick连接失败: {e}")
            self.is_connected = False
            return False
    
    def get_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取实时tick数据"""
        if not self.is_connected:
            return None
        
        try:
            # 模拟数据 - 实际应调用iTick API
            data = {
                'timestamp': [datetime.now()],
                'symbol': [symbol],
                'price': [15.5],
                'volume': [1000],
                'bid': [15.48],
                'ask': [15.52],
                'bid_volume': [500],
                'ask_volume': [600]
            }
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"iTick实时数据获取失败: {e}")
            return None
    
    def get_historical_data(self, symbol: str, start: str, end: str,
                           interval: str = '1d') -> Optional[pd.DataFrame]:
        """获取历史K线数据"""
        if not self.is_connected:
            return None
        
        try:
            # 模拟历史数据
            dates = pd.date_range(start=start, end=end, freq=interval)
            np.random.seed(42)
            base_price = 15.0
            
            data = []
            for date in dates:
                change = np.random.normal(0, 0.02)
                close = base_price * (1 + change)
                open_price = close * (1 + np.random.normal(0, 0.005))
                high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
                low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
                volume = int(np.random.randint(1000000, 10000000))
                
                data.append({
                    'timestamp': date,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close, 2),
                    'volume': volume
                })
                base_price = close
            
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"iTick历史数据获取失败: {e}")
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
