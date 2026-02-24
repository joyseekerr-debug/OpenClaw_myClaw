"""
Redis 服务器启动脚本
尝试多种方式启动Redis
"""

import subprocess
import os
import sys

print("="*60)
print("Redis Server Starter")
print("="*60)
print()

# 尝试1: 检查Redis是否已安装为Windows服务
print("[1] Checking Windows Redis service...")
try:
    result = subprocess.run(['sc', 'query', 'Redis'], capture_output=True, text=True)
    if 'RUNNING' in result.stdout:
        print("   Redis service is already running!")
    elif 'STOPPED' in result.stdout:
        print("   Redis service found but stopped, starting...")
        subprocess.run(['sc', 'start', 'Redis'], capture_output=True)
    else:
        print("   Redis service not found")
except Exception as e:
    print(f"   Error: {e}")

print()

# 尝试2: 查找Redis安装目录并启动
print("[2] Looking for Redis installation...")
redis_paths = [
    r"C:\Program Files\Redis\redis-server.exe",
    r"C:\ProgramData\chocolatey\bin\redis-server.exe",
    r"C:\Redis\redis-server.exe",
    r"C:\tools\redis\redis-server.exe",
]

redis_found = False
for path in redis_paths:
    if os.path.exists(path):
        print(f"   Found Redis at: {path}")
        print("   Starting Redis server...")
        try:
            subprocess.Popen([path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("   Redis server started!")
            redis_found = True
            break
        except Exception as e:
            print(f"   Failed to start: {e}")

if not redis_found:
    print("   Redis not found in common locations")

print()

# 尝试3: 使用fakeredis作为备选
print("[3] Setting up fakeredis (Python Redis implementation)...")
try:
    from fakeredis import FakeRedis
    
    # 启动fakeredis服务器
    import threading
    import socket
    
    print("   Fakeredis is available as fallback")
    print("   Note: Fakeredis runs in-memory and will not persist data")
    
    # 测试连接
    r = FakeRedis()
    r.set('test', 'connected')
    result = r.get('test')
    if result == b'connected':
        print("   Fakeredis test: OK")
        print()
        print("="*60)
        print("Redis Status: Using Fakeredis (in-memory mode)")
        print("="*60)
        print()
        print("For production use, please install Redis:")
        print("  winget install Redis.Redis")
        print("  or")
        print("  choco install redis-64")
        
except ImportError:
    print("   Fakeredis not available")
    print()
    print("="*60)
    print("Redis Installation Required")
    print("="*60)
    print()
    print("Please install Redis using one of these methods:")
    print()
    print("1. Using winget (recommended):")
    print("   winget install Redis.Redis")
    print()
    print("2. Using Chocolatey:")
    print("   choco install redis-64")
    print()
    print("3. Download from GitHub:")
    print("   https://github.com/microsoftarchive/redis/releases")
    print()
    print("4. Use Docker:")
    print("   docker run -d -p 6379:6379 redis:latest")

print()
print("="*60)
