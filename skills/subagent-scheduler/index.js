/**
 * 子代理调度器主入口
 * 整合所有模块
 */

const scheduler = require('./scheduler');
const database = require('./database');
const feishu = require('./feishu');
const config = require('./config.json');

/**
 * 初始化调度器
 */
async function init() {
  // 初始化数据库
  database.initDatabase();
  console.log('[SubagentScheduler] 初始化完成');
  return true;
}

/**
 * 执行任务（带飞书确认）
 */
async function executeWithConfirm(taskInput, options = {}) {
  const task = typeof taskInput === 'string' ? taskInput : taskInput.task;
  const chatId = options.chatId || config.feishu.defaultChatId;
  
  // 1. 任务分类
  const classification = await scheduler.classifyTask(task, database);
  const branch = classification.branch;
  
  // 2. Simple分支直接执行（无需确认）
  if (branch === 'Simple') {
    console.log('[SubagentScheduler] Simple分支，直接执行');
    return await scheduler.execute(task, { ...options, forceBranch: 'Simple' });
  }
  
  // 3. 获取估算和历史统计
  const estimation = {
    duration: scheduler.estimateDuration(branch, task.length),
    cost: scheduler.estimateCost(branch, task.length).total
  };
  
  const historyStats = await database.getHistoryStats(branch, 7);
  
  // 4. 发送确认卡片（如果启用）
  if (config.confirmation.enabled) {
    const card = feishu.buildConfirmCard(branch, estimation, historyStats);
    const message = await feishu.sendMessage(chatId, card);
    
    console.log('[SubagentScheduler] 已发送确认卡片，等待用户响应...');
    console.log('[SubagentScheduler] 消息ID:', message.message_id);
    
    // 记录到数据库
    await database.run(
      `INSERT INTO feishu_messages (task_id, message_id, chat_id, msg_type, content_preview)
       VALUES (?, ?, ?, ?, ?)`,
      [scheduler.hashTask(task), message.message_id, chatId, 'card', '确认卡片']
    );
    
    // 注意：实际应用中需要等待用户点击回调
    // 这里模拟用户确认
    console.log('[SubagentScheduler] 模拟用户点击确认...');
  }
  
  // 5. 执行前发送进度消息
  const progressMsg = await feishu.sendMessage(
    chatId, 
    feishu.buildProgressMessage(0, 0)
  );
  
  // 6. 执行子代理
  const startTime = Date.now();
  let lastProgress = 0;
  
  // 模拟进度更新（实际应用中使用Cron轮询）
  const progressInterval = setInterval(async () => {
    lastProgress += 10;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    
    if (lastProgress < 100) {
      await feishu.updateMessage(
        progressMsg.message_id,
        feishu.buildProgressMessage(lastProgress, elapsed)
      );
    }
  }, config.monitoring.progressUpdateInterval * 1000);
  
  // 执行
  const result = await scheduler.execute(task, { 
    ...options, 
    forceBranch: branch,
    db: database 
  });
  
  clearInterval(progressInterval);
  
  // 7. 发送完成消息
  const duration = Math.floor((Date.now() - startTime) / 1000);
  const completeMsg = feishu.buildCompleteMessage(
    result.success,
    duration,
    estimation.cost,
    result.result,
    result.error?.message
  );
  
  await feishu.updateMessage(progressMsg.message_id, completeMsg);
  
  return result;
}

/**
 * 生成日报
 */
async function generateDailyReport(chatId) {
  const dataPath = config.database.path + '.data.json';
  const fs = require('fs');
  
  if (!fs.existsSync(dataPath)) {
    await feishu.sendMessage(chatId, {
      msg_type: 'text',
      content: { text: '暂无历史数据' }
    });
    return;
  }
  
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
  const history = data.task_history || [];
  
  const today = new Date().toISOString().split('T')[0];
  const todayTasks = history.filter(h => h.created_at && h.created_at.startsWith(today));
  
  if (todayTasks.length === 0) {
    await feishu.sendMessage(chatId, {
      msg_type: 'text',
      content: { text: '今日暂无任务' }
    });
    return;
  }
  
  // 统计
  const stats = {
    date: today,
    totalTasks: todayTasks.length,
    totalCost: todayTasks.reduce((sum, h) => sum + (h.actual_cost || 0), 0),
    overallSuccessRate: (todayTasks.filter(h => h.success).length / todayTasks.length * 100).toFixed(1),
    byBranch: {}
  };
  
  // 按分支统计
  todayTasks.forEach(h => {
    if (!stats.byBranch[h.branch]) {
      stats.byBranch[h.branch] = { count: 0, success: 0, totalDuration: 0 };
    }
    stats.byBranch[h.branch].count++;
    if (h.success) stats.byBranch[h.branch].success++;
    stats.byBranch[h.branch].totalDuration += h.duration_ms || 0;
  });
  
  // 计算平均值
  Object.keys(stats.byBranch).forEach(branch => {
    const b = stats.byBranch[branch];
    b.successRate = (b.success / b.count * 100).toFixed(1);
    b.avgDuration = Math.round(b.totalDuration / b.count / 1000);
  });
  
  // 发送日报
  const report = feishu.buildDailyReport(stats);
  await feishu.sendMessage(chatId, report);
}

module.exports = {
  init,
  executeWithConfirm,
  generateDailyReport,
  scheduler,
  database,
  feishu
};
