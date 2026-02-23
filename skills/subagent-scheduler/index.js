/**
 * 子代理调度器主入口 - 完整版
 * 整合所有模块：SQLite、Redis、Cron、成本监控、重试机制
 */

const scheduler = require('./scheduler');
const database = require('./database');
const feishu = require('./feishu');
const { FeishuCallbackHandler } = require('./feishu-callback');
const { getCronManager } = require('./cron-manager');
const { CostMonitor } = require('./cost-monitor');
const { RetryExecutor } = require('./retry-executor');
const config = require('./config.json');

// 可选模块（需要外部依赖）
let RedisController = null;
let SubagentAdapter = null;

try {
  const redisModule = require('./redis-concurrency');
  RedisController = redisModule.RedisConcurrencyController;
} catch (e) {
  console.log('[Scheduler] Redis模块未加载');
}

try {
  SubagentAdapter = require('./subagent-adapter');
} catch (e) {
  console.log('[Scheduler] 子代理适配器未加载');
}

/**
 * 子代理调度器类
 */
class SubagentScheduler {
  constructor(options = {}) {
    this.db = database;
    this.cronManager = getCronManager();
    this.costMonitor = new CostMonitor(this.db, options.budget);
    this.retryExecutor = new RetryExecutor(options.retry);
    this.feishuCallback = new FeishuCallbackHandler(feishu);
    this.concurrencyController = null;
    
    // 初始化并发控制
    this.initConcurrency(options.redis);
  }

  /**
   * 初始化并发控制
   */
  async initConcurrency(redisConfig) {
    if (RedisController && redisConfig) {
      try {
        this.concurrencyController = new RedisController(redisConfig);
        console.log('[Scheduler] Redis并发控制已启用');
      } catch (e) {
        console.log('[Scheduler] Redis连接失败，使用本地并发控制');
      }
    }
    
    if (!this.concurrencyController) {
      const { LocalConcurrencyController } = require('./redis-concurrency');
      this.concurrencyController = new LocalConcurrencyController();
      console.log('[Scheduler] 本地并发控制已启用');
    }
  }

  /**
   * 初始化
   */
  async init() {
    this.db.initDatabase();
    console.log('[Scheduler] 初始化完成');
    return this;
  }

  /**
   * 执行任务（完整流程）
   */
  async execute(taskInput, options = {}) {
    const startTime = Date.now();
    const task = typeof taskInput === 'string' ? taskInput : taskInput.task;
    const chatId = options.chatId || config.feishu.defaultChatId;
    
    try {
      // 1. 任务分类
      const classification = await scheduler.classifyTask(task, this.db);
      let branch = options.forceBranch || classification.branch;
      
      // 2. Simple分支直接执行
      if (branch === 'Simple') {
        return await this.executeSimple(task, startTime);
      }
      
      // 3. 成本估算和预算检查
      const costEstimate = this.costMonitor.estimateCost(branch, task.length);
      const budgetCheck = await this.costMonitor.checkBudget(costEstimate.total);
      
      if (!budgetCheck.allowed) {
        return {
          success: false,
          error: `预算检查失败: ${budgetCheck.reasons.join(', ')}`,
          errorType: 'BUDGET_EXCEEDED'
        };
      }
      
      // 4. 用户确认（飞书）
      if (chatId && config.confirmation.enabled) {
        const historyStats = await this.db.getHistoryStats(branch, 7);
        
        const confirmResult = await this.feishuCallback.sendTextConfirm({
          branch,
          duration: costEstimate.estimatedTime,
          cost: costEstimate.total,
          history: historyStats
        }, chatId);
        
        if (confirmResult.action === 'cancel') {
          return { success: false, error: '用户取消', errorType: 'USER_CANCELLED' };
        }
        
        if (confirmResult.action === 'downgrade') {
          branch = 'Simple';
          return await this.executeSimple(task, startTime);
        }
      }
      
      // 5. 并发控制 - 获取槽位
      const taskId = `task_${Date.now()}`;
      await this.concurrencyController.waitForSlot(branch, taskId, 30000);
      
      // 6. 构建任务配置
      const taskConfig = scheduler.buildTaskConfig(branch, task, options);
      
      // 7. 发送进度消息
      let progressMessageId = null;
      if (chatId) {
        const progressMsg = await feishu.sendMessage(
          chatId,
          feishu.buildProgressMessage(0, 0)
        );
        progressMessageId = progressMsg.message_id;
        
        // 启动进度更新定时任务
        this.cronManager.startFeishuUpdater(
          taskId,
          progressMessageId,
          async (msgId, status) => {
            await feishu.updateMessage(
              msgId,
              feishu.buildProgressMessage(status.progress, Math.floor((Date.now() - startTime) / 1000))
            );
          },
          config.monitoring.progressUpdateInterval
        );
      }
      
      // 8. 执行子代理（带重试）
      let executionResult;
      
      if (options.toolExecutor) {
        // 使用主会话传入的toolExecutor
        const adapter = SubagentAdapter?.createSubagentExecutor(options.toolExecutor);
        executionResult = await this.retryExecutor.execute(async () => {
          return await adapter.spawn(taskConfig);
        }, { task, branch });
      } else {
        // 模拟执行（实际应在主会话中执行）
        executionResult = await this.simulateExecution(taskConfig);
      }
      
      // 9. 停止进度更新
      this.cronManager.stop(taskId);
      
      // 10. 释放并发槽位
      await this.concurrencyController.releaseSlot(branch, taskId);
      
      // 11. 记录历史
      const duration = Date.now() - startTime;
      await this.db.insertTaskHistory({
        task_hash: scheduler.hashTask(task),
        task_preview: task.substring(0, 100),
        branch,
        duration_ms: duration,
        estimated_cost: costEstimate.total,
        actual_cost: executionResult.success ? costEstimate.total : 0,
        success: executionResult.success ? 1 : 0,
        retry_count: executionResult.attempts || 0,
        error_message: executionResult.error?.message
      });
      
      // 12. 发送完成消息
      if (chatId && progressMessageId) {
        await feishu.updateMessage(
          progressMessageId,
          feishu.buildCompleteMessage(
            executionResult.success,
            Math.floor(duration / 1000),
            costEstimate.total,
            executionResult.result,
            executionResult.error
          )
        );
      }
      
      return {
        success: executionResult.success,
        branch,
        result: executionResult.result,
        duration,
        attempts: executionResult.attempts || 1,
        error: executionResult.error
      };
      
    } catch (error) {
      // 错误处理
      const duration = Date.now() - startTime;
      const errorBranch = typeof branch !== 'undefined' ? branch : 'Unknown';
      
      await this.db.insertTaskHistory({
        task_hash: scheduler.hashTask(task),
        task_preview: task.substring(0, 100),
        branch: errorBranch,
        duration_ms: duration,
        success: 0,
        retry_count: 0,
        error_message: error.message
      });
      
      return {
        success: false,
        error,
        errorType: 'EXECUTION_ERROR',
        duration
      };
    }
  }

