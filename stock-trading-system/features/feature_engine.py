"""
特征工程主模块
整合技术指标、Alpha因子、特征缓存
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

from features.technical import TechnicalIndicatorCalculator
from features.alpha import AlphaFactorCalculator
from utils.cache import FeatureCache, get_cache

logger = logging.getLogger(__name__)


class FeatureEngine:
    """特征工程主类"""
    
    def __init__(self, use_cache: bool = True):
        self.technical_calc = TechnicalIndicatorCalculator()
        self.alpha_calc = AlphaFactorCalculator()
        self.use_cache = use_cache
        
        if use_cache:
            self.cache = FeatureCache(get_cache())
            logger.info("✅ 特征缓存已启用")
        else:
            self.cache = None
            logger.info("⚠️ 特征缓存已禁用")
    
    def calculate_features(self, df: pd.DataFrame, symbol: str,
                          use_cache: bool = True) -> pd.DataFrame:
        """
        计算所有特征
        
        Args:
            df: 原始OHLCV数据
            symbol: 股票代码，用于缓存
            use_cache: 是否使用缓存
        
        Returns:
            包含所有特征的DataFrame
        """
        if df.empty:
            logger.warning("输入数据为空")
            return df
        
        # 确保有timestamp列
        if 'timestamp' not in df.columns:
            df['timestamp'] = df.index
        
        result = df.copy()
        
        # 逐行计算特征（支持缓存）
        if use_cache and self.cache:
            result = self._calculate_with_cache(result, symbol)
        else:
            # 批量计算（不使用缓存）
            result = self.technical_calc.calculate_all(result)
            result = self.alpha_calc.calculate_all(result)
        
        # 填充NaN值
        result = self._fill_na(result)
        
        logger.info(f"✅ 特征计算完成: {len(result.columns)} 列, {len(result)} 行")
        
        return result
    
    def _calculate_with_cache(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """使用缓存计算特征"""
        result = df.copy()
        
        # 需要计算的技术指标列表
        tech_features = self.technical_calc.get_feature_names()
        alpha_features = self.alpha_calc.get_alpha_feature_names()
        all_features = tech_features + alpha_features
        
        # 检查哪些特征需要计算
        missing_features = set()
        
        for timestamp in result['timestamp']:
            ts_str = str(timestamp)
            
            # 尝试从缓存获取
            cached_features = {}
            for feat_name in all_features:
                cached_value = self.cache.get_feature(symbol, ts_str, feat_name)
                if cached_value is not None:
                    cached_features[feat_name] = cached_value
            
            # 记录缺失的特征
            for feat_name in all_features:
                if feat_name not in cached_features:
                    missing_features.add(feat_name)
        
        if missing_features:
            logger.info(f"需要计算 {len(missing_features)} 个缺失特征")
            
            # 批量计算所有特征
            result = self.technical_calc.calculate_all(result)
            result = self.alpha_calc.calculate_all(result)
            
            # 保存到缓存
            self._save_to_cache(result, symbol, all_features)
        else:
            logger.info("所有特征均已缓存")
        
        return result
    
    def _save_to_cache(self, df: pd.DataFrame, symbol: str, feature_names: List[str]):
        """保存特征到缓存"""
        if not self.cache:
            return
        
        for _, row in df.iterrows():
            timestamp = str(row['timestamp'])
            
            for feat_name in feature_names:
                if feat_name in row and pd.notna(row[feat_name]):
                    self.cache.set_feature(
                        symbol, timestamp, feat_name, float(row[feat_name])
                    )
        
        logger.info(f"💾 已缓存 {len(df)} 行数据")
    
    def _fill_na(self, df: pd.DataFrame) -> pd.DataFrame:
        """填充缺失值"""
        # 向前填充
        df = df.fillna(method='ffill')
        
        # 向后填充（处理开头的NaN）
        df = df.fillna(method='bfill')
        
        # 剩余的填充为0
        df = df.fillna(0)
        
        return df
    
    def get_feature_importance(self, df: pd.DataFrame, target_col: str = 'close') -> Dict[str, float]:
        """
        计算特征重要性（基于相关系数）
        
        Args:
            df: 包含特征的DataFrame
            target_col: 目标列
        
        Returns:
            特征重要性字典
        """
        # 计算与目标变量的相关性
        correlations = {}
        
        # 计算未来收益率作为目标
        if 'returns' not in df.columns:
            df['future_returns'] = df[target_col].shift(-1) / df[target_col] - 1
        else:
            df['future_returns'] = df['returns'].shift(-1)
        
        feature_cols = [c for c in df.columns if c not in 
                       ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'future_returns']]
        
        for col in feature_cols:
            corr = df[col].corr(df['future_returns'])
            if pd.notna(corr):
                correlations[col] = abs(corr)
        
        # 排序
        sorted_corr = dict(sorted(correlations.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_corr
    
    def select_top_features(self, df: pd.DataFrame, n_features: int = 50,
                           target_col: str = 'close') -> List[str]:
        """
        选择最重要的特征
        
        Args:
            df: 包含特征的DataFrame
            n_features: 选择特征数量
            target_col: 目标列
        
        Returns:
            选中的特征名列表
        """
        importance = self.get_feature_importance(df, target_col)
        
        top_features = list(importance.keys())[:n_features]
        
        logger.info(f"选择前 {len(top_features)} 个重要特征")
        
        return top_features
    
    def create_sequences(self, df: pd.DataFrame, feature_cols: List[str],
                        target_col: str, sequence_length: int = 60) -> tuple:
        """
        创建时间序列数据（用于深度学习）
        
        Args:
            df: 特征DataFrame
            feature_cols: 特征列名
            target_col: 目标列名
            sequence_length: 序列长度
        
        Returns:
            X, y 数组
        """
        X, y = [], []
        
        data = df[feature_cols].values
        target = df[target_col].values
        
        for i in range(len(data) - sequence_length):
            X.append(data[i:(i + sequence_length)])
            y.append(target[i + sequence_length])
        
        return np.array(X), np.array(y)
    
    def normalize_features(self, df: pd.DataFrame, feature_cols: List[str],
                          method: str = 'zscore') -> pd.DataFrame:
        """
        特征归一化
        
        Args:
            df: 特征DataFrame
            feature_cols: 需要归一化的特征列
            method: 'zscore' 或 'minmax'
        
        Returns:
            归一化后的DataFrame
        """
        result = df.copy()
        
        for col in feature_cols:
            if col in result.columns:
                if method == 'zscore':
                    mean = result[col].mean()
                    std = result[col].std()
                    if std != 0:
                        result[col] = (result[col] - mean) / std
                elif method == 'minmax':
                    min_val = result[col].min()
                    max_val = result[col].max()
                    if max_val != min_val:
                        result[col] = (result[col] - min_val) / (max_val - min_val)
        
        return result
    
    def get_all_feature_names(self) -> List[str]:
        """获取所有特征名称"""
        tech_features = self.technical_calc.get_feature_names()
        alpha_features = self.alpha_calc.get_alpha_feature_names()
        return tech_features + alpha_features


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    base_price = 15.0
    prices = [base_price]
    for i in range(99):
        change = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + change))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [p * np.random.uniform(0.995, 1.0) for p in prices],
        'high': [p * np.random.uniform(1.0, 1.02) for p in prices],
        'low': [p * np.random.uniform(0.98, 1.0) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # 初始化特征工程
    engine = FeatureEngine(use_cache=False)
    
    # 计算特征
    result = engine.calculate_features(df, symbol='1810.HK')
    
    print(f"\n✅ 特征工程完成!")
    print(f"输入列数: {len(df.columns)}")
    print(f"输出列数: {len(result.columns)}")
    print(f"新增特征: {len(result.columns) - len(df.columns)}")
    
    # 特征重要性
    importance = engine.get_feature_importance(result)
    print("\n🔝 前10个重要特征:")
    for feat, score in list(importance.items())[:10]:
        print(f"  {feat}: {score:.4f}")
    
    # 选择Top特征
    top_features = engine.select_top_features(result, n_features=30)
    print(f"\n✅ 已选择 {len(top_features)} 个特征用于建模")
