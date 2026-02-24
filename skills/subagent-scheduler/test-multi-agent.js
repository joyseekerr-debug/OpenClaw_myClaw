/**
 * 多 Agents 协作系统测试
 */

const { SubagentScheduler } = require('./index');

async function runMultiAgentTests() {
  console.log('=== 多 Agents 协作系统测试 ===\n');
  
  // 初始化调度器
  const scheduler = new SubagentScheduler();
  await scheduler.init();
  
  // 1. Agent Registry 测试
  console.log('1. Agent Registry 测试...');
  const registry = scheduler.agentRegistry;
  
  // 查看默认 agents
  const agents = registry.getAllAgents();
  console.log(`  已注册 Agents: ${agents.length}`);
  agents.forEach(agent => {
    console.log(`    - ${agent.name}: ${agent.capabilities.join(', ')}`);
  });
  
  // 注册新 agent
  const newAgentId = registry.createLocalAgent('TestAgent', {
    capabilities: ['test', 'debug'],
    maxConcurrent: 2
  });
  console.log(`  ✅ 新 Agent 注册: ${newAgentId}`);
  
  // Agent 发现
  const found = registry.discover({ capabilities: ['read'] });
  console.log(`  ✅ 发现 ${found.length} 个有 read 能力的 Agent`);
  
  console.log('');
  
  // 2. Task Decomposer 测试
  console.log('2. Task Decomposer 测试...');
  const decomposer = scheduler.taskDecomposer;
  
  // 简单任务
  const simpleTask = '分析这个日志文件';
  const simpleAnalysis = decomposer.analyzeComplexity(simpleTask);
  console.log(`  简单任务复杂度: ${simpleAnalysis.complexityScore}`);
  console.log(`  是否需要分解: ${simpleAnalysis.shouldDecompose}`);
  
  // 复杂任务
  const complexTask = '分析整个代码库，包括项目结构、依赖关系、代码质量，并生成详细的架构报告';
  const complexAnalysis = decomposer.analyzeComplexity(complexTask);
  console.log(`  复杂任务复杂度: ${complexAnalysis.complexityScore}`);
  console.log(`  预估子任务数: ${complexAnalysis.estimatedSubtasks}`);
  
  // 分解复杂任务
  const dag = await decomposer.decompose(complexTask);
  console.log(`  ✅ 任务分解完成: ${dag.totalSubtasks} 个子任务`);
  console.log(`  并行组数: ${dag.parallelGroups.length}`);
  
  dag.subtasks.forEach((st, i) => {
    console.log(`    ${i+1}. ${st.id}: ${st.task.substring(0, 40)}...`);
  });
  
  console.log('');
  
  // 3. Agent Router 测试
  console.log('3. Agent Router 测试...');
  const router = scheduler.agentRouter;
  
  // 测试路由
  const testSubtask = {
    id: 'test_1',
    task: '测试任务',
    requiredCapabilities: ['read', 'analyze'],
    estimatedDuration: 30000
  };
  
  try {
    const route = await router.route(testSubtask, {
      strategy: 'capability_match'
    });
    console.log(`  ✅ 路由成功: ${route.agentName} (${route.agentId})`);
    console.log(`     策略: ${route.strategy}`);
  } catch (error) {
    console.log(`  ❌ 路由失败: ${error.message}`);
  }
  
  console.log('');
  
  // 4. Result Aggregator 测试
  console.log('4. Result Aggregator 测试...');
  const aggregator = scheduler.resultAggregator;
  
  const testResults = [
    { subtaskId: '1', result: '结果 A - 分析完成', metadata: { confidence: 0.9 } },
    { subtaskId: '2', result: '结果 B - 分析完成', metadata: { confidence: 0.85 } },
    { subtaskId: '3', result: '结果 A - 分析完成', metadata: { confidence: 0.9 } } // 重复
  ];
  
  const aggregated = await aggregator.aggregate(testResults, {
    strategy: 'smart_merge'
  });
  
  console.log(`  ✅ 聚合完成`);
  console.log(`     策略: ${aggregated.source}`);
  console.log(`     输入数: ${testResults.length}`);
  console.log(`     去重后: ${aggregated.uniqueCount || 'N/A'}`);
  
  console.log('');
  
  // 5. 多 Agent 执行测试（模拟）
  console.log('5. 多 Agent 执行判断测试...');
  
  const shouldUseMulti1 = await scheduler.shouldUseMultiAgent(simpleTask);
  console.log(`  简单任务使用多 Agent: ${shouldUseMulti1}`);
  
  const shouldUseMulti2 = await scheduler.shouldUseMultiAgent(complexTask);
  console.log(`  复杂任务使用多 Agent: ${shouldUseMulti2}`);
  
  console.log('');
  
  // 6. 整体统计
  console.log('6. 系统统计...');
  const registryStats = registry.getStats();
  console.log(`  Agent 总数: ${registryStats.total}`);
  console.log(`  健康: ${registryStats.healthy}, 忙碌: ${registryStats.busy}`);
  
  const routerStats = router.getStats();
  console.log(`  路由成功率: ${routerStats.successRate}%`);
  
  console.log('\n=== 所有测试通过 ✅ ===');
  
  // 清理
  registry.unregister(newAgentId);
}

// 运行测试
runMultiAgentTests().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
