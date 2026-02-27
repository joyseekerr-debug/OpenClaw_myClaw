# -*- coding: utf-8 -*-
"""
Stock Price Prediction System - Test Execution
"""

import sys
import os

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("=" * 60)
print("Stock Price Prediction System - Test Execution")
print("=" * 60)

# ==================== Test Environment Check ====================
print("\n[1/4] Test Environment Check...")

try:
    import pandas as pd
    print(f"  [OK] pandas {pd.__version__}")
except ImportError as e:
    print(f"  [FAIL] pandas: {e}")
    sys.exit(1)

try:
    import numpy as np
    print(f"  [OK] numpy {np.__version__}")
except ImportError as e:
    print(f"  [FAIL] numpy: {e}")
    sys.exit(1)

try:
    import requests
    print(f"  [OK] requests {requests.__version__}")
except ImportError as e:
    print(f"  [WARN] requests: {e}")

print("\n  [OK] Test environment ready")

# ==================== Test Data Preparation ====================
print("\n[2/4] Test Data Preparation...")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate mock stock data
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

# Generate random walk price
price = 20
prices = []
for _ in range(100):
    price = price * (1 + np.random.normal(0, 0.02))
    prices.append(price)

# Build OHLCV data
test_data = pd.DataFrame({
    'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
    'high': [p * (1 + abs(np.random.normal(0, 0.015))) for p in prices],
    'low': [p * (1 - abs(np.random.normal(0, 0.015))) for p in prices],
    'close': prices,
    'volume': np.random.randint(1000000, 5000000, 100)
}, index=dates)

test_data.index.name = 'timestamp'
test_data['symbol'] = 'TEST.HK'
test_data['timeframe'] = '1d'

# Save test data
test_data.to_csv('data/test_data.csv')
print(f"  [OK] Test data generated: data/test_data.csv")
print(f"       Records: {len(test_data)}")
print(f"       Date range: {test_data.index[0]} to {test_data.index[-1]}")

# ==================== Data Layer Test (L1) ====================
print("\n[3/4] L1 Unit Test - Data Layer...")

test_results = []

# TC-DATA-001: Data Loader Import Test
try:
    from data.data_loader import DataLoader, load_stock_data
    print("  [OK] TC-DATA-001: Data loader import success")
    test_results.append(('TC-DATA-001', 'PASS'))
except Exception as e:
    print(f"  [FAIL] TC-DATA-001: Import failed - {e}")
    test_results.append(('TC-DATA-001', 'FAIL'))

# TC-DATA-003: Data Processor Import Test
try:
    from data.data_processor import DataProcessor, process_stock_data
    print("  [OK] TC-DATA-003: Data processor import success")
    test_results.append(('TC-DATA-003', 'PASS'))
except Exception as e:
    print(f"  [FAIL] TC-DATA-003: Import failed - {e}")
    test_results.append(('TC-DATA-003', 'FAIL'))

# TC-DATA-004: Data Processing Function Test
try:
    processor = DataProcessor()
    
    # Test clean function
    df_with_na = test_data.copy()
    df_with_na.loc[df_with_na.index[5:10], 'close'] = np.nan
    cleaned = processor.clean_data(df_with_na)
    
    # Test resample
    resampled = processor.resample_data(test_data, '1w')
    
    # Test time features
    with_features = processor.add_time_features(test_data)
    
    print("  [OK] TC-DATA-004: Data processing functions normal")
    print(f"       Cleaned data: {len(cleaned)} rows")
    print(f"       Resampled: {len(resampled)} rows")
    print(f"       Feature columns: {len(with_features.columns)}")
    test_results.append(('TC-DATA-004', 'PASS'))
except Exception as e:
    print(f"  [FAIL] TC-DATA-004: Function test failed - {e}")
    test_results.append(('TC-DATA-004', 'FAIL'))

# ==================== Feature Layer Test (L1-L2) ====================
print("\n[4/4] L1 Unit Test - Feature Layer...")

# TC-FEAT-001: Feature Engineering Import Test
try:
    from features.feature_engineering import FeatureEngineer, engineer_features
    print("  [OK] TC-FEAT-001: Feature engineering import success")
    test_results.append(('TC-FEAT-001', 'PASS'))
except Exception as e:
    print(f"  [FAIL] TC-FEAT-001: Import failed - {e}")
    test_results.append(('TC-FEAT-001', 'FAIL'))

# TC-FEAT-002: Feature Generation Function Test
try:
    engineer = FeatureEngineer()
    df_features = engineer.create_all_features(test_data)
    
    print("  [OK] TC-FEAT-002: Feature generation function normal")
    print(f"       Input features: {len(test_data.columns)}")
    print(f"       Output features: {len(df_features.columns)}")
    print(f"       Samples: {len(df_features)}")
    test_results.append(('TC-FEAT-002', 'PASS'))
except Exception as e:
    print(f"  [FAIL] TC-FEAT-002: Function test failed - {e}")
    test_results.append(('TC-FEAT-002', 'FAIL'))

# TC-FEAT-003: Support Resistance Detection Test
try:
    from features.support_resistance import SupportResistanceDetector
    
    detector = SupportResistanceDetector()
    levels = detector.detect_levels(test_data)
    
    print("  [OK] TC-FEAT-003: Support resistance detection normal")
    print(f"       Support levels: {len(levels['support'])}")
    print(f"       Resistance levels: {len(levels['resistance'])}")
    test_results.append(('TC-FEAT-003', 'PASS'))
except Exception as e:
    print(f"  [FAIL] TC-FEAT-003: Detection failed - {e}")
    test_results.append(('TC-FEAT-003', 'FAIL'))

# ==================== Summary ====================
print("\n" + "=" * 60)
print("Test Summary")
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
    print("\n[WARNING] Some tests failed, please check code")
    sys.exit(1)
else:
    print("\n[PASS] All tests passed")
    sys.exit(0)
