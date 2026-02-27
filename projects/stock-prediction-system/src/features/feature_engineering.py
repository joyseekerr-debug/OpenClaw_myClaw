"""
股价预测系统 - 特征工程主类
整合技术指标、价格行为、Alpha因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """特征工程主类"""
    
    def __init__(self):
        self.feature_cache = {}
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建所有特征
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            DataFrame with all features
        """
        if df.empty:
            return df
        
        logger.info(f"Creating features for {len(df)} rows...")
        
        # 1. 基础价格特征
        df = self._add_price_features(df)
        
        # 2. 技术指标特征
        df = self._add_technical_features(df)
        
        # 3. 价格行为特征
        df = self._add_price_action_features(df)
        
        # 4. Alpha因子
        df = self._add_alpha_factors(df)
        
        # 5. 目标变量 (未来N期涨跌)
        df = self._add_target(df)
        
        # 去除包含空值的行
        df.dropna(inplace=True)
        
        logger.info(f"Feature engineering complete: {len(df)} rows, {len(df.columns)} features")
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """基础价格特征"""
        df = df.copy()
        
        # 收益率
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 价格位置
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10)
        
        # 价格波动
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['body_ratio'] = abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-10)
        
        # 方向
        df['direction'] = np.where(df['close'] > df['open'], 1, 
                          np.where(df['close'] < df['open'], -1, 0))
        
        return df
    
    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """技术指标特征 (简化版核心指标)"""
        df = df.copy()
        
        # 简单移动平均
        for period in [5, 10, 20, 60]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
            df[f'close_sma_{period}_ratio'] = df['close'] / df[f'sma_{period}']
        
        # RSI (14期)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * bb_std
        df['bb_lower'] = df['bb_middle'] - 2 * bb_std
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
        
        # ATR (平均真实波幅)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(14).mean()
        
        # 成交量指标
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # KDJ简化版
        low_min = df['low'].rolling(9).min()
        high_max = df['high'].rolling(9).max()
        rsv = (df['close'] - low_min) / (high_max - low_min + 1e-10) * 100
        df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        return df
    
    def _add_price_action_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """价格行为特征"""
        df = df.copy()
        
        # 支撑阻力位 (简化版：使用N期高低点)
        lookback = 20
        df['support_level'] = df['low'].rolling(lookback).min()
        df['resistance_level'] = df['high'].rolling(lookback).max()
        
        # 距离支撑阻力的距离
        df['dist_to_support'] = (df['close'] - df['support_level']) / df['close']
        df['dist_to_resistance'] = (df['resistance_level'] - df['close']) / df['close']
        
        # 趋势强度 (线性回归斜率)
        df['trend_slope'] = df['close'].rolling(20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else 0
        )
        
        # 波动率
        df['volatility_20'] = df['returns'].rolling(20).std() * np.sqrt(252)
        
        # 动量
        df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        return df
    
    def _add_alpha_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Alpha因子 (简化版)"""
        df = df.copy()
        
        # 1. 价格动量
        df['alpha_momentum'] = df['close'].shift(5) / df['close'].shift(20) - 1
        
        # 2. 波动率调整动量
        df['alpha_risk_adj_momentum'] = df['alpha_momentum'] / (df['returns'].rolling(20).std() + 1e-10)
        
        # 3. 均值回归 (Z-score)
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['alpha_zscore'] = (df['close'] - sma_20) / (std_20 + 1e-10)
        
        # 4. 成交量趋势
        df['alpha_volume_trend'] = df['volume'].rolling(5).mean() / df['volume'].rolling(20).mean()
        
        # 5. 价格加速度
        df['alpha_acceleration'] = df['returns'].diff(5)
        
        return df
    
    def _add_target(self, df: pd.DataFrame, periods: List[int] = [1, 5, 10]) -> pd.DataFrame:
        """添加目标变量"""
        df = df.copy()
        
        for period in periods:
            # 未来N期收益率
            df[f'target_return_{period}'] = df['close'].shift(-period) / df['close'] - 1
            
            # 未来N期方向 (分类任务)
            df[f'target_direction_{period}'] = np.where(
                df[f'target_return_{period}'] > 0.005, 1,  # 上涨 > 0.5%
                np.where(df[f'target_return_{period}'] < -0.005, 0, 2)  # 下跌 < -0.5%, 震荡
            )
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称列表"""
        return [
            # 价格特征
            'returns', 'log_returns', 'price_position', 'price_range', 'body_ratio', 'direction',
            # 技术指标
            'sma_5', 'sma_10', 'sma_20', 'sma_60',
            'ema_5', 'ema_10', 'ema_20', 'ema_60',
            'close_sma_5_ratio', 'close_sma_10_ratio', 'close_sma_20_ratio', 'close_sma_60_ratio',
            'rsi_14', 'macd', 'macd_signal', 'macd_hist',
            'bb_position', 'atr_14', 'volume_ratio',
            'kdj_k', 'kdj_d', 'kdj_j',
            # 价格行为
            'dist_to_support', 'dist_to_resistance', 'trend_slope', 'volatility_20',
            'momentum_10', 'momentum_20',
            # Alpha因子
            'alpha_momentum', 'alpha_risk_adj_momentum', 'alpha_zscore',
            'alpha_volume_trend', 'alpha_acceleration'
        ]


# 便捷函数
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """便捷函数：特征工程"""
    engineer = FeatureEngineer()
    return engineer.create_all_features(df)


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=365)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 特征工程
        engineer = FeatureEngineer()
        df_features = engineer.create_all_features(df)
        
        print(f"Original features: {len(df.columns)}")
        print(f"Engineered features: {len(df_features.columns)}")
        print(f"\nFeature names: {engineer.get_feature_names()}")
        print(f"\nSample data:")
        print(df_features[['close', 'rsi_14', 'macd', 'target_direction_1']].tail())
