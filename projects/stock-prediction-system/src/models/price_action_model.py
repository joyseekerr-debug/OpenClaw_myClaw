"""
股价预测系统 - 价格行为预测模型
基于支撑阻力、形态识别、趋势分析的规则+统计模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入支持阻力检测
try:
    from features.support_resistance import SupportResistanceDetector, Level
    from features.chart_patterns import ChartPatternRecognizer, Pattern
    from features.candlestick_patterns import CandlestickRecognizer, CandlePattern
except ImportError:
    # 如果相对导入失败，使用绝对导入
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from features.support_resistance import SupportResistanceDetector, Level
    from features.chart_patterns import ChartPatternRecognizer, Pattern
    from features.candlestick_patterns import CandlestickRecognizer, CandlePattern


@dataclass
class PriceActionSignal:
    """价格行为信号"""
    signal: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0-1
    reason: str  # 信号原因
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


class PriceActionPredictor:
    """价格行为预测器"""
    
    def __init__(self,
                 sr_lookback: int = 100,
                 pattern_confidence_threshold: float = 0.6,
                 min_risk_reward: float = 1.5):
        """
        Args:
            sr_lookback: 支撑阻力回看周期
            pattern_confidence_threshold: 形态置信度阈值
            min_risk_reward: 最小风险收益比
        """
        self.sr_detector = SupportResistanceDetector(lookback=sr_lookback)
        self.pattern_recognizer = ChartPatternRecognizer()
        self.candle_recognizer = CandlestickRecognizer()
        
        self.pattern_threshold = pattern_confidence_threshold
        self.min_risk_reward = min_risk_reward
    
    def predict(self, df: pd.DataFrame) -> PriceActionSignal:
        """
        基于价格行为生成预测
        
        综合评估：
        1. 支撑阻力位置
        2. 图表形态
        3. K线形态
        4. 趋势方向
        """
        current_price = df['close'].iloc[-1]
        
        # 1. 支撑阻力分析
        sr_analysis = self._analyze_support_resistance(df, current_price)
        
        # 2. 图表形态分析
        pattern_analysis = self._analyze_patterns(df, current_price)
        
        # 3. K线形态分析
        candle_analysis = self._analyze_candlestick(df)
        
        # 4. 趋势分析
        trend_analysis = self._analyze_trend(df)
        
        # 5. 综合信号
        signal = self._combine_signals(
            sr_analysis, pattern_analysis, candle_analysis, trend_analysis,
            current_price
        )
        
        return signal
    
    def _analyze_support_resistance(self, df: pd.DataFrame, 
                                   current_price: float) -> Dict:
        """分析支撑阻力"""
        levels = self.sr_detector.detect_levels(df)
        
        nearest = self.sr_detector.get_nearest_levels(current_price, levels, n=1)
        
        result = {
            'score': 0,
            'direction': 'hold',
            'confidence': 0,
            'nearest_support': None,
            'nearest_resistance': None
        }
        
        if nearest['support']:
            support = nearest['support'][0]
            result['nearest_support'] = support.price
            
            # 距离支撑很近，看涨
            dist_to_support = (current_price - support.price) / current_price
            if dist_to_support < 0.02 and support.strength > 0.5:
                result['score'] += 2
                result['direction'] = 'buy'
                result['confidence'] = support.strength
        
        if nearest['resistance']:
            resistance = nearest['resistance'][0]
            result['nearest_resistance'] = resistance.price
            
            # 距离阻力很近，看跌
            dist_to_resistance = (resistance.price - current_price) / current_price
            if dist_to_resistance < 0.02 and resistance.strength > 0.5:
                result['score'] -= 2
                result['direction'] = 'sell'
                result['confidence'] = resistance.strength
        
        return result
    
    def _analyze_patterns(self, df: pd.DataFrame, 
                         current_price: float) -> Dict:
        """分析图表形态"""
        patterns = self.pattern_recognizer.detect_all_patterns(df)
        
        result = {
            'score': 0,
            'direction': 'hold',
            'confidence': 0,
            'pattern_name': None,
            'target_price': None,
            'stop_loss': None
        }
        
        if not patterns:
            return result
        
        # 取置信度最高的形态
        best_pattern = patterns[0]
        
        if best_pattern.confidence >= self.pattern_threshold:
            result['pattern_name'] = best_pattern.name
            result['target_price'] = best_pattern.target_price
            result['stop_loss'] = best_pattern.stop_loss
            
            if best_pattern.direction == 'bullish':
                result['score'] += 3
                result['direction'] = 'buy'
            elif best_pattern.direction == 'bearish':
                result['score'] -= 3
                result['direction'] = 'sell'
            
            result['confidence'] = best_pattern.confidence
        
        return result
    
    def _analyze_candlestick(self, df: pd.DataFrame) -> Dict:
        """分析K线形态"""
        patterns = self.candle_recognizer.detect_all_patterns(df)
        
        result = {
            'score': 0,
            'direction': 'hold',
            'confidence': 0,
            'patterns': []
        }
        
        if not patterns:
            return result
        
        # 统计最近5个形态
        recent_patterns = patterns[:5]
        
        bullish_count = sum(1 for p in recent_patterns if p.type == 'bullish')
        bearish_count = sum(1 for p in recent_patterns if p.type == 'bearish')
        
        result['patterns'] = [p.name for p in recent_patterns]
        
        if bullish_count > bearish_count:
            result['score'] += 1
            result['direction'] = 'buy'
            result['confidence'] = bullish_count / len(recent_patterns)
        elif bearish_count > bullish_count:
            result['score'] -= 1
            result['direction'] = 'sell'
            result['confidence'] = bearish_count / len(recent_patterns)
        
        return result
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析趋势"""
        # 计算简单趋势指标
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
        current_price = df['close'].iloc[-1]
        
        result = {
            'score': 0,
            'direction': 'hold',
            'trend': 'sideways',
            'trend_strength': 0
        }
        
        if current_price > sma_20 > sma_50:
            result['trend'] = 'up'
            result['trend_strength'] = (current_price - sma_50) / sma_50
            result['score'] += 1
            result['direction'] = 'buy'
        elif current_price < sma_20 < sma_50:
            result['trend'] = 'down'
            result['trend_strength'] = (sma_50 - current_price) / sma_50
            result['score'] -= 1
            result['direction'] = 'sell'
        
        return result
    
    def _combine_signals(self, sr: Dict, pattern: Dict, 
                        candle: Dict, trend: Dict,
                        current_price: float) -> PriceActionSignal:
        """综合所有信号"""
        
        # 加权总分
        total_score = (
            sr.get('score', 0) * 1.5 +      # 支撑阻力权重
            pattern.get('score', 0) * 2.0 +  # 图表形态权重最高
            candle.get('score', 0) * 1.0 +   # K线形态权重
            trend.get('score', 0) * 1.0      # 趋势权重
        )
        
        # 确定方向
        if total_score >= 3:
            signal = 'buy'
        elif total_score <= -3:
            signal = 'sell'
        else:
            signal = 'hold'
        
        # 计算置信度
        confidences = [
            sr.get('confidence', 0),
            pattern.get('confidence', 0),
            candle.get('confidence', 0)
        ]
        avg_confidence = np.mean([c for c in confidences if c > 0]) if any(confidences) else 0.5
        
        # 确定目标价和止损
        target_price = pattern.get('target_price')
        stop_loss = pattern.get('stop_loss')
        
        # 如果没有形态目标，使用支撑阻力
        if target_price is None and signal == 'buy':
            target_price = sr.get('nearest_resistance', current_price * 1.05)
        elif target_price is None and signal == 'sell':
            target_price = sr.get('nearest_support', current_price * 0.95)
        
        if stop_loss is None and signal == 'buy':
            stop_loss = sr.get('nearest_support', current_price * 0.98)
        elif stop_loss is None and signal == 'sell':
            stop_loss = sr.get('nearest_resistance', current_price * 1.02)
        
        # 计算风险收益比
        risk_reward = None
        if target_price and stop_loss:
            if signal == 'buy':
                risk = current_price - stop_loss
                reward = target_price - current_price
            else:
                risk = stop_loss - current_price
                reward = current_price - target_price
            
            if risk > 0:
                risk_reward = reward / risk
        
        # 生成原因
        reasons = []
        if pattern.get('pattern_name'):
            reasons.append(f"{pattern['pattern_name']}")
        if sr.get('nearest_support') and signal == 'buy':
            reasons.append(f"支撑位{sr['nearest_support']:.2f}")
        if sr.get('nearest_resistance') and signal == 'sell':
            reasons.append(f"阻力位{sr['nearest_resistance']:.2f}")
        if trend.get('trend') != 'sideways':
            reasons.append(f"{trend['trend']}趋势")
        
        reason = " + ".join(reasons) if reasons else "综合信号"
        
        # 风险收益比过滤
        if risk_reward and risk_reward < self.min_risk_reward and signal != 'hold':
            signal = 'hold'
            reason += " (风险收益比不足)"
        
        return PriceActionSignal(
            signal=signal,
            confidence=avg_confidence,
            reason=reason,
            target_price=target_price,
            stop_loss=stop_loss,
            risk_reward_ratio=risk_reward
        )
    
    def get_probability(self, df: pd.DataFrame) -> Dict:
        """
        获取涨跌概率
        
        Returns:
            {
                'up_probability': float,
                'down_probability': float,
                'confidence': float
            }
        """
        signal = self.predict(df)
        
        if signal.signal == 'buy':
            up_prob = signal.confidence
            down_prob = 1 - signal.confidence
        elif signal.signal == 'sell':
            up_prob = 1 - signal.confidence
            down_prob = signal.confidence
        else:
            up_prob = 0.5
            down_prob = 0.5
        
        return {
            'up_probability': up_prob,
            'down_probability': down_prob,
            'confidence': signal.confidence,
            'reason': signal.reason
        }


# 便捷函数
def predict_with_price_action(df: pd.DataFrame) -> PriceActionSignal:
    """便捷函数：价格行为预测"""
    predictor = PriceActionPredictor()
    return predictor.predict(df)


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    
    # 加载数据
    data = load_stock_data('1810.HK', ['1d'], days=200)
    df = data.get('1d')
    
    if df is not None and not df.empty:
        # 价格行为预测
        predictor = PriceActionPredictor()
        signal = predictor.predict(df)
        
        print(f"\nPrice Action Prediction:")
        print(f"Signal: {signal.signal}")
        print(f"Confidence: {signal.confidence:.2f}")
        print(f"Reason: {signal.reason}")
        print(f"Target: {signal.target_price}")
        print(f"Stop Loss: {signal.stop_loss}")
        print(f"Risk/Reward: {signal.risk_reward_ratio:.2f}" if signal.risk_reward_ratio else "N/A")
        
        # 概率
        prob = predictor.get_probability(df)
        print(f"\nProbabilities: Up={prob['up_probability']:.2f}, Down={prob['down_probability']:.2f}")
