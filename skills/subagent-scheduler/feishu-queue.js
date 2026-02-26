/**
 * 飞书指令队列集成示例
 * 演示如何在飞书中使用指令队列功能
 */

const { CommandQueue } = require('./command-queue');
const { SubagentScheduler } = require('./index');

/**
 * 创建飞书指令队列处理器
 */
function createFeishuCommandQueue(options = {}) {
  // 创建调度器
  const scheduler = new SubagentScheduler();
  let initialized = false;
  
  // 创建队列
  const queue = new CommandQueue({
    maxQueueSize: options.maxQueueSize || 50,
    enableNotification: true,
    ...options.queueOptions
  });

  // 设置任务处理器
  queue.setTaskHandler(async (taskData, metadata) => {
    // 初始化调度器
    if (!initialized) {
      await scheduler.init({ autoStartLearning: false });
      initialized = true;
    }
    
    // 通过调度器执行任务
    const result = await scheduler.execute({
      task: taskData,
      chatId: metadata.chatId,
      ...metadata.executeOptions
    });
    
    return result;
  });

  // 设置飞书通知处理器
  queue.setNotificationHandler(async (notification, metadata) => {
    const { feishu } = require('./feishu');
    
    const chatId = metadata?.chatId;
    if (!chatId) return;

    let messageText = '';
    
    switch (notification.type) {
      case 'enqueued':
        if (notification.position === 1 && queue.getStatus().currentTask) {
          messageText = `⏳ 任务已加入队列\n当前正在执行其他任务，预计等待: ${notification.estimatedWait}秒`;
        } else if (notification.position > 1) {
          messageText = `📋 任务已加入队列\n当前位置: ${notification.position}\n预计等待: ${notification.estimatedWait}秒`;
        } else {
          messageText = `🚀 任务已加入队列，正在立即执行...`;
        }
        break;
        
      case 'started':
        messageText = `▶️ 开始执行任务\n队列中还有 ${notification.queueLength} 个任务等待`;
        break;
        
      case 'completed':
        messageText = `✅ 任务执行完成\n耗时: ${Math.floor(notification.duration / 1000)}秒`;
        break;
        
      case 'failed':
        messageText = `❌ 任务执行失败\n${notification.error}`;
        break;
        
      case 'retry':
        messageText = `🔄 ${notification.message}`;
        break;
        
      case 'queue-update':
        messageText = `📊 队列更新\n还有 ${notification.queueLength} 个任务等待`;
        break;
        
      case 'queue-empty':
        messageText = `✨ ${notification.message}`;
        break;
        
      default:
        messageText = notification.message || '队列通知';
    }

    try {
      await feishu.sendMessage(chatId, {
        msg_type: 'text',
        content: { text: messageText }
      });
    } catch (error) {
      console.error('[FeishuQueue] 发送通知失败:', error);
    }
  });

  // 包装后的enqueue方法，自动提取chatId
  const enqueue = async (message, chatId, options = {}) => {
    return await queue.enqueue(message, {
      metadata: {
        chatId,
        userId: options.userId,
        executeOptions: options.executeOptions
      },
      priority: options.priority || 0,
      timeout: options.timeout,
      maxRetries: options.maxRetries
    });
  };

  // 获取队列状态
  const getStatus = () => queue.getStatus();
  
  // 获取队列详情
  const getQueueDetails = () => queue.getQueueDetails();
  
  // 取消任务
  const cancelTask = (taskId) => queue.cancelTask(taskId);
  
  // 清空队列
  const clear = () => queue.clear();
  
  // 关闭资源
  const close = async () => {
    queue.clear();
    if (initialized) {
      await scheduler.close();
    }
  };

  return {
    enqueue,
    getStatus,
    getQueueDetails,
    cancelTask,
    clear,
    close,
    // 暴露原始队列对象以便高级使用
    _queue: queue
  };
}

module.exports = {
  createFeishuCommandQueue
};
