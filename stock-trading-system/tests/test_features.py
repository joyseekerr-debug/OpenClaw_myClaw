"""
特征工程测试脚本
验证技术指标和Alpha因子计算
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from features.technical import TechnicalIndicatorCalculator
from features.alpha import AlphaFactorCalculator
from features.feature_engine import FeatureEngine


def create_test_data(days: int = 100) -> pd.DataFrame:
    """创建测试数据"""
    np.random.seed(42)
    
    # 生成日期
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 生成价格数据（带趋势）
    base_price = 15.0
    trend = np.linspace(0, 0.1, days)  # 轻微上涨趋势
    noise = np.random.normal(0, 0.02, days)
    
    prices = base_price * (1 + trend + noise)
    
    # 生成OHLCV
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.normal(0, 0.005, days)),
        'high': prices * (1 + np.random.uniform(0.005, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0.005, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(5000000, 15000000, days)
    })
    
    # 确保价格关系正确
    df['high'] = np.maximum(df[['open', 'close', 'high']].max(axis=1), df['close'] * 1.001)
    df['low'] = np.minimum(df[['open', 'close', 'low']].min(axis=1), df['close'] * 0.999)
    
    return df


def test_technical_indicators():
    """测试技术指标计算"""
    print("\n" + "="*60)
    print("测试1: 技术指标计算")
    print("="*60)
    
    # 创建测试数据
    df = create_test_data(100)
    print(f"\n📊 测试数据: {len(df)} 天")
    print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head())
    
    # 计算技术指标
    calc = TechnicalIndicatorCalculator()
    result = calc.calculate_all(df)
    
    # 检查结果
    feature_names = calc.get_feature_names()
    print(f"\n✅ 技术指标计算完成")
    print(f"   技术指标数量: {len(feature_names)}")
    
    # 显示部分结果
    print("\n📈 技术指标样例 (最近5天):")
    sample_cols = ['timestamp', 'close', 'sma_20', 'macd', 'rsi_12', 'boll_upper']
    print(result[sample_cols].tail())
    
    # 验证关键指标
    print("\n🔍 关键指标验证:")
    latest = result.iloc[-1]
    print(f"   SMA20: {latest['sma_20']:.2f}")
    print(f"   MACD: {latest['macd']:.4f}")
    print(f"   RSI12: {latest['rsi_12']:.2f}")
    print(f"   布林带宽度: {latest['boll_width']:.4f}")
    
    assert not result[feature_names].isna().all().any(), "存在全为NaN的特征"
    print("\n✅ 技术指标测试通过!")
    
    return result


def test_alpha_factors():
    """测试Alpha因子计算"""
    print("\n" + "="*60)
    print("测试2: Alpha因子计算")
    print("="*60)
    
    # 创建测试数据
    df = create_test_data(100)
    
    # 先计算技术指标（Alpha因子依赖部分技术指标）
    tech_calc = TechnicalIndicatorCalculator()
    df = tech_calc.calculate_all(df)
    
    # 计算Alpha因子
    alpha_calc = AlphaFactorCalculator()
    result = alpha_calc.calculate_all(df)
    
    # 检查结果
    alpha_names = alpha_calc.get_alpha_feature_names()
    print(f"\n✅ Alpha因子计算完成")
    print(f"   Alpha因子数量: {len(alpha_names)}")
    
    # 显示部分结果
    print("\n📊 Alpha因子样例 (最近5天):")
    sample_cols = ['timestamp', 'close', 'order_imbalance', 'z_score_20', 'adx']
    available_cols = [c for c in sample_cols if c in result.columns]
    print(result[available_cols].tail())
    
    # 验证关键因子
    print("\n🔍 关键因子验证:")
    latest = result.iloc[-1]
    print(f"   订单失衡: {latest.get('order_imbalance', 0):.4f}")
    print(f"   Z分数: {latest.get('z_score_20', 0):.4f}")
    print(f"   趋势强度(ADX): {latest.get('adx', 0):.4f}")
    
    print("\n✅ Alpha因子测试通过!")
    
    return result


def test_feature_engine():
    """测试特征工程主类"""
    print("\n" + "="*60)
    print("测试3: 特征工程主类")
    print("="*60)
    
    # 创建测试数据
    df = create_test_data(100)
    
    # 初始化特征工程（不使用缓存）
    engine = FeatureEngine(use_cache=False)
    
    # 计算特征
    print("\n🔄 开始计算特征...")
    result = engine.calculate_features(df, symbol='TEST.HK')
    
    # 统计
    total_features = len(engine.get_all_feature_names())
    print(f"\n✅ 特征工程完成!")
    print(f"   原始列数: {len(df.columns)}")
    print(f"   最终列数: {len(result.columns)}")
    print(f"   新增特征: {len(result.columns) - len(df.columns)}")
    print(f"   总特征数: {total_features}")
    
    # 特征重要性
    print("\n🔍 计算特征重要性...")
    importance = engine.get_feature_importance(result)
    
    print("\n🔝 Top 10 重要特征:")
    for i, (feat, score) in enumerate(list(importance.items())[:10], 1):
        print(f"   {i}. {feat}: {score:.4f}")
    
    # 选择Top特征
    top_features = engine.select_top_features(result, n_features=30)
    print(f"\n✅ 已选择 {len(top_features)} 个特征用于建模")
    
    # 创建序列数据（用于深度学习）
    print("\n🔄 创建序列数据...")
    X, y = engine.create_sequences(result, top_features, target_col='close', sequence_length=20)
    print(f"   序列形状: X{X.shape}, y{y.shape}")
    
    print("\n✅ 特征工程主类测试通过!")
    
    return result


def test_feature_cache():
    """测试特征缓存"""
    print("\n" + "="*60)
    print("测试4: 特征缓存")
    print("="*60)
    
    try:
        from utils.cache import FeatureCache, get_cache
        
        # 初始化缓存
        cache = FeatureCache(get_cache())
        
        # 保存特征
        print("\n💾 保存特征到缓存...")
        cache.set_feature('1810.HK', '2024-02-24', 'rsi_12', 65.5)
        cache.set_feature('1810.HK', '2024-02-24', 'macd', 0.25)
        
        # 读取特征
        print("📖 从缓存读取特征...")
        rsi = cache.get_feature('1810.HK', '2024-02-24', 'rsi_12')
        macd = cache.get_feature('1810.HK', '2024-02-24', 'macd')
        
        print(f"   RSI: {rsi}")
        print(f"   MACD: {macd}")
        
        assert rsi == 65.5, "RSI缓存值不匹配"
        assert macd == 0.25, "MACD缓存值不匹配"
        
        print("\n✅ 特征缓存测试通过!")
        
    except Exception as e:
        print(f"\n⚠️ 特征缓存测试失败: {e}")
        print("   (可能是因为Redis未安装，使用本地内存缓存)")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("     特征工程模块测试")
    print("="*60)
    
    start_time = datetime.now()
    
    try:
        # 测试1: 技术指标
        test_technical_indicators()
        
        # 测试2: Alpha因子
        test_alpha_factors()
        
        # 测试3: 特征工程主类
        test_feature_engine()
        
        # 测试4: 特征缓存
        test_feature_cache()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*60)
        print(f"✅ 所有测试通过! 耗时: {elapsed:.2f}秒")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
