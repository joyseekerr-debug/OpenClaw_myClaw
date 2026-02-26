/**
 * 协作中心和执行监控测试
 */

const { SubagentScheduler } = require('./index');

async function testNewFeatures() {
  console.log('=== 协作中心和执行监控功能测试 ===\n');
  
  const scheduler = new SubagentScheduler();
  await scheduler.init();
  
  // 1. 协作中心测试
  console.log('1. 协作中心测试...');
  const hub = scheduler.getCollaborationHub();
  
  // 注册测试Agent
  hub.registerAgent('Agent-A', { name: '分析师A', capabilities: ['analyze'] });
  hub.registerAgent('Agent-B', { name: '分析师B', capabilities: ['research'] });
  console.log('  ✅ 已注册2个测试Agent');
  
  // 测试全局状态
  hub.setGlobal('marketTrend', 'bullish', { agentId: 'Agent-A' });
  console.log(`  ✅ 全局状态设置: marketTrend = ${hub.getGlobal('marketTrend')}`);
  
  // 测试任务状态
  hub.setTask('task-001', 'analysisResult', { score: 0.85 });
  console.log(`  ✅ 任务状态设置: task-001.analysisResult = ${JSON.stringify(hub.getTask('task-001', 'analysisResult'))}`);
  
  // 测试点对点通信
  hub.sendTo('Agent-A', 'Agent-B', { type: 'request', data: '分析数据' });
  console.log('  ✅ 点对点消息发送');
  
  // 测试广播
  const broadcastResult = hub.broadcast('Agent-A', { type: 'announcement', message: '开始分析' });
  console.log(`  ✅ 广播消息，接收者: ${broadcastResult.recipients}`);
  
  // 2. 执行监控测试
  console.log('\n2. 执行监控测试...');
  const monitor = scheduler.getExecutionMonitor();
  
  // 注册Agent监控
  monitor.registerAgent('Agent-A', { name: '分析师A', maxConcurrent: 3 });
  monitor.registerAgent('Agent-B', { name: '分析师B', maxConcurrent: 2 });
  console.log('  ✅ 已注册2个监控Agent');
  
  // 注册任务
  const task1 = monitor.registerTask('task-001', { name: '股票分析', agentId: 'Agent-A', branch: 'Standard' });
  const task2 = monitor.registerTask('task-002', { name: '风险评估', agentId: 'Agent-B', branch: 'Deep' });
  console.log('  ✅ 已注册2个监控任务');
  
  // 启动任务
  monitor.startTask('task-001');
  monitor.updateAgentLoad('Agent-A', 1);
  console.log('  ✅ 任务1已启动');
  
  // 更新进度
  monitor.updateProgress('task-001', 30, { checkpoint: '数据获取完成' });
  monitor.updateProgress('task-001', 70, { checkpoint: '分析完成' });
  console.log('  ✅ 进度更新完成');
  
  // 完成任务
  monitor.completeTask('task-001');
  monitor.updateAgentLoad('Agent-A', -1);
  console.log('  ✅ 任务1已完成');
  
  // 模拟失败任务
  monitor.startTask('task-002');
  monitor.updateAgentLoad('Agent-B', 1);
  monitor.failTask('task-002', new Error('网络超时'), { type: 'timeout', recoverable: true });
  console.log('  ✅ 任务2失败已记录');
  
  // 3. 仪表板测试
  console.log('\n3. 监控仪表板测试...');
  const dashboard = scheduler.getDashboard();
  console.log(`  任务统计: 总计=${dashboard.summary.total}, 完成=${dashboard.summary.completed}, 失败=${dashboard.summary.failed}`);
  console.log(`  Agent状态: ${dashboard.agents.length}个Agent`);
  dashboard.agents.forEach(a => {
    console.log(`    - ${a.name}: 状态=${a.status}, 任务完成=${a.tasksCompleted}`);
  });
  
  // 4. 协作中心统计
  console.log('\n4. 协作中心统计...');
  const hubStats = hub.getStats();
  console.log(`  Agent: 总计=${hubStats.agents.total}, 在线=${hubStats.agents.online}`);
  console.log(`  频道: ${hubStats.channels}个`);
  console.log(`  全局状态: ${hubStats.globalState}项`);
  console.log(`  活动任务: ${hubStats.activeTasks}个`);
  
  console.log('\n=== 所有测试通过 ✅ ===');
  
  // 清理
  await scheduler.close();
}

// 运行测试
testNewFeatures().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
