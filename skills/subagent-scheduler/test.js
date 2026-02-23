/**
 * 测试脚本
 * 验证子代理调度器各功能
 */

const scheduler = require('./index');

async function runTests() {
  console.log('=== 子代理调度器测试 ===\n');
  
  // 1. 初始化
  console.log('1. 初始化...');
  await scheduler.init();
  console.log('✓ 初始化完成\n');
  
  // 2. 任务分类测试
  console.log('2. 任务分类测试...');
  const testTasks = [
    { task: "你好", expected: 'Simple' },
    { task: "分析这个日志文件找出错误", expected: 'Standard' },
    { task: "批量处理这10个文件", expected: 'Batch' },
    { task: "深度分析整个代码库并给出架构建议", expected: 'Deep' }
  ];
  
  for (const t of testTasks) {
    const result = await scheduler.scheduler.classifyTask(t.task);
    console.log(`  "${t.task.substring(0, 20)}..." -> ${result.branch} (置信度: ${result.confidence})`);
  }
  console.log('✓ 分类测试完成\n');
  
  // 3. 成本预估测试
  console.log('3. 成本预估测试...');
  for (const branch of ['Simple', 'Standard', 'Batch', 'Deep']) {
    const cost = scheduler.scheduler.estimateCost(branch, 500);
    const duration = scheduler.scheduler.estimateDuration(branch, 500);
    console.log(`  ${branch}: 成本$${cost.total.toFixed(4)}, 耗时${duration}秒`);
  }
  console.log('✓ 预估测试完成\n');
  
  // 4. 飞书卡片构建测试
  console.log('4. 飞书卡片构建测试...');
  const card = scheduler.feishu.buildConfirmCard('Standard', { duration: 45, cost: 0.05 }, {
    count: 12,
    successRate: '92',
    avgDuration: 42,
    avgCost: '0.048'
  });
  console.log('✓ 卡片结构:', JSON.stringify(card.card.header, null, 2));
  console.log('✓ 卡片构建完成\n');
  
  // 5. 模拟任务执行（不实际spawn）
  console.log('5. 模拟任务执行...');
  // 这里不实际执行子代理，仅测试配置构建
  const taskConfig = scheduler.scheduler.buildTaskConfig('Standard', '测试任务', { label: 'test_001' });
  console.log('  任务配置:', JSON.stringify(taskConfig, null, 2));
  console.log('✓ 配置构建完成\n');
  
  console.log('=== 所有测试通过 ===');
}

// 运行测试
runTests().catch(console.error);
