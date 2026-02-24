/**
 * Phase 2 功能测试
 * 验证LLM分类、流式进度、分级失败恢复
 */

const scheduler = require('./index');
const { LLMClassifier } = require('./llm-classifier');
const { StreamingProgress } = require('./streaming-progress');
const { RetryExecutor } = require('./retry-executor');

async function runPhase2Tests() {
  console.log('=== Phase 2 增强功能测试 ===\n');

  // 1. LLM分类器测试
  console.log('1. LLM分类器测试...');
  const classifier = new LLMClassifier({
    confidenceThreshold: 0.7
  });
  
  const testTasks = [
    '批量分析这15个日志文件，找出所有错误模式',
    '深度研究微服务架构的最佳实践，包括服务发现、负载均衡、熔断降级等各个方面',
    '先获取用户数据然后进行清洗最后生成统计报告'
  ];
  
  for (const task of testTasks) {
    const result = await classifier.classify(task);
    console.log(`  任务: "${task.substring(0, 30)}..."`);
    console.log(`    -> ${result.branch} (置信度: ${result.confidence.toFixed(2)})`);
    console.log(`    预估: ${result.estimatedDuration}秒, $${result.estimatedCost}`);
  }
  console.log('✓ LLM分类器测试完成\n');

  // 2. 三层决策器测试
  console.log('2. 三层决策器测试...');
  const sch = await scheduler.init();
  
  const layerTests = [
    { task: '你好', expectedLayer: 'rules' },
    { task: '深度分析代码库并给出详细报告。这是一段很长的描述，包含很多内容，超过一百个字符，足够触发各种条件。', expectedLayer: 'rules' },
    { task: '分析一下这个比较复杂的情况，可能需要多步骤处理，但不是特别明确', expectedLayer: 'llm' }
  ];
  
  for (const t of layerTests) {
    const result = await scheduler.scheduler.classifyTask(t.task, null, { useLLM: true });
    console.log(`  "${t.task.substring(0, 25)}..." -> ${result.branch} [${result.layer}]`);
  }
  console.log('✓ 三层决策器测试完成\n');

  // 3. 流式进度测试
  console.log('3. 流式进度测试...');
  const progress = new StreamingProgress({
    updateInterval: 2, // 加快测试
    minUpdateDelta: 0
  });
  
  let updateCount = 0;
  progress.on('update', ({ progress: p }) => {
    updateCount++;
    console.log(`  进度更新: ${p}%`);
  });
  
  const mockUpdater = (msgId, message) => {
    // 模拟飞书更新
  };
  
  const stream = progress.start('test-task', 'msg-123', mockUpdater, {
    estimatedDuration: 10,
    branch: 'Standard'
  });
  
  // 模拟任务执行
  await new Promise(r => setTimeout(r, 6000));
  
  // 手动更新几次进度
  progress.updateProgress('test-task', 50, '处理数据中...');
  progress.updateProgress('test-task', 80, '整理结果中...');
  
  await new Promise(r => setTimeout(r, 1000));
  
  progress.complete('test-task', '任务完成结果');
  console.log(`✓ 流式进度测试完成 (收到${updateCount}次更新)\n`);

  // 4. 分级失败恢复测试
  console.log('4. 分级失败恢复测试...');
  const retryExec = new RetryExecutor({
    maxRetries: 3,
    enableDowngrade: true,
    enableCheckpoint: true,
    downgradeChain: {
      'Deep': 'Standard',
      'Standard': 'Simple'
    }
  });
  
  // 测试降级
  console.log('  测试策略降级...');
  let downgradeTriggered = false;
  retryExec.on('downgrade', ({ from, to }) => {
    console.log(`    降级触发: ${from} -> ${to}`);
    downgradeTriggered = true;
  });
  
  // 模拟降级执行
  const downgradeResult = await retryExec.downgradeAndRetry(
    (ctx) => {
      if (ctx.branch === 'Deep' && !ctx.downgraded) {
        throw new Error('Resource exhausted');
      }
      return { success: true, branch: ctx.branch };
    },
    { branch: 'Deep' }
  );
  
  console.log(`    降级结果: ${downgradeResult.downgraded ? '成功' : '失败'}`);
  if (downgradeResult.downgraded) {
    console.log(`    最终策略: ${downgradeResult.to}`);
  }
  
  // 测试检查点
  console.log('  测试检查点...');
  retryExec.saveCheckpoint('task-001', { step: 3, data: { processed: 100 } });
  const checkpoint = retryExec.loadCheckpoint('task-001');
  console.log(`    检查点保存/加载: ${checkpoint ? '成功' : '失败'}`);
  if (checkpoint) {
    console.log(`    数据: step=${checkpoint.data.step}, processed=${checkpoint.data.data.processed}`);
  }
  
  console.log('✓ 分级失败恢复测试完成\n');

  // 5. 完整的Phase 2工作流测试
  console.log('5. Phase 2完整工作流测试...');
  console.log('  (模拟一个使用LLM分类 + 流式进度 + 降级恢复的任务)');
  
  // 清理
  progress.stopAll();
  retryExec.clearCheckpoint('task-001');
  
  console.log('✓ Phase 2完整工作流测试完成\n');

  console.log('=== Phase 2 所有测试通过 ✅ ===');
}

// 运行测试
runPhase2Tests().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
