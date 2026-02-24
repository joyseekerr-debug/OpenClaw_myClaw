"""
股价获取测试与解决方案
"""

import sys
import time

def test_akshare():
    """测试AKShare"""
    print("="*60)
    print("[方案1] 使用 AKShare 获取股价")
    print("="*60)
    
    try:
        import akshare as ak
        
        print("正在获取港股实时数据...")
        hk_df = ak.stock_hk_spot_em()
        
        # 查找小米
        xiaomi = hk_df[hk_df['代码'] == '01810']
        
        if not xiaomi.empty:
            row = xiaomi.iloc[0]
            print("\n✅ 成功获取小米股价!")
            print(f"股票代码: 01810 (1810.HK)")
            print(f"股票名称: {row.get('名称', '小米集团-W')}")
            print(f"最新价格: ¥{row.get('最新价')} 港元")
            print(f"涨跌额: ¥{row.get('涨跌额')} 港元")
            print(f"涨跌幅: {row.get('涨跌幅')}%")
            print(f"今日最高: ¥{row.get('最高价')} 港元")
            print(f"今日最低: ¥{row.get('最低价')} 港元")
            print(f"成交量: {row.get('成交量')}")
            return True
        else:
            print("\n❌ 未找到小米数据")
            return False
            
    except Exception as e:
        print(f"\n❌ AKShare 失败: {e}")
        return False


def test_sina_api():
    """测试新浪财经API"""
    print("\n" + "="*60)
    print("[方案2] 使用新浪财经API")
    print("="*60)
    
    try:
        import requests
        
        # 新浪财经港股API
        url = "https://hq.sinajs.cn/list=rt_hk01810"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print("正在请求新浪财经...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 解析数据
            data = response.text
            print(f"\n✅ 成功获取数据!")
            print(f"原始数据: {data[:200]}")
            return True
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 新浪财经API失败: {e}")
        return False


def test_local_data():
    """使用本地模拟数据"""
    print("\n" + "="*60)
    print("[方案3] 使用本地模拟数据")
    print("="*60)
    
    print("\n⚠️ 网络受限，使用模拟数据演示:")
    print("\n小米集团 (1810.HK)")
    print("最新价: ¥15.23 港元 (模拟)")
    print("涨跌幅: +0.85% (模拟)")
    print("\n注: 实际使用时请检查网络连接")
    
    return True


def main():
    print("="*60)
    print("股价获取测试")
    print("="*60)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试各种方案
    results = []
    
    # 方案1: AKShare
    results.append(("AKShare", test_akshare()))
    
    # 方案2: 新浪财经
    results.append(("新浪财经API", test_sina_api()))
    
    # 方案3: 本地数据
    results.append(("本地模拟", test_local_data()))
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name}: {status}")
    
    # 检查是否有成功的
    if any(success for _, success in results[:2]):
        print("\n✅ 已找到可用方案，可以获取实时股价!")
    else:
        print("\n⚠️ 所有网络方案失败")
        print("建议:")
        print("  1. 检查网络连接")
        print("  2. 配置代理设置")
        print("  3. 使用股票交易软件API")


if __name__ == "__main__":
    main()
    input("\n按回车退出...")
