"""
股价预测系统 - 支撑阻力位自动识别模块
基于价格行为学，自动检测关键支撑阻力水平
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Level:
    """支撑阻力水平"""
    price: float
    strength: float  # 强度 0-1
    touches: int     # 触及次数
    type: str        # 'support' 或 'resistance'
    first_touch: int # 首次触及的索引
    last_touch: int  # 最后触及的索引


class SupportResistanceDetector:
    """支撑阻力检测器"""
    
    def __init__(self, 
                 lookback: int = 100,
                 tolerance: float = 0.02,
                 min_touches: int = 2,
                 strength_threshold: float = 0.3):
        """
        Args:
            lookback: 回看周期数
            tolerance: 价格容忍度 (2% = 0.02)
            min_touches: 最小触及次数
            strength_threshold: 强度阈值
        """
        self.lookback = lookback
        self.tolerance = tolerance
        self.min_touches = min_touches
        self.strength_threshold = strength_threshold
    
    def detect_levels(self, df: pd.DataFrame) -> Dict[str, List[Level]]:
        """
        检测支撑阻力位
        
        Returns:
            {'support': [Level, ...], 'resistance': [Level, ...]}
        """
        if len(df) < self.lookback:
            logger.warning(f"Insufficient data: {len(df)} < {self.lookback}")
            return {'support': [], 'resistance': []}
        
        # 使用最近lookback的数据
        data = df.tail(self.lookback)
        
        # 方法1: 基于枢轴点 (Pivot Points)
        pivot_levels = self._detect_pivot_levels(data)
        
        # 方法2: 基于成交量加权
        volume_levels = self._detect_volume_levels(data)
        
        # 方法3: 基于价格聚类
        cluster_levels = self._detect_cluster_levels(data)
        
        # 合并所有水平
        all_support = []
        all_resistance = []
        
        for level in pivot_levels + volume_levels + cluster_levels:
            if level.type == 'support':
                all_support.append(level)
            else:
                all_resistance.append(level)
        
        # 去重和排序
        support = self._merge_levels(all_support)
        resistance = self._merge_levels(all_resistance)
        
        # 只保留当前价格附近的水平
        current_price = df['close'].iloc[-1]
        support = [s for s in support if s.price < current_price * 1.05]
        resistance = [r for r in resistance if r.price > current_price * 0.95]
        
        logger.info(f"Detected {len(support)} support levels, {len(resistance)} resistance levels")
        
        return {'support': support, 'resistance': resistance}
    
    def _detect_pivot_levels(self, df: pd.DataFrame) -> List[Level]:
        """基于枢轴点检测"""
        levels = []
        
        # 找局部高点 (阻力位候选)
        highs = df['high'].values
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                level = Level(
                    price=highs[i],
                    strength=0.5,
                    touches=1,
                    type='resistance',
                    first_touch=i,
                    last_touch=i
                )
                levels.append(level)
        
        # 找局部低点 (支撑位候选)
        lows = df['low'].values
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                level = Level(
                    price=lows[i],
                    strength=0.5,
                    touches=1,
                    type='support',
                    first_touch=i,
                    last_touch=i
                )
                levels.append(level)
        
        return levels
    
    def _detect_volume_levels(self, df: pd.DataFrame) -> List[Level]:
        """基于成交量加权检测"""
        levels = []
        
        # 高成交量区域的价格水平更重要
        volume = df['volume'].values
        high_volume_threshold = np.percentile(volume, 80)
        
        # 对高成交量K线的收盘价格聚类
        for i, (idx, row) in enumerate(df.iterrows()):
            if row['volume'] > high_volume_threshold:
                # 根据方向判断支撑还是阻力
                if row['close'] > row['open']:  # 阳线
                    level = Level(
                        price=row['close'],
                        strength=0.6,
                        touches=1,
                        type='support',
                        first_touch=i,
                        last_touch=i
                    )
                else:  # 阴线
                    level = Level(
                        price=row['close'],
                        strength=0.6,
                        touches=1,
                        type='resistance',
                        first_touch=i,
                        last_touch=i
                    )
                levels.append(level)
        
        return levels
    
    def _detect_cluster_levels(self, df: pd.DataFrame) -> List[Level]:
        """基于价格聚类检测"""
        levels = []
        
        # 使用高低价进行聚类
        prices = np.concatenate([
            df['high'].values,
            df['low'].values,
            df['close'].values
        ])
        
        # 简单的直方图聚类
        hist, bin_edges = np.histogram(prices, bins=20)
        
        # 高频价格区域
        for i, count in enumerate(hist):
            if count > len(prices) * 0.1:  # 超过10%的价格聚集
                price_level = (bin_edges[i] + bin_edges[i+1]) / 2
                
                # 判断是支撑还是阻力 (相对于当前价格)
                current_price = df['close'].iloc[-1]
                if price_level < current_price:
                    level_type = 'support'
                else:
                    level_type = 'resistance'
                
                level = Level(
                    price=price_level,
                    strength=min(count / len(prices), 1.0),
                    touches=int(count / 3),  # 估算触及次数
                    type=level_type,
                    first_touch=0,
                    last_touch=len(df) - 1
                )
                levels.append(level)
        
        return levels
    
    def _merge_levels(self, levels: List[Level]) -> List[Level]:
        """合并相近的水平"""
        if not levels:
            return []
        
        # 按价格排序
        levels = sorted(levels, key=lambda x: x.price)
        
        merged = []
        current_group = [levels[0]]
        
        for level in levels[1:]:
            # 检查是否与前一个组接近
            avg_price = np.mean([l.price for l in current_group])
            if abs(level.price - avg_price) / avg_price < self.tolerance:
                current_group.append(level)
            else:
                # 合并当前组
                merged.append(self._merge_group(current_group))
                current_group = [level]
        
        # 合并最后一组
        if current_group:
            merged.append(self._merge_group(current_group))
        
        # 过滤低强度水平
        merged = [m for m in merged if m.strength >= self.strength_threshold]
        
        # 按强度排序
        merged = sorted(merged, key=lambda x: x.strength, reverse=True)
        
        # 只保留前10个
        return merged[:10]
    
    def _merge_group(self, levels: List[Level]) -> Level:
        """合并一组水平"""
        avg_price = np.mean([l.price for l in levels])
        total_touches = sum(l.touches for l in levels)
        avg_strength = np.mean([l.strength for l in levels])
        
        # 强度随触及次数增加
        final_strength = min(avg_strength + total_touches * 0.05, 1.0)
        
        return Level(
            price=avg_price,
            strength=final_strength,
            touches=total_touches,
            type=levels[0].type,
            first_touch=min(l.first_touch for l in levels),
            last_touch=max(l.last_touch for l in levels)
        )
    
    def get_nearest_levels(self, current_price: float, 
                          levels: Dict[str, List[Level]],
                          n: int = 3) -> Dict[str, List[Level]]:
        """
        获取最近的支撑阻力位
        
        Args:
            current_price: 当前价格
            levels: 支撑阻力水平字典
            n: 返回数量
        
        Returns:
            {'support': [最近的n个], 'resistance': [最近的n个]}
        """
        result = {'support': [], 'resistance': []}
        
        # 支撑位 (低于当前价格)
        supports = sorted([s for s in levels['support'] if s.price < current_price],
                         key=lambda x: x.price, reverse=True)
        result['support'] = supports[:n]
        
        # 阻力位 (高于当前价格)
        resistances = sorted([r for r in levels['resistance'] if r.price > current_price],
                            key=lambda x: x.price)
        result['resistance'] = resistances[:n]
        
        return result
    
    def calculate_signal(self, df: pd.DataFrame, levels: Dict[str, List[Level]]) -> Dict:
        """
        基于支撑阻力计算交易信号
        
        Returns:
            {
                'signal': 'buy'/'sell'/'hold',
                'confidence': 0-1,
                'nearest_support': float,
                'nearest_resistance': float,
                'position': 'near_support'/'middle'/'near_resistance'
            }
        """
        current_price = df['close'].iloc[-1]
        
        # 获取最近的水平
        nearest = self.get_nearest_levels(current_price, levels, n=1)
        
        nearest_support = nearest['support'][0].price if nearest['support'] else current_price * 0.95
        nearest_resistance = nearest['resistance'][0].price if nearest['resistance'] else current_price * 1.05
        
        # 计算位置
        range_size = nearest_resistance - nearest_support
        if range_size == 0:
            position = 'middle'
        else:
            position_ratio = (current_price - nearest_support) / range_size
            if position_ratio < 0.3:
                position = 'near_support'
            elif position_ratio > 0.7:
                position = 'near_resistance'
            else:
                position = 'middle'
        
        # 生成信号
        if position == 'near_support':
            signal = 'buy'
            confidence = nearest['support'][0].strength if nearest['support'] else 0.5
        elif position == 'near_resistance':
            signal = 'sell'
            confidence = nearest['resistance'][0].strength if nearest['resistance'] else 0.5
        else:
            signal = 'hold'
            confidence = 0.3
        
        return {
            'signal': signal,
            'confidence': confidence,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'position': position,
            'distance_to_support': (current_price - nearest_support) / current_price,
            'distance_to_resistance': (nearest_resistance - current_price) / current_price
        }


# 便捷函数
def detect_support_resistance(df: pd.DataFrame, **kwargs) -> Dict[str, List[Level]]:
    """便捷函数：检测支撑阻力"""
    detector = SupportResistanceDetector(**kwargs)
    return detector.detect_levels(df)


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=200)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 检测支撑阻力
        detector = SupportResistanceDetector(lookback=100)
        levels = detector.detect_levels(df)
        
        current_price = df['close'].iloc[-1]
        print(f"Current Price: {current_price:.2f}")
        print(f"\nSupport Levels:")
        for level in levels['support'][:5]:
            print(f"  {level.price:.2f} (strength: {level.strength:.2f}, touches: {level.touches})")
        
        print(f"\nResistance Levels:")
        for level in levels['resistance'][:5]:
            print(f"  {level.price:.2f} (strength: {level.strength:.2f}, touches: {level.touches})")
        
        # 计算信号
        signal = detector.calculate_signal(df, levels)
        print(f"\nSignal: {signal}")
