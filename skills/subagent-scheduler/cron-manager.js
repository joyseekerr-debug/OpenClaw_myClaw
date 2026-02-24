/**
 * Cron定时任务管理器
 * 使用node-cron实现定时轮询
 */

const cron = require('node-cron');
const EventEmitter = require('events');

class CronManager extends EventEmitter {
  constructor() {
    super();
    this.tasks = new Map();
  }

  /**
   * 启动进度监控任务
   * @param {string} taskId - 任务ID
   * @param {Function} checkFn - 检查函数
   * @param {Function} callback - 回调函数
   * @param {number} intervalSeconds - 间隔秒数
   */
  startProgressMonitor(taskId, checkFn, callback, intervalSeconds = 10) {
    // 使用node-cron创建定时任务
    const cronExpression = `*/${intervalSeconds} * * * * *`; // 每N秒执行
    
    const task = cron.schedule(cronExpression, async () => {
      try {
        const status = await checkFn();
        callback(null, status);
        
        // 如果任务完成，停止监控
        if (status.completed || status.failed) {
          this.stop(taskId);
        }
      } catch (error) {
        callback(error, null);
      }
    }, { scheduled: true });
    
    this.tasks.set(taskId, task);
    console.log(`[Cron] 启动进度监控: ${taskId}, 间隔: ${intervalSeconds}秒`);
    
    return taskId;
  }

  /**
   * 启动飞书消息更新任务
   */
  startFeishuUpdater(taskId, messageId, feishuUpdater, intervalSeconds = 10) {
    const cronExpression = `*/${intervalSeconds} * * * * *`;
    
    let lastProgress = 0;
    const task = cron.schedule(cronExpression, async () => {
      try {
        // 模拟进度增长（实际应从子代理获取）
        lastProgress += Math.floor(Math.random() * 15) + 5;
        if (lastProgress > 100) lastProgress = 100;
        
        await feishuUpdater(messageId, {
          progress: lastProgress,
          elapsed: Date.now()
        });
        
        if (lastProgress >= 100) {
          this.stop(taskId);
        }
      } catch (error) {
        console.error('[Cron] 更新失败:', error);
      }
    }, { scheduled: true });
    
    this.tasks.set(taskId, task);
    return taskId;
  }

  /**
   * 启动日报生成任务
   * @param {Function} reportGenerator - 日报生成函数
   * @param {string} schedule - cron表达式，默认每天9点
   */
  startDailyReport(reportGenerator, schedule = '0 9 * * *') {
    const task = cron.schedule(schedule, async () => {
      console.log('[Cron] 生成日报...');
      try {
        await reportGenerator();
      } catch (error) {
        console.error('[Cron] 日报生成失败:', error);
      }
    }, { scheduled: true, timezone: 'Asia/Shanghai' });
    
    this.tasks.set('daily-report', task);
    console.log('[Cron] 日报任务已启动，每天9:00执行');
    return 'daily-report';
  }

  /**
   * 停止任务
   */
  stop(taskId) {
    const task = this.tasks.get(taskId);
    if (task) {
      task.stop();
      this.tasks.delete(taskId);
      console.log(`[Cron] 停止任务: ${taskId}`);
      return true;
    }
    return false;
  }

  /**
   * 停止所有任务
   */
  stopAll() {
    for (const [taskId, task] of this.tasks) {
      task.stop();
      console.log(`[Cron] 停止任务: ${taskId}`);
    }
    this.tasks.clear();
  }

  /**
   * 启动学习引擎定时任务
   * @param {LearningEngine} learningEngine - 学习引擎实例
   * @param {Function} feishuSender - 飞书发送函数
   * @param {string} schedule - cron表达式，默认每天9点
   */
  startLearningTask(learningEngine, feishuSender = null, schedule = '0 9 * * *') {
    const task = cron.schedule(schedule, async () => {
      console.log('[Cron] 执行每日学习...');
      try {
        const report = await learningEngine.dailyLearning();
        
        // 如果有飞书发送函数，推送报告
        if (feishuSender) {
          const card = learningEngine.buildFeishuCard(report);
          await feishuSender(card);
        }
        
        console.log('[Cron] 每日学习完成');
      } catch (error) {
        console.error('[Cron] 每日学习失败:', error);
      }
    }, { scheduled: true, timezone: 'Asia/Shanghai' });
    
    this.tasks.set('daily-learning', task);
    console.log('[Cron] 学习引擎任务已启动，每天9:00执行');
    return 'daily-learning';
  }

  /**
   * 获取运行中的任务列表
   */
  list() {
    return Array.from(this.tasks.keys());
  }
}

// 单例模式
let instance = null;

function getCronManager() {
  if (!instance) {
    instance = new CronManager();
  }
  return instance;
}

module.exports = {
  CronManager,
  getCronManager
};
