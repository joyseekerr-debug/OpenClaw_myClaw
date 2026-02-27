"""
股价预测系统 - 数据处理模块
数据清洗、预处理、对齐
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.quality_thresholds = {
            'min_data_points': 100,
            'max_missing_ratio': 0.1,
            'max_duplicate_ratio': 0.05
        }
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗数据
        
        处理内容:
        1. 去除空值
        2. 去除异常值
        3. 去除重复数据
        4. 数据类型转换
        """
        if df.empty:
            logger.warning("Empty DataFrame received")
            return df
        
        original_len = len(df)
        df = df.copy()
        
        # 1. 去除完全空值行
        df.dropna(how='all', inplace=True)
        
        # 2. 去除OHLCV核心字段为空的行
        core_cols = ['open', 'high', 'low', 'close', 'volume']
        df.dropna(subset=[col for col in core_cols if col in df.columns], inplace=True)
        
        # 3. 去除重复数据（基于时间戳）
        if df.index.name == 'timestamp' or 'timestamp' in df.columns:
            df = df[~df.index.duplicated(keep='first')]
        
        # 4. 异常值检测与处理
        df = self._handle_outliers(df)
        
        # 5. 确保数据逻辑正确
        df = self._validate_ohlc(df)
        
        cleaned_len = len(df)
        removed = original_len - cleaned_len
        
        if removed > 0:
            logger.info(f"Cleaned data: removed {removed} rows ({removed/original_len*100:.1f}%)")
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理异常值"""
        df = df.copy()
        
        # 价格异常值 (使用IQR方法)
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                # 标记异常值
                outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                if outliers.sum() > 0:
                    logger.warning(f"Found {outliers.sum()} outliers in {col}")
                    # 使用中位数填充异常值
                    df.loc[outliers, col] = df[col].median()
        
        # 成交量异常值
        if 'volume' in df.columns:
            Q1 = df['volume'].quantile(0.25)
            Q3 = df['volume'].quantile(0.75)
            IQR = Q3 - Q1
            
            upper_bound = Q3 + 5 * IQR  # 成交量用更宽松的阈值
            outliers = df['volume'] > upper_bound
            
            if outliers.sum() > 0:
                logger.warning(f"Found {outliers.sum()} volume outliers")
                # 限制在95分位数
                df.loc[outliers, 'volume'] = df['volume'].quantile(0.95)
        
        return df
    
    def _validate_ohlc(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证OHLC数据逻辑"""
        df = df.copy()
        
        # 确保 high >= max(open, close, low)
        # 确保 low <= min(open, close, high)
        
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # 修正high
            df['high'] = df[['open', 'high', 'close']].max(axis=1)
            
            # 修正low
            df['low'] = df[['open', 'low', 'close']].min(axis=1)
            
            # 检查是否有high < low的异常
            invalid = df['high'] < df['low']
            if invalid.sum() > 0:
                logger.error(f"Found {invalid.sum()} invalid OHLC rows, removing...")
                df = df[~invalid]
        
        return df
    
    def resample_data(self, df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """
        重采样数据到不同时间框架
        
        Args:
            df: 原始数据 (需要有timestamp索引)
            target_timeframe: 目标时间框架 (1m/5m/15m/1h/4h/1d/1w)
        """
        if df.empty:
            return df
        
        # 时间框架到pandas规则的映射
        timeframe_rules = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D',
            '1w': '1W'
        }
        
        rule = timeframe_rules.get(target_timeframe)
        if not rule:
            logger.error(f"Unknown timeframe: {target_timeframe}")
            return df
        
        # 确保索引是datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.error("DataFrame index must be DatetimeIndex")
            return df
        
        # 重采样
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # 去除空值
        resampled.dropna(inplace=True)
        
        # 保留元数据
        if 'symbol' in df.columns:
            resampled['symbol'] = df['symbol'].iloc[0]
        resampled['timeframe'] = target_timeframe
        
        logger.info(f"Resampled from {len(df)} to {len(resampled)} rows ({target_timeframe})")
        
        return resampled
    
    def align_multi_timeframe(self, data_dict: Dict[str, pd.DataFrame],
                             base_timeframe: str = '1d') -> Dict[str, pd.DataFrame]:
        """
        对齐多个时间框架的数据
        
        确保所有时间框架的数据时间范围一致
        """
        if not data_dict:
            return {}
        
        # 找出共同的时间范围
        start_times = []
        end_times = []
        
        for tf, df in data_dict.items():
            if not df.empty:
                start_times.append(df.index.min())
                end_times.append(df.index.max())
        
        if not start_times or not end_times:
            return data_dict
        
        common_start = max(start_times)
        common_end = min(end_times)
        
        logger.info(f"Aligning data to common range: {common_start} to {common_end}")
        
        # 裁剪所有数据到共同范围
        aligned_data = {}
        for tf, df in data_dict.items():
            if not df.empty:
                aligned_df = df[(df.index >= common_start) & (df.index <= common_end)].copy()
                aligned_data[tf] = aligned_df
                logger.info(f"{tf}: {len(aligned_df)} rows after alignment")
        
        return aligned_data
    
    def fill_missing_data(self, df: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
        """填充缺失数据"""
        if df.empty:
            return df
        
        df = df.copy()
        
        if method == 'ffill':
            # 前向填充
            df.fillna(method='ffill', inplace=True)
        elif method == 'interpolate':
            # 线性插值
            df.interpolate(method='linear', inplace=True)
        elif method == 'drop':
            # 删除缺失值
            df.dropna(inplace=True)
        
        return df
    
    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加时间特征"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 确保索引是datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.error("DataFrame index must be DatetimeIndex")
            return df
        
        # 基础时间特征
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek  # 0=Monday, 6=Sunday
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['year'] = df.index.year
        
        # 是否为交易日开始/结束
        df['is_market_open'] = (df['hour'] == 9) & (df.index.minute < 30)
        df['is_market_close'] = (df['hour'] == 16)
        
        # 周期性编码
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        logger.info("Added time features")
        
        return df
    
    def check_data_quality(self, df: pd.DataFrame) -> Dict:
        """检查数据质量"""
        if df.empty:
            return {'status': 'error', 'message': 'Empty DataFrame'}
        
        quality_report = {
            'total_rows': len(df),
            'missing_values': {},
            'missing_ratio': 0,
            'duplicate_rows': 0,
            'date_range': {
                'start': df.index.min(),
                'end': df.index.max()
            },
            'status': 'ok'
        }
        
        # 检查缺失值
        for col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                quality_report['missing_values'][col] = missing
        
        total_cells = df.size
        missing_cells = sum(quality_report['missing_values'].values())
        quality_report['missing_ratio'] = missing_cells / total_cells if total_cells > 0 else 0
        
        # 检查重复值
        quality_report['duplicate_rows'] = df.index.duplicated().sum()
        
        # 质量评估
        if quality_report['missing_ratio'] > self.quality_thresholds['max_missing_ratio']:
            quality_report['status'] = 'warning'
            quality_report['message'] = f"High missing ratio: {quality_report['missing_ratio']:.2%}"
        
        if len(df) < self.quality_thresholds['min_data_points']:
            quality_report['status'] = 'error'
            quality_report['message'] = f"Insufficient data: {len(df)} points"
        
        return quality_report
    
    def process_pipeline(self, df: pd.DataFrame, 
                        target_timeframe: str = None,
                        add_time_features: bool = True) -> pd.DataFrame:
        """
        完整的数据处理流程
        
        Args:
            df: 原始数据
            target_timeframe: 目标时间框架 (可选)
            add_time_features: 是否添加时间特征
        """
        logger.info("Starting data processing pipeline...")
        
        # 1. 清洗数据
        df = self.clean_data(df)
        
        # 2. 填充缺失值
        df = self.fill_missing_data(df, method='ffill')
        
        # 3. 重采样 (如果需要)
        if target_timeframe:
            df = self.resample_data(df, target_timeframe)
        
        # 4. 添加时间特征
        if add_time_features:
            df = self.add_time_features(df)
        
        # 5. 质量检查
        quality = self.check_data_quality(df)
        logger.info(f"Data quality: {quality['status']}")
        
        logger.info(f"Processing complete: {len(df)} rows")
        
        return df


# 便捷函数
def process_stock_data(df: pd.DataFrame, 
                      target_timeframe: str = None,
                      add_time_features: bool = True) -> pd.DataFrame:
    """便捷函数：处理股票数据"""
    processor = DataProcessor()
    return processor.process_pipeline(df, target_timeframe, add_time_features)


if __name__ == '__main__':
    # 测试代码
    from data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=365)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 处理数据
        processor = DataProcessor()
        
        # 质量检查
        quality = processor.check_data_quality(df)
        print("Data Quality Report:")
        print(quality)
        
        # 清洗数据
        cleaned = processor.clean_data(df)
        print(f"\nCleaned data: {len(cleaned)} rows")
        
        # 添加时间特征
        with_features = processor.add_time_features(cleaned)
        print(f"\nFeatures added: {with_features.columns.tolist()}")
        print(with_features.head())
