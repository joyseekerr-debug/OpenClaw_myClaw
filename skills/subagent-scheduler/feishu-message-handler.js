/**
 * 飞书消息处理器 - 集成指令队列 + 自动路由 + 多Agent协作
 * 自动启用所有功能
 */

const { createFeishuCommandQueue } = require('./feishu-queue');
const { CommandQueue } = require('./command-queue');
const { TaskComplexityAnalyzer } = require('./auto-router');
const { SubagentScheduler } = require('./index');
const queueConfig = require('./queue-config.json');
const config = require('./config.json');

/**
 * 创建增强版飞书消息处理器
 * 集成：指令队列 + 自动路由 + 多Agent协作
 */
function createFeishuMessageHandler(options = {}) {
  const configMerged = { ...queueConfig, ...options };
  
  // 创建调度器（用于复杂任务）
  const scheduler = new SubagentScheduler();
  let schedulerInitialized = false;
  
  // 创建复杂度分析器
  const complexityAnalyzer = new TaskComplexityAnalyzer();
  
  // 创建队列实例（直接使用CommandQueue以获得完整控制）
  const queue = new CommandQueue({
    maxQueueSize: configMerged.maxQueueSize,
    enableNotification: configMerged.enableNotification,
    defaultTimeout: configMerged.defaultTimeout
  });

  // 初始化调度器并启动学习定时任务
  async function initScheduler() {
    if (!schedulerInitialized) {
      await scheduler.init({ 
        autoStartLearning: config.phase4?.learning?.autoStart 
      });
      
      // 如果配置了自动启动学习，启动定时任务
      if (config.phase4?.learning?.autoStart) {
        const chatId = config.feishu?.defaultChatId;
        if (chatId) {
          scheduler.startDailyLearning(chatId);
          console.log('[FeishuQueue] 每日学习定时任务已启动 (6:00分析, 9:00推送)');
        }
      }
      
      schedulerInitialized = true;
      console.log('[FeishuQueue] 调度器已初始化，全功能启用');
    }
  }

  // 设置智能任务处理器
  queue.setTaskHandler(async (taskData, metadata) => {
    // 确保调度器已初始化
    await initScheduler();
    
    // 分析任务复杂度
    const analysis = complexityAnalyzer.analyze(taskData);
    console.log(`[FeishuQueue] 任务复杂度分析: ${analysis.level} (分数: ${analysis.score})`);
    
    // 决定是否使用多Agent
    const useMultiAgent = config.phase5?.multiAgent?.autoTrigger 
      && analysis.score >= (config.phase5?.multiAgent?.complexityThreshold || 70);
    
    // 决定是否使用自动路由（复杂任务触发确认）
    const useAutoRouter = config.phase5?.autoRouter?.enabled 
      && analysis.level !== 'simple';
    
    // 执行任务
    const result = await scheduler.execute({
      task: taskData,
      chatId: metadata.chatId,
      multiAgent: useMultiAgent,
      forceBranch: useAutoRouter ? undefined : analysis.suggestedBranch
    });
    
    return result;
  });

  /**
   * 处理用户消息（智能路由）
   */
  async function handleMessage(message, chatId, userInfo = {}) {
    // 分析复杂度
    const analysis = complexityAnalyzer.analyze(message);
    
    // 检测优先级
    const priority = detectPriority(message);
    
    // 如果是简单任务且队列空，直接处理（更快）
    if (analysis.level === 'simple' && queue.getStatus().queueLength === 0 && !queue.getStatus().processing) {
      console.log('[FeishuQueue] 简单任务，快速处理');
      await initScheduler();
      return await scheduler.execute({
        task: message,
        chatId: chatId,
        forceBranch: 'Simple'
      });
    }
    
    // 添加到队列
    const taskId = await queue.enqueue(message, chatId, {
      priority,
      userId: userInfo.userId,
      userName: userInfo.userName,
      executeOptions: {
        complexity: analysis
      }
    });
    
    return {
      taskId,
      queued: true,
      priority,
      complexity: analysis.level,
      status: queue.getStatus()
    };
  }
  
  /**
   * 检测消息优先级
   */
  function detectPriority(message) {
    const text = message.toLowerCase();
    
    // 高优先级关键词
    for (const keyword of configMerged.priorityKeywords.high) {
      if (text.includes(keyword)) return 10;
    }
    
    // 低优先级关键词
    for (const keyword of configMerged.priorityKeywords.low) {
      if (text.includes(keyword)) return -5;
    }
    
    return 0;
  }
  
  /**
   * 获取队列状态
   */
  function getStatus() {
    return queue.getStatus();
  }
  
  /**
   * 获取队列详情
   */
  function getQueueDetails() {
    return queue.getQueueDetails();
  }
  
  /**
   * 获取监控仪表板
   */
  function getDashboard() {
    if (schedulerInitialized) {
      return scheduler.getDashboard();
    }
    return null;
  }
  
  /**
   * 关闭队列
   */
  async function close() {
    queue.clear();
    if (schedulerInitialized) {
      await scheduler.close();
    }
  }
  
  // 初始化
  initScheduler().catch(console.error);
  
  return {
    handleMessage,
    getStatus,
    getQueueDetails,
    getDashboard,
    close,
    _queue: queue,
    _scheduler: scheduler
  };
}

// 单例模式
let messageHandlerInstance = null;

/**
 * 获取或创建消息处理器（全功能版）
 */
function getMessageHandler(options = {}) {
  if (!messageHandlerInstance) {
    messageHandlerInstance = createFeishuMessageHandler(options);
  }
  return messageHandlerInstance;
}

/**
 * 重置消息处理器
 */
function resetMessageHandler() {
  if (messageHandlerInstance) {
    messageHandlerInstance.close();
    messageHandlerInstance = null;
  }
}

module.exports = {
  createFeishuMessageHandler,
  getMessageHandler,
  resetMessageHandler
};
