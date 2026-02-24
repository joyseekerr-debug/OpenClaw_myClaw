"""
Alpha因子计算模块
高级特征工程，包含订单流特征、市场情绪特征等
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlphaFactors:
    """Alpha因子特征集"""
    # 订单流特征
    order_imbalance: float = 0.0  # 订单失衡
    trade_intensity: float = 0.0  # 交易强度
    large_order_ratio: float = 0.0  # 大单比率
    
    # 价格特征
    returns: float = 0.0  # 收益率
    log_returns: float = 0.0  # 对数收益率
    realized_volatility: float = 0.0  # 实际波动率
    
    # 趋势特征
    trend_strength: float = 0.0  # 趋势强度
    price_acceleration: float = 0.0  # 价格加速度
    
    # 均值回归
    z_score_20: float = 0.0  # 20日Z分数
    distance_from_ma: float = 0.0  # 距均线距离
    
    # 流动性
    amihud_illiquidity: float = 0.0  # Amihud非流动性指标
    turnover_rate: float = 0.0  # 换手率


class AlphaFactorCalculator:
    """Alpha因子计算器"""
    
    def __init__(self):
        self.features_calculated = 0
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有Alpha因子
        
        Args:
            df: 包含OHLCV和tick数据的DataFrame
        
        Returns:
            添加了Alpha因子的DataFrame
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        try:
            # 1. 订单流特征 (需要L2数据)
            result = self._calculate_order_flow_features(result)
            
            # 2. 价格特征
            result = self._calculate_price_features(result)
            
            # 3. 趋势特征
            result = self._calculate_trend_features(result)
            
            # 4. 均值回归特征
            result = self._calculate_mean_reversion_features(result)
            
            # 5. 流动性特征
            result = self._calculate_liquidity_features(result)
            
            # 6. 波动率特征
            result = self._calculate_volatility_features(result)
            
            # 7. 市场情绪特征
            result = self._calculate_sentiment_features(result)
            
            # 8. 时间特征
            result = self._calculate_time_features(result)
            
            logger.info(f"✅ Alpha因子计算完成")
            
        except Exception as e:
            logger.error(f"Alpha因子计算失败: {e}")
        
        return result
    
    def _calculate_order_flow_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算订单流特征
        注: 需要L2数据，如果没有则使用替代计算
        """
        # 如果有买卖盘数据
        if 'bid_volume' in df.columns and 'ask_volume' in df.columns:
            # 订单失衡 (Order Imbalance)
            total_volume = df['bid_volume'] + df['ask_volume']
            df['order_imbalance'] = (df['bid_volume'] - df['ask_volume']) / total_volume
            
            # 买卖压力
            df['buying_pressure'] = df['bid_volume'] / total_volume
            df['selling_pressure'] = df['ask_volume'] / total_volume
        else:
            # 使用价格变动方向估算
            price_change = df['close'].diff()
            volume = df['volume']
            
            # 估算买盘量 (价格上涨时的成交量)
            df['estimated_bid_volume'] = np.where(price_change > 0, volume, volume * 0.3)
            df['estimated_ask_volume'] = np.where(price_change < 0, volume, volume * 0.3)
            
            total_est = df['estimated_bid_volume'] + df['estimated_ask_volume']
            df['order_imbalance'] = (df['estimated_bid_volume'] - df['estimated_ask_volume']) / total_est
        
        # 交易强度
        df['trade_intensity'] = df['volume'] / df['volume'].rolling(window=20).mean()
        
        # 大单比率 (估算)
        avg_volume = df['volume'].rolling(window=20).mean()
        std_volume = df['volume'].rolling(window=20).std()
        df['large_order_ratio'] = (df['volume'] > (avg_volume + 2 * std_volume)).astype(float)
        df['large_order_ratio'] = df['large_order_ratio'].rolling(window=5).mean()
        
        return df
    
    def _calculate_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算价格特征"""
        close = df['close']
        
        # 收益率
        df['returns'] = close.pct_change()
        df['log_returns'] = np.log(close / close.shift(1))
        
        # 实际波动率 (日内已实现波动率)
        if all(col in df.columns for col in ['high', 'low', 'open']):
            # 使用Garman-Klass估计
            log_hl = np.log(df['high'] / df['low']) ** 2
            log_co = np.log(df['close'] / df['open']) ** 2
            df['realized_volatility'] = np.sqrt(0.5 * log_hl - (2 * np.log(2) - 1) * log_co)
        else:
            df['realized_volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # 收益率偏度
        df['returns_skewness'] = df['returns'].rolling(window=20).skew()
        
        # 收益率峰度
        df['returns_kurtosis'] = df['returns'].rolling(window=20).kurt()
        
        # 最大回撤
        rolling_max = close.rolling(window=20).max()
        df['drawdown'] = (close - rolling_max) / rolling_max
        df['max_drawdown_20'] = df['drawdown'].rolling(window=20).min()
        
        return df
    
    def _calculate_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算趋势特征"""
        close = df['close']
        
        # 趋势强度 (使用ADX思想简化版)
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        tr = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - close.shift(1)),
            abs(df['low'] - close.shift(1))
        ], axis=1).max(axis=1)
        
        plus_di = 100 * plus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean()
        minus_di = 100 * minus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean()
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=14).mean()
        df['trend_strength'] = df['adx'] / 100  # 归一化
        
        # 价格加速度 (二阶导数)
        velocity = close.diff()
        df['price_acceleration'] = velocity.diff()
        
        # 动量持续性
        df['momentum_consistency'] = (
            (close > close.shift(1)).astype(int) +
            (close.shift(1) > close.shift(2)).astype(int) +
            (close.shift(2) > close.shift(3)).astype(int)
        ) / 3
        
        return df
    
    def _calculate_mean_reversion_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算均值回归特征"""
        close = df['close']
        
        # Z分数
        mean_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        df['z_score_20'] = (close - mean_20) / std_20
        
        # 距均线距离
        if 'sma_20' in df.columns:
            df['distance_from_ma'] = (close - df['sma_20']) / df['sma_20'] * 100
        
        # 均值回归强度
        df['mean_reversion_strength'] = -df['z_score_20'] * df['volatility_20'] if 'volatility_20' in df.columns else -df['z_score_20']
        
        # 区间突破后的回归
        high_20 = df['high'].rolling(window=20).max()
        low_20 = df['low'].rolling(window=20).min()
        
        df['breakout_up'] = (close > high_20.shift(1)).astype(int)
        df['breakout_down'] = (close < low_20.shift(1)).astype(int)
        
        return df
    
    def _calculate_liquidity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算流动性特征"""
        close = df['close']
        volume = df['volume']
        
        # Amihud非流动性指标
        returns_abs = df['returns'].abs()
        df['amihud_illiquidity'] = returns_abs / (volume * close) * 1000000
        df['amihud_illiquidity'] = df['amihud_illiquidity'].rolling(window=20).mean()
        
        # 换手率
        if 'market_cap' in df.columns:
            shares_outstanding = df['market_cap'] / close
            df['turnover_rate'] = volume / shares_outstanding * 100
        else:
            # 使用相对换手率
            df['turnover_rate'] = volume / volume.rolling(window=60).mean()
        
        # 流动性冲击
        df['liquidity_shock'] = (df['turnover_rate'] > df['turnover_rate'].quantile(0.95)).astype(int)
        
        # 价格冲击 (价格变动与成交量的关系)
        df['price_impact'] = df['returns'].abs() / np.log(volume)
        
        return df
    
    def _calculate_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算波动率特征"""
        returns = df['returns']
        
        # GARCH类特征 (简化版)
        # EWMA波动率
        df['ewma_volatility_10'] = returns.ewm(span=10).std() * np.sqrt(252)
        df['ewma_volatility_30'] = returns.ewm(span=30).std() * np.sqrt(252)
        
        # 波动率趋势
        df['volatility_trend'] = df['ewma_volatility_10'] / df['ewma_volatility_30'] - 1
        
        # 波动率聚类
        df['high_vol_persistence'] = (
            (returns.abs() > returns.abs().quantile(0.8)).astype(int) +
            (returns.shift(1).abs() > returns.abs().quantile(0.8)).astype(int)
        ) / 2
        
        # Parkinson波动率 (使用高低价)
        log_hl_squared = np.log(df['high'] / df['low']) ** 2
        df['parkinson_volatility'] = np.sqrt(log_hl_squared / (4 * np.log(2))) * np.sqrt(252)
        
        return df
    
    def _calculate_sentiment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算市场情绪特征
        注: 实际应用需要外部情感数据源
        """
        # 基于价格和成交量的情绪代理变量
        
        # 上涨日与下跌日的成交量比
        up_volume = df.loc[df['returns'] > 0, 'volume'].rolling(window=20).mean()
        down_volume = df.loc[df['returns'] < 0, 'volume'].rolling(window=20).mean()
        df['volume_sentiment'] = up_volume / down_volume
        
        # 收盘位置 (收盘在日内区间的位置)
        df['close_position_daily'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # 连续涨跌天数
        df['consecutive_up'] = df['returns'].gt(0).astype(int).groupby(
            (df['returns'].le(0)).cumsum()
        ).cumsum()
        
        df['consecutive_down'] = df['returns'].lt(0).astype(int).groupby(
            (df['returns'].ge(0)).cumsum()
        ).cumsum()
        
        return df
    
    def _calculate_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算时间特征"""
        if 'timestamp' in df.columns:
            ts = pd.to_datetime(df['timestamp'])
            
            # 日内时间 (如果是分钟级数据)
            df['hour'] = ts.dt.hour
            df['minute'] = ts.dt.minute
            df['day_of_week'] = ts.dt.dayofweek
            df['day_of_month'] = ts.dt.day
            df['month'] = ts.dt.month
            
            # 是否月初/月末
            df['is_month_start'] = ts.dt.is_month_start.astype(int)
            df['is_month_end'] = ts.dt.is_month_end.astype(int)
            
            # 是否周一/周五
            df['is_monday'] = (ts.dt.dayofweek == 0).astype(int)
            df['is_friday'] = (ts.dt.dayofweek == 4).astype(int)
        
        return df
    
    def get_alpha_feature_names(self) -> List[str]:
        """获取所有Alpha因子名称"""
        return [
            # 订单流
            'order_imbalance', 'buying_pressure', 'selling_pressure',
            'estimated_bid_volume', 'estimated_ask_volume',
            'trade_intensity', 'large_order_ratio',
            
            # 价格
            'returns', 'log_returns', 'realized_volatility',
            'returns_skewness', 'returns_kurtosis',
            'drawdown', 'max_drawdown_20',
            
            # 趋势
            'adx', 'trend_strength', 'price_acceleration', 'momentum_consistency',
            
            # 均值回归
            'z_score_20', 'distance_from_ma', 'mean_reversion_strength',
            'breakout_up', 'breakout_down',
            
            # 流动性
            'amihud_illiquidity', 'turnover_rate', 'liquidity_shock', 'price_impact',
            
            # 波动率
            'ewma_volatility_10', 'ewma_volatility_30', 'volatility_trend',
            'high_vol_persistence', 'parkinson_volatility',
            
            # 情绪
            'volume_sentiment', 'close_position_daily',
            'consecutive_up', 'consecutive_down',
            
            # 时间
            'hour', 'minute', 'day_of_week', 'day_of_month', 'month',
            'is_month_start', 'is_month_end', 'is_monday', 'is_friday'
        ]


# 使用示例
if __name__ == "__main__":
    from technical import TechnicalIndicatorCalculator
    
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
    
    # 先计算技术指标
    tech_calc = TechnicalIndicatorCalculator()
    df = tech_calc.calculate_all(df)
    
    # 再计算Alpha因子
    alpha_calc = AlphaFactorCalculator()
    result = alpha_calc.calculate_all(df)
    
    print(f"\n总特征数: {len(result.columns)}")
    print(f"技术指标: {len(tech_calc.get_feature_names())} 个")
    print(f"Alpha因子: {len(alpha_calc.get_alpha_feature_names())} 个")
    
    # 显示部分Alpha因子
    alpha_cols = alpha_calc.get_alpha_feature_names()[:10]
    print("\nAlpha因子样例:")
    print(result[['timestamp', 'close'] + alpha_cols].tail())
