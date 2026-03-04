import akshare as ak
import pandas as pd

print("=" * 70)
print("A股能源/航运板块数据获取 (真实数据)")
print("=" * 70)

try:
    # 获取A股实时行情
    print("\n正在获取A股实时行情...")
    a_spot = ak.stock_zh_a_spot_em()
    print(f"✅ 成功获取 {len(a_spot)} 只A股数据")
    
    # 筛选能源相关股票
    energy_keywords = ['石油', '石化', '海油', '油服', '能源', '航运', '船舶', '黄金']
    energy_stocks = []
    
    for keyword in energy_keywords:
        matches = a_spot[a_spot['名称'].str.contains(keyword, case=False, na=False)]
        if len(matches) > 0:
            energy_stocks.append(matches)
    
    if energy_stocks:
        energy_df = pd.concat(energy_stocks).drop_duplicates(subset=['代码'])
        print(f"\n能源/航运/黄金相关股票 ({len(energy_df)}只):")
        
        # 选择关键列
        columns = ['代码', '名称', '最新价', '涨跌幅', '换手率', '市盈率-动态', '总市值', '60日涨跌幅']
        available_cols = [c for c in columns if c in energy_df.columns]
        
        print(energy_df[available_cols].head(30).to_string())
        
        # 保存数据
        energy_df.to_csv('a_share_energy_real.csv', index=False, encoding='utf-8-sig')
        print(f"\n✅ 数据已保存到 a_share_energy_real.csv")
        
        # 计算3个月涨跌幅排名
        if '60日涨跌幅' in energy_df.columns:
            print("\n【60日涨跌幅排名 (能源板块)】")
            energy_df['60日涨跌幅_num'] = pd.to_numeric(energy_df['60日涨跌幅'], errors='coerce')
            top_gainers = energy_df.nlargest(10, '60日涨跌幅_num')[['代码', '名称', '最新价', '60日涨跌幅']]
            print(top_gainers.to_string(index=False))
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
