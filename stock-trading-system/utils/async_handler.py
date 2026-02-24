"""
异步消息处理器 - 优化飞书消息响应速度
先回复"处理中"，后台处理完成后推送结果
"""

import threading
import queue
import time
from datetime import datetime
from typing import Callable, Any
import json


class AsyncMessageHandler:
    """异步消息处理器"""
    
    def __init__(self, max_workers: int = 5):
        self.task_queue = queue.Queue()
        self.max_workers = max_workers
        self.workers = []
        self.running = False
        self._start_workers()
    
    def _start_workers(self):
        """启动工作线程"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"AsyncWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self):
        """工作线程循环"""
        while self.running:
            try:
                # 获取任务 (阻塞等待，超时1秒)
                task = self.task_queue.get(timeout=1)
                if task is None:
                    continue
                
                # 执行任务
                self._execute_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[AsyncHandler] Worker error: {e}")
    
    def _execute_task(self, task: dict):
        """执行具体任务"""
        try:
            func = task.get('function')
            args = task.get('args', ())
            kwargs = task.get('kwargs', {})
            callback = task.get('callback')
            task_id = task.get('task_id')
            
            # 记录开始时间
            start_time = time.time()
            print(f"[AsyncHandler] Starting task {task_id} at {datetime.now()}")
            
            # 执行实际任务
            result = func(*args, **kwargs)
            
            # 计算耗时
            elapsed = time.time() - start_time
            print(f"[AsyncHandler] Task {task_id} completed in {elapsed:.2f}s")
            
            # 调用回调函数推送结果
            if callback:
                callback(result, task_id, elapsed)
                
        except Exception as e:
            print(f"[AsyncHandler] Task execution error: {e}")
            # 错误回调
            if task.get('error_callback'):
                task['error_callback'](e, task_id)
    
    def submit(self, func: Callable, callback: Callable, 
               *args, **kwargs) -> str:
        """
        提交异步任务
        
        Args:
            func: 要执行的函数
            callback: 完成后的回调函数
            *args, **kwargs: 函数参数
            
        Returns:
            task_id: 任务ID
        """
        task_id = f"task_{int(time.time() * 1000)}_{hash(func.__name__) % 10000}"
        
        task = {
            'task_id': task_id,
            'function': func,
            'args': args,
            'kwargs': kwargs,
            'callback': callback,
            'submit_time': datetime.now()
        }
        
        self.task_queue.put(task)
        print(f"[AsyncHandler] Task {task_id} submitted, queue size: {self.task_queue.qsize()}")
        
        return task_id
    
    def shutdown(self):
        """关闭处理器"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)


# 全局实例
_async_handler = None

def get_async_handler() -> AsyncMessageHandler:
    """获取异步处理器实例"""
    global _async_handler
    if _async_handler is None:
        _async_handler = AsyncMessageHandler(max_workers=5)
    return _async_handler


# 使用示例
def example_long_task(duration: int) -> str:
    """模拟耗时任务"""
    time.sleep(duration)
    return f"Task completed after {duration} seconds"


def example_callback(result: Any, task_id: str, elapsed: float):
    """示例回调函数"""
    print(f"[Callback] Task {task_id}: {result} (took {elapsed:.2f}s)")
    # 这里可以调用飞书通知API推送结果


if __name__ == "__main__":
    print("="*60)
    print("Async Message Handler Test")
    print("="*60)
    print()
    
    handler = get_async_handler()
    
    # 提交几个测试任务
    print("Submitting tasks...")
    task1 = handler.submit(example_long_task, example_callback, 2)
    task2 = handler.submit(example_long_task, example_callback, 3)
    task3 = handler.submit(example_long_task, example_callback, 1)
    
    print(f"Tasks submitted: {task1}, {task2}, {task3}")
    print()
    
    # 模拟先回复"处理中"
    print("Immediate response: 'Processing...'")
    print()
    
    # 等待所有任务完成
    time.sleep(5)
    
    print()
    print("="*60)
    handler.shutdown()
