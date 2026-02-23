/**
 * 完整功能测试
 * 测试所有模块集成
 */

const { SubagentScheduler } = require('./index');

async function runFullTest() {
  console.log('=== 子代理调度器完整功能测试 ===\n');
  
  const scheduler = new SubagentScheduler({
    budget: {
      perTask: 1.0,
      perSession: 10.0,
      perDay: 50.0
    },
    retry: {
      maxRetries: 3,
      baseDelay: 1000
    }
  });
  
  await scheduler.init();
  
  // 测试1: 并发状态
  console.log('1. 测试并发控制...');
  const concurrencyStatus = await scheduler.getConcurrencyStatus();
  console.log('✓ 并发状态:', JSON.stringify(concurrencyStatus, null, 2));
  
  // 测试2: 成本估算
  console.log('\n2. 测试成本监控...');
  const costEstimate = scheduler.costMonitor.estimateCost('Standard', 500);
  console.log('✓ 成本预估:', costEstimate);
  
  const budgetCheck = await scheduler.costMonitor.checkBudget(costEstimate.total);
  console.log('✓ 预算检查:', budgetCheck);
  
  // 测试3: 重试执行器
  console.log('\n3. 测试重试机制...');
  const retryResult = await scheduler.retryExecutor.execute(async () => {
    // 模拟成功
    return '成功结果';
  });
  console.log('✓ 重试执行:', retryResult);
  
  // 测试4: 完整任务执行（模拟）
  console.log('\n4. 测试完整任务执行...');
  const result = await scheduler.execute({
    task: "分析这10个日志文件，找出错误模式",
    chatId: null // 不发送飞书消息
  }, {
    forceBranch: 'Standard'
  });
  
  console.log('✓ 执行结果:', JSON.stringify(result, null, 2));
  
  // 测试5: 历史数据查询
  console.log('\n5. 测试历史数据...');
  const historyStats = await scheduler.db.getHistoryStats('Standard', 7);
  console.log('✓ 历史统计:', historyStats);
  
  // 测试6: Cron管理器
  console.log('\n6. 测试Cron管理器...');
  const { getCronManager } = require('./cron-manager');
  const cronManager = getCronManager();
  console.log('✓ Cron任务列表:', cronManager.list());
  
  // 清理
  await scheduler.close();
  
  console.log('\n=== 所有测试通过 ===');
}

runFullTest().catch(error => {
  console.error('❌ 测试失败:', error);
  console.error(error.stack);
  process.exit(1);
});
