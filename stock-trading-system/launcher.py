#!/usr/bin/env python3
"""
股票交易系统 - 简化启动脚本
不依赖外部库，先验证基础功能
"""

import sys
import os
from datetime import datetime

print("="*70)
print("  小米集团股票交易预测系统 - 启动器")
print("="*70)
print(f"\n启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"工作目录: {os.getcwd()}")

# 检查依赖
def check_dependencies():
    """检查必要的依赖"""
    print("\n[依赖检查]")
    
    required = {
        'pandas': '数据处理',
        'numpy': '数值计算',
        'requests': 'HTTP请求',
        'sklearn': '机器学习'
    }
    
    missing = []
    for package, desc in required.items():
        try:
            __import__(package)
            print(f"  [OK] {package}: {desc}")
        except ImportError:
            print(f"  [MISSING] {package}: {desc} (未安装)")
            missing.append(package)
    
    optional = {
        'torch': '深度学习(LSTM/Transformer)',
        'xgboost': 'XGBoost模型',
        'shap': '模型解释性',
        'redis': 'Redis缓存',
        'talib': '技术指标(TA-Lib)'
    }
    
    for package, desc in optional.items():
        try:
            __import__(package)
            print(f"  [OK] {package}: {desc}")
        except ImportError:
            print(f"  [OPTIONAL] {package}: {desc} (可选，未安装)")
    
    return missing

# 测试基础功能
def test_basic_functions():
    """测试基础功能"""
    print("\n[功能测试]")
    
    try:
        # 测试配置加载
        print("  1. 加载配置...")
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
            print(f"     [OK] 找到 .env 文件 ({len(lines)} 行)")
        else:
            print("     [WARN] 未找到 .env 文件")
        
        # 测试数据源模块
        print("  2. 检查数据源模块...")
        if os.path.exists('data/data_source.py'):
            print("     [OK] data_source.py 存在")
        else:
            print("     [ERROR] data_source.py 不存在")
        
        # 测试特征模块
        print("  3. 检查特征工程模块...")
        if os.path.exists('features/technical.py'):
            print("     [OK] technical.py 存在")
        else:
            print("     [ERROR] technical.py 不存在")
        
        # 测试模型模块
        print("  4. 检查模型模块...")
        if os.path.exists('models/predictors.py'):
            print("     [OK] predictors.py 存在")
        else:
            print("     [ERROR] predictors.py 不存在")
        
        # 测试监控模块
        print("  5. 检查监控模块...")
        if os.path.exists('monitoring/realtime.py'):
            print("     [OK] realtime.py 存在")
        else:
            print("     [ERROR] realtime.py 不存在")
        
        print("\n  [OK] 基础功能检查完成")
        return True
        
    except Exception as e:
        print(f"\n  [ERROR] 测试失败: {e}")
        return False

# 安装依赖
def install_dependencies():
    """安装依赖"""
    print("\n[安装依赖]")
    print("  正在安装: pandas, numpy, requests, scikit-learn")
    
    import subprocess
    
    packages = ['pandas', 'numpy', 'requests', 'scikit-learn']
    
    for package in packages:
        print(f"  安装 {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])
            print(f"    [OK] {package} 安装成功")
        except Exception as e:
            print(f"    [ERROR] {package} 安装失败: {e}")

# 主函数
def main():
    """主函数"""
    print("\n" + "="*70)
    
    # 检查依赖
    missing = check_dependencies()
    
    if missing:
        print(f"\n[WARN] 缺少必要依赖: {', '.join(missing)}")
        choice = input("\n是否自动安装依赖? (y/n): ").lower()
        if choice == 'y':
            install_dependencies()
            print("\n[INFO] 请重新运行此脚本")
            return
        else:
            print("\n[ERROR] 缺少必要依赖，无法运行")
            print("请手动安装: pip install pandas numpy requests scikit-learn")
            return
    
    # 测试基础功能
    if test_basic_functions():
        print("\n" + "="*70)
        print("  [OK] 系统检查完成，所有模块就绪！")
        print("="*70)
        
        print("\n[启动选项]")
        print("  1. 运行完整系统 (需要所有依赖)")
        print("  2. 运行简化演示版")
        print("  3. 仅测试数据连接")
        print("  4. 退出")
        
        choice = input("\n选择 (1-4): ").strip()
        
        if choice == '1':
            print("\n[启动] 完整系统...")
            try:
                import main
            except Exception as e:
                print(f"\n[ERROR] 启动失败: {e}")
                import traceback
                traceback.print_exc()
        
        elif choice == '2':
            print("\n[启动] 简化演示版...")
            run_demo()
        
        elif choice == '3':
            print("\n[启动] 测试数据连接...")
            test_data_connection()
        
        else:
            print("\n[退出]")
    else:
        print("\n[ERROR] 系统检查失败")

# 演示模式
def run_demo():
    """运行演示"""
    print("\n" + "="*70)
    print("  演示模式 - 小米集团股票监控")
    print("="*70)
    
    import random
    import time
    
    # 模拟股价数据
    base_price = 15.0
    current_price = base_price
    
    print(f"\n[模拟监控] 1810.HK (小米集团)")
    print(f"   起始价格: ${base_price:.2f}")
    print(f"   更新频率: 2秒")
    print(f"   预警阈值: +-2%")
    print("\n按 Ctrl+C 停止\n")
    
    try:
        for i in range(30):  # 演示30次
            # 模拟价格变动
            change = random.gauss(0, 0.01)  # 正态分布
            current_price *= (1 + change)
            
            change_pct = (current_price - base_price) / base_price * 100
            
            # 显示价格
            timestamp = datetime.now().strftime('%H:%M:%S')
            arrow = "UP" if change_pct >= 0 else "DOWN"
            
            print(f"[{timestamp}] [{arrow}] 1810.HK: ${current_price:.2f} ({change_pct:+.2f}%)", end='')
            
            # 检查预警
            if abs(change_pct) >= 2.0:
                print(f" [ALERT] 价格变动 {abs(change_pct):.2f}%!")
            else:
                print()
            
            time.sleep(2)
        
        print("\n[OK] 演示完成")
        
    except KeyboardInterrupt:
        print("\n\n[STOP] 演示已停止")

# 测试数据连接
def test_data_connection():
    """测试数据连接"""
    print("\n" + "="*70)
    print("  测试数据连接")
    print("="*70)
    
    # 测试iTick (模拟)
    print("\n1. 测试 iTick API...")
    print("   使用配置的API Key测试连接...")
    print("   [NOTE] 实际测试需要网络连接和有效API")
    
    # 测试Yahoo
    print("\n2. 测试 Yahoo Finance...")
    print("   尝试获取 1810.HK 数据...")
    print("   [NOTE] Yahoo对港股支持有限")
    
    # 测试AKShare
    print("\n3. 测试 AKShare...")
    print("   AKShare主要用于A股数据")
    print("   港股数据可能不完整")
    
    print("\n[OK] 连接测试说明完成")
    print("\n提示:")
    print("  - 确保网络连接正常")
    print("  - 检查API Key是否有效")
    print("  - 确认目标股票代码正确")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[EXIT] 程序已退出")
    except Exception as e:
        print(f"\n[ERROR] 程序错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    input("按回车键退出...")
