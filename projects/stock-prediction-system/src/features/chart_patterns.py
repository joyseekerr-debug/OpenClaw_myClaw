"""
股价预测系统 - 图表形态识别模块
识别反转形态和持续形态
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """形态类型"""
    REVERSAL = "reversal"  # 反转形态
    CONTINUATION = "continuation"  # 持续形态


@dataclass
class Pattern:
    """图表形态"""
    name: str
    type: PatternType
    start_idx: int
    end_idx: int
    confidence: float  # 置信度 0-1
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    direction: str = ""  # 'bullish' 或 'bearish'


class ChartPatternRecognizer:
    """图表形态识别器"""
    
    def __init__(self, min_pattern_length: int = 10, max_pattern_length: int = 50):
        """
        Args:
            min_pattern_length: 最小形态长度
            max_pattern_length: 最大形态长度
        """
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length
    
    def detect_all_patterns(self, df: pd.DataFrame) -> List[Pattern]:
        """
        检测所有图表形态
        
        Returns:
            List of Pattern objects
        """
        patterns = []
        
        # 反转形态
        patterns.extend(self._detect_head_and_shoulders(df))
        patterns.extend(self._detect_double_top_bottom(df))
        patterns.extend(self._detect_triangles(df))
        
        # 持续形态
        patterns.extend(self._detect_flags(df))
        patterns.extend(self._detect_rectangles(df))
        
        # 按置信度排序
        patterns = sorted(patterns, key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Detected {len(patterns)} chart patterns")
        return patterns
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> List[Pattern]:
        """检测头肩顶/底形态"""
        patterns = []
        
        if len(df) < 20:
            return patterns
        
        highs = df['high'].values
        lows = df['low'].values
        
        # 找局部高点和低点
        local_highs = self._find_local_extrema(highs, 'high')
        local_lows = self._find_local_extrema(lows, 'low')
        
        # 头肩顶 (Left Shoulder - Head - Right Shoulder)
        for i in range(1, len(local_highs) - 1):
            if i >= len(local_lows) or i+1 >= len(local_lows):
                continue
            
            left_shoulder = local_highs[i-1]
            head = local_highs[i]
            right_shoulder = local_highs[i+1]
            
            # 验证头肩顶条件
            if head[1] > left_shoulder[1] and head[1] > right_shoulder[1]:
                # 肩膀高度相近 (相差不超过10%)
                shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1]
                
                if shoulder_diff < 0.1:
                    # 找到颈线 (两个肩膀之间的低点)
                    neck_line = min(local_lows[i-1][1], local_lows[i][1]) if i < len(local_lows) else min(lows)
                    
                    # 计算目标价
                    head_height = head[1] - neck_line
                    target = neck_line - head_height
                    
                    confidence = 1 - shoulder_diff
                    
                    pattern = Pattern(
                        name="Head and Shoulders",
                        type=PatternType.REVERSAL,
                        start_idx=left_shoulder[0],
                        end_idx=right_shoulder[0],
                        confidence=confidence,
                        target_price=target,
                        stop_loss=head[1] * 1.02,
                        direction='bearish'
                    )
                    patterns.append(pattern)
        
        # 头肩底 (Inverse Head and Shoulders)
        for i in range(1, len(local_lows) - 1):
            if i >= len(local_highs) or i+1 >= len(local_highs):
                continue
            
            left_shoulder = local_lows[i-1]
            head = local_lows[i]
            right_shoulder = local_lows[i+1]
            
            if head[1] < left_shoulder[1] and head[1] < right_shoulder[1]:
                shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1]
                
                if shoulder_diff < 0.1:
                    neck_line = max(local_highs[i-1][1], local_highs[i][1]) if i < len(local_highs) else max(highs)
                    
                    head_depth = neck_line - head[1]
                    target = neck_line + head_depth
                    
                    confidence = 1 - shoulder_diff
                    
                    pattern = Pattern(
                        name="Inverse Head and Shoulders",
                        type=PatternType.REVERSAL,
                        start_idx=left_shoulder[0],
                        end_idx=right_shoulder[0],
                        confidence=confidence,
                        target_price=target,
                        stop_loss=head[1] * 0.98,
                        direction='bullish'
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_double_top_bottom(self, df: pd.DataFrame) -> List[Pattern]:
        """检测双顶/双底形态"""
        patterns = []
        
        if len(df) < 15:
            return patterns
        
        highs = df['high'].values
        lows = df['low'].values
        
        local_highs = self._find_local_extrema(highs, 'high')
        local_lows = self._find_local_extrema(lows, 'low')
        
        # 双顶 (Double Top)
        for i in range(len(local_highs) - 1):
            for j in range(i+1, min(i+5, len(local_highs))):
                peak1 = local_highs[i]
                peak2 = local_highs[j]
                
                # 两个高点相近
                diff = abs(peak1[1] - peak2[1]) / peak1[1]
                
                if diff < 0.05:  # 5%以内
                    # 找中间的低点作为颈线
                    if i < len(local_lows):
                        neck_line = local_lows[i][1]
                    else:
                        neck_line = min(lows[peak1[0]:peak2[0]])
                    
                    height = peak1[1] - neck_line
                    target = neck_line - height
                    
                    confidence = 1 - diff
                    
                    pattern = Pattern(
                        name="Double Top",
                        type=PatternType.REVERSAL,
                        start_idx=peak1[0],
                        end_idx=peak2[0],
                        confidence=confidence,
                        target_price=target,
                        stop_loss=max(peak1[1], peak2[1]) * 1.02,
                        direction='bearish'
                    )
                    patterns.append(pattern)
        
        # 双底 (Double Bottom)
        for i in range(len(local_lows) - 1):
            for j in range(i+1, min(i+5, len(local_lows))):
                bottom1 = local_lows[i]
                bottom2 = local_lows[j]
                
                diff = abs(bottom1[1] - bottom2[1]) / bottom1[1]
                
                if diff < 0.05:
                    if i < len(local_highs):
                        neck_line = local_highs[i][1]
                    else:
                        neck_line = max(highs[bottom1[0]:bottom2[0]])
                    
                    depth = neck_line - bottom1[1]
                    target = neck_line + depth
                    
                    confidence = 1 - diff
                    
                    pattern = Pattern(
                        name="Double Bottom",
                        type=PatternType.REVERSAL,
                        start_idx=bottom1[0],
                        end_idx=bottom2[0],
                        confidence=confidence,
                        target_price=target,
                        stop_loss=min(bottom1[1], bottom2[1]) * 0.98,
                        direction='bullish'
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_triangles(self, df: pd.DataFrame) -> List[Pattern]:
        """检测三角形形态"""
        patterns = []
        
        if len(df) < 20:
            return patterns
        
        window = min(30, len(df) - 1)
        highs = df['high'].values[-window:]
        lows = df['low'].values[-window:]
        
        # 计算趋势线
        x = np.arange(len(highs))
        
        # 上轨 (阻力线)
        slope_high, intercept_high = np.polyfit(x, highs, 1)
        # 下轨 (支撑线)
        slope_low, intercept_low = np.polyfit(x, lows, 1)
        
        # 对称三角形: 上轨下降，下轨上升
        if slope_high < -0.001 and slope_low > 0.001:
            # 收敛程度
            convergence = abs(slope_high) + abs(slope_low)
            
            if convergence > 0.01:  # 足够收敛
                # 突破方向不确定，通常延续原趋势
                # 简化: 假设看涨
                pattern = Pattern(
                    name="Symmetrical Triangle",
                    type=PatternType.CONTINUATION,
                    start_idx=len(df) - window,
                    end_idx=len(df) - 1,
                    confidence=min(convergence * 10, 1.0),
                    direction='bullish'  # 或根据趋势判断
                )
                patterns.append(pattern)
        
        # 上升三角形: 上轨水平，下轨上升
        elif abs(slope_high) < 0.001 and slope_low > 0.001:
            pattern = Pattern(
                name="Ascending Triangle",
                type=PatternType.CONTINUATION,
                start_idx=len(df) - window,
                end_idx=len(df) - 1,
                confidence=0.7,
                direction='bullish'
            )
            patterns.append(pattern)
        
        # 下降三角形: 上轨下降，下轨水平
        elif slope_high < -0.001 and abs(slope_low) < 0.001:
            pattern = Pattern(
                name="Descending Triangle",
                type=PatternType.CONTINUATION,
                start_idx=len(df) - window,
                end_idx=len(df) - 1,
                confidence=0.7,
                direction='bearish'
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_flags(self, df: pd.DataFrame) -> List[Pattern]:
        """检测旗形/三角旗形"""
        patterns = []
        
        if len(df) < 15:
            return patterns
        
        # 简单实现: 检测旗杆后的整理
        window = min(15, len(df) - 1)
        closes = df['close'].values[-window:]
        
        # 计算波动率
        volatility = np.std(np.diff(closes) / closes[:-1])
        
        # 如果波动率较低，可能是整理形态
        if volatility < 0.02:  # 2%以内波动
            pattern = Pattern(
                name="Flag/Pennant",
                type=PatternType.CONTINUATION,
                start_idx=len(df) - window,
                end_idx=len(df) - 1,
                confidence=0.6,
                direction='bullish'  # 假设看涨，实际需要看前面趋势
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_rectangles(self, df: pd.DataFrame) -> List[Pattern]:
        """检测矩形整理"""
        patterns = []
        
        if len(df) < 15:
            return patterns
        
        window = min(20, len(df) - 1)
        highs = df['high'].values[-window:]
        lows = df['low'].values[-window:]
        
        # 检查是否在区间内震荡
        max_high = np.max(highs)
        min_low = np.min(lows)
        range_size = max_high - min_low
        
        # 如果高点和低点都相对集中
        high_cluster = np.std(highs) < range_size * 0.1
        low_cluster = np.std(lows) < range_size * 0.1
        
        if high_cluster and low_cluster and range_size / np.mean(highs) > 0.03:
            pattern = Pattern(
                name="Rectangle",
                type=PatternType.CONTINUATION,
                start_idx=len(df) - window,
                end_idx=len(df) - 1,
                confidence=0.65,
                target_price=max_high + range_size,
                direction='bullish'
            )
            patterns.append(pattern)
        
        return patterns
    
    def _find_local_extrema(self, data: np.ndarray, type: str) -> List[Tuple[int, float]]:
        """找局部极值点"""
        extrema = []
        
        for i in range(2, len(data) - 2):
            if type == 'high':
                if data[i] > data[i-1] and data[i] > data[i-2] and \
                   data[i] > data[i+1] and data[i] > data[i+2]:
                    extrema.append((i, data[i]))
            else:  # low
                if data[i] < data[i-1] and data[i] < data[i-2] and \
                   data[i] < data[i+1] and data[i] < data[i+2]:
                    extrema.append((i, data[i]))
        
        return extrema
    
    def get_trading_signal(self, patterns: List[Pattern]) -> Dict:
        """
        基于形态生成交易信号
        
        Returns:
            {
                'signal': 'buy'/'sell'/'hold',
                'confidence': float,
                'pattern': str,
                'target': float,
                'stop_loss': float
            }
        """
        if not patterns:
            return {'signal': 'hold', 'confidence': 0, 'pattern': None}
        
        # 取置信度最高的形态
        best_pattern = patterns[0]
        
        if best_pattern.direction == 'bullish':
            signal = 'buy'
        elif best_pattern.direction == 'bearish':
            signal = 'sell'
        else:
            signal = 'hold'
        
        return {
            'signal': signal,
            'confidence': best_pattern.confidence,
            'pattern': best_pattern.name,
            'target': best_pattern.target_price,
            'stop_loss': best_pattern.stop_loss
        }


# 便捷函数
def recognize_patterns(df: pd.DataFrame) -> List[Pattern]:
    """便捷函数：识别图表形态"""
    recognizer = ChartPatternRecognizer()
    return recognizer.detect_all_patterns(df)


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=200)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 识别形态
        recognizer = ChartPatternRecognizer()
        patterns = recognizer.detect_all_patterns(df)
        
        print(f"\nDetected {len(patterns)} patterns:")
        for p in patterns[:5]:
            print(f"  {p.name} ({p.type.value}): confidence={p.confidence:.2f}, direction={p.direction}")
        
        # 交易信号
        signal = recognizer.get_trading_signal(patterns)
        print(f"\nTrading Signal: {signal}")
