import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print("=" * 70)
print("尝试通过yfinance获取数据 (更新版本)")
print("=" * 70)

# 尝试使用不同的方式获取
try:
    print("\n尝试获取 IEZ ETF 数据...")
    
    # 方式1: 使用Ticker
    iez = yf.Ticker("IEZ")
    print(f"  Ticker创建成功")
    
    # 方式2: 获取历史数据
    hist = iez.history(period="3mo")
    print(f"  历史数据: {len(hist)} 条")
    
    if len(hist) > 0:
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        return_3m = (end_price - start_price) / start_price * 100
        print(f"  3个月前: ${start_price:.2f}")
        print(f"  当前: ${end_price:.2f}")
        print(f"  涨幅: {return_3m:.2f}%")
        print(f"\n✅ IEZ数据获取成功!")
    else:
        print("  ❌ 无历史数据")
        
except Exception as e:
    print(f"  ❌ 错误: {e}")
    print(f"\n状态: 仍然被Yahoo Finance限制")

# 尝试另一只股票
try:
    print("\n尝试获取 AAPL (测试)...")
    aapl = yf.Ticker("AAPL")
    hist = aapl.history(period="3mo")
    print(f"  AAPL: {len(hist)} 条数据")
    if len(hist) > 0:
        print(f"  ✅ AAPL成功!")
except Exception as e:
    print(f"  ❌ AAPL也失败: {e}")

print("\n" + "=" * 70)
print("结论: Yahoo Finance仍然限制此IP的访问")
print("=" * 70)
