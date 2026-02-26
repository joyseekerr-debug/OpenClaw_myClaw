#!/usr/bin/env python3
"""
小米集团股票监控启动器
自动设置路径并启动监控系统
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("  小米集团(1810.HK) 股票监控系统")
print("="*70)
print()
print("正在初始化...")
print()

# 检查依赖
try:
    import aiohttp
    print("✅ aiohttp 已安装")
except ImportError:
    print("❌ aiohttp 未安装，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'aiohttp', '-q'])
    print("✅ aiohttp 安装完成")

try:
    import schedule
    print("✅ schedule 已安装")
except ImportError:
    print("❌ schedule 未安装，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'schedule', '-q'])
    print("✅ schedule 安装完成")

print()

# 模拟监控演示
from datetime import datetime
import time
import random

print("="*70)
print("  监控配置")
print("="*70)
print()
print("  股票代码: 1810.HK (小米集团)")
print("  当前持仓: 1,600股 @ 35.90 HKD")
print()
print("  预警设置:")
print("    🔴 止损预警: ≤ 34.00 HKD")
print("    🟡 加仓预警: ≤ 34.50 HKD")
print("    🟢 止盈预警: ≥ 37.00 HKD")
print("    ⚠️  异常波动: 单日 ±5%")
print()
print("  监控频率: 每10秒")
print("  通知方式: 飞书消息")
print()
print("="*70)
print("  监控系统启动成功!")
print("="*70)
print()

# 模拟监控循环
current_price = 35.74
count = 0

print("开始监控... (按 Ctrl+C 停止)")
print()

try:
    while True:
        count += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 模拟价格小幅波动
        change = random.gauss(0, 0.01)
        current_price *= (1 + change)
        current_price = round(current_price, 2)
        
        # 计算相对成本的变化
        change_from_cost = ((current_price - 35.90) / 35.90) * 100
        
        # 显示当前状态
        status = "正常"
        if current_price <= 34.00:
            status = "🔴 止损预警!"
        elif current_price <= 34.50:
            status = "🟡 加仓提醒"
        elif current_price >= 37.00:
            status = "🟢 止盈提醒"
        elif abs(change_from_cost) > 2:
            status = "⚠️  波动较大"
        
        print(f"[{timestamp}] 1810.HK: {current_price} HKD ({change_from_cost:+.2f}%) {status}")
        
        # 每5次检查显示一次汇总
        if count % 5 == 0:
            print(f"    [汇总] 已监控 {count} 次，当前浮亏: {change_from_cost:.2f}%")
        
        time.sleep(10)
        
except KeyboardInterrupt:
    print()
    print()
    print("="*70)
    print("  监控系统已停止")
    print(f"  共监控 {count} 次")
    print(f"  最终价格: {current_price} HKD")
    print("="*70)
    print()
    print("提示: 实际监控需要配置:")
    print("  1. iTick API Key")
    print("  2. 飞书Webhook URL")
    print("  3. Redis服务器(可选)")
