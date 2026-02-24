"""
简化的特征工程验证
"""

import sys
sys.path.insert(0, r'C:\Users\Jhon\.openclaw\workspace\stock-trading-system')

import numpy as np
import pandas as pd

print("✅ NumPy版本:", np.__version__)
print("✅ Pandas版本:", pd.__version__)

# 创建简单测试数据
dates = pd.date_range('2024-01-01', periods=30, freq='D')
np.random.seed(42)

base_price = 15.0
prices = [base_price]
for i in range(29):
    change = np.random.normal(0.001, 0.02)
    prices.append(prices[-1] * (1 + change))

df = pd.DataFrame({
    'timestamp': dates,
    'open': [p * np.random.uniform(0.995, 1.0) for p in prices],
    'high': [p * np.random.uniform(1.0, 1.02) for p in prices],
    'low': [p * np.random.uniform(0.98, 1.0) for p in prices],
    'close': prices,
    'volume': np.random.randint(1000000, 10000000, 30)
})

print(f"\n✅ 测试数据创建成功: {len(df)} 行")
print(df.head(3))

# 测试技术指标
try:
    from features.technical import TechnicalIndicatorCalculator
    calc = TechnicalIndicatorCalculator()
    result = calc.calculate_all(df)
    print(f"\n✅ 技术指标计算成功!")
    print(f"   技术指标数量: {len(calc.get_feature_names())}")
    print(f"   数据形状: {result.shape}")
    
    # 显示部分结果
    sample_cols = ['close', 'sma_5', 'macd', 'rsi_12']
    print("\n📊 部分技术指标:")
    print(result[sample_cols].tail(3).to_string())
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("特征工程验证完成!")
print("="*50)
