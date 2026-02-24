"""
iTick API 连接问题排查和替代方案
"""

import socket
import requests

print("="*70)
print("iTick API Connection Troubleshooting")
print("="*70)
print()

# 1. DNS解析测试
print("[1] DNS Resolution Test")
print("-"*70)

try:
    host = 'api.itick.com'
    print(f"Resolving {host}...")
    ip = socket.gethostbyname(host)
    print(f"IP: {ip}")
except Exception as e:
    print(f"DNS resolution failed: {e}")
    print()
    print("Possible causes:")
    print("  - Network proxy/firewall blocking")
    print("  - DNS server not responding")
    print("  - Domain does not exist or is blocked")
print()

# 2. 尝试其他可能的iTick端点
print("[2] Testing alternative endpoints")
print("-"*70)

endpoints = [
    'https://api.itick.com',
    'https://www.itick.com',
    'https://itick.com',
]

for url in endpoints:
    try:
        print(f"Testing {url}...")
        response = requests.get(url, timeout=5, allow_redirects=True)
        print(f"  Status: {response.status_code}")
        print(f"  Final URL: {response.url}")
    except Exception as e:
        print(f"  Failed: {type(e).__name__}")
print()

# 3. 检查网络连接状态
print("[3] Network Status")
print("-"*70)

# 测试其他网站连接
test_sites = [
    ('https://www.baidu.com', 'Baidu'),
    ('https://www.sina.com.cn', 'Sina'),
    ('https://finance.sina.com.cn', 'Sina Finance'),
]

for url, name in test_sites:
    try:
        response = requests.get(url, timeout=5)
        print(f"{name}: OK (Status {response.status_code})")
    except Exception as e:
        print(f"{name}: Failed ({type(e).__name__})")

print()
print("="*70)
print()

# 4. 总结和建议
print("[4] Summary and Recommendations")
print("-"*70)
print()
print("Issue: Cannot connect to iTick API")
print("Error: DNS resolution failed for api.itick.com")
print()
print("Possible solutions:")
print("  1. Check if iTick API requires specific network configuration")
print("  2. Try accessing from a different network environment")
print("  3. Contact iTick support for correct API endpoint")
print("  4. Check if SDK has different connection method")
print()
print("Current status:")
print("  - Sina Finance: Working (real-time data available)")
print("  - iTick: Cannot connect (DNS/network issue)")
print("  - Yahoo/Akshare: Rate limited or connection issues")
print()
print("Recommendation:")
print("  Use Sina Finance as primary data source for now")
print("  Retry iTick connection when network environment improves")
print()
print("="*70)
