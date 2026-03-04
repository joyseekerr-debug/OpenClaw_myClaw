import akshare as ak
import pandas as pd

print("=" * 70)
print("尝试使用akshare获取数据")
print("=" * 70)

# 尝试获取美股实时行情
print("\n【美股实时行情】")
try:
    # 使用akshare的美股接口
    us_spot = ak.stock_us_spot_em()
    print(f"成功获取 {len(us_spot)} 只美股数据")
    print("\n前10行数据:")
    print(us_spot[['代码', '名称', '最新价', '涨跌幅', '总市值']].head(10))
    
    # 筛选能源相关股票
    energy_keywords = ['Halliburton', 'Schlumberger', 'NOV', 'Nabors', 'Energy', 'Oil', 'Schlumberger']
    energy_stocks = us_spot[us_spot['名称'].str.contains('|'.join(energy_keywords), case=False, na=False)]
    
    print(f"\n能源相关股票 ({len(energy_stocks)}只):")
    if len(energy_stocks) > 0:
        print(energy_stocks[['代码', '名称', '最新价', '涨跌幅', '总市值']])
    
    # 保存数据
    us_spot.to_csv('us_spot_real.csv', index=False, encoding='utf-8-sig')
    print(f"\n✅ 数据已保存到 us_spot_real.csv")
    
except Exception as e:
    print(f"获取美股数据失败: {e}")
    import traceback
    traceback.print_exc()

# 尝试获取港股数据
print("\n" + "=" * 70)
print("【港股实时行情】")
try:
    hk_spot = ak.stock_hk_spot_em()
    print(f"成功获取 {len(hk_spot)} 只港股数据")
    print("\n能源相关港股:")
    hk_energy = hk_spot[hk_spot['名称'].str.contains('石油|能源|航运', case=False, na=False)]
    if len(hk_energy) > 0:
        print(hk_energy[['代码', '名称', '最新价', '涨跌幅']].head(10))
except Exception as e:
    print(f"获取港股数据失败: {e}")
