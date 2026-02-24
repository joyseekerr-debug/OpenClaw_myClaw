"""
技术指标计算模块
基于 TA-Lib 和自定义实现
支持多时间尺度的技术指标计算
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TechnicalFeatures:
    """技术指标特征集"""
    # 趋势指标
    sma_5: float = 0.0
    sma_10: float = 0.0
    sma_20: float = 0.0
    sma_60: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    
    # MACD
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    
    # RSI
    rsi_6: float = 0.0
    rsi_12: float = 0.0
    rsi_24: float = 0.0
    
    # 布林带
    boll_upper: float = 0.0
    boll_middle: float = 0.0
    boll_lower: float = 0.0
    boll_width: float = 0.0
    boll_position: float = 0.0
    
    # KDJ
    k: float = 0.0
    d: float = 0.0
    j: float = 0.0
    
    # 波动率
    atr_14: float = 0.0
    volatility_20: float = 0.0
    
    # 动量
    momentum_10: float = 0.0
    roc_10: float = 0.0
    
    # 成交量
    volume_ma_5: float = 0.0
    volume_ma_20: float = 0.0
    volume_ratio: float = 0.0
    obv: float = 0.0
    
    # 价格位置
    price_position: float = 0.0  # 价格在近期区间的位置
    distance_to_high: float = 0.0
    distance_to_low: float = 0.0


class TechnicalIndicatorCalculator:
    """技术指标计算器"""
    
    def __init__(self):
        self.talib_available = self._check_talib()
    
    def _check_talib(self) -> bool:
        """检查TA-Lib是否可用"""
        try:
            import talib
            logger.info("✅ TA-Lib 已安装")
            return True
        except ImportError:
            logger.warning("⚠️ TA-Lib 未安装，使用自定义实现")
            return False
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
                columns: ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
            添加了技术指标的DataFrame
        """
        if df.empty:
            logger.warning("输入数据为空")
            return df
        
        result = df.copy()
        
        # 确保列名小写
        result.columns = [c.lower() for c in result.columns]
        
        try:
            # 1. 移动平均线
            result = self._calculate_ma(result)
            
            # 2. MACD
            result = self._calculate_macd(result)
            
            # 3. RSI
            result = self._calculate_rsi(result)
            
            # 4. 布林带
            result = self._calculate_bollinger(result)
            
            # 5. KDJ
            result = self._calculate_kdj(result)
            
            # 6. 波动率指标
            result = self._calculate_volatility(result)
            
            # 7. 动量指标
            result = self._calculate_momentum(result)
            
            # 8. 成交量指标
            result = self._calculate_volume_indicators(result)
            
            # 9. 价格位置
            result = self._calculate_price_position(result)
            
            logger.info(f"✅ 技术指标计算完成，共 {len(result.columns)} 列")
            
        except Exception as e:
            logger.error(f"技术指标计算失败: {e}")
        
        return result
    
    def _calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均线"""
        close = df['close']
        
        # 简单移动平均
        df['sma_5'] = close.rolling(window=5).mean()
        df['sma_10'] = close.rolling(window=10).mean()
        df['sma_20'] = close.rolling(window=20).mean()
        df['sma_60'] = close.rolling(window=60).mean()
        
        # 指数移动平均
        df['ema_12'] = close.ewm(span=12, adjust=False).mean()
        df['ema_26'] = close.ewm(span=26, adjust=False).mean()
        
        # 价格与均线关系
        df['close_above_sma20'] = (close > df['sma_20']).astype(int)
        df['close_above_sma60'] = (close > df['sma_60']).astype(int)
        
        return df
    
    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        close = df['close']
        
        if self.talib_available:
            try:
                import talib
                macd, macd_signal, macd_hist = talib.MACD(
                    close, fastperiod=12, slowperiod=26, signalperiod=9
                )
                df['macd'] = macd
                df['macd_signal'] = macd_signal
                df['macd_hist'] = macd_hist
            except:
                pass
        
        # 自定义实现作为备用
        if 'macd' not in df.columns or df['macd'].isna().all():
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # MACD相关信号
        df['macd_golden_cross'] = ((df['macd'] > df['macd_signal']) & 
                                    (df['macd'].shift(1) <= df['macd_signal'].shift(1))).astype(int)
        df['macd_dead_cross'] = ((df['macd'] < df['macd_signal']) & 
                                  (df['macd'].shift(1) >= df['macd_signal'].shift(1))).astype(int)
        
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算RSI指标"""
        close = df['close']
        
        def calculate_rsi(prices, window=14):
            """自定义RSI计算"""
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        if self.talib_available:
            try:
                import talib
                df['rsi_6'] = talib.RSI(close, timeperiod=6)
                df['rsi_12'] = talib.RSI(close, timeperiod=12)
                df['rsi_24'] = talib.RSI(close, timeperiod=24)
            except:
                pass
        
        # 备用实现
        if 'rsi_6' not in df.columns or df['rsi_6'].isna().all():
            df['rsi_6'] = calculate_rsi(close, 6)
            df['rsi_12'] = calculate_rsi(close, 12)
            df['rsi_24'] = calculate_rsi(close, 24)
        
        # RSI信号
        df['rsi_overbought'] = (df['rsi_12'] > 70).astype(int)
        df['rsi_oversold'] = (df['rsi_12'] < 30).astype(int)
        
        return df
    
    def _calculate_bollinger(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算布林带"""
        close = df['close']
        
        # 计算20日均线和标准差
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        
        df['boll_middle'] = sma_20
        df['boll_upper'] = sma_20 + (std_20 * 2)
        df['boll_lower'] = sma_20 - (std_20 * 2)
        
        # 布林带宽度 (带宽)
        df['boll_width'] = (df['boll_upper'] - df['boll_lower']) / df['boll_middle']
        
        # 价格在布林带中的位置
        df['boll_position'] = (close - df['boll_lower']) / (df['boll_upper'] - df['boll_lower'])
        
        # 布林带相关信号
        df['boll_squeeze'] = (df['boll_width'] < df['boll_width'].rolling(window=20).mean() * 0.8).astype(int)
        df['price_above_boll_upper'] = (close > df['boll_upper']).astype(int)
        df['price_below_boll_lower'] = (close < df['boll_lower']).astype(int)
        
        return df
    
    def _calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ指标"""
        low = df['low']
        high = df['high']
        close = df['close']
        
        # RSV (未成熟随机值)
        period = 9
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        
        # K值 (平滑 RSV)
        df['k'] = rsv.ewm(com=2, adjust=False).mean()
        
        # D值 (平滑 K)
        df['d'] = df['k'].ewm(com=2, adjust=False).mean()
        
        # J值
        df['j'] = 3 * df['k'] - 2 * df['d']
        
        # KDJ信号
        df['kdj_golden_cross'] = ((df['k'] > df['d']) & 
                                   (df['k'].shift(1) <= df['d'].shift(1))).astype(int)
        df['kdj_dead_cross'] = ((df['k'] < df['d']) & 
                                 (df['k'].shift(1) >= df['d'].shift(1))).astype(int)
        
        return df
    
    def _calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算波动率指标"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # ATR (真实波动幅度)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14).mean()
        
        # ATR比率 (相对于价格)
        df['atr_ratio'] = df['atr_14'] / close * 100
        
        # 历史波动率 (20日收益率标准差)
        returns = close.pct_change()
        df['volatility_20'] = returns.rolling(window=20).std() * np.sqrt(252) * 100
        
        # 波动率状态
        df['high_volatility'] = (df['volatility_20'] > df['volatility_20'].rolling(window=60).mean() * 1.5).astype(int)
        
        return df
    
    def _calculate_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算动量指标"""
        close = df['close']
        
        # 价格动量
        df['momentum_10'] = close - close.shift(10)
        
        # 变动率 (ROC)
        df['roc_10'] = (close / close.shift(10) - 1) * 100
        df['roc_20'] = (close / close.shift(20) - 1) * 100
        
        # CCI (商品通道指数)
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=20).mean()
        mean_dev = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        df['cci_20'] = (tp - sma_tp) / (0.015 * mean_dev)
        
        # Williams %R
        highest_high = df['high'].rolling(window=14).max()
        lowest_low = df['low'].rolling(window=14).min()
        df['williams_r'] = (highest_high - close) / (highest_high - lowest_low) * -100
        
        return df
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量指标"""
        volume = df['volume']
        close = df['close']
        
        # 成交量均线
        df['volume_ma_5'] = volume.rolling(window=5).mean()
        df['volume_ma_20'] = volume.rolling(window=20).mean()
        
        # 成交量比率
        df['volume_ratio'] = volume / df['volume_ma_20']
        
        # OBV (能量潮)
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        df['obv'] = obv
        
        # OBV斜率
        df['obv_slope'] = df['obv'].diff(5)
        
        # 量价背离信号
        price_up = close > close.shift(1)
        volume_down = volume < volume.shift(1)
        df['volume_price_divergence'] = (price_up & volume_down).astype(int)
        
        # 放量上涨
        df['volume_price_surge'] = ((close > close.shift(1)) & 
                                     (volume > volume.shift(1) * 1.5)).astype(int)
        
        return df
    
    def _calculate_price_position(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算价格在近期区间的位置"""
        close = df['close']
        
        # 20日区间
        high_20 = df['high'].rolling(window=20).max()
        low_20 = df['low'].rolling(window=20).min()
        
        # 价格在区间中的位置 (0-1)
        df['price_position'] = (close - low_20) / (high_20 - low_20)
        
        # 距离高低点的百分比
        df['distance_to_high'] = (high_20 - close) / high_20 * 100
        df['distance_to_low'] = (close - low_20) / low_20 * 100
        
        # 创近期新高/新低
        df['new_high_20'] = (close == high_20).astype(int)
        df['new_low_20'] = (close == low_20).astype(int)
        
        # 60日区间
        high_60 = df['high'].rolling(window=60).max()
        low_60 = df['low'].rolling(window=60).min()
        df['price_position_60'] = (close - low_60) / (high_60 - low_60)
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """获取所有特征名称"""
        return [
            # 均线
            'sma_5', 'sma_10', 'sma_20', 'sma_60',
            'ema_12', 'ema_26',
            'close_above_sma20', 'close_above_sma60',
            
            # MACD
            'macd', 'macd_signal', 'macd_hist',
            'macd_golden_cross', 'macd_dead_cross',
            
            # RSI
            'rsi_6', 'rsi_12', 'rsi_24',
            'rsi_overbought', 'rsi_oversold',
            
            # 布林带
            'boll_upper', 'boll_middle', 'boll_lower',
            'boll_width', 'boll_position',
            'boll_squeeze', 'price_above_boll_upper', 'price_below_boll_lower',
            
            # KDJ
            'k', 'd', 'j',
            'kdj_golden_cross', 'kdj_dead_cross',
            
            # 波动率
            'atr_14', 'atr_ratio', 'volatility_20', 'high_volatility',
            
            # 动量
            'momentum_10', 'roc_10', 'roc_20', 'cci_20', 'williams_r',
            
            # 成交量
            'volume_ma_5', 'volume_ma_20', 'volume_ratio', 'obv', 'obv_slope',
            'volume_price_divergence', 'volume_price_surge',
            
            # 价格位置
            'price_position', 'distance_to_high', 'distance_to_low',
            'new_high_20', 'new_low_20', 'price_position_60'
        ]


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # 生成模拟股价数据
    base_price = 15.0
    prices = [base_price]
    for i in range(99):
        change = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + change))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * np.random.uniform(0.995, 1.0, 100),
        'high': [p * np.random.uniform(1.0, 1.02) for p in prices],
        'low': [p * np.random.uniform(0.98, 1.0) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # 计算技术指标
    calc = TechnicalIndicatorCalculator()
    result = calc.calculate_all(df)
    
    # 查看结果
    print(f"原始列数: {len(df.columns)}")
    print(f"计算后列数: {len(result.columns)}")
    print(f"\n新增技术指标: {len(calc.get_feature_names())} 个")
    
    # 显示部分结果
    feature_cols = calc.get_feature_names()
    print("\n技术指标样例:")
    print(result[['timestamp', 'close'] + feature_cols[:10]].tail())
