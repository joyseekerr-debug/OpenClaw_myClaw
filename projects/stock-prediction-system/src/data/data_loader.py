"""
股价预测系统 - 数据加载模块
支持多数据源、多时间框架数据获取
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import json
import time
from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源基类"""
    
    @abstractmethod
    def get_kline_data(self, symbol: str, timeframe: str, 
                       start_date: str, end_date: str) -> pd.DataFrame:
        """获取K线数据"""
        pass
    
    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> Dict:
        """获取实时行情"""
        pass


class iTickDataSource(DataSource):
    """iTick数据源"""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.base_url = "https://api-free.itick.org/stock"
        self.timeframe_map = {
            '1m': '1min',
            '5m': '5min', 
            '15m': '15min',
            '30m': '30min',
            '1h': '1hour',
            '4h': '4hour',
            '1d': 'day',
            '1w': 'week'
        }
    
    def _get_api_key(self) -> str:
        """轮询API Key"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def get_kline_data(self, symbol: str, timeframe: str,
                       start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取iTick K线数据
        
        Args:
            symbol: 股票代码 (如: '1810.HK')
            timeframe: 时间框架 (1m/5m/15m/1h/4h/1d/1w)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume]
        """
        try:
            # 港股代码处理 (去掉.HK后缀)
            if '.HK' in symbol:
                code = symbol.replace('.HK', '')
            else:
                code = symbol
            
            url = f"{self.base_url}/kline"
            params = {
                'code': code,
                'period': self.timeframe_map.get(timeframe, 'day'),
                'startDate': start_date,
                'endDate': end_date
            }
            headers = {
                'token': self._get_api_key()
            }
            
            logger.info(f"Fetching {symbol} {timeframe} data from iTick...")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) == 0:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # 解析数据
            df = pd.DataFrame(data)
            
            # 重命名列
            column_map = {
                't': 'timestamp',
                'o': 'open',
                'h': 'high', 
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            }
            df = df.rename(columns=column_map)
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 确保数值类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 添加元数据
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            df['source'] = 'itick'
            
            logger.info(f"Successfully loaded {len(df)} records for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from iTick: {e}")
            return pd.DataFrame()
    
    def get_realtime_quote(self, symbol: str) -> Dict:
        """获取实时行情"""
        try:
            if '.HK' in symbol:
                code = symbol.replace('.HK', '')
            else:
                code = symbol
            
            url = f"{self.base_url}/tick"
            params = {'code': code}
            headers = {'token': self._get_api_key()}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析实时数据
            quote = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'price': data.get('ld', 0),  # 最新价
                'open': data.get('o', 0),
                'high': data.get('h', 0),
                'low': data.get('l', 0),
                'prev_close': data.get('p', 0),
                'volume': data.get('v', 0),
                'change': data.get('ch', 0),
                'change_pct': data.get('chp', 0),
                'source': 'itick'
            }
            
            return quote
            
        except Exception as e:
            logger.error(f"Error fetching realtime quote from iTick: {e}")
            return {}


class YahooFinanceDataSource(DataSource):
    """Yahoo Finance数据源 (备用)"""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    def get_kline_data(self, symbol: str, timeframe: str,
                       start_date: str, end_date: str) -> pd.DataFrame:
        """获取Yahoo Finance K线数据"""
        try:
            # 代码转换
            if '.HK' in symbol:
                yahoo_symbol = symbol.replace('.HK', '.HK')
            else:
                yahoo_symbol = symbol
            
            # 时间范围转换
            start_ts = int(pd.Timestamp(start_date).timestamp())
            end_ts = int(pd.Timestamp(end_date).timestamp())
            
            # 时间框架映射
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m',
                '1h': '1h', '4h': '1h',  # Yahoo不支持4h
                '1d': '1d', '1w': '1wk'
            }
            interval = interval_map.get(timeframe, '1d')
            
            url = f"{self.base_url}/{yahoo_symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': interval,
                'events': 'history'
            }
            
            logger.info(f"Fetching {symbol} {timeframe} data from Yahoo Finance...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
                logger.warning(f"No data returned from Yahoo for {symbol}")
                return pd.DataFrame()
            
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            ohlcv = result['indicators']['quote'][0]
            
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(timestamps, unit='s'),
                'open': ohlcv.get('open', []),
                'high': ohlcv.get('high', []),
                'low': ohlcv.get('low', []),
                'close': ohlcv.get('close', []),
                'volume': ohlcv.get('volume', [])
            })
            
            df.set_index('timestamp', inplace=True)
            df.dropna(inplace=True)
            
            # 添加元数据
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            df['source'] = 'yahoo'
            
            logger.info(f"Successfully loaded {len(df)} records from Yahoo")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Yahoo: {e}")
            return pd.DataFrame()
    
    def get_realtime_quote(self, symbol: str) -> Dict:
        """获取Yahoo实时行情"""
        # Yahoo Finance实时数据需要特殊处理
        # 这里简化实现
        return {}


