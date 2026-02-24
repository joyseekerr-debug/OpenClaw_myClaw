"""
飞书快速响应通知器
优化消息处理速度：先回复"处理中"，异步推送结果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.async_handler import get_async_handler
from datetime import datetime
import json


class FeishuFastNotifier:
    """飞书快速响应通知器"""
    
    def __init__(self):
        self.async_handler = get_async_handler()
        self.pending_tasks = {}
    
    def notify_processing(self, message: str = "Processing...") -> dict:
        """
        立即发送"处理中"响应
        
        Returns:
            包含task_id的字典，用于后续更新
        """
        task_id = f"fs_{int(datetime.now().timestamp() * 1000)}"
        
        # 构建"处理中"消息
        processing_msg = {
            "task_id": task_id,
            "status": "processing",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "type": "interactive",
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "处理中..."
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"⏳ {message}\n\n正在后台处理，完成后自动推送结果..."
                        }
                    }
                ]
            }
        }
        
        return processing_msg
    
    def notify_result(self, task_id: str, result: dict, elapsed: float = None):
        """
        推送处理结果
        
        Args:
            task_id: 任务ID
            result: 处理结果
            elapsed: 处理耗时
        """
        # 构建结果消息
        result_msg = {
            "task_id": task_id,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "result": result
        }
        
        # 这里调用飞书API发送消息
        # 实际实现需要接入飞书SDK或Webhook
        print(f"[FeishuNotifier] Pushing result for task {task_id}")
        print(f"[FeishuNotifier] Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result_msg
    
    def notify_error(self, task_id: str, error: str):
        """
        推送错误信息
        
        Args:
            task_id: 任务ID
            error: 错误信息
        """
        error_msg = {
            "task_id": task_id,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": error
        }
        
        print(f"[FeishuNotifier] Pushing error for task {task_id}: {error}")
        
        return error_msg
    
    def execute_async(self, func, *args, **kwargs) -> str:
        """
        异步执行任务，完成后自动推送结果
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            task_id: 任务ID
        """
        # 先发送"处理中"通知
        processing_msg = self.notify_processing(f"Executing {func.__name__}...")
        task_id = processing_msg["task_id"]
        
        # 定义回调函数
        def callback(result, tid, elapsed):
            self.notify_result(tid, {"data": result}, elapsed)
        
        def error_callback(error, tid):
            self.notify_error(tid, str(error))
        
        # 提交异步任务
        actual_task_id = self.async_handler.submit(
            func, 
            callback,
            *args, 
            **kwargs
        )
        
        # 保存任务映射
        self.pending_tasks[task_id] = actual_task_id
        
        return task_id


# 使用示例
if __name__ == "__main__":
    import time
    
    print("="*60)
    print("Feishu Fast Notifier Demo")
    print("="*60)
    print()
    
    notifier = FeishuFastNotifier()
    
    # 定义一个耗时任务
    def long_calculation_task(a: int, b: int) -> int:
        """模拟耗时计算"""
        time.sleep(3)  # 模拟3秒计算
        return a + b
    
    # 方式1: 手动分步
    print("[Demo 1] Manual async execution")
    print("-"*60)
    
    # 立即发送"处理中"
    processing = notifier.notify_processing("Calculating stock price...")
    print(f"Immediate response: {processing}")
    print()
    
    # 异步执行
    task_id = notifier.execute_async(long_calculation_task, 100, 200)
    print(f"Task submitted: {task_id}")
    print()
    
    # 等待完成
    time.sleep(5)
    
    print()
    print("="*60)
    print("Demo completed!")
    print("="*60)
