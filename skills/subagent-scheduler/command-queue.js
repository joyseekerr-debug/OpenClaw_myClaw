/**
 * 指令队列管理器
 * 处理飞书消息的队列功能，支持顺序执行和并发控制
 */

const EventEmitter = require('events');

/**
 * 任务状态枚举
 */
const TaskStatus = {
  PENDING: 'pending',       // 等待中
  RUNNING: 'running',       // 执行中
  COMPLETED: 'completed',   // 已完成
  FAILED: 'failed',         // 失败
  CANCELLED: 'cancelled'    // 已取消
};

/**
 * 指令队列管理器
 */
class CommandQueue extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.queue = [];           // 任务队列
    this.currentTask = null;   // 当前执行的任务
    this.processing = false;   // 是否正在处理
    
    // 配置
    this.config = {
      maxQueueSize: options.maxQueueSize || 100,        // 最大队列长度
      defaultTimeout: options.defaultTimeout || 300000,  // 默认超时5分钟
      autoStart: options.autoStart !== false,            // 自动启动
      concurrency: options.concurrency || 1,             // 并发数（默认单线程）
      enableNotification: options.enableNotification !== false  // 启用通知
    };
    
    this.stats = {
      totalProcessed: 0,
      totalFailed: 0,
      totalCancelled: 0,
      averageWaitTime: 0
    };
    
    // 处理器函数（由外部设置）
    this.taskHandler = null;
    this.notificationHandler = null;
  }

  /**
   * 设置任务处理器
   */
  setTaskHandler(handler) {
    this.taskHandler = handler;
  }

  /**
   * 设置通知处理器
   */
  setNotificationHandler(handler) {
    this.notificationHandler = handler;
  }

  /**
   * 添加任务到队列
   */
  async enqueue(taskData, options = {}) {
    const task = {
      id: `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      data: taskData,
      status: TaskStatus.PENDING,
      priority: options.priority || 0,  // 优先级（数字越大优先级越高）
      createdAt: Date.now(),
      startedAt: null,
      completedAt: null,
      timeout: options.timeout || this.config.defaultTimeout,
      metadata: options.metadata || {},  // 额外信息（如chatId、userId等）
      retryCount: 0,
      maxRetries: options.maxRetries || 0
    };

    // 检查队列是否已满
    if (this.queue.length >= this.config.maxQueueSize) {
      throw new Error('队列已满，请稍后重试');
    }

    // 根据优先级插入队列
    const insertIndex = this.queue.findIndex(t => t.priority < task.priority);
    if (insertIndex === -1) {
      this.queue.push(task);
    } else {
      this.queue.splice(insertIndex, 0, task);
    }

    this.emit('task-enqueued', task);
    
    // 发送通知
    if (this.config.enableNotification && this.notificationHandler) {
      const position = this.getQueuePosition(task.id);
      await this.notificationHandler({
        type: 'enqueued',
        taskId: task.id,
        position: position,
        estimatedWait: this.estimateWaitTime(position),
        message: position === 1 && !this.currentTask 
          ? '任务已加入队列，正在立即执行...'
          : `任务已加入队列，当前位置: ${position}，预计等待: ${this.estimateWaitTime(position)}秒`
      }, task.metadata);
    }

    // 如果没有正在执行的任务，立即开始处理
    if (!this.processing && this.config.autoStart) {
      this.processQueue();
    }

    return task.id;
  }

  /**
   * 处理队列
   */
  async processQueue() {
    if (this.processing || this.queue.length === 0) {
      return;
    }

    this.processing = true;

    try {
      // 获取下一个任务
      const task = this.queue.shift();
      this.currentTask = task;
      
      task.status = TaskStatus.RUNNING;
      task.startedAt = Date.now();
      
      this.emit('task-started', task);

      // 发送开始执行通知
      if (this.config.enableNotification && this.notificationHandler) {
        await this.notificationHandler({
          type: 'started',
          taskId: task.id,
          message: '开始执行任务...',
          queueLength: this.queue.length
        }, task.metadata);
      }

      // 执行任务
      let result;
      try {
        if (!this.taskHandler) {
          throw new Error('未设置任务处理器');
        }

        // 设置超时
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('任务执行超时')), task.timeout);
        });

        result = await Promise.race([
          this.taskHandler(task.data, task.metadata),
          timeoutPromise
        ]);

        task.status = TaskStatus.COMPLETED;
        task.result = result;
        task.completedAt = Date.now();
        
        this.stats.totalProcessed++;
        this.emit('task-completed', task);

        // 发送完成通知
        if (this.config.enableNotification && this.notificationHandler) {
          await this.notificationHandler({
            type: 'completed',
            taskId: task.id,
            message: '任务执行完成',
            duration: task.completedAt - task.startedAt,
            result: result
          }, task.metadata);
        }

      } catch (error) {
        task.status = TaskStatus.FAILED;
        task.error = error.message;
        task.completedAt = Date.now();
        
        this.stats.totalFailed++;
        this.emit('task-failed', task, error);

        // 发送失败通知
        if (this.config.enableNotification && this.notificationHandler) {
          await this.notificationHandler({
            type: 'failed',
            taskId: task.id,
            message: `任务执行失败: ${error.message}`,
            error: error.message
          }, task.metadata);
        }

        // 重试逻辑
        if (task.retryCount < task.maxRetries) {
          task.retryCount++;
          task.status = TaskStatus.PENDING;
          this.queue.unshift(task); // 放到队列头部优先重试
          
          if (this.notificationHandler) {
            await this.notificationHandler({
              type: 'retry',
              taskId: task.id,
              message: `任务将在3秒后重试 (${task.retryCount}/${task.maxRetries})...`
            }, task.metadata);
          }
          
          await this.delay(3000);
        }
      }

      this.currentTask = null;

      // 如果队列中还有任务，继续处理
      if (this.queue.length > 0) {
        // 发送队列更新通知
        if (this.config.enableNotification && this.notificationHandler) {
          const nextTask = this.queue[0];
          await this.notificationHandler({
            type: 'queue-update',
            queueLength: this.queue.length,
            nextTaskId: nextTask.id,
            message: `队列中还有 ${this.queue.length} 个任务，即将开始执行下一个...`
          }, nextTask.metadata);
        }

        // 短暂延迟后开始下一个任务
        await this.delay(1000);
        this.processing = false;
        this.processQueue();
      } else {
        this.processing = false;
        this.emit('queue-empty');
        
        if (this.config.enableNotification && this.notificationHandler) {
          await this.notificationHandler({
            type: 'queue-empty',
            message: '所有任务已处理完毕'
          });
        }
      }

    } catch (error) {
      this.processing = false;
      this.currentTask = null;
      this.emit('error', error);
      console.error('[CommandQueue] 处理队列时发生错误:', error);
    }
  }

  /**
   * 延迟函数
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 获取任务在队列中的位置
   */
  getQueuePosition(taskId) {
    const index = this.queue.findIndex(t => t.id === taskId);
    return index === -1 ? 0 : index + 1;
  }

  /**
   * 预估等待时间（秒）
   */
  estimateWaitTime(position) {
    if (position <= 1) return 0;
    
    // 假设每个任务平均60秒
    const avgTaskDuration = 60;
    const remainingCurrent = this.currentTask 
      ? Math.max(0, avgTaskDuration - (Date.now() - this.currentTask.startedAt) / 1000)
      : 0;
    
    return Math.ceil(remainingCurrent + (position - 1) * avgTaskDuration);
  }

  /**
   * 取消任务
   */
  cancelTask(taskId) {
    // 如果是当前执行的任务
    if (this.currentTask && this.currentTask.id === taskId) {
      // 注意：这里只是标记，实际取消需要任务处理器配合
      this.currentTask.status = TaskStatus.CANCELLED;
      this.emit('task-cancelled', this.currentTask);
      this.stats.totalCancelled++;
      return true;
    }

    // 如果是队列中的任务
    const index = this.queue.findIndex(t => t.id === taskId);
    if (index !== -1) {
      const task = this.queue[index];
      task.status = TaskStatus.CANCELLED;
      this.queue.splice(index, 1);
      this.emit('task-cancelled', task);
      this.stats.totalCancelled++;
      return true;
    }

    return false;
  }

  /**
   * 获取队列状态
   */
  getStatus() {
    return {
      processing: this.processing,
      queueLength: this.queue.length,
      currentTask: this.currentTask ? {
        id: this.currentTask.id,
        status: this.currentTask.status,
        startedAt: this.currentTask.startedAt,
        duration: this.currentTask.startedAt 
          ? Date.now() - this.currentTask.startedAt 
          : 0
      } : null,
      stats: this.stats
    };
  }

  /**
   * 获取队列详情
   */
  getQueueDetails() {
    return {
      current: this.currentTask,
      pending: this.queue.map(t => ({
        id: t.id,
        priority: t.priority,
        status: t.status,
        createdAt: t.createdAt,
        metadata: t.metadata
      }))
    };
  }

  /**
   * 清空队列
   */
  clear() {
    this.queue.forEach(task => {
      task.status = TaskStatus.CANCELLED;
      this.emit('task-cancelled', task);
    });
    
    this.queue = [];
    this.emit('queue-cleared');
  }

  /**
   * 暂停队列
   */
  pause() {
    this.config.autoStart = false;
    this.emit('queue-paused');
  }

  /**
   * 恢复队列
   */
  resume() {
    this.config.autoStart = true;
    this.emit('queue-resumed');
    
    if (!this.processing && this.queue.length > 0) {
      this.processQueue();
    }
  }

  /**
   * 更新统计信息
   */
  updateStats() {
    if (this.stats.totalProcessed > 0) {
      // 这里可以计算更复杂的统计数据
    }
  }
}

module.exports = {
  CommandQueue,
  TaskStatus
};
