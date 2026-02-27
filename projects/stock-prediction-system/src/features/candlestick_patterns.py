"""
股价预测系统 - K线形态识别模块
识别单根K线和K线组合形态
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CandlestickPattern(Enum):
    """K线形态枚举"""
    # 单根K线
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    DOJI = "doji"
    SPINNING_TOP = "spinning_top"
    MARUBOZU = "marubozu"
    
    # 双根K线
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    HARAMI_BULLISH = "harami_bullish"
    HARAMI_BEARISH = "harami_bearish"
    PIERCING = "piercing"
    DARK_CLOUD_COVER = "dark_cloud_cover"
    
    # 三根K线
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"


@dataclass
class CandlePattern:
    """K线形态"""
    name: str
    type: str  # 'bullish' 或 'bearish'
    confidence: float
    position: int  # 形态结束的索引位置


class CandlestickRecognizer:
    """K线形态识别器"""
    
    def __init__(self, body_threshold: float = 0.01, 
                 shadow_threshold: float = 0.02):
        """
        Args:
            body_threshold: 实体阈值 (%)
            shadow_threshold: 影线阈值 (%)
        """
        self.body_threshold = body_threshold
        self.shadow_threshold = shadow_threshold
    
    def detect_all_patterns(self, df: pd.DataFrame) -> List[CandlePattern]:
        """
        检测所有K线形态
        
        Returns:
            List of CandlePattern objects
        """
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        # 单根K线形态
        for i in range(len(df)):
            pattern = self._detect_single_candle(df, i)
            if pattern:
                patterns.append(pattern)
        
        # 双根K线形态
        for i in range(1, len(df)):
            pattern = self._detect_double_candle(df, i)
            if pattern:
                patterns.append(pattern)
        
        # 三根K线形态
        for i in range(2, len(df)):
            pattern = self._detect_triple_candle(df, i)
            if pattern:
                patterns.append(pattern)
        
        # 只保留最近的10个形态
        patterns = sorted(patterns, key=lambda x: x.position, reverse=True)[:10]
        
        logger.info(f"Detected {len(patterns)} candlestick patterns")
        return patterns
    
    def _detect_single_candle(self, df: pd.DataFrame, idx: int) -> Optional[CandlePattern]:
        """检测单根K线形态"""
        if idx >= len(df):
            return None
        
        row = df.iloc[idx]
        open_p = row['open']
        high = row['high']
        low = row['low']
        close = row['close']
        
        body = abs(close - open_p)
        upper_shadow = high - max(open_p, close)
        lower_shadow = min(open_p, close) - low
        total_range = high - low
        
        if total_range == 0:
            return None
        
        # 锤子线 (Hammer) - 底部反转
        if lower_shadow > body * 2 and upper_shadow < body * 0.5 and close > open_p:
            # 需要确认是在下跌趋势后
            if idx > 0 and close < df['close'].iloc[max(0, idx-5):idx].mean() * 0.98:
                return CandlePattern(
                    name="Hammer",
                    type="bullish",
                    confidence=0.7,
                    position=idx
                )
        
        # 流星线 (Shooting Star) - 顶部反转
        if upper_shadow > body * 2 and lower_shadow < body * 0.5 and close < open_p:
            if idx > 0 and close > df['close'].iloc[max(0, idx-5):idx].mean() * 1.02:
                return CandlePattern(
                    name="Shooting Star",
                    type="bearish",
                    confidence=0.7,
                    position=idx
                )
        
        # 十字星 (Doji)
        if body <= total_range * 0.05:
            return CandlePattern(
                name="Doji",
                type="neutral",
                confidence=0.5,
                position=idx
            )
        
        return None
    
    def _detect_double_candle(self, df: pd.DataFrame, idx: int) -> Optional[CandlePattern]:
        """检测双根K线形态"""
        if idx < 1 or idx >= len(df):
            return None
        
        prev = df.iloc[idx-1]
        curr = df.iloc[idx]
        
        # 看涨吞没 (Bullish Engulfing)
        if (prev['close'] < prev['open'] and  # 第一根阴线
            curr['close'] > curr['open'] and   # 第二根阳线
            curr['open'] < prev['close'] and  # 阳线开盘价低于阴线收盘价
            curr['close'] > prev['open']):    # 阳线收盘价高于阴线开盘价
            return CandlePattern(
                name="Bullish Engulfing",
                type="bullish",
                confidence=0.75,
                position=idx
            )
        
        # 看跌吞没 (Bearish Engulfing)
        if (prev['close'] > prev['open'] and  # 第一根阳线
            curr['close'] < curr['open'] and   # 第二根阴线
            curr['open'] > prev['close'] and  # 阴线开盘价高于阳线收盘价
            curr['close'] < prev['open']):    # 阴线收盘价低于阳线开盘价
            return CandlePattern(
                name="Bearish Engulfing",
                type="bearish",
                confidence=0.75,
                position=idx
            )
        
        # 刺透形态 (Piercing) - 看涨
        if (prev['close'] < prev['open'] and  # 第一根阴线
            curr['close'] > curr['open'] and   # 第二根阳线
            curr['open'] < prev['low'] and     # 跳空低开
            curr['close'] > (prev['open'] + prev['close']) / 2):  # 收盘在前实体中点之上
            return CandlePattern(
                name="Piercing Pattern",
                type="bullish",
                confidence=0.7,
                position=idx
            )
        
        # 乌云盖顶 (Dark Cloud Cover) - 看跌
        if (prev['close'] > prev['open'] and  # 第一根阳线
            curr['close'] < curr['open'] and   # 第二根阴线
            curr['open'] > prev['high'] and    # 跳空高开
            curr['close'] < (prev['open'] + prev['close']) / 2):  # 收盘在前实体中点之下
            return CandlePattern(
                name="Dark Cloud Cover",
                type="bearish",
                confidence=0.7,
                position=idx
            )
        
        return None
    
    def _detect_triple_candle(self, df: pd.DataFrame, idx: int) -> Optional[CandlePattern]:
        """检测三根K线形态"""
        if idx < 2 or idx >= len(df):
            return None
        
        first = df.iloc[idx-2]
        second = df.iloc[idx-1]
        third = df.iloc[idx]
        
        # 启明星 (Morning Star) - 看涨
        if (first['close'] < first['open'] and  # 第一根大阴线
            abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.3 and  # 第二根小实体
            third['close'] > third['open'] and   # 第三根阳线
            third['close'] > (first['open'] + first['close']) / 2):  # 深入第一根实体
            return CandlePattern(
                name="Morning Star",
                type="bullish",
                confidence=0.8,
                position=idx
            )
        
        # 黄昏星 (Evening Star) - 看跌
        if (first['close'] > first['open'] and  # 第一根大阳线
            abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.3 and  # 第二根小实体
            third['close'] < third['open'] and   # 第三根阴线
            third['close'] < (first['open'] + first['close']) / 2):  # 深入第一根实体
            return CandlePattern(
                name="Evening Star",
                type="bearish",
                confidence=0.8,
                position=idx
            )
        
        # 三白兵 (Three White Soldiers) - 看涨
        if (first['close'] > first['open'] and
            second['close'] > second['open'] and
            third['close'] > third['open'] and
            third['close'] > second['close'] > first['close'] and  # 依次上升
            abs(second['open'] - first['close']) < abs(first['close'] - first['open']) * 0.5):  # 小缺口
            return CandlePattern(
                name="Three White Soldiers",
                type="bullish",
                confidence=0.75,
                position=idx
            )
        
        # 三乌鸦 (Three Black Crows) - 看跌
        if (first['close'] < first['open'] and
            second['close'] < second['open'] and
            third['close'] < third['open'] and
            third['close'] < second['close'] < first['close'] and  # 依次下降
            abs(second['open'] - first['close']) < abs(first['close'] - first['open']) * 0.5):  # 小缺口
            return CandlePattern(
                name="Three Black Crows",
                type="bearish",
                confidence=0.75,
                position=idx
            )
        
        return None
    
    def get_signal(self, patterns: List[CandlePattern]) -> Dict:
        """
        基于K线形态生成信号
        """
        if not patterns:
            return {'signal': 'hold', 'confidence': 0}
        
        # 统计最近形态
        bullish_count = sum(1 for p in patterns if p.type == 'bullish')
        bearish_count = sum(1 for p in patterns if p.type == 'bearish')
        
        if bullish_count > bearish_count:
            signal = 'buy'
            confidence = min(bullish_count / len(patterns) * 1.5, 1.0)
        elif bearish_count > bullish_count:
            signal = 'sell'
            confidence = min(bearish_count / len(patterns) * 1.5, 1.0)
        else:
            signal = 'hold'
            confidence = 0.5
        
        return {
            'signal': signal,
            'confidence': confidence,
            'patterns': [p.name for p in patterns[:3]]
        }


# 便捷函数
def recognize_candlestick_patterns(df: pd.DataFrame) -> List[CandlePattern]:
    """便捷函数：识别K线形态"""
    recognizer = CandlestickRecognizer()
    return recognizer.detect_all_patterns(df)


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=100)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 识别K线形态
        recognizer = CandlestickRecognizer()
        patterns = recognizer.detect_all_patterns(df)
        
        print(f"\nDetected {len(patterns)} candlestick patterns:")
        for p in patterns[:5]:
            print(f"  {p.name} ({p.type}): confidence={p.confidence:.2f}")
        
        # 信号
        signal = recognizer.get_signal(patterns)
        print(f"\nSignal: {signal}")
