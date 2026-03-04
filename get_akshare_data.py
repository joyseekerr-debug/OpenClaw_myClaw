# 尝试使用akshare获取数据
try:
    import akshare as ak
    print("akshare已安装")
    
    # 获取美股实时行情
    print("\n获取美股实时行情...")
    us_stock = ak.stock_us_spot_em()
    print(f"获取到 {len(us_stock)} 只美股数据")
    print("\n前5行数据:")
    print(us_stock.head())
    
    # 筛选能源板块
    energy_stocks = us_stock[us_stock['名称'].str.contains('Halliburton|Schlumberger|NOV|Nabors|Energy|Oil', case=False, na=False)]
    print(f"\n能源相关股票: {len(energy_stocks)} 只")
    if len(energy_stocks) > 0:
        print(energy_stocks[['代码', '名称', '最新价', '涨跌额', '涨跌幅', '总市值']].head(20))
        
except ImportError:
    print("akshare未安装，尝试安装...")
    import subprocess
    subprocess.run(['py', '-3', '-m', 'pip', 'install', 'akshare', '-q'])
    print("安装完成，请重新运行脚本")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
