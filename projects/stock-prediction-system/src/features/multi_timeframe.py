"""
股价预测系统 - 多时间框架分析模块
大周期定方向，小周期定时机
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TimeframeAnalysis:
    """单时间框架分析结果"""
    timeframe: str
    trend: str  # 'up', 'down', 'sideways'
    trend_strength: float  # 0-1
    support: float
    resistance: float
    signal: str  # 'buy', 'sell', 'hold'
    confidence: float


class MultiTimeframeAnalyzer:
    """多时间框架分析器"""
    
    def __init__(self):
        self.timeframe_hierarchy = ['1w', '1d', '4h', '1h', '15m', '5m', '1m']
        self.weights = {
            '1w': 0.05,
            '1d': 0.15,
            '4h': 0.15,
            '1h': 0.20,
            '15m': 0.20,
            '5m': 0.15,
            '1m': 0.10
        }
    
    def analyze_all_timeframes(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, TimeframeAnalysis]:
        """
        分析所有时间框架
        
        Args:
            data_dict: {timeframe: DataFrame}
        
        Returns:
            {timeframe: TimeframeAnalysis}
        """
        results = {}
        
        for tf, df in data_dict.items():
            if df.empty:
                continue
            
            analysis = self._analyze_single_timeframe(df, tf)
            results[tf] = analysis
        
        logger.info(f"Analyzed {len(results)} timeframes")
        return results
    
    def _analyze_single_timeframe(self, df: pd.DataFrame, timeframe: str) -> TimeframeAnalysis:
        """分析单个时间框架"""
        
        # 计算趋势方向
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
        current_price = df['close'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            trend = 'up'
            trend_strength = min((current_price - sma_50) / sma_50 * 10, 1.0)
        elif current_price < sma_20 < sma_50:
            trend = 'down'
            trend_strength = min((sma_50 - current_price) / sma_50 * 10, 1.0)
        else:
            trend = 'sideways'
            trend_strength = 0.3
        
        # 计算支撑阻力
        recent_highs = df['high'].tail(20)
        recent_lows = df['low'].tail(20)
        resistance = recent_highs.max()
        support = recent_lows.min()
        
        # 生成信号
        signal, confidence = self._generate_signal(df, trend)
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            trend_strength=trend_strength,
            support=support,
            resistance=resistance,
            signal=signal,
            confidence=confidence
        )
    
    def _generate_signal(self, df: pd.DataFrame, trend: str) -> Tuple[str, float]:
        """生成交易信号"""
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = (ema_12 - ema_26).iloc[-1]
        
        # 综合判断
        if trend == 'up' and rsi < 70 and macd > 0:
            return 'buy', 0.7
        elif trend == 'down' and rsi > 30 and macd < 0:
            return 'sell', 0.7
        else:
            return 'hold', 0.5
    
    def get_confluence_signal(self, analyses: Dict[str, TimeframeAnalysis]) -> Dict:
        """
        多时间框架共振信号
        
        原则:
        - 大周期(1d/1w)定方向
        - 小周期(1h/15m)定时机
        - 多周期共振时信号最强
        """
        if not analyses:
            return {'signal': 'hold', 'confidence': 0, 'alignment': 0}
        
        # 按权重聚合信号
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        for tf, analysis in analyses.items():
            weight = self.weights.get(tf, 0.1)
            
            if analysis.signal == 'buy':
                bullish_score += weight * analysis.confidence
            elif analysis.signal == 'sell':
                bearish_score += weight * analysis.confidence
            
            total_weight += weight
        
        # 归一化
        if total_weight > 0:
            bullish_score /= total_weight
            bearish_score /= total_weight
        
        # 判断共振
        if bullish_score > bearish_score and bullish_score > 0.6:
            signal = 'buy'
            confidence = bullish_score
            alignment = bullish_score - bearish_score
        elif bearish_score > bullish_score and bearish_score > 0.6:
            signal = 'sell'
            confidence = bearish_score
            alignment = bearish_score - bullish_score
        else:
            signal = 'hold'
            confidence = max(bullish_score, bearish_score)
            alignment = abs(bullish_score - bearish_score)
        
        # 趋势一致性检查
        higher_tf_trend = self._get_higher_tf_trend(analyses)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'alignment': alignment,
            'higher_tf_trend': higher_tf_trend,
            'recommendation': self._generate_recommendation(signal, higher_tf_trend)
        }
    
    def _get_higher_tf_trend(self, analyses: Dict[str, TimeframeAnalysis]) -> str:
        """获取大周期趋势"""
        # 优先使用日线和周线
        for tf in ['1w', '1d']:
            if tf in analyses:
                return analyses[tf].trend
        
        # 如果没有，使用最高可用时间框架
        for tf in self.timeframe_hierarchy:
            if tf in analyses:
                return analyses[tf].trend
        
        return 'sideways'
    
    def _generate_recommendation(self, signal: str, higher_tf_trend: str) -> str:
        """生成交易建议"""
        if signal == 'buy' and higher_tf_trend == 'up':
            return "强烈看涨 - 多周期共振，顺势做多"
        elif signal == 'buy' and higher_tf_trend == 'down':
            return "谨慎看涨 - 小周期反弹，注意趋势背离"
        elif signal == 'sell' and higher_tf_trend == 'down':
            return "强烈看跌 - 多周期共振，顺势做空"
        elif signal == 'sell' and higher_tf_trend == 'up':
            return "谨慎看跌 - 小周期回调，注意趋势背离"
        else:
            return "观望 - 信号不明确，等待更明确的机会"
    
    def check_divergence(self, data_dict: Dict[str, pd.DataFrame]) -> Optional[Dict]:
        """
        检查多时间框架背离
        
        例如：
        - 日线创新高但4小时MACD未创新高 → 顶背离
        - 日线创新低但4小时MACD未创新低 → 底背离
        """
        # 简化实现：检查两个相邻时间框架的趋势差异
        divergence_signals = []
        
        tfs = list(data_dict.keys())
        for i in range(len(tfs) - 1):
            tf1, tf2 = tfs[i], tfs[i+1]
            
            df1 = data_dict[tf1]
            df2 = data_dict[tf2]
            
            if df1.empty or df2.empty:
                continue
            
            # 检查价格趋势
            trend1 = 'up' if df1['close'].iloc[-1] > df1['close'].iloc[-5] else 'down'
            trend2 = 'up' if df2['close'].iloc[-1] > df2['close'].iloc[-5] else 'down'
            
            if trend1 != trend2:
                divergence_signals.append({
                    'timeframes': (tf1, tf2),
                    'type': 'divergence',
                    'description': f"{tf1}趋势与{tf2}不一致"
                })
        
        return divergence_signals[0] if divergence_signals else None


# 便捷函数
def analyze_multi_timeframe(data_dict: Dict[str, pd.DataFrame]) -> Dict:
    """便捷函数：多时间框架分析"""
    analyzer = MultiTimeframeAnalyzer()
    analyses = analyzer.analyze_all_timeframes(data_dict)
    return analyzer.get_confluence_signal(analyses)


if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.append('..')
    from data.data_loader import load_stock_data
    
    # 加载多个时间框架
    data = load_stock_data('1810.HK', ['1d', '1h'], days=100)
    
    if data:
        # 多时间框架分析
        result = analyze_multi_timeframe(data)
        print(f"\nMulti-Timeframe Analysis:")
        print(f"Signal: {result['signal']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Higher TF Trend: {result['higher_tf_trend']}")
        print(f"Recommendation: {result['recommendation']}")