class DataLoader:
    """数据加载器主类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 初始化数据源
        self.sources = {}
        
        # iTick数据源
        itick_keys = self.config.get('itick_api_keys', [])
        if itick_keys:
            self.sources['itick'] = iTickDataSource(itick_keys)
            logger.info(f"Initialized iTick data source with {len(itick_keys)} API keys")
        
        # Yahoo Finance数据源 (备用)
        self.sources['yahoo'] = YahooFinanceDataSource()
        logger.info("Initialized Yahoo Finance data source (fallback)")
        
        # 默认主数据源
        self.primary_source = 'itick' if 'itick' in self.sources else 'yahoo'
    
    def load_data(self, symbol: str, timeframe: str,
                  start_date: str, end_date: str,
                  source: str = None) -> pd.DataFrame:
        """
        加载K线数据
        
        Args:
            symbol: 股票代码
            timeframe: 时间框架
            start_date: 开始日期
            end_date: 结束日期
            source: 指定数据源 (None则使用主数据源，失败时自动切换)
        
        Returns:
            DataFrame with OHLCV data
        """
        # 尝试主数据源
        if source is None:
            source = self.primary_source
        
        if source in self.sources:
            df = self.sources[source].get_kline_data(symbol, timeframe, start_date, end_date)
            
            if not df.empty:
                return df
            
            logger.warning(f"Primary source {source} failed, trying fallback...")
        
        # 尝试备用数据源
        for src_name, src_obj in self.sources.items():
            if src_name != source:
                df = src_obj.get_kline_data(symbol, timeframe, start_date, end_date)
                if not df.empty:
                    logger.info(f"Using fallback source: {src_name}")
                    return df
        
        logger.error(f"All data sources failed for {symbol} {timeframe}")
        return pd.DataFrame()
    
    def load_multi_timeframe(self, symbol: str, timeframes: List[str],
                            start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        加载多个时间框架数据
        
        Returns:
            Dict {timeframe: DataFrame}
        """
        data = {}
        
        for tf in timeframes:
            logger.info(f"Loading {symbol} {tf} data...")
            df = self.load_data(symbol, tf, start_date, end_date)
            
            if not df.empty:
                data[tf] = df
            else:
                logger.warning(f"Failed to load {tf} data")
        
        return data
    
    def get_realtime_quote(self, symbol: str, source: str = None) -> Dict:
        """获取实时行情"""
        if source is None:
            source = self.primary_source
        
        if source in self.sources:
            return self.sources[source].get_realtime_quote(symbol)
        
        return {}


# 便捷函数
def load_stock_data(symbol: str = '1810.HK',
                   timeframes: List[str] = ['1d'],
                   days: int = 365,
                   config: Dict = None) -> Dict[str, pd.DataFrame]:
    """
    便捷函数：加载股票数据
    
    Args:
        symbol: 股票代码
        timeframes: 时间框架列表
        days: 历史天数
        config: 配置
    
    Returns:
        Dict of DataFrames
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    loader = DataLoader(config)
    return loader.load_multi_timeframe(symbol, timeframes, start_date, end_date)


if __name__ == '__main__':
    # 测试代码
    config = {
        'itick_api_keys': [
            '62842f6d5e1244.52881530',
            '12c411af00d44.37624341'
        ]
    }
    
    loader = DataLoader(config)
    
    # 测试加载日线数据
    df = loader.load_data('1810.HK', '1d', '2024-01-01', '2024-12-31')
    print(f"Loaded {len(df)} records")
    print(df.head())
    
    # 测试实时行情
    quote = loader.get_realtime_quote('1810.HK')
    print(f"\nRealtime quote: {quote}")
