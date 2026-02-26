/**
 * 股票交易系统任务规划分析
 */

const { SubagentScheduler } = require('./skills/subagent-scheduler');

async function analyzeTaskComplexity() {
  const scheduler = new SubagentScheduler();
  await scheduler.init();
  
  const task = `深度学习股票交易相关知识，建立系统化结构化的知识网络，能够深入分析公司财报，并能够根据公开信息对未来的财报进行预测，深入了解小米集团主营业务的相关产业现状及发展前景，构建小米集团的个股价格监控以及信息监控系统，能够预测未来一定时间内的价格走势。`;
  
  console.log('═══════════════════════════════════════════════════════════');
  console.log('          股票交易系统 - 任务复杂度分析');
  console.log('═══════════════════════════════════════════════════════════\n');
  
  // 1. 复杂度分析
  const analysis = scheduler.taskDecomposer.analyzeComplexity(task);
  console.log('📊 复杂度分析结果:');
  console.log(`   - 任务字数: ${analysis.length}`);
  console.log(`   - 复杂度评分: ${analysis.complexityScore}/10`);
  console.log(`   - 是否多步骤: ${analysis.hasMultipleSteps}`);
  console.log(`   - 是否深度分析: ${analysis.hasDeepAnalysis}`);
  console.log(`   - 预估子任务: ${analysis.estimatedSubtasks}`);
  console.log(`   - 是否分解: ${analysis.shouldDecompose}`);
  
  // 2. 多Agent判断
  const shouldMultiAgent = await scheduler.shouldUseMultiAgent(task);
  console.log(`\n🤖 多Agent协作建议: ${shouldMultiAgent ? '是' : '否'}`);
  
  // 3. 任务分解
  if (analysis.shouldDecompose) {
    console.log('\n🔄 初步任务分解:');
    // 这里只是演示，实际分解需要更多上下文
    const subtasks = [
      '构建股票交易知识图谱',
      '研究财报分析方法论',
      '开发财报预测模型',
      '研究小米集团产业',
      '构建股价监控系统',
      '开发价格预测算法'
    ];
    
    subtasks.forEach((st, i) => {
      console.log(`   ${i+1}. ${st}`);
    });
  }
  
  console.log('\n═══════════════════════════════════════════════════════════');
  
  return analysis;
}

analyzeTaskComplexity().catch(console.error);
