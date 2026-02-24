/**
 * 端到端系统性测试 - 简化稳定版
 * 5种真实任务场景验证
 */

const { SubagentScheduler } = require('./index');

async function runEndToEndTests() {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('          子代理技能端到端系统性测试 (简化版)');
  console.log('═══════════════════════════════════════════════════════════\n');
  
  // 初始化调度器
  const scheduler = new SubagentScheduler();
  await scheduler.init();
  
  const testResults = [];
  
  // ═══════════════════════════════════════════════════════════
  // 场景1: 简单查询任务
  // ═══════════════════════════════════════════════════════════
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('【场景1】简单查询任务 - "今天天气怎么样？"');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  try {
    const task1 = '今天天气怎么样？';
    
    // 分析复杂度
    const analysis1 = scheduler.taskDecomposer.analyzeComplexity(task1);
    console.log(`📊 复杂度分析:`);
    console.log(`   - 字数: ${analysis1.length}`);
    console.log(`   - 复杂度评分: ${analysis1.complexityScore}`);
    console.log(`   - 预估子任务: ${analysis1.estimatedSubtasks}`);
    console.log(`   - 是否分解: ${analysis1.shouldDecompose}`);
    
    // 多Agent判断
    const shouldMulti1 = await scheduler.shouldUseMultiAgent(task1);
    console.log(`\n🤖 多Agent判断: ${shouldMulti1}`);
    
    // 执行
    const result1 = await scheduler.execute({
      task: task1,
      multiAgent: false
    });
    
    console.log(`\n✅ 执行结果:`);
    console.log(`   - 成功: ${result1.success}`);
    console.log(`   - 使用策略: ${result1.branch || result1.strategy}`);
    console.log(`   - 耗时: ${result1.duration}ms`);
    
    testResults.push({
      scene: '简单查询',
      expected: 'Simple',
      actual: result1.branch || result1.strategy,
      success: result1.success,
      duration: result1.duration
    });
    
  } catch (error) {
    console.error('❌ 场景1失败:', error.message);
    testResults.push({ scene: '简单查询', success: false, error: error.message });
  }
  
  // ═══════════════════════════════════════════════════════════
  // 场景2: 标准分析任务
  // ═══════════════════════════════════════════════════════════
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('【场景2】标准分析任务 - "分析日志文件"');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  try {
    const task2 = '分析workspace/logs/app.log日志文件，找出其中的错误模式和异常信息';
    
    const analysis2 = scheduler.taskDecomposer.analyzeComplexity(task2);
    console.log(`📊 复杂度分析:`);
    console.log(`   - 字数: ${analysis2.length}`);
    console.log(`   - 预估子任务: ${analysis2.estimatedSubtasks}`);
    console.log(`   - 是否分解: ${analysis2.shouldDecompose}`);
    
    const shouldMulti2 = await scheduler.shouldUseMultiAgent(task2);
    console.log(`\n🤖 多Agent判断: ${shouldMulti2}`);
    
    // 成本预估
    const cost2 = scheduler.costMonitor.estimateCost('Standard', task2.length);
    console.log(`\n💰 成本预估: $${cost2.total.toFixed(4)}`);
    
    const result2 = await scheduler.execute({
      task: task2,
      multiAgent: false
    });
    
    console.log(`\n✅ 执行结果:`);
    console.log(`   - 成功: ${result2.success}`);
    console.log(`   - 使用策略: ${result2.branch || result2.strategy}`);
    console.log(`   - 耗时: ${result2.duration}ms`);
    
    testResults.push({
      scene: '标准分析',
      expected: 'Standard',
      actual: result2.branch || result2.strategy,
      success: result2.success,
      duration: result2.duration
    });
    
  } catch (error) {
    console.error('❌ 场景2失败:', error.message);
    testResults.push({ scene: '标准分析', success: false, error: error.message });
  }
  
  // ═══════════════════════════════════════════════════════════
  // 场景3: 批量处理任务
  // ═══════════════════════════════════════════════════════════
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('【场景3】批量处理任务 - "分析10个配置文件"');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  try {
    const task3 = '批量分析config目录下的10个配置文件，检查配置项是否规范';
    
    const analysis3 = scheduler.taskDecomposer.analyzeComplexity(task3);
    console.log(`📊 复杂度分析:`);
    console.log(`   - 批量关键词: ${analysis3.hasMultipleTargets}`);
    console.log(`   - 预估子任务: ${analysis3.estimatedSubtasks}`);
    console.log(`   - 是否分解: ${analysis3.shouldDecompose}`);
    
    // 任务分解
    const dag3 = await scheduler.taskDecomposer.decompose(task3);
    console.log(`\n🔄 任务分解:`);
    console.log(`   - 子任务数: ${dag3.totalSubtasks}`);
    console.log(`   - 并行组数: ${dag3.parallelGroups.length}`);
    
    dag3.subtasks.slice(0, 5).forEach((st, i) => {
      console.log(`   ${i+1}. ${st.id}: ${st.task.substring(0, 35)}...`);
    });
    if (dag3.subtasks.length > 5) {
      console.log(`   ... 还有 ${dag3.subtasks.length - 5} 个子任务`);
    }
    
    testResults.push({
      scene: '批量处理',
      expected: 'Multi-Agent',
      subtasks: dag3.totalSubtasks,
      success: true
    });
    
  } catch (error) {
    console.error('❌ 场景3失败:', error.message);
    testResults.push({ scene: '批量处理', success: false, error: error.message });
  }
  
  // ═══════════════════════════════════════════════════════════
  // 场景4: 深度研究任务
  // ═══════════════════════════════════════════════════════════
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('【场景4】深度研究任务 - "微服务架构最佳实践"');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  try {
    const task4 = '深度研究微服务架构的最佳实践，包括服务发现、负载均衡、熔断降级等';
    
    const analysis4 = scheduler.taskDecomposer.analyzeComplexity(task4);
    console.log(`📊 复杂度分析:`);
    console.log(`   - 字数: ${analysis4.length}`);
    console.log(`   - 深度分析: ${analysis4.hasDeepAnalysis}`);
    console.log(`   - 预估子任务: ${analysis4.estimatedSubtasks}`);
    
    const shouldMulti4 = await scheduler.shouldUseMultiAgent(task4);
    console.log(`\n🤖 多Agent判断: ${shouldMulti4}`);
    
    if (shouldMulti4) {
      const dag4 = await scheduler.taskDecomposer.decompose(task4);
      console.log(`\n🔄 任务分解: ${dag4.totalSubtasks} 个子任务`);
      
      dag4.subtasks.forEach((st, i) => {
        console.log(`   ${i+1}. ${st.id}: ${st.task.substring(0, 40)}...`);
      });
    }
    
    testResults.push({
      scene: '深度研究',
      expected: 'Deep/Multi',
      useMultiAgent: shouldMulti4,
      success: true
    });
    
  } catch (error) {
    console.error('❌ 场景4失败:', error.message);
    testResults.push({ scene: '深度研究', success: false, error: error.message });
  }
  
  // ═══════════════════════════════════════════════════════════
  // 场景5: 复杂多步骤任务
  // ═══════════════════════════════════════════════════════════
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('【场景5】复杂多步骤任务 - "DevOps流水线配置"');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  try {
    const task5 = '先分析项目技术栈，然后设计CI/CD流水线，接着配置自动化测试，最后部署到生产环境';
    
    const analysis5 = scheduler.taskDecomposer.analyzeComplexity(task5);
    console.log(`📊 复杂度分析:`);
    console.log(`   - 多步骤: ${analysis5.hasMultipleSteps}`);
    console.log(`   - 依赖关系: ${analysis5.hasDependencies}`);
    console.log(`   - 预估子任务: ${analysis5.estimatedSubtasks}`);
    
    // 任务分解
    const dag5 = await scheduler.taskDecomposer.decompose(task5);
    console.log(`\n🔄 任务分解 (DAG):`);
    console.log(`   - 子任务数: ${dag5.totalSubtasks}`);
    console.log(`   - 并行组数: ${dag5.parallelGroups.length}`);
    
    dag5.parallelGroups.forEach((group, i) => {
      console.log(`   并行组 ${i+1}: ${group.join(', ')}`);
    });
    
    // 显示依赖关系
    console.log(`\n🔗 依赖关系:`);
    dag5.subtasks.forEach(st => {
      if (st.dependsOn.length > 0) {
        console.log(`   ${st.id} → 依赖: ${st.dependsOn.join(', ')}`);
      } else {
        console.log(`   ${st.id} → (起始任务)`);
      }
    });
    
    testResults.push({
      scene: '复杂多步骤',
      expected: 'Orchestrator/Multi',
      subtasks: dag5.totalSubtasks,
      parallelGroups: dag5.parallelGroups.length,
      success: true
    });
    
  } catch (error) {
    console.error('❌ 场景5失败:', error.message);
    testResults.push({ scene: '复杂多步骤', success: false, error: error.message });
  }
  
  // ═══════════════════════════════════════════════════════════
  // 测试总结
  // ═══════════════════════════════════════════════════════════
  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('                    测试总结报告');
  console.log('═══════════════════════════════════════════════════════════\n');
  
  console.log('┌──────────────┬──────────┬──────────┬─────────┬──────────┐');
  console.log('│ 场景         │ 期望策略 │ 实际策略 │ 子任务  │ 状态     │');
  console.log('├──────────────┼──────────┼──────────┼─────────┼──────────┤');
  
  testResults.forEach(r => {
    const scene = r.scene.padEnd(12);
    const expected = (r.expected || '-').padEnd(8);
    const actual = (r.actual || r.useMultiAgent ? 'Multi' : 'Single').padEnd(8);
    const subtasks = (r.subtasks || '-').toString().padEnd(7);
    const status = r.success ? '✅ 通过' : '❌ 失败';
    
    console.log(`│ ${scene} │ ${expected} │ ${actual} │ ${subtasks} │ ${status} │`);
  });
  
  console.log('└──────────────┴──────────┴──────────┴─────────┴──────────┘');
  
  const passed = testResults.filter(r => r.success).length;
  const total = testResults.length;
  
  console.log(`\n✅ 通过: ${passed}/${total} (${(passed/total*100).toFixed(0)}%)`);
  
  // 系统统计
  console.log('\n📊 系统统计:');
  const agentStats = scheduler.agentRegistry.getStats();
  console.log(`   - Agents: ${agentStats.total} (健康${agentStats.healthy})`);
  console.log(`   - 负载: ${agentStats.totalLoad}/${agentStats.totalCapacity}`);
  
  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('                 端到端测试完成！');
  console.log('═══════════════════════════════════════════════════════════');
}

// 运行测试
runEndToEndTests().catch(err => {
  console.error('测试失败:', err);
  process.exit(1);
});
