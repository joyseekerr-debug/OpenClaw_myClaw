# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第3-4小时: 高级特征工程与多模型集成测试
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("24-Hour Optimization Task - Hour 3-4")
print("Advanced Features & Model Ensemble")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Load data
print("[1/5] Loading data...")
df = pd.read_csv('data/historical_2y.csv', index_col='timestamp', parse_dates=True)

# 2. Multi-timeframe analysis
print("\n[2/5] Multi-timeframe analysis...")
from features.multi_timeframe import MultiTimeframeAnalyzer

# Create multiple timeframes
df_1d = df
df_1w = df.resample('1W').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()

data_dict = {'1d': df_1d, '1w': df_1w}

analyzer = MultiTimeframeAnalyzer()
analyses = analyzer.analyze_all_timeframes(data_dict)

print(f"  Analyzed {len(analyses)} timeframes:")
for tf, analysis in analyses.items():
    print(f"    {tf}: trend={analysis.trend}, signal={analysis.signal}")

# 3. Pattern detection
print("\n[3/5] Pattern detection...")
from features.chart_patterns import ChartPatternRecognizer
from features.candlestick_patterns import CandlestickRecognizer

chart_recognizer = ChartPatternRecognizer()
candle_recognizer = CandlestickRecognizer()

chart_patterns = chart_recognizer.detect_all_patterns(df)
candle_patterns = candle_recognizer.detect_all_patterns(df)

print(f"  Chart patterns: {len(chart_patterns)}")
print(f"  Candlestick patterns: {len(candle_patterns)}")

if chart_patterns:
    print("  Top patterns:")
    for p in chart_patterns[:3]:
        print(f"    - {p.name}: {p.direction}, conf={p.confidence:.2f}")

# 4. Support/Resistance levels
print("\n[4/5] Support/Resistance analysis...")
from features.support_resistance import SupportResistanceDetector

sr_detector = SupportResistanceDetector()
levels = sr_detector.detect_levels(df)

print(f"  Support levels: {len(levels['support'])}")
print(f"  Resistance levels: {len(levels['resistance'])}")

if levels['support']:
    nearest_support = levels['support'][0]
    print(f"  Nearest support: {nearest_support.price:.2f} (strength: {nearest_support.strength:.2f})")

if levels['resistance']:
    nearest_resistance = levels['resistance'][0]
    print(f"  Nearest resistance: {nearest_resistance.price:.2f} (strength: {nearest_resistance.strength:.2f})")

# 5. Model ensemble test
print("\n[5/5] Model ensemble test...")
from ensemble.model_ensemble import ModelEnsemble, ModelPrediction

# Create mock predictions from different models
mock_predictions = [
    ModelPrediction('PriceAction', '1d', 0.35, 0.65, 'down', 0.6, 0.3),
    ModelPrediction('SupportResistance', '1d', 0.4, 0.6, 'down', 0.5, 0.2),
    ModelPrediction('ChartPattern', '1d', 0.3, 0.7, 'down', 0.7, 0.3),
    ModelPrediction('Candlestick', '1d', 0.45, 0.55, 'down', 0.4, 0.2),
]

ensemble = ModelEnsemble()
result = ensemble.predict(mock_predictions)

print(f"  Ensemble prediction: {result.prediction}")
print(f"  Up probability: {result.up_probability:.2f}")
print(f"  Down probability: {result.down_probability:.2f}")
print(f"  Confidence: {result.confidence:.2f}")
print(f"  Consensus: {result.consensus_level:.2f}")

recommendation = ensemble.get_recommendation(result)
print(f"  Recommendation: {recommendation}")

print("\n" + "=" * 70)
print("Hour 3-4 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
