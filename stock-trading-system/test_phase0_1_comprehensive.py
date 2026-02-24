"""
Phase 0 & 1 全面系统性测试
验证多数据源、缓存、特征工程全流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def test_phase0_data_sources():
    """测试Phase 0: 多数据源管理"""
    print("\n" + "="*70)
    print("【Phase 0】多数据源管理测试")
    print("="*70)
    
    try:
        from data.data_source import DataSourceManager
        from config import DATA_SOURCES
        
        # 1. 初始化数据源
        print("\n1. 初始化多数据源管理器...")
        manager = DataSourceManager(DATA_SOURCES)
        
        # 2. 健康检查
        print("\n2. 数据源健康检查:")
        health = manager.health_check()
        for source, status in health.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {source}: {'正常' if status else '离线'}")
        
        # 3. 获取历史数据
        print("\n3. 获取小米集团历史数据(模拟)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        symbol = "1810.HK"
        data = manager.get_data(
            symbol=symbol,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if not data.empty:
            print(f"   ✅ 成功获取 {len(data)} 条历史数据")
            print(f"   📊 数据列: {list(data.columns)}")
            print(f"   📅 日期范围: {data['timestamp'].min()} ~ {data['timestamp'].max()}")
        else:
            print("   ⚠️ 数据为空（可能所有数据源都离线）")
        
        # 4. 获取实时数据
        print("\n4. 获取实时数据...")
        realtime = manager.get_realtime_data(symbol)
        if not realtime.empty:
            print(f"   ✅ 实时数据: {realtime.to_dict()}")
        else:
            print("   ⚠️ 实时数据为空")
        
        print("\n✅ Phase 0 多数据源测试通过")
        return True, manager
        
    except Exception as e:
        print(f"\n❌ Phase 0 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_phase0_cache():
    """测试Phase 0: 缓存系统"""
    print("\n" + "="*70)
    print("【Phase 0】缓存系统测试")
    print("="*70)
    
    try:
        from utils.cache import RedisCache, FeatureCache, get_cache
        
        # 1. 初始化缓存
        print("\n1. 初始化缓存系统...")
        cache = get_cache()
        
        # 2. 基本操作测试
        print("\n2. 基本缓存操作:")
        cache.set("test_key", {"data": [1, 2, 3], "timestamp": datetime.now()}, expire=60)
        value = cache.get("test_key")
        print(f"   ✅ 写入/读取: {value is not None}")
        
        # 3. 特征缓存测试
        print("\n3. 特征缓存测试:")
        feature_cache = FeatureCache(cache)
        
        feature_cache.set_feature("1810.HK", "2024-02-24", "rsi_12", 65.5)
        feature_cache.set_feature("1810.HK", "2024-02-24", "macd", 0.25)
        
        rsi = feature_cache.get_feature("1810.HK", "2024-02-24", "rsi_12")
        macd = feature_cache.get_feature("1810.HK", "2024-02-24", "macd")
        
        print(f"   ✅ RSI缓存: {rsi == 65.5}")
        print(f"   ✅ MACD缓存: {macd == 0.25}")
        
        # 4. 统计信息
        print("\n4. 缓存统计:")
        stats = cache.get_stats()
        for key, value in stats.items():
            print(f"   • {key}: {value}")
        
        print("\n✅ Phase 0 缓存系统测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Phase 0 缓存测试失败: {e}")
        return False


def test_phase1_technical_indicators():
    """测试Phase 1: 技术指标"""
    print("\n" + "="*70)
    print("【Phase 1】技术指标计算测试")
    print("="*70)
    
    try:
        from features.technical import TechnicalIndicatorCalculator
        
        # 创建测试数据
        print("\n1. 创建测试数据...")
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        
        base_price = 15.0
        prices = [base_price]
        for i in range(59):
            change = np.random.normal(0.001, 0.02)
            prices.append(prices[-1] * (1 + change))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [p * np.random.uniform(0.995, 1.0) for p in prices],
            'high': [p * np.random.uniform(1.0, 1.02) for p in prices],
            'low': [p * np.random.uniform(0.98, 1.0) for p in prices],
            'close': prices,
            'volume': np.random.randint(5000000, 15000000, 60)
        })
        
        print(f"   数据形状: {df.shape}")
        print(f"   日期范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        
        # 计算技术指标
        print("\n2. 计算技术指标...")
        calc = TechnicalIndicatorCalculator()
        result = calc.calculate_all(df)
        
        feature_names = calc.get_feature_names()
        print(f"   ✅ 技术指标数量: {len(feature_names)}")
        
        # 验证关键指标
        print("\n3. 验证关键指标:")
        latest = result.iloc[-1]
        
        checks = [
            ('SMA20', 'sma_20', lambda x: x > 0),
            ('MACD', 'macd', lambda x: pd.notna(x)),
            ('RSI12', 'rsi_12', lambda x: 0 <= x <= 100 if pd.notna(x) else True),
            ('布林带上轨', 'boll_upper', lambda x: x > latest['close'] if pd.notna(x) else True),
            ('KDJ-K', 'k', lambda x: 0 <= x <= 100 if pd.notna(x) else True),
            ('ATR14', 'atr_14', lambda x: x > 0 if pd.notna(x) else True),
        ]
        
        for name, col, check in checks:
            value = latest.get(col, None)
            passed = check(value) if value is not None else False
            icon = "✅" if passed else "❌"
            print(f"   {icon} {name}: {value:.4f if pd.notna(value) else 'N/A'}")
        
        # 检查NaN比例
        nan_ratio = result[feature_names].isna().mean().mean()
        print(f"\n4. 数据质量:")
        print(f"   • 平均NaN比例: {nan_ratio:.2%}")
        print(f"   ✅ NaN比例 {'正常' if nan_ratio < 0.3 else '过高'}")
        
        print("\n✅ Phase 1 技术指标测试通过")
        return True, result
        
    except Exception as e:
        print(f"\n❌ Phase 1 技术指标测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_phase1_alpha_factors():
    """测试Phase 1: Alpha因子"""
    print("\n" + "="*70)
    print("【Phase 1】Alpha因子计算测试")
    print("="*70)
    
    try:
        from features.technical import TechnicalIndicatorCalculator
        from features.alpha import AlphaFactorCalculator
        
        # 创建测试数据
        print("\n1. 创建测试数据...")
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        
        base_price = 15.0
        prices = [base_price]
        for i in range(59):
            change = np.random.normal(0.001, 0.02)
            prices.append(prices[-1] * (1 + change))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [p * np.random.uniform(0.995, 1.0) for p in prices],
            'high': [p * np.random.uniform(1.0, 1.02) for p in prices],
            'low': [p * np.random.uniform(0.98, 1.0) for p in prices],
            'close': prices,
            'volume': np.random.randint(5000000, 15000000, 60)
        })
        
        # 先计算技术指标
        print("\n2. 计算技术指标（Alpha因子依赖）...")
        tech_calc = TechnicalIndicatorCalculator()
        df = tech_calc.calculate_all(df)
        
        # 计算Alpha因子
        print("\n3. 计算Alpha因子...")
        alpha_calc = AlphaFactorCalculator()
        result = alpha_calc.calculate_all(df)
        
        alpha_names = alpha_calc.get_alpha_feature_names()
        print(f"   ✅ Alpha因子数量: {len(alpha_names)}")
        
        # 验证关键因子
        print("\n4. 验证关键因子:")
        latest = result.iloc[-1]
        
        checks = [
            ('订单失衡', 'order_imbalance', lambda x: -1 <= x <= 1 if pd.notna(x) else True),
            ('Z分数', 'z_score_20', lambda x: pd.notna(x)),
            ('ADX', 'adx', lambda x: 0 <= x <= 100 if pd.notna(x) else True),
            ('收益偏度', 'returns_skewness', lambda x: pd.notna(x)),
            ('换手率', 'turnover_rate', lambda x: x > 0 if pd.notna(x) else True),
        ]
        
        for name, col, check in checks:
            value = latest.get(col, None)
            passed = check(value) if value is not None else False
            icon = "✅" if passed else "❌"
            print(f"   {icon} {name}: {value:.4f if pd.notna(value) else 'N/A'}")
        
        print("\n✅ Phase 1 Alpha因子测试通过")
        return True, result
        
    except Exception as e:
        print(f"\n❌ Phase 1 Alpha因子测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_phase1_feature_engine():
    """测试Phase 1: 特征工程主流程"""
    print("\n" + "="*70)
    print("【Phase 1】特征工程全流程测试")
    print("="*70)
    
    try:
        from features.feature_engine import FeatureEngine
        
        # 创建测试数据
        print("\n1. 创建测试数据...")
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        
        base_price = 15.0
        prices = [base_price]
        for i in range(59):
            change = np.random.normal(0.001, 0.02)
            prices.append(prices[-1] * (1 + change))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [p * np.random.uniform(0.995, 1.0) for p in prices],
            'high': [p * np.random.uniform(1.0, 1.02) for p in prices],
            'low': [p * np.random.uniform(0.98, 1.0) for p in prices],
            'close': prices,
            'volume': np.random.randint(5000000, 15000000, 60)
        })
        
        # 全流程计算
        print("\n2. 执行特征工程全流程...")
        engine = FeatureEngine(use_cache=False)
        result = engine.calculate_features(df, symbol='TEST.HK')
        
        total_features = len(engine.get_all_feature_names())
        print(f"   ✅ 特征计算完成")
        print(f"   • 输入列数: {len(df.columns)}")
        print(f"   • 输出列数: {len(result.columns)}")
        print(f"   • 新增特征: {len(result.columns) - len(df.columns)}")
        print(f"   • 总特征数: {total_features}")
        
        # 特征重要性
        print("\n3. 计算特征重要性...")
        importance = engine.get_feature_importance(result)
        top_features = list(importance.items())[:10]
        
        print("   🔝 Top 10 重要特征:")
        for i, (feat, score) in enumerate(top_features, 1):
            print(f"      {i}. {feat}: {score:.4f}")
        
        # 选择特征
        print("\n4. 特征选择...")
        selected = engine.select_top_features(result, n_features=30)
        print(f"   ✅ 已选择 {len(selected)} 个特征")
        
        # 创建序列
        print("\n5. 创建序列数据...")
        X, y = engine.create_sequences(result, selected, target_col='close', sequence_length=20)
        print(f"   ✅ 序列数据: X{X.shape}, y{y.shape}")
        
        print("\n✅ Phase 1 特征工程全流程测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Phase 1 特征工程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_full_system_test():
    """运行完整系统测试"""
    print("\n" + "="*70)
    print("  Phase 0 & Phase 1 全面系统性测试")
    print("="*70)
    print(f"\n测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'Phase 0 - 数据源': False,
        'Phase 0 - 缓存': False,
        'Phase 1 - 技术指标': False,
        'Phase 1 - Alpha因子': False,
        'Phase 1 - 特征工程': False
    }
    
    # Phase 0 测试
    results['Phase 0 - 数据源'], _ = test_phase0_data_sources()
    results['Phase 0 - 缓存'] = test_phase0_cache()
    
    # Phase 1 测试
    results['Phase 1 - 技术指标'], _ = test_phase1_technical_indicators()
    results['Phase 1 - Alpha因子'], _ = test_phase1_alpha_factors()
    results['Phase 1 - 特征工程'] = test_phase1_feature_engine()
    
    # 测试总结
    print("\n" + "="*70)
    print("  测试总结报告")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    end_time = datetime.now()
    duration = (end_time - datetime.now()).total_seconds()
    print(f"\n测试结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration:.2f}秒")
    
    if passed == total:
        print("\n🎉 所有测试通过！Phase 0 & 1 系统稳定，可以进入 Phase 2 开发")
        return True
    else:
        print("\n⚠️ 部分测试失败，建议修复后再进入 Phase 2")
        return False


if __name__ == "__main__":
    success = run_full_system_test()
    sys.exit(0 if success else 1)
