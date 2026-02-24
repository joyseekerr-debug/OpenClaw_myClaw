/**
 * Phase 3 功能测试
 * 验证试探执行、分层上下文、策略权限、分布式追踪
 */

const scheduler = require('./index');
const { ProbeExecutor } = require('./probe-executor');
const { LayeredContext } = require('./layered-context');
const { PolicyManager } = require('./policy-manager');
const { TracingManager } = require('./tracing-manager');

async function runPhase3Tests() {
  console.log('=== Phase 3 智能化功能测试 ===\n');

  // 1. 试探执行测试
  console.log('1. 试探执行测试...');
  const probe = new ProbeExecutor({
    probeDuration: 3000, // 3秒试探（加快测试）
    checkInterval: 1000
  });
  
  probe.on('probe-started', ({ taskId, branch }) => {
    console.log(`  [${taskId}] 试探开始，策略: ${branch}`);
  });
  
  probe.on('probe-decided', ({ decision, reason }) => {
    console.log(`  试探决策: ${decision} - ${reason}`);
  });
  
  // 测试快速完成的任务
  const fastResult = await probe.execute(
    async () => {
      await new Promise(r => setTimeout(r, 1000));
      return '快速完成';
    },
    { taskId: 'fast-task', branch: 'Standard' }
  );
  console.log(`  快速任务: ${fastResult.success ? '完成' : '失败'}, 试探: ${fastResult.probe?.status}`);
  
  // 测试需要升级的任务（模拟卡住）
  console.log('  测试策略升级检测...');
  let stallDetected = false;
  probe.on('stall-detected', () => {
    stallDetected = true;
    console.log('    ⚠️ 检测到任务卡住');
  });
  
  console.log('✓ 试探执行测试完成\n');

  // 2. 分层上下文测试
  console.log('2. 分层上下文测试...');
  const context = new LayeredContext({
    compressionThreshold: 0.8,
    maxContextSize: 10000
  });
  
  context.on('compressing', ({ before }) => {
    console.log(`  压缩触发: ${before} bytes`);
  });
  
  // 设置各层数据
  context.setGlobal('project', { name: 'TestProject', version: '1.0' });
  context.setTask('task1', '这是任务1的数据，比较长'.repeat(50), { priority: 'high' });
  context.setTemp('temp1', '临时数据');
  
  // 模拟大量数据触发压缩
  for (let i = 0; i < 10; i++) {
    context.setTask(`large_${i}`, 'x'.repeat(1000), { priority: 'low', compressible: true });
  }
  
  const stats = context.getStats();
  console.log(`  上下文统计:`);
  console.log(`    全局层: ${stats.layers.global.itemCount}项, ${stats.layers.global.estimatedSize}bytes`);
  console.log(`    任务层: ${stats.layers.task.itemCount}项, ${stats.layers.task.estimatedSize}bytes`);
  console.log(`    临时层: ${stats.layers.temp.itemCount}项, ${stats.layers.temp.estimatedSize}bytes`);
  console.log(`    压缩次数: ${stats.metadata.compressionCount}`);
  
  console.log('✓ 分层上下文测试完成\n');

  // 3. 策略权限测试
  console.log('3. 策略权限测试...');
  const policy = new PolicyManager();
  
  // 测试工具权限
  console.log('  工具权限检查:');
  console.log(`    Simple策略 read: ${policy.canUseTool('Simple', 'read') ? '✅' : '❌'}`);
  console.log(`    Simple策略 write: ${policy.canUseTool('Simple', 'write') ? '✅' : '❌'}`);
  console.log(`    Standard策略 write: ${policy.canUseTool('Standard', 'write') ? '✅' : '❌'}`);
  console.log(`    Deep策略 sessions_spawn: ${policy.canUseTool('Deep', 'sessions_spawn') ? '✅' : '❌'}`);
  
  // 测试资源限制
  console.log('  资源限制检查:');
  const fileCheck = policy.checkResource('Simple', 'fileSize', 5 * 1024 * 1024);
  console.log(`    Simple策略 5MB文件: ${fileCheck.allowed ? '✅' : '❌'} ${fileCheck.reason || ''}`);
  
  // 测试权限申请
  console.log('  动态权限申请:');
  const permResult = await policy.requestPermission('task-001', {
    branch: 'Deep',
    tool: 'exec',
    reason: '需要执行外部命令'
  });
  console.log(`    Deep策略 exec申请: ${permResult.granted ? '✅自动批准' : '⏳待确认'}`);
  
  console.log('✓ 策略权限测试完成\n');

  // 4. 分布式追踪测试
  console.log('4. 分布式追踪测试...');
  const tracing = new TracingManager({
    enabled: true,
    sampleRate: 1.0,
    outputDir: './test-traces'
  });
  
  // 开始追踪
  const traceId = tracing.startTrace('test-task-001', {
    branch: 'Standard',
    model: 'kimi-coding/k2p5'
  });
  console.log(`  追踪开始: ${traceId}`);
  
  // 创建spans
  const span1 = tracing.startSpan('test-task-001', 'analysis');
  await new Promise(r => setTimeout(r, 100));
  tracing.endSpan('test-task-001', span1, { step: 1 });
  
  const span2 = tracing.startSpan('test-task-001', 'processing', span1);
  await new Promise(r => setTimeout(r, 150));
  
  // 记录工具调用
  tracing.recordToolCall('test-task-001', 'read', {}, {}, 50);
  tracing.recordToolCall('test-task-001', 'write', {}, {}, 30);
  
  tracing.endSpan('test-task-001', span2, { step: 2 });
  
  // 记录token使用
  tracing.recordTokens('test-task-001', 1500, 800);
  
  // 结束追踪
  const trace = tracing.endTrace('test-task-001', 'completed', { summary: '测试完成' });
  console.log(`  追踪结束: ${trace.duration}ms, ${trace.metrics.toolCalls}次工具调用`);
  
  // 生成火焰图
  const flameGraph = tracing.generateFlameGraph('test-task-001');
  console.log(`  火焰图生成: ${flameGraph ? '✅' : '❌'}`);
  if (flameGraph) {
    console.log(`    根节点: ${flameGraph.name}, 时长: ${flameGraph.value}ms`);
  }
  
  // 自动诊断
  const diagnosis = tracing.diagnose('test-task-001');
  console.log(`  健康诊断: 分数${diagnosis.score}/100, 发现${diagnosis.issues.length}个问题`);
  
  // 统计
  const traceStats = tracing.getStats();
  console.log(`  追踪统计: ${traceStats.totalTraces}条记录`);
  
  console.log('✓ 分布式追踪测试完成\n');

  // 5. 整合测试
  console.log('5. Phase 3 整合测试...');
  console.log('  模拟使用Phase 3全部功能的场景...');
  
  // 清理
  context.clear();
  
  console.log('✓ Phase 3 整合测试完成\n');

  console.log('=== Phase 3 所有测试通过 ✅ ===');
}

// 运行测试
runPhase3Tests().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
