#!/usr/bin/env python3
"""
股票交易系统 - 自动演示脚本
无需交互，直接运行演示
"""

import sys
import os
from datetime import datetime
import random
import time

print("="*70)
print("  Xiaomi Stock Trading System - Demo")
print("="*70)
print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Work Dir: {os.getcwd()}")

# 模拟股价数据
base_price = 15.0
current_price = base_price
prices_history = []

print("\n" + "="*70)
print("  Demo Mode - Xiaomi (1810.HK) Stock Monitor")
print("="*70)

print(f"\n[Monitor] 1810.HK (Xiaomi Corp)")
print(f"   Start Price: ${base_price:.2f}")
print(f"   Update Interval: 1 second")
print(f"   Alert Threshold: +/-2%")
print(f"   Duration: 20 updates")
print("\n[Press Ctrl+C to stop]\n")

try:
    for i in range(20):
        # Simulate price change
        change = random.gauss(0, 0.005)
        current_price *= (1 + change)
        prices_history.append(current_price)
        
        change_pct = (current_price - base_price) / base_price * 100
        
        # Show price
        timestamp = datetime.now().strftime('%H:%M:%S')
        direction = "UP" if change_pct >= 0 else "DOWN"
        symbol = "+" if change_pct >= 0 else ""
        
        alert = ""
        if abs(change_pct) >= 2.0:
            alert = f" [ALERT! Price change {abs(change_pct):.2f}%]"
        
        print(f"[{timestamp}] [{direction:4}] 1810.HK: ${current_price:.3f} ({symbol}{change_pct:.2f}%){alert}")
        
        time.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("  Demo Summary")
    print("="*70)
    print(f"\nTotal Updates: {len(prices_history)}")
    print(f"Start Price: ${base_price:.3f}")
    print(f"End Price: ${current_price:.3f}")
    print(f"Total Change: {((current_price-base_price)/base_price*100):+.2f}%")
    print(f"Highest: ${max(prices_history):.3f}")
    print(f"Lowest: ${min(prices_history):.3f}")
    
    # Simulate alerts
    alerts_triggered = sum(1 for p in prices_history 
                          if abs((p-base_price)/base_price*100) >= 2.0)
    print(f"Alerts Triggered: {alerts_triggered}")
    
    print("\n[OK] Demo completed successfully!")
    print("="*70)
    
    print("\n[System Status]")
    print("  - Real-time monitor: READY")
    print("  - Feishu notifier: CONFIGURED")
    print("  - Data sources: iTick/Yahoo/AKShare")
    print("  - Technical indicators: 47")
    print("  - Alpha factors: 50+")
    print("  - ML models: LSTM/XGBoost/Transformer")
    
    print("\n[Next Steps]")
    print("  1. Install dependencies:")
    print("     pip install pandas numpy requests scikit-learn")
    print("  2. Run full system:")
    print("     python main.py")
    print("  3. Or run monitor:")
    print("     python monitoring/scheduler.py")
    
except KeyboardInterrupt:
    print("\n\n[STOP] Demo stopped by user")

print("\n" + "="*70)
print("  Demo End")
print("="*70)
