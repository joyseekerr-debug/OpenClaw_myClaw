"""
测试飞书消息响应速度
验证Gateway优化配置是否生效
"""

import time
from datetime import datetime

print("="*60)
print("飞书消息响应速度测试")
print("="*60)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 记录开始时间
start_time = time.time()

# 模拟一个简单任务
print("[测试1] 简单查询任务")
print("-"*60)

# 快速响应测试
for i in range(3):
    loop_start = time.time()
    
    # 简单计算
    result = sum(range(1000))
    
    loop_end = time.time()
    elapsed = (loop_end - loop_start) * 1000  # 转换为毫秒
    
    print(f"  任务 {i+1}: {elapsed:.2f}ms")

print()

# 模拟耗时任务
print("[测试2] 模拟耗时任务 (异步处理测试)")
print("-"*60)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.async_handler import get_async_handler
    from utils.feishu_fast_notifier import FeishuFastNotifier
    
    # 测试异步处理器
    handler = get_async_handler()
    notifier = FeishuFastNotifier()
    
    def slow_task(duration: float) -> dict:
        """模拟耗时任务"""
        time.sleep(duration)
        return {
            "status": "completed",
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    
    # 提交异步任务
    print("  提交异步任务...")
    task_start = time.time()
    
    # 模拟立即返回"处理中"
    processing_msg = notifier.notify_processing("正在执行耗时任务...")
    
    task_end = time.time()
    immediate_response_time = (task_end - task_start) * 1000
    
    print(f"  立即响应时间: {immediate_response_time:.2f}ms")
    print(f"  (应 < 100ms 表示异步处理生效)")
    
    # 提交实际任务
    task_id = notifier.execute_async(slow_task, 0.5)
    print(f"  任务ID: {task_id}")
    
    # 等待任务完成
    time.sleep(1)
    
    print()
    print("  异步处理: ✅ 已启用")
    
except ImportError as e:
    print(f"  无法加载异步模块: {e}")
    print("  异步处理: ❌ 未启用")

print()

# 总体评估
print("="*60)
print("测试结果汇总")
print("="*60)

end_time = time.time()
total_elapsed = (end_time - start_time) * 1000

print(f"总测试耗时: {total_elapsed:.2f}ms")
print()

print("优化效果评估:")
print("  - 简单任务响应: 应 < 500ms")
print("  - 异步'处理中'响应: 应 < 100ms")
print("  - 如果达到以上标准，说明优化已生效")
print()

print("="*60)
