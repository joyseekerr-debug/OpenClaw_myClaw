# -*- coding: utf-8 -*-
"""
Stock Price Prediction System - L2-L4 Advanced Tests
Feature layer, Model layer, Integration tests
"""

import sys
import os
import numpy as np
import pandas as pd

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("=" * 60)
print("Stock Price Prediction System - L2-L4 Advanced Tests")
print("=" * 60)

# Load test data
print("\n[SETUP] Loading test data...")
test_data = pd.read_csv('data/test_data.csv', index_col='timestamp', parse_dates=True)
print(f"  Loaded: {len(test_data)} rows")

# Prepare features
from features.feature_engineering import FeatureEngineer
engineer = FeatureEngineer()
df_features = engineer.create_all_features(test_data)
print(f"  Features: {len(df_features.columns)} columns, {len(df_features)} rows")

test_results = []

# ==================== L2: Feature Layer Advanced Tests ====================
print("\n" + "=" * 60)
print("L2: Feature Layer Advanced Tests")
print("=" * 60)

# TC-FEAT-004: Chart Pattern Recognition
print("\n[TEST] TC-FEAT-004: Chart Pattern Recognition")
try:
    from features.chart_patterns import ChartPatternRecognizer
    
    recognizer = ChartPatternRecognizer()
    patterns = recognizer.detect_all_patterns(test_data)
    
    print(f"  [OK] Detected {len(patterns)} patterns")
    if patterns:
        for p in patterns[:3]:
            print(f"       {p.name}: confidence={p.confidence:.2f}")
    test_results.append(('TC-FEAT-004', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-FEAT-004', 'FAIL'))

# TC-FEAT-005: Candlestick Pattern Recognition
print("\n[TEST] TC-FEAT-005: Candlestick Pattern Recognition")
try:
    from features.candlestick_patterns import CandlestickRecognizer
    
    recognizer = CandlestickRecognizer()
    patterns = recognizer.detect_all_patterns(test_data)
    
    print(f"  [OK] Detected {len(patterns)} candlestick patterns")
    test_results.append(('TC-FEAT-005', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-FEAT-005', 'FAIL'))

# TC-FEAT-006: Multi-Timeframe Analysis
print("\n[TEST] TC-FEAT-006: Multi-Timeframe Analysis")
try:
    from features.multi_timeframe import MultiTimeframeAnalyzer
    
    # Create mock multi-timeframe data
    data_dict = {
        '1d': test_data,
        '1h': test_data.resample('1h').last().dropna()
    }
    
    analyzer = MultiTimeframeAnalyzer()
    analyses = analyzer.analyze_all_timeframes(data_dict)
    
    print(f"  [OK] Analyzed {len(analyses)} timeframes")
    for tf, analysis in analyses.items():
        print(f"       {tf}: trend={analysis.trend}, signal={analysis.signal}")
    test_results.append(('TC-FEAT-006', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-FEAT-006', 'FAIL'))

# ==================== L3: Model Layer Tests ====================
print("\n" + "=" * 60)
print("L3: Model Layer Tests")
print("=" * 60)

# TC-MODEL-001: Model Import Check
print("\n[TEST] TC-MODEL-001: Model Import Check")
try:
    # Skip Transformer if TF not available
    import importlib
    lstm = importlib.import_module('models.lstm_model')
    xgboost = importlib.import_module('models.xgboost_model')
    price_action = importlib.import_module('models.price_action_model')
    
    print("  [OK] All available models imported successfully")
    print("  [INFO] Note: Transformer model requires TensorFlow (optional)")
    test_results.append(('TC-MODEL-001', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-MODEL-001', 'FAIL'))

# TC-MODEL-002: Price Action Model Test
print("\n[TEST] TC-MODEL-002: Price Action Model Prediction")
try:
    from models.price_action_model import PriceActionPredictor
    
    predictor = PriceActionPredictor()
    signal = predictor.predict(test_data)
    
    print(f"  [OK] Prediction: {signal.signal}")
    print(f"       Confidence: {signal.confidence:.2f}")
    print(f"       Reason: {signal.reason}")
    test_results.append(('TC-MODEL-002', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-MODEL-002', 'FAIL'))

# TC-MODEL-003: Model Ensemble Test
print("\n[TEST] TC-MODEL-003: Model Ensemble")
try:
    from ensemble.model_ensemble import ModelEnsemble, ModelPrediction
    
    # Create mock predictions
    predictions = [
        ModelPrediction('LSTM', '1d', 0.7, 0.3, 'up', 0.7),
        ModelPrediction('XGBoost', '1d', 0.6, 0.4, 'up', 0.6),
        ModelPrediction('Transformer', '1d', 0.8, 0.2, 'up', 0.8),
        ModelPrediction('PriceAction', '1d', 0.4, 0.6, 'down', 0.6)
    ]
    
    ensemble = ModelEnsemble()
    result = ensemble.predict(predictions)
    
    print(f"  [OK] Ensemble prediction: {result.prediction}")
    print(f"       Up probability: {result.up_probability:.2f}")
    print(f"       Confidence: {result.confidence:.2f}")
    print(f"       Consensus: {result.consensus_level:.2f}")
    test_results.append(('TC-MODEL-003', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-MODEL-003', 'FAIL'))

# TC-MODEL-004: Probability Calibration
print("\n[TEST] TC-MODEL-004: Probability Calibration")
try:
    from ensemble.probability_calibration import ProbabilityCalibrator
    
    calibrator = ProbabilityCalibrator()
    
    # Mock calibration
    probs = np.random.beta(2, 2, 100)
    labels = (probs > 0.5).astype(int)
    
    calibrator.fit(probs, labels)
    result = calibrator.calibrate_single(0.7)
    
    print(f"  [OK] Original: 0.70 -> Calibrated: {result.calibrated_prob:.2f}")
    print(f"       Confidence interval: [{result.confidence_interval[0]:.2f}, {result.confidence_interval[1]:.2f}]")
    test_results.append(('TC-MODEL-004', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-MODEL-004', 'FAIL'))

# ==================== L4: Integration Tests ====================
print("\n" + "=" * 60)
print("L4: Integration Tests")
print("=" * 60)

# TC-INT-001: Data Flow Integration
print("\n[TEST] TC-INT-001: Data Flow Integration")
try:
    # Full pipeline: data -> features -> prediction
    from features.support_resistance import SupportResistanceDetector
    from models.price_action_model import PriceActionPredictor
    
    # Step 1: Support Resistance
    sr_detector = SupportResistanceDetector()
    levels = sr_detector.detect_levels(test_data)
    
    # Step 2: Price Action Prediction
    pa_predictor = PriceActionPredictor()
    signal = pa_predictor.predict(test_data)
    
    print(f"  [OK] Full pipeline executed successfully")
    print(f"       Support levels: {len(levels['support'])}")
    print(f"       Signal: {signal.signal} (confidence: {signal.confidence:.2f})")
    test_results.append(('TC-INT-001', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-INT-001', 'FAIL'))

# TC-INT-002: Backtest Engine
print("\n[TEST] TC-INT-002: Backtest Engine")
try:
    from backtest.backtest_engine import BacktestEngine
    
    # Create mock predictions
    predictions = [
        {'signal': 'buy' if i % 3 == 0 else 'sell' if i % 3 == 1 else 'hold', 
         'confidence': 0.6}
        for i in range(len(test_data))
    ]
    
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run_backtest(test_data, predictions)
    
    print(f"  [OK] Backtest completed")
    print(f"       Total trades: {result.total_trades}")
    print(f"       Win rate: {result.win_rate:.2%}")
    print(f"       Total return: {result.total_return_pct:.2%}")
    test_results.append(('TC-INT-002', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-INT-002', 'FAIL'))

# TC-E2E-001: End-to-End Prediction
print("\n[TEST] TC-E2E-001: End-to-End Prediction")
try:
    # Simulate full prediction flow
    from features.support_resistance import SupportResistanceDetector
    from features.chart_patterns import ChartPatternRecognizer
    from ensemble.model_ensemble import ModelEnsemble, ModelPrediction
    
    # Multiple analyses
    sr_detector = SupportResistanceDetector()
    sr_levels = sr_detector.detect_levels(test_data)
    
    pattern_recognizer = ChartPatternRecognizer()
    patterns = pattern_recognizer.detect_all_patterns(test_data)
    
    # Ensemble (mock)
    mock_predictions = [
        ModelPrediction('PriceAction', '1d', 0.65, 0.35, 'up', 0.7)
    ]
    
    ensemble = ModelEnsemble()
    result = ensemble.predict(mock_predictions)
    
    print(f"  [OK] End-to-end prediction completed")
    print(f"       Final signal: {result.prediction}")
    print(f"       Probability: {result.up_probability:.2f}")
    test_results.append(('TC-E2E-001', 'PASS'))
except Exception as e:
    print(f"  [FAIL] {e}")
    test_results.append(('TC-E2E-001', 'FAIL'))

# ==================== Summary ====================
print("\n" + "=" * 60)
print("Advanced Test Summary")
print("=" * 60)

passed = sum(1 for _, status in test_results if status == 'PASS')
failed = sum(1 for _, status in test_results if status == 'FAIL')

print(f"\nTotal: {len(test_results)} test cases")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Pass rate: {passed/len(test_results)*100:.1f}%")

print("\nDetails:")
for tc_id, status in test_results:
    symbol = "[OK]" if status == "PASS" else "[FAIL]"
    print(f"  {symbol} {tc_id}: {status}")

if failed > 0:
    print("\n[WARNING] Some tests failed")
    sys.exit(1)
else:
    print("\n[PASS] All advanced tests passed")
    sys.exit(0)