  /**
   * 执行Simple任务
   */
  async executeSimple(task, startTime) {
    // Simple任务直接处理，不spawn
    return {
      success: true,
      branch: 'Simple',
      result: '直接执行完成',
      duration: Date.now() - startTime
    };
  }

  /**
   * 模拟子代理执行（测试用）
   */
  async simulateExecution(config) {
    // 模拟执行时间
    const delay = config.runTimeoutSeconds > 60000 ? 5000 : 2000;
    await new Promise(r => setTimeout(r, delay));
    
    return {
      success: true,
      result: '模拟执行结果',
      attempts: 1
    };
  }

  /**
   * 生成日报
   */
  async generateDailyReport(chatId) {
    const stats = await this.costMonitor.generateReport();
    
    if (!stats || stats.length === 0) {
      await feishu.sendMessage(chatId, {
        msg_type: 'text',
        content: { text: '暂无历史数据' }
      });
      return;
    }
    
    // 构建日报
    const report = this.buildReport(stats);
    await feishu.sendMessage(chatId, feishu.buildDailyReport(report));
  }

  /**
   * 构建报告数据
   */
  buildReport(stats) {
    const today = new Date().toISOString().split('T')[0];
    const todayStats = stats.filter(s => s.date === today);
    
    return {
      date: today,
      totalTasks: todayStats.reduce((sum, s) => sum + s.count, 0),
      totalCost: todayStats.reduce((sum, s) => sum + s.total_cost, 0),
      byBranch: todayStats.reduce((obj, s) => {
        obj[s.branch] = {
          count: s.count,
          totalCost: s.total_cost,
          avgCost: s.avg_cost
        };
        return obj;
      }, {})
    };
  }

  /**
   * 获取并发状态
   */
  async getConcurrencyStatus() {
    return await this.concurrencyController.getAllStatus();
  }

  /**
   * 关闭资源
   */
  async close() {
    this.cronManager.stopAll();
    if (this.concurrencyController) {
      await this.concurrencyController.close();
    }
  }
}

// 兼容旧版API
async function init() {
  const scheduler = new SubagentScheduler();
  return scheduler.init();
}

async function executeWithConfirm(taskInput, options = {}) {
  const scheduler = new SubagentScheduler();
  await scheduler.init();
  return scheduler.execute(taskInput, options);
}

module.exports = {
  SubagentScheduler,
  init,
  executeWithConfirm,
  generateDailyReport: async (chatId) => {
    const scheduler = new SubagentScheduler();
    await scheduler.init();
    return scheduler.generateDailyReport(chatId);
  },
  // 子模块
  scheduler,
  database,
  feishu,
  getCronManager,
  CostMonitor,
  RetryExecutor,
  FeishuCallbackHandler
};
