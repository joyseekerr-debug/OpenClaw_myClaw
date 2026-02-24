"""
iTick API连接测试
验证API Key有效性并获取实时数据
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import requests
import json
from datetime import datetime

# iTick API配置
API_KEY = os.getenv('ITICK_API_KEY')
API_KEY_BACKUP = os.getenv('ITICK_API_KEY_BACKUP')
BASE_URL = "https://api.itick.com"

def test_api_key(api_key, key_name):
    """测试API Key有效性"""
    print(f"\n🔑 测试 {key_name}...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 测试获取小米集团实时行情
    # 港股代码格式: 1810.HK
    symbol = "1810.HK"
    
    try:
        # 尝试获取实时报价
        url = f"{BASE_URL}/quote/realtime"
        params = {
            'symbol': symbol,
            'region': 'HK'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {key_name} 连接成功!")
            print(f"📊 小米集团实时数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True, data
        elif response.status_code == 401:
            print(f"❌ {key_name} 认证失败，请检查API Key")
            return False, None
        else:
            print(f"⚠️ {key_name} 返回状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print(f"⏱️ {key_name} 连接超时")
        return False, None
    except Exception as e:
        print(f"❌ {key_name} 连接异常: {e}")
        return False, None

def test_historical_data(api_key):
    """测试获取历史数据"""
    print("\n📈 测试历史数据接口...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        url = f"{BASE_URL}/quote/history"
        params = {
            'symbol': '1810.HK',
            'region': 'HK',
            'period': '1d',  # 日线
            'start': '2024-02-01',
            'end': '2024-02-24'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ 历史数据获取成功!")
                print(f"📊 获取到 {len(data)} 条K线数据")
                print(f"样例数据: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"⚠️ 历史数据为空")
                return False
        else:
            print(f"❌ 历史数据获取失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 历史数据接口异常: {e}")
        return False

def main():
    """主测试函数"""
    print("═══════════════════════════════════════════════════════════")
    print("          iTick API 连接测试")
    print("═══════════════════════════════════════════════════════════")
    
    if not API_KEY:
        print("❌ 未配置ITICK_API_KEY，请检查.env文件")
        return
    
    print(f"\n📝 主API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
    
    # 测试主API Key
    success1, data1 = test_api_key(API_KEY, "主API Key")
    
    if not success1 and API_KEY_BACKUP:
        print("\n⚠️ 主API Key失败，尝试备用API Key...")
        success2, data2 = test_api_key(API_KEY_BACKUP, "备用API Key")
        if success2:
            # 如果备用成功，更新使用备用
            print("\n🔄 将使用备用API Key作为数据源")
    
    # 测试历史数据
    if success1:
        test_historical_data(API_KEY)
    elif API_KEY_BACKUP:
        test_historical_data(API_KEY_BACKUP)
    
    print("\n═══════════════════════════════════════════════════════════")
    
    if success1:
        print("✅ iTick API测试完成，数据源可用!")
    else:
        print("⚠️ iTick API测试未通过，将使用备用数据源(Yahoo/AKShare)")

if __name__ == "__main__":
    main()
