/**
 * 自动路由功能测试
 */

const { createAutoRouter, TaskComplexityAnalyzer } = require('./auto-router');

async function testAutoRouter() {
  console.log('=== 自动路由功能测试 ===\n');
  
  // 1. 复杂度分析器测试
  console.log('1. 任务复杂度分析测试...');
  const analyzer = new TaskComplexityAnalyzer();
  
  const testTasks = [
    {
      name: '简单查询',
      text: '查询今天的天气'
    },
    {
      name: '中等任务',
      text: '分析这个项目的代码结构，找出主要的模块和依赖关系'
    },
    {
      name: '复杂任务',
      text: '我需要对现有的交易系统进行完整的重构和优化，包括：1）分析当前的性能瓶颈；2）重新设计架构；3）实现新的风控模块；4）编写完整的测试用例；5）生成详细的文档报告。这是一个非常复杂的工程，需要深度分析和多步骤执行。'
    }
  ];
  
  for (const task of testTasks) {
    const analysis = analyzer.analyze(task.text);
    console.log(`  ${task.name}:`);
    console.log(`    复杂度: ${analysis.level} (分数: ${analysis.score})`);
    console.log(`    预估工具: ${analysis.estimatedTools}个`);
    console.log(`    预估时间: ${analysis.estimatedTime}秒`);
    console.log(`    建议分支: ${analysis.suggestedBranch}`);
    console.log(`    使用调度器: ${analysis.shouldUseScheduler ? '是' : '否'}`);
    console.log('');
  }
  
  // 2. 自动路由测试（模拟，不实际执行）
  console.log('2. 自动路由判断测试...');
  const router = createAutoRouter({
    enabled: true,
    confirmThreshold: 'medium',
    chatId: 'test_chat_id'
  });
  
  for (const task of testTasks) {
    const shouldRoute = router.shouldRoute(task.text);
    console.log(`  ${task.name}: ${shouldRoute ? '→ 调度器' : '→ 直接处理'}`);
  }
  
  console.log('\n=== 测试完成 ✅ ===');
  console.log('\n使用说明:');
  console.log('  简单任务 (<100字符, 少量工具) → 直接处理');
  console.log('  中等任务 (100-200字符, 多工具) → 调度器+确认');
  console.log('  复杂任务 (>200字符, 多步骤) → 调度器+确认 (Deep分支)');
}

// 运行测试
testAutoRouter().catch(console.error);
