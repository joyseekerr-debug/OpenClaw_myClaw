# -*- coding: utf-8 -*-
"""
24小时优化任务 - 第1-2小时: 数据优化与特征工程
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
print("24-Hour Optimization Task - Hour 1-2")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Load historical data
print("[1/5] Loading historical data...")
df = pd.read_csv('data/historical_2y.csv', index_col='timestamp', parse_dates=True)
print(f"  Records: {len(df)}")
print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")

# 2. Feature engineering optimization
print("\n[2/5] Feature engineering...")
from features.feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
df_features = engineer.create_all_features(df)

print(f"  Original features: {len(df.columns)}")
print(f"  Engineered features: {len(df_features.columns)}")
print(f"  Samples: {len(df_features)}")

# 3. Feature quality check
print("\n[3/5] Feature quality check...")
numeric_df = df_features.select_dtypes(include=[np.number])
missing_ratio = numeric_df.isnull().mean()
high_missing = missing_ratio[missing_ratio > 0.1]

if len(high_missing) > 0:
    print(f"  Warning: {len(high_missing)} features have >10% missing")
else:
    print("  Feature quality: Good")

# 4. Feature correlation analysis
print("\n[4/5] Feature correlation analysis...")
if 'target_direction_1' in numeric_df.columns:
    target_corr = numeric_df.corr()['target_direction_1'].abs().sort_values(ascending=False)
    top_features = target_corr.head(10)
    
    print("  Top 10 features correlated with target:")
    for feature, corr in top_features.items():
        if feature != 'target_direction_1':
            print(f"    {feature}: {corr:.3f}")
else:
    print("  Target column not found")

# 5. Save optimized data
print("\n[5/5] Saving optimized data...")
df_features.to_csv('data/features_optimized.csv')
print("  Saved to: data/features_optimized.csv")

print("\n" + "=" * 70)
print("Hour 1-2 task completed")
print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
